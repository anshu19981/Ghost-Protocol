#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         GHOST PROTOCOL v11.0 — DEEP RECON ENGINE                ║
║              Bug Bounty Hunter Edition                           ║
╠══════════════════════════════════════════════════════════════════╣
║  FIXED in v10.0 (over v9.0):                                    ║
║  ✔ CRITICAL FIX: phase6 mein live_200 path bug fix              ║
║  ✔ CRITICAL FIX: alterx input — FQDNs nahi, prefixes feed karo  ║
║  ✔ FIX: dnsx threads — hardcoded 100 → THREADS_DNSX var         ║
║  ✔ FIX: gowitness flags — latest v3 API compatible              ║
║  ✔ FIX: 403 bypass bash quoting — proper escaping               ║
║  ✔ FIX: summary resolved path — final vs regular handle karo    ║
║  ✔ FIX: massdns newer output format parsing                     ║
║  ✔ FIX: /tmp race condition — session-unique temp files         ║
║  ✔ FIX: puredns -w vs --write fallback                         ║
║  NEW: Graceful Ctrl+C handler — cleanup on exit                 ║
║  NEW: Per-phase resume markers — crash ke baad wahan se shuru   ║
║  NEW: Scope validation — wildcards + explicit scope file        ║
║  NEW: nuclei auto-update templates before scan                  ║
║  NEW: Rate limit guard — naabu/httpx adaptive throttle          ║
║  NEW: Duplicate-safe merges — sed/awk nahi, Python sets         ║
║  NEW: --dry-run mode — commands print karo, execute mat karo    ║
║  NEW: --phase flag — sirf specific phases run karo              ║
║  NEW: S3/GCS bucket finder (cloud asset enum)                   ║
║  NEW: Param discovery — paramspider integration                 ║
║  NEW: Technology fingerprinting — wappalyzer-go                 ║
║  NEW: HTML report generator — summary.html in output dir        ║
╠══════════════════════════════════════════════════════════════════╣
║  MERGED + WIRED in v11.0 (single-file build):                   ║
║  ✔ GhostConfig — env/.env se proxy, rate-limit, webhook load   ║
║  ✔ StealthEngine — UA rotation + proxy pool + adaptive backoff  ║
║  ✔ SmartNuclei — smart template selection (fast + CVE mode)     ║
║  ✔ Bypass403 — full 19-header + path + verb bypass engine       ║
║  ✔ prioritize_subdomains — admin/api/dev targets pehle          ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MERGED SINGLE-FILE BUILD
# gp_config.py + gp_stealth.py + gp_modules.py — all inlined below
# No separate patch files needed.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from collections import defaultdict, deque
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse
import argparse
import datetime
import hashlib
import heapq
import json
import logging
import os
import random
import re
import requests
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib3


# ══════════════════════════════════════════════════════════════
# SECTION: Config Manager (from gp_config.py)
# ══════════════════════════════════════════════════════════════



# ── Optional dependency — graceful fallback ─────────────────────────────────
try:
    _DOTENV_AVAILABLE = True
except ImportError:
    _DOTENV_AVAILABLE = False


def _load_env():
    """
    Priority order:
      1. .env in CWD
      2. ~/.ghost_protocol/.env
      3. Pure environment variables (already set in shell)
    """
    if not _DOTENV_AVAILABLE:
        return
    for candidate in [Path(".env"), Path.home() / ".ghost_protocol" / ".env"]:
        if candidate.exists():
            load_dotenv(dotenv_path=candidate, override=False)
            return


_load_env()


# ── Proxy Loader ─────────────────────────────────────────────────────────────
def _load_proxy_list() -> list:
    """
    Proxy file format (one per line):
      http://host:port
      http://user:pass@host:port
      socks5://host:port

    BrightData/Oxylabs: env vars se construct karo.
    """
    proxies = []

    # 1. BrightData rotating proxy construct karo
    bd_user = os.getenv("GP_BRIGHTDATA_USER", "")
    bd_pass = os.getenv("GP_BRIGHTDATA_PASS", "")
    bd_host = os.getenv("GP_BRIGHTDATA_HOST", "brd.superproxy.io:22225")
    if bd_user and bd_pass:
        proxies.append(f"http://{bd_user}:{bd_pass}@{bd_host}")

    # 2. Local proxy file se load karo
    proxy_file = os.getenv("GP_PROXY_FILE", "")
    if proxy_file:
        proxy_file = os.path.expanduser(proxy_file)
        if os.path.exists(proxy_file):
            with open(proxy_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        proxies.append(line)

    # 3. Single proxy env var
    single = os.getenv("GP_PROXY", "")
    if single:
        proxies.append(single)

    return proxies


@dataclass
class GhostConfig:
    # Discord
    discord_webhook: str = field(
        default_factory=lambda: os.getenv("GP_DISCORD_WEBHOOK", "")
    )

    # Proxies
    proxies: list = field(default_factory=_load_proxy_list)

    # Rate limit thresholds
    rate_limit_429_backoff: float = float(os.getenv("GP_BACKOFF_429", "30.0"))
    rate_limit_base_delay:  float = float(os.getenv("GP_BASE_DELAY",  "0.3"))
    jitter_range:           tuple = (0.1, 1.2)   # seconds

    # Scan tuning
    max_403_targets:        int   = int(os.getenv("GP_MAX_403",     "100"))
    max_js_scan_targets:    int   = int(os.getenv("GP_MAX_JS",      "300"))
    nuclei_fast_only:       bool  = os.getenv("GP_NUCLEI_FAST_ONLY", "0") == "1"

    # GitHub dorking
    github_token: str = field(
        default_factory=lambda: os.getenv("GP_GITHUB_TOKEN", "")
    )

    # User-Agent pool — extend karna ho to .env mein GP_UA_FILE set karo
    ua_file: str = field(
        default_factory=lambda: os.path.expanduser(
            os.getenv("GP_UA_FILE", "~/.ghost_protocol/user_agents.txt")
        )
    )

    def proxy_dict(self, proxy_url: str) -> dict:
        """requests-compatible proxy dict."""
        return {"http": proxy_url, "https": proxy_url}

    def has_proxies(self) -> bool:
        return bool(self.proxies)

    def dump_safe(self) -> dict:
        """Log karne ke liye safe version — credentials mask karo."""
        safe_proxies = []
        for p in self.proxies:
            parsed = urlparse(p)
            if parsed.password:
                safe_proxies.append(p.replace(parsed.password, "***"))
            else:
                safe_proxies.append(p)
        return {
            "discord_configured": bool(self.discord_webhook),
            "proxy_count":        len(self.proxies),
            "proxies_masked":     safe_proxies,
            "base_delay":         self.rate_limit_base_delay,
            "jitter_range":       self.jitter_range,
            "nuclei_fast_only":   self.nuclei_fast_only,
        }


# Singleton — script mein `from gp_config import cfg` karo
cfg = GhostConfig()


# ══════════════════════════════════════════════════════════════
# SECTION: Stealth Engine (from gp_stealth.py)
# ══════════════════════════════════════════════════════════════




urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("DeepRecon.Stealth")

# ── Real browser User-Agents (sampled from actual traffic) ──────────────────
_USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Firefox macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Safari macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Firefox Linux
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Mobile Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    # Mobile Safari iOS
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

# ── Accept headers matching each browser family ──────────────────────────────
_ACCEPT_HEADERS = {
    "Chrome": {
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Sec-Fetch-Site":  "none",
        "Sec-Fetch-Mode":  "navigate",
        "Sec-Fetch-User":  "?1",
        "Sec-Fetch-Dest":  "document",
        "Upgrade-Insecure-Requests": "1",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    },
    "Firefox": {
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest":  "document",
        "Sec-Fetch-Mode":  "navigate",
        "Sec-Fetch-Site":  "none",
        "Sec-Fetch-User":  "?1",
    },
    "Safari": {
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
}

def _ua_family(ua: str) -> str:
    if "Firefox" in ua:
        return "Firefox"
    if "Safari" in ua and "Chrome" not in ua:
        return "Safari"
    return "Chrome"


# ── Proxy health tracker ──────────────────────────────────────────────────────
class ProxyPool:
    """
    Round-robin proxy rotation with circuit breaker.
    Proxy 3 consecutive failures pe dead mark ho jaata hai — 5 min ke liye skip.
    """
    _DEAD_TIMEOUT = 300   # seconds

    def __init__(self, proxy_list: list):
        self._all    = list(proxy_list)
        self._idx    = 0
        self._fails  = defaultdict(int)    # proxy → consecutive failures
        self._dead_until: dict = {}        # proxy → epoch timestamp
        self._lock   = threading.Lock()

    def get(self) -> Optional[str]:
        """Next healthy proxy return karo. None = no proxy mode."""
        if not self._all:
            return None
        with self._lock:
            now = time.time()
            attempts = len(self._all)
            for _ in range(attempts):
                proxy = self._all[self._idx % len(self._all)]
                self._idx += 1
                dead_until = self._dead_until.get(proxy, 0)
                if now >= dead_until:
                    return proxy
            return None  # all dead — direct connection

    def mark_success(self, proxy: str):
        if proxy:
            self._fails[proxy] = 0
            self._dead_until.pop(proxy, None)

    def mark_failure(self, proxy: str):
        if not proxy:
            return
        with self._lock:
            self._fails[proxy] += 1
            if self._fails[proxy] >= 3:
                self._dead_until[proxy] = time.time() + self._DEAD_TIMEOUT
                logger.warning(f"Proxy dead-listed (3 fails): {proxy[:40]}")
                self._fails[proxy] = 0

    @property
    def healthy_count(self) -> int:
        now = time.time()
        return sum(1 for p in self._all
                   if now >= self._dead_until.get(p, 0))

    @property
    def total(self) -> int:
        return len(self._all)


# ── Per-domain rate state ─────────────────────────────────────────────────────
class _DomainRateState:
    def __init__(self, base_delay: float):
        self.delay      = base_delay
        self.last_req   = 0.0
        self.consecutive_429s = 0
        self.lock       = threading.Lock()


class StealthEngine:
    """
    Requests wrapper with stealth features.
    Use like requests.Session() — .get(), .post(), .request()
    """

    MAX_RETRIES       = 3
    BACKOFF_429_BASE  = 15.0   # seconds — 429 pe pehla wait
    MAX_BACKOFF       = 120.0  # upper cap

    def __init__(
        self,
        proxies: list         = None,
        base_delay: float     = 0.3,
        jitter_range: tuple   = (0.1, 1.2),
        ua_file: str          = "",
        respect_robots: bool  = False,
    ):
        self.base_delay   = base_delay
        self.jitter_range = jitter_range
        self.pool         = ProxyPool(proxies or [])
        self._ua_list     = self._load_uas(ua_file)
        self._domain_state: dict = {}  # domain → _DomainRateState
        self._state_lock  = threading.Lock()
        self._session     = requests.Session()
        self._session.verify = False

    # ── UA management ─────────────────────────────────────────────────────────
    def _load_uas(self, ua_file: str) -> list:
        if ua_file and __import__("os").path.exists(ua_file):
            try:
                with open(ua_file) as f:
                    custom = [l.strip() for l in f if l.strip()]
                if custom:
                    return custom
            except Exception:
                pass
        return list(_USER_AGENTS)

    def _random_ua(self) -> str:
        return random.choice(self._ua_list)

    def _build_headers(self, extra: dict = None) -> dict:
        ua     = self._random_ua()
        family = _ua_family(ua)
        base   = dict(_ACCEPT_HEADERS.get(family, _ACCEPT_HEADERS["Chrome"]))
        base["User-Agent"] = ua
        if extra:
            base.update(extra)
        return base

    # ── Domain rate state ────────────────────────────────────────────────────
    def _get_state(self, domain: str) -> _DomainRateState:
        with self._state_lock:
            if domain not in self._domain_state:
                self._domain_state[domain] = _DomainRateState(self.base_delay)
            return self._domain_state[domain]

    def _throttle(self, domain: str):
        """
        Adaptive throttle:
          - Base delay + jitter between requests
          - 429/503 pe exponential backoff per-domain
        """
        state = self._get_state(domain)
        with state.lock:
            jitter   = random.uniform(*self.jitter_range)
            wait_for = state.delay + jitter
            elapsed  = time.time() - state.last_req
            if elapsed < wait_for:
                time.sleep(wait_for - elapsed)
            state.last_req = time.time()

    def _on_429(self, domain: str):
        state = self._get_state(domain)
        with state.lock:
            state.consecutive_429s += 1
            backoff = min(
                self.BACKOFF_429_BASE * (2 ** (state.consecutive_429s - 1)),
                self.MAX_BACKOFF
            )
            state.delay = min(state.delay * 2, 10.0)  # also slow down base rate
            logger.warning(f"429 on {domain} — backing off {backoff:.0f}s "
                           f"(consecutive: {state.consecutive_429s})")
            time.sleep(backoff)

    def _on_success(self, domain: str):
        state = self._get_state(domain)
        with state.lock:
            state.consecutive_429s = 0
            # Slowly recover base delay toward original
            state.delay = max(state.delay * 0.9, self.base_delay)

    # ── Core request method ──────────────────────────────────────────────────
    def request(
        self,
        method: str,
        url: str,
        headers: dict    = None,
        timeout: int     = 10,
        allow_redirects: bool = True,
        retries: int     = None,
        **kwargs
    ) -> Optional[requests.Response]:

        domain = urlparse(url).netloc or url
        max_retries = retries if retries is not None else self.MAX_RETRIES

        merged_headers = self._build_headers(headers)

        for attempt in range(max_retries + 1):
            proxy = self.pool.get()
            proxy_dict = {"http": proxy, "https": proxy} if proxy else None

            self._throttle(domain)

            try:
                resp = self._session.request(
                    method, url,
                    headers       = merged_headers,
                    proxies       = proxy_dict,
                    timeout       = timeout,
                    verify        = False,
                    allow_redirects = allow_redirects,
                    **kwargs
                )

                if resp.status_code in (429, 503):
                    if proxy:
                        # Proxy ke through bhi 429 aa raha — maybe proxy hi blocked
                        self.pool.mark_failure(proxy)
                    self._on_429(domain)
                    if attempt < max_retries:
                        merged_headers = self._build_headers(headers)  # fresh UA
                        continue
                    return resp

                if proxy:
                    self.pool.mark_success(proxy)
                self._on_success(domain)
                return resp

            except (requests.exceptions.ProxyError,
                    requests.exceptions.SSLError):
                if proxy:
                    self.pool.mark_failure(proxy)
                if attempt < max_retries:
                    continue
                return None

            except requests.exceptions.Timeout:
                logger.debug(f"Timeout on {url} (attempt {attempt+1})")
                if attempt < max_retries:
                    continue
                return None

            except Exception as e:
                logger.debug(f"Request error {url}: {e}")
                return None

        return None

    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request("POST", url, **kwargs)

    def head(self, url: str, **kwargs) -> Optional[requests.Response]:
        return self.request("HEAD", url, **kwargs)

    @property
    def verify(self):
        return self._session.verify

    @verify.setter
    def verify(self, val):
        self._session.verify = val

    def close(self):
        self._session.close()


# ══════════════════════════════════════════════════════════════
# SECTION: Enhancement Modules (from gp_modules.py)
# ══════════════════════════════════════════════════════════════



# ═══════════════════════════════════════════════════════════════
# 1. PRIORITY QUEUE — Interesting subdomains pehle scan karo
# ═══════════════════════════════════════════════════════════════

# Lower score = higher priority (min-heap)
_PRIORITY_KEYWORDS = {
    # Tier 0 — Critical attack surface
    "admin":    0, "administrator": 0, "root":   0,
    "api":      0, "api-v1":  0, "api-v2": 0,
    "dev":      1, "develop": 1, "development": 1, "staging": 1,
    "test":     1, "qa":      1, "uat":    1,
    # Tier 2 — Medium value
    "auth":     2, "login":   2, "sso":    2, "oauth":   2,
    "internal": 2, "corp":    2, "intranet": 2, "vpn":    2,
    "portal":   2, "dashboard": 2, "panel":  2, "manage":  2,
    "git":      2, "gitlab":  2, "github":  2, "bitbucket": 2,
    "jira":     2, "confluence": 2, "jenkins": 2, "ci":    2, "cd": 2,
    "jenkins":  2, "build":   2, "deploy":  2,
    "smtp":     2, "mail":    2, "email":   2,
    "db":       2, "database": 2, "mysql":  2, "postgres": 2, "redis": 2,
    "s3":       2, "storage": 2, "cdn":     2, "static":  3,
    "backup":   2, "bak":     2, "old":     3, "archive": 3,
    # Tier 3 — Lower priority
    "www":      4, "www2":    4, "web":     4,
    "blog":     5, "shop":    5, "store":   5,
    "media":    5, "img":     5, "assets":  5,
}


def prioritize_subdomains(subdomains: list) -> list:
    """
    Subdomains ko priority order mein sort karo.
    Interesting ones (admin, api, dev) pehle scan honge.
    Returns: sorted list (highest priority first)
    """
    heap = []
    for sub in subdomains:
        prefix = sub.split(".")[0].lower().strip("-")
        # Exact match first, then prefix match
        score = _PRIORITY_KEYWORDS.get(prefix, 6)
        # Tiebreak: alphabetical
        heapq.heappush(heap, (score, sub))

    return [sub for _, sub in sorted(heap)]


# ═══════════════════════════════════════════════════════════════
# 2. SMART NUCLEI — Template categories
# ═══════════════════════════════════════════════════════════════

class SmartNuclei:
    """
    Nuclei templates ko categories mein divide karo.
    
    FAST_IMPACT  → High yield, low noise — default mein run
    DEEP_SCAN    → Slow/noisy — --deep flag pe hi run
    SKIP_ALWAYS  → Too noisy/FP-heavy for bug bounty
    """

    # Fast, high-signal templates — always run karo
    FAST_IMPACT_TAGS = [
        "cve",              # CVE-based detection — high signal
        "exposures",        # sensitive file exposure
        "misconfiguration", # default creds, misconfigs
        "takeover",         # subdomain takeover
        "default-login",    # default credentials
        "exposed-panels",   # admin panels
        "tokens",           # exposed API tokens/secrets
        "xss",              # reflected XSS (fast)
        "sqli",             # SQLi detection
        "ssrf",             # SSRF
        "lfi",              # LFI
        "open-redirect",    # open redirects
        "xxe",              # XXE
        "rce",              # RCE (critical)
        "fileupload",       # file upload vulns
        "deserialization",  # deserialization
    ]

    # Slow / noisy — deep scan mode mein hi use karo
    DEEP_SCAN_TAGS = [
        "fuzzing",          # generic fuzzing — bohot requests
        "bruteforce",       # brute force — time + rate limit heavy
        "dos",              # denial of service — never run in BB
        "network",          # network-level scans — slow
        "dns",              # DNS scans — slow
        "ssl",              # TLS/SSL scans — low-yield in BB
    ]

    # Skip completely — too noisy or BB-irrelevant
    SKIP_TAGS = [
        "dos",              # don't DoS targets
        "bruteforce",       # too many requests
        "intrusive",        # might break things
    ]

    # High-priority CVE patterns worth running always (recent, critical)
    PRIORITY_CVE_TEMPLATES = [
        "CVE-2021-44228",  # Log4Shell
        "CVE-2021-26855",  # Exchange SSRF
        "CVE-2022-22965",  # Spring4Shell
        "CVE-2023-44487",  # HTTP/2 rapid reset
        "CVE-2021-21985",  # VMware vCenter RCE
        "CVE-2022-26134",  # Confluence RCE
        "CVE-2023-23397",  # Outlook zero-click
        "CVE-2024-21887",  # Ivanti RCE
        "CVE-2024-1709",   # ConnectWise CVSS 10
    ]

    def __init__(self, rate_limit: str = "150", deep: bool = False):
        self.rate_limit = rate_limit
        self.deep = deep

    def build_cmd(self, targets_file: str, output_file: str,
                  severity: str = "critical,high,medium") -> str:
        """
        Smart Nuclei command build karo.
        Fast mode: focused tags, higher rate
        Deep mode:  all templates, lower rate (polite)
        """
        if self.deep:
            # Deep scan: sab templates, slower
            skip_tags = ",".join(self.SKIP_TAGS)
            return (
                f"nuclei -l {targets_file} "
                f"-severity {severity} "
                f"-etags {skip_tags} "
                f"-rl {self.rate_limit} "
                f"-silent -no-color "
                f"-o {output_file}"
            )
        else:
            # Fast scan: only high-yield tags
            fast_tags = ",".join(self.FAST_IMPACT_TAGS)
            skip_tags = ",".join(self.SKIP_TAGS)
            # Custom templates folder — apne templates auto-load
            import os as _os
            custom_flag = (
                f"-t {NUCLEI_CUSTOM_TEMPLATES} "
                if _os.path.isdir(NUCLEI_CUSTOM_TEMPLATES) else ""
            )
            return (
                f"nuclei -l {targets_file} "
                f"-severity {severity} "
                f"-tags {fast_tags} "
                f"-etags {skip_tags} "
                f"{custom_flag}"
                f"-rl {self.rate_limit} "
                f"-silent -no-color "
                f"-o {output_file}"
            )

    def build_cve_cmd(self, targets_file: str, output_file: str) -> str:
        """
        Recent critical CVEs ke liye targeted scan.
        Fast + high-value.
        """
        template_ids = ",".join(self.PRIORITY_CVE_TEMPLATES)
        return (
            f"nuclei -l {targets_file} "
            f"-id {template_ids} "
            f"-rl {self.rate_limit} "
            f"-silent -no-color "
            f"-o {output_file}"
        )


# ═══════════════════════════════════════════════════════════════
# 3. ADVANCED 403 BYPASS
# ═══════════════════════════════════════════════════════════════

class Bypass403:
    """
    Advanced 403 bypass techniques.
    
    Techniques covered:
      ✔ Header-based IP spoofing (14 headers)
      ✔ Path manipulation (URL encoding, case, traversal)
      ✔ HTTP method override
      ✔ Verb tampering
      ✔ Protocol header tricks
      ✔ Double URL encoding
    """

    # ── Header-based bypasses ─────────────────────────────────────────────
    SPOOF_HEADERS = [
        # IP spoofing headers
        {"X-Forwarded-For":          "127.0.0.1"},
        {"X-Forwarded-For":          "127.0.0.1, 127.0.0.2"},
        {"X-Real-IP":                "127.0.0.1"},
        {"X-Originating-IP":         "127.0.0.1"},
        {"X-Remote-IP":              "127.0.0.1"},
        {"X-Remote-Addr":            "127.0.0.1"},
        {"X-Client-IP":              "127.0.0.1"},
        {"X-Custom-IP-Authorization":"127.0.0.1"},
        {"X-Host":                   "127.0.0.1"},
        {"X-Forwarded-Host":         "127.0.0.1"},
        # URL override headers
        {"X-Original-URL":           "/"},
        {"X-Rewrite-URL":            "/"},
        {"X-Override-URL":           "/"},
        # Misc
        {"X-ProxyUser-Ip":           "127.0.0.1"},
        {"X-HTTP-Method-Override":   "PUT"},  # verb tamper
        {"X-Forwarded-Proto":        "https"},
        # Referer trick — some WAFs whitelist internal referers
        {"Referer":                  "https://127.0.0.1/"},
        # Admin path tricks via header
        {"X-Original-URL":           "/admin"},
        {"X-Rewrite-URL":            "/admin"},
    ]

    # ── Path-based bypasses ───────────────────────────────────────────────
    @staticmethod
    def _path_variants(url: str) -> list:
        """
        Given a URL, generate path-mutated variants.
        """
        parsed  = urlparse(url)
        path    = parsed.path or "/"
        base    = path.rstrip("/")
        if not base:
            base = ""

        def build(p: str) -> str:
            return urlunparse(parsed._replace(path=p))

        variants = [
            # Double slash
            build(f"/{base.lstrip('/')}//"),
            # Dot slash
            build(f"/{base.lstrip('/')}/./"),
            # Trailing dot
            build(f"{base}."),
            # Semicolon trick (Tomcat/JBoss)
            build(f"{base};/"),
            # Null byte trick
            build(f"{base}%00"),
            # Double URL encode slash
            build(f"%2f{base.lstrip('/')}"),
            build(f"/{base.lstrip('/')}%2f"),
            # Unicode overlong encoding
            build(f"/{base.lstrip('/')}%ef%bc%8f"),
            # Path traversal wrapping
            build(f"/..;/{base.lstrip('/')}"),
            build(f"/./{base.lstrip('/')}"),
            # Case switching (uppercase first letter)
            build(f"/{base.lstrip('/').capitalize()}"),
            build(f"/{base.lstrip('/').upper()}"),
            # Double path encoding
            build(f"/{base.lstrip('/').replace('/', '%252f')}"),
            # Alternate encoding
            build(f"/{base.lstrip('/')}%20"),
        ]
        return variants

    # ── HTTP verb tampering ───────────────────────────────────────────────
    HTTP_VERBS = ["HEAD", "OPTIONS", "TRACE", "PUT", "POST", "PATCH"]

    @classmethod
    def run(
        cls,
        targets_file: str,
        output_file: str,
        engine: "StealthEngine",
        max_targets: int = 100,
        timeout: int     = 8,
    ) -> int:
        """
        Full 403 bypass sweep.
        Returns: number of bypasses found.
        """
        urls = []
        try:
            with open(targets_file) as f:
                urls = [l.strip() for l in f if l.strip()][:max_targets]
        except FileNotFoundError:
            return 0

        bypassed = []

        for url in urls:
            found = cls._try_url(url, engine, timeout)
            if found:
                bypassed.extend(found)
                print(f"      {Fore.RED}{'─'*3} 403 BYPASS FOUND: {url}")
                for b in found:
                    print(f"          {Fore.RED}{b}")

        if bypassed:
            with open(output_file, "w") as f:
                f.write("\n".join(bypassed) + "\n")

        return len(bypassed)

    @classmethod
    def _try_url(
        cls,
        url: str,
        engine: "StealthEngine",
        timeout: int
    ) -> list:
        found = []

        # ── 1. Header-based ───────────────────────────────────────────────
        for hdr in cls.SPOOF_HEADERS:
            try:
                r = engine.get(url, headers=hdr, timeout=timeout,
                               allow_redirects=False, retries=0)
                if r and r.status_code == 200:
                    hname = list(hdr.keys())[0]
                    hval  = list(hdr.values())[0]
                    found.append(f"HEADER [{hname}: {hval}] → {url}")
                    break  # First win enough for this URL
            except Exception:
                continue
            # Small jitter between attempts
            time.sleep(random.uniform(0.05, 0.2))

        if found:
            return found  # Already bypassed via header — skip path tests

        # ── 2. Path manipulation ──────────────────────────────────────────
        for variant in cls._path_variants(url):
            try:
                r = engine.get(variant, timeout=timeout,
                               allow_redirects=False, retries=0)
                if r and r.status_code == 200:
                    found.append(f"PATH [{variant}] → {url}")
                    break
            except Exception:
                continue
            time.sleep(random.uniform(0.03, 0.15))

        if found:
            return found

        # ── 3. HTTP Verb tampering ────────────────────────────────────────
        for verb in cls.HTTP_VERBS:
            try:
                r = engine.request(verb, url, timeout=timeout,
                                   allow_redirects=False, retries=0)
                if r and r.status_code == 200:
                    found.append(f"VERB [{verb}] → {url}")
                    break
            except Exception:
                continue

        return found


# ══════════════════════════════════════════════════════════════
# SECTION: Main Engine (ghost_protocol_v11.py)
# ══════════════════════════════════════════════════════════════

init(autoreset=True)

# ─── CONFIGURATION ─────────────────────────────────────────────────────────────
THREADS_HTTPX        = "100"
THREADS_GOWITNESS    = "5"
THREADS_NAABU        = "500"
THREADS_DNSX         = "100"   # FIX: was hardcoded in dnsx calls
MAX_DOMAINS_PARALLEL = 2       # 16GB RAM ke liye safe
KATANA_DEPTH         = 3
NUCLEI_RATE_LIMIT    = "150"
NUCLEI_AUTO_UPDATE   = True    # templates auto-update karo

# ── Bruteforce Settings ────────────────────────────────────────────────────────
WORDLIST_CANDIDATES = [
    os.path.expanduser("~/wordlists/subdomains-top1million-110000.txt"),
    "/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt",
    "/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt",
    "/usr/share/wordlists/dnsmap.txt",
    os.path.expanduser("~/wordlists/dns_wordlist.txt"),
]
BRUTE_THREADS        = "100"
RESOLVERS_FILE       = os.path.expanduser("~/wordlists/resolvers.txt")
RESOLVERS_FALLBACK   = ["8.8.8.8", "1.1.1.1", "9.9.9.9", "208.67.222.222"]
RECURSIVE_BRUTE      = True
RECURSIVE_TOP_N      = 10
VHOST_BRUTE          = True
VHOST_WORDLIST       = "/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt"
PERMUTATION_ENGINE   = True

# ── Cloud Enum ────────────────────────────────────────────────────────────────
CLOUD_ENUM_ENABLED   = True
S3_WORDLIST_COUNT    = 100   # Top N permutations for S3/GCS bucket bruteforce

# ── Param Discovery ───────────────────────────────────────────────────────────
PARAM_DISCOVERY      = True

# Discord webhook URL — cfg se aata hai (.env GP_DISCORD_WEBHOOK)
DISCORD_WEBHOOK_URL  = cfg.discord_webhook

# Non-standard ports
NAABU_PORTS = "80,81,443,591,2082,2087,2095,8000,8008,8080,8443,8888,9000,9090,10000"

# GF patterns
GF_PATTERNS = {
    "xss":          "evidence/xss.txt",
    "ssrf":         "evidence/ssrf.txt",
    "sqli":         "evidence/sqli.txt",
    "redirect":     "evidence/open_redirect.txt",
    "lfi":          "evidence/lfi.txt",
    "rce":          "evidence/rce.txt",
    "idor":         "evidence/idor.txt",
    "debug_logic":  "evidence/debug.txt",
    "ssti":         "evidence/ssti.txt",
    "cors":         "evidence/cors_params.txt",
}

# Nuclei custom templates folder — apne templates yahan rakho
NUCLEI_CUSTOM_TEMPLATES = os.path.expanduser("~/.ghost_protocol/templates")

# Required tools
REQUIRED_TOOLS = [
    "subfinder", "assetfinder", "httpx",
    "nuclei", "katana", "gf", "dnsx",
    "naabu", "gau",
]
# Optional tools
OPTIONAL_TOOLS = [
    "amass", "waybackurls", "subjs", "corsy", "subzy",
    "puredns", "shuffledns", "alterx", "ffuf", "massdns",
    "gowitness", "paramspider", "wappalyzergo", "cloud_enum",
    "asnmap",
]

INTERESTING_PORTS = {
    "8080": "Alt HTTP / Dev server",
    "8443": "Alt HTTPS",
    "8888": "Jupyter / Dev panel",
    "9090": "Prometheus / Grafana",
    "9000": "PHP-FPM / SonarQube",
    "81":   "Alt HTTP",
    "10000":"Webmin panel",
    "2082": "cPanel HTTP",
    "2087": "WHM / cPanel",
    "2095": "cPanel Webmail",
    "591":  "FileMaker Alt",
    "8000": "Django / Dev server",
    "8008": "Alt HTTP",
}
STANDARD_PORTS = {"80", "443"}

# Phase names — resume ke liye markers
PHASE_MARKERS = {
    "enum":      ".phase1_done",
    "recursive": ".phase1b_done",
    "probe":     ".phase2_done",
    "history":   ".phase3_done",
    "scan":      ".phase4_done",
    "js":        ".phase5_done",
    "mine":      ".phase6_done",
    "cloud":     ".phase7_done",
    "github":    ".phase8_done",
    "takeover":  ".phase9_done",
    "asn":       ".phase10_done",
    "jsdiff":    ".phase11_done",
}

DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


# ─── SIGNAL HANDLER ────────────────────────────────────────────────────────────
_CLEANUP_DIRS: list = []

def _signal_handler(sig, frame):
    print(f"\n{Fore.RED}[!] Interrupted! Cleaning up temp files...{Style.RESET_ALL}")
    for d in _CLEANUP_DIRS:
        try:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT,  _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


# ─── LOGGING SETUP ─────────────────────────────────────────────────────────────
def setup_logger(log_file: str) -> logging.Logger:
    logger = logging.getLogger("DeepRecon")
    logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logger.addHandler(fh)
    return logger


# ─── SCOPE VALIDATOR ───────────────────────────────────────────────────────────
class ScopeValidator:
    """
    Scope file format (one per line):
      *.example.com      → wildcard subdomain
      example.com        → exact match + all subs
      !internal.example.com  → explicit exclusion
    """
    def __init__(self, scope_file: str = ""):
        self.patterns: list  = []
        self.exclusions: list = []
        if scope_file and os.path.exists(scope_file):
            self._load(scope_file)

    def _load(self, path: str):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                raw = line[1:] if line.startswith("!") else line
                cleaned = raw.lstrip("*.").lower().rstrip(".")
                if not DOMAIN_RE.match(cleaned):
                    continue
                if line.startswith("!"):
                    self.exclusions.append(cleaned)
                else:
                    self.patterns.append(cleaned)

    def in_scope(self, domain: str) -> bool:
        if not self.patterns:
            return True   # no scope file = everything in scope
        domain = domain.lower().strip()
        for excl in self.exclusions:
            if domain == excl or domain.endswith(f".{excl}"):
                return False
        for pat in self.patterns:
            if domain == pat or domain.endswith(f".{pat}"):
                return True
        return False


# ─── MAIN CLASS ────────────────────────────────────────────────────────────────
class DeepRecon:
    def __init__(self, target_file: str, scope_file: str = "",
                 dry_run: bool = False, phases: list = None,
                 skip_nuclei_update: bool = False,
                 output_dir: str = "",
                 force: bool = False):
        self.targets      = self._load_targets(target_file)
        self.session_id   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        self.base_dir     = os.path.abspath(output_dir) if output_dir else f"DEEP_RECON_{self.session_id}"
        self.dry_run      = dry_run
        self.phases       = phases or list(PHASE_MARKERS.keys())
        self._passive_mode = "recursive" not in self.phases and "probe" not in self.phases
        self.scope        = ScopeValidator(scope_file)
        self.skip_nupdate = skip_nuclei_update
        self.force        = force
        self._http        = StealthEngine(
            proxies      = cfg.proxies,
            base_delay   = cfg.rate_limit_base_delay,
            jitter_range = cfg.jitter_range,
        )

        os.makedirs(self.base_dir, exist_ok=True)
        self.logger   = setup_logger(f"{self.base_dir}/recon.log")
        self.wordlist = self._detect_wordlist()
        self.resolvers = self._detect_resolvers()
        self.available = self._check_tools()

        # FIX: session-unique temp dir — no /tmp race conditions
        self._tmpdir = tempfile.mkdtemp(prefix=f"gp_{self.session_id}_")
        _CLEANUP_DIRS.append(self._tmpdir)

        if self.dry_run:
            print(f"{Fore.YELLOW}[DRY RUN MODE] Commands will be printed, not executed.\n")

    # ── Helpers ─────────────────────────────────────────────────────────────────
    def _normalize_domain(self, value: str) -> str:
        """Strict domain normalization to reduce command injection risk."""
        d = value.strip().lower().rstrip(".")
        if not DOMAIN_RE.match(d):
            raise ValueError(f"Invalid domain in targets/scope: {value}")
        return d

    def _safe_dirname(self, value: str) -> str:
        """Filesystem-safe directory name."""
        return re.sub(r"[^a-zA-Z0-9._-]", "_", value)

    def _q(self, value: str) -> str:
        """Shell-safe quoting helper."""
        return shlex.quote(str(value))

    def _load_targets(self, file_path: str) -> list:
        if not os.path.exists(file_path):
            print(f"{Fore.RED}[!] Error: {file_path} not found.")
            sys.exit(1)
        targets = []
        with open(file_path) as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    targets.append(self._normalize_domain(line))
                except ValueError as e:
                    print(f"{Fore.YELLOW}[~] Skipping unsafe target: {e}")
        if not targets:
            print(f"{Fore.RED}[!] targets.txt empty hai.")
            sys.exit(1)
        return sorted(set(targets))

    def _tmpfile(self, name: str) -> str:
        """Session-unique temp file path."""
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", name)
        return os.path.join(self._tmpdir, safe)

    def _detect_wordlist(self) -> str:
        for w in WORDLIST_CANDIDATES:
            if os.path.exists(w):
                print(f"{Fore.GREEN}[✔] Wordlist: {w}")
                return w
        print(f"{Fore.YELLOW}[~] Wordlist nahi mili — bruteforce skip hoga.")
        return ""

    def _detect_resolvers(self) -> str:
        # 1. Pehle check karo — file already hai
        if os.path.exists(RESOLVERS_FILE) and os.path.getsize(RESOLVERS_FILE) > 100:
            count = sum(1 for _ in open(RESOLVERS_FILE))
            self.logger.info(f"Resolvers: {RESOLVERS_FILE} ({count} entries)")
            return RESOLVERS_FILE

        # 2. Auto-download — trickest resolvers list (best quality, ~10k resolvers)
        print(f"{Fore.YELLOW}  [~] resolvers.txt nahi mili — auto-download kar rahe hain...")
        os.makedirs(os.path.expanduser("~/wordlists"), exist_ok=True)
        RESOLVER_URLS = [
            "https://raw.githubusercontent.com/trickest/resolvers/main/resolvers.txt",
            "https://raw.githubusercontent.com/janmasarik/resolvers/master/resolvers.txt",
        ]
        for url in RESOLVER_URLS:
            try:
                r = requests.get(url, timeout=30)
                if r.status_code == 200 and len(r.text) > 500:
                    with open(RESOLVERS_FILE, "w") as f:
                        f.write(r.text)
                    count = r.text.strip().count("\n") + 1
                    print(f"{Fore.GREEN}  [✔] Resolvers downloaded: {count} entries → {RESOLVERS_FILE}")
                    return RESOLVERS_FILE
            except Exception as e:
                self.logger.warning(f"Resolver download failed ({url}): {e}")
                continue

        # 3. Fallback — sirf 4 IPs se kaam chalao (slow but works)
        print(f"{Fore.YELLOW}  [~] Download failed — fallback resolvers use kar rahe hain (slow)")
        tmp = os.path.join(tempfile.gettempdir(), f"gp_resolvers_{os.getpid()}.txt")
        with open(tmp, "w") as f:
            f.write("\n".join(RESOLVERS_FALLBACK) + "\n")
        return tmp

    def _check_tools(self) -> dict:
        """Tool availability dict return karo — crash nahi, gracefully skip karo."""
        print(f"{Fore.YELLOW}[~] Checking tools...")
        available = {}
        missing_req = []
        for t in REQUIRED_TOOLS:
            found = bool(shutil.which(t))
            available[t] = found
            if not found:
                missing_req.append(t)
        for t in OPTIONAL_TOOLS:
            available[t] = bool(shutil.which(t))

        if missing_req:
            print(f"{Fore.RED}[!] MISSING (required): {', '.join(missing_req)}")
            print(f"{Fore.RED}    Install karke dobara chalao. Exiting.")
            sys.exit(1)

        opt_miss = [t for t in OPTIONAL_TOOLS if not available[t]]
        if opt_miss:
            print(f"{Fore.YELLOW}[~] Optional (will skip): {', '.join(opt_miss)}")

        brute_ok = available.get("puredns") or available.get("shuffledns") or available.get("massdns")
        if not brute_ok:
            print(f"{Fore.YELLOW}[~] puredns/shuffledns/massdns — none found, bruteforce skip.")

        print(f"{Fore.GREEN}[✔] Tool check done.\n")
        return available

    def run_cmd(self, cmd: str, msg: str = None, output_file: str = None,
                timeout: int = 900, append: bool = True,
                allow_exit_codes: tuple = (0,)) -> str:
        """Execute shell command. Returns stdout."""
        if msg:
            print(f"{Fore.CYAN}  [*] {msg}...")
        self.logger.debug(f"CMD: {cmd}")

        if self.dry_run:
            print(f"{Fore.MAGENTA}  [DRY] {cmd}")
            return ""

        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode not in allow_exit_codes:
                self.logger.warning(f"Exit {result.returncode}: {cmd}\n{result.stderr[:300]}")
            if output_file and result.stdout:
                mode = "a" if append else "w"
                with open(output_file, mode) as f:
                    f.write(result.stdout)
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            self.logger.error(f"TIMEOUT ({timeout}s): {cmd}")
            print(f"{Fore.YELLOW}  [!] Timeout: {msg or cmd[:60]}")
            return ""
        except Exception as e:
            self.logger.error(f"EXCEPTION [{cmd}]: {e}")
            return ""

    def run_cmd_list(self, args: list, msg: str = None, timeout: int = 900,
                     allow_exit_codes: tuple = (0,)) -> str:
        """Execute command safely without shell interpolation."""
        if msg:
            print(f"{Fore.CYAN}  [*] {msg}...")
        shown = " ".join(shlex.quote(str(x)) for x in args)
        self.logger.debug(f"CMD_LIST: {shown}")

        if self.dry_run:
            print(f"{Fore.MAGENTA}  [DRY] {shown}")
            return ""

        try:
            result = subprocess.run(
                args, capture_output=True, text=True, timeout=timeout, check=False
            )
            if result.returncode not in allow_exit_codes:
                self.logger.warning(f"Exit {result.returncode}: {shown}\n{result.stderr[:300]}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            self.logger.error(f"TIMEOUT ({timeout}s): {shown}")
            print(f"{Fore.YELLOW}  [!] Timeout: {msg or shown[:60]}")
            return ""
        except Exception as e:
            self.logger.error(f"EXCEPTION [{shown}]: {e}")
            return ""

    def file_has_content(self, path: str) -> bool:
        return bool(path) and os.path.exists(path) and os.path.getsize(path) > 0

    def count_lines(self, path: str) -> int:
        if not self.file_has_content(path):
            return 0
        try:
            with open(path) as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def _write_unique_sorted_lines(self, path: str, values: list):
        uniq = sorted({v.strip() for v in values if v and v.strip()})
        with open(path, "w") as f:
            if uniq:
                f.write("\n".join(uniq) + "\n")

    def notify_discord(self, message: str):
        if not DISCORD_WEBHOOK_URL:
            return
        try:
            requests.post(
                DISCORD_WEBHOOK_URL,
                json={"content": f"🚨 **GHOST PROTOCOL ALERT**\n```{message}```"},
                timeout=10
            )
        except Exception as e:
            self.logger.warning(f"Discord notify failed: {e}")

    def _phase_done_marker(self, d_dir: str, phase: str) -> str:
        return os.path.join(d_dir, PHASE_MARKERS.get(phase, f".{phase}_done"))

    def _phase_enabled(self, phase: str) -> bool:
        return phase in self.phases

    def _phase_is_done(self, d_dir: str, phase: str) -> bool:
        return os.path.exists(self._phase_done_marker(d_dir, phase))

    def _mark_phase_done(self, d_dir: str, phase: str):
        with open(self._phase_done_marker(d_dir, phase), "w") as f:
            f.write(datetime.datetime.now().isoformat())

    def is_already_scanned(self, domain: str) -> bool:
        return os.path.exists(f"{self.base_dir}/{self._safe_dirname(domain)}/.scan_complete")

    def mark_scan_complete(self, domain: str, d_dir: str):
        with open(f"{d_dir}/.scan_complete", "w") as f:
            f.write(datetime.datetime.now().isoformat())

    def phase_timer(self, name: str) -> float:
        print(f"\n{Fore.YELLOW}  ── {name} ──")
        return time.time()

    def phase_done(self, t0: float):
        print(f"{Fore.CYAN}      ⏱  {round(time.time()-t0, 1)}s")

    def _merge_unique(self, *paths: str, out: str):
        """
        FIX: Python-based unique merge instead of shell sort -u
        Handles encoding issues + newline variations safely.
        FIX v2: out file pehle read karo (agar paths mein hai), phir overwrite karo
        """
        seen = set()
        lines_out = []
        for path in paths:
            # out file bhi paths mein ho sakti hai — safe read
            try:
                if not os.path.exists(path) or os.path.getsize(path) == 0:
                    continue
                with open(path, encoding="utf-8", errors="replace") as fin:
                    for line in fin:
                        line = line.strip()
                        if line and line not in seen:
                            seen.add(line)
                            lines_out.append(line)
            except Exception as e:
                self.logger.warning(f"Merge error for {path}: {e}")
        # Sab read hone ke baad write karo
        with open(out, "w") as fout:
            for line in lines_out:
                fout.write(line + "\n")
        return len(seen)

    # ── DNS resolve kar ke sirf domain names nikalo ───────────────────────────
    def extract_domains_from_dnsx(self, dnsx_out: str, clean_file: str):
        """
        FIX: dnsx multiple output formats handle karo:
          domain.com [IP]         (older dnsx)
          domain.com              (plain)
          domain.com. [A] [IP]    (verbose mode)
        """
        domains = set()
        if not self.file_has_content(dnsx_out):
            return
        with open(dnsx_out, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Pehla token — domain
                token = line.split()[0].rstrip(".")
                # Basic sanity: valid domain chars only
                if token and re.match(r'^[a-zA-Z0-9._-]+$', token):
                    domains.add(token.lower())
        with open(clean_file, "w") as f:
            f.write("\n".join(sorted(domains)) + "\n")

    def _extract_httpx_200_urls(self, live_file: str, out_file: str):
        urls = []
        if self.file_has_content(live_file):
            with open(live_file, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line or "[200]" not in line:
                        continue
                    parts = line.split()
                    if parts:
                        urls.append(parts[0])
        self._write_unique_sorted_lines(out_file, urls)

    def _extract_nonstandard_live_entries(self, live_file: str, out_file: str):
        matched = []
        if self.file_has_content(live_file):
            with open(live_file, encoding="utf-8", errors="replace") as f:
                for line in f:
                    item = line.strip()
                    if not item or "[200]" not in item:
                        continue
                    url = item.split()[0]
                    port = self._extract_port_from_url(url)
                    if port not in STANDARD_PORTS:
                        matched.append(item)
        self._write_unique_sorted_lines(out_file, matched)

    def _extract_403_urls(self, live_file: str, out_file: str):
        urls = []
        if self.file_has_content(live_file):
            with open(live_file, encoding="utf-8", errors="replace") as f:
                for line in f:
                    item = line.strip()
                    if not item or "[403]" not in item:
                        continue
                    parts = item.split()
                    if parts:
                        urls.append(parts[0])
        self._write_unique_sorted_lines(out_file, urls)

    # ── Nuclei template update ────────────────────────────────────────────────
    def _update_nuclei_templates(self):
        if self.skip_nupdate or not NUCLEI_AUTO_UPDATE:
            return
        print(f"{Fore.CYAN}  [*] Nuclei templates update karo...")
        self.run_cmd("nuclei -update-templates -silent", timeout=120)

    # ─── PHASE 1: SUBDOMAIN ENUMERATION ────────────────────────────────────────
    def phase1_subdomain_enum(self, domain: str, d_dir: str) -> str:
        phase = "enum"
        if not self._phase_enabled(phase):
            return self._get_resolved_path(d_dir)
        if not self.force and self._phase_is_done(d_dir, phase):
            print(f"{Fore.YELLOW}  [~] Phase 1 already done, skipping.")
            return self._get_resolved_path(d_dir)

        t0  = self.phase_timer("PHASE 1: SUBDOMAIN ENUMERATION")
        raw = f"{d_dir}/raw_subs.txt"
        resolved_raw = f"{d_dir}/resolved_dnsx.txt"
        resolved     = f"{d_dir}/resolved_subs.txt"

        # ── 1a. Passive Enumeration ──
        print(f"{Fore.CYAN}  [*] 1a. Passive enum (crt.sh + subfinder + assetfinder + amass)...")
        self.get_crt_sh(domain, raw)

        sf_tmp = self._tmpfile(f"sf_{domain}.txt")
        self.run_cmd(f"subfinder -d {self._q(domain)} -silent -all -o {self._q(sf_tmp)}")
        self._merge_unique(raw, sf_tmp, out=raw)

        self.run_cmd(f"assetfinder --subs-only {self._q(domain)}", output_file=raw)

        if self.available.get("amass"):
            self.run_cmd(f"amass enum -passive -d {self._q(domain)} -silent", output_file=raw)

        if self.file_has_content(raw):
            with open(raw, encoding="utf-8", errors="replace") as f:
                self._write_unique_sorted_lines(raw, [line.strip() for line in f])
        passive_count = self.count_lines(raw)
        print(f"      Passive subdomains: {Fore.GREEN}{passive_count}")

        # ── 1b. Active Bruteforcing ──
        brute_out = f"{d_dir}/brute_subs.txt"
        if self._passive_mode:
            print(f"{Fore.YELLOW}  [~] 1b. Bruteforce skip (passive mode)")
            Path(brute_out).touch()
        elif self.wordlist:
            print(f"{Fore.CYAN}  [*] 1b. Subdomain bruteforcing...")
            self._run_brute(domain, brute_out)
            brute_count = self.count_lines(brute_out)
            print(f"      Brute subdomains: {Fore.GREEN}{brute_count}")
            total = self._merge_unique(raw, brute_out, out=raw)
            print(f"      After merge: {Fore.GREEN}{total}")
        else:
            print(f"{Fore.YELLOW}  [~] 1b. Bruteforce skip (wordlist nahi mili)")

        # ── 1c. Permutation Bruteforcing (alterx) ──
        perm_out = f"{d_dir}/perm_subs.txt"
        if PERMUTATION_ENGINE and self.available.get("alterx"):
            print(f"{Fore.CYAN}  [*] 1c. Permutation bruteforcing (alterx)...")
            self._run_permutation(domain, raw, d_dir, perm_out)
            perm_count = self.count_lines(perm_out)
            print(f"      Permutation subs: {Fore.GREEN}{perm_count}")
            self._merge_unique(raw, perm_out, out=raw)
        else:
            if PERMUTATION_ENGINE:
                print(f"{Fore.YELLOW}  [~] 1c. Permutation skip (alterx not found)")

        # ── 1d. DNS Resolution ──
        total_raw = self.count_lines(raw)
        print(f"{Fore.CYAN}  [*] 1d. DNS resolution ({total_raw} candidates)...")
        self.run_cmd(
            f"dnsx -l {self._q(raw)} -silent -a -t {THREADS_DNSX} -o {self._q(resolved_raw)}",
        )
        self.extract_domains_from_dnsx(resolved_raw, resolved)
        resolved_count = self.count_lines(resolved)
        dead = total_raw - resolved_count
        print(f"      Resolved: {Fore.GREEN}{resolved_count} "
              f"({Fore.RED}-{dead} wildcards/dead{Fore.WHITE})")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, phase)
        return resolved

    def _get_resolved_path(self, d_dir: str) -> str:
        """FIX: Correct resolved path — final ya regular, jo bhi exist kare."""
        final = f"{d_dir}/resolved_subs_final.txt"
        regular = f"{d_dir}/resolved_subs.txt"
        return final if self.file_has_content(final) else regular

    def _run_brute(self, domain: str, out_file: str):
        """puredns → shuffledns → massdns fallback chain."""
        wl = self.wordlist
        if not wl:
            return

        if self.available.get("puredns"):
            cmd = (
                f"puredns bruteforce {self._q(wl)} {self._q(domain)} "
                f"-r {self._q(self.resolvers)} "
                f"--threads {BRUTE_THREADS} "
                f"-q "
                f"-w {self._q(out_file)}"
            )
            out = self.run_cmd(cmd, "puredns bruteforce")
            # puredns v2 might print to stdout
            if not self.file_has_content(out_file) and out:
                with open(out_file, "w") as f:
                    f.write(out)
            # FIX: puredns silent fail — fallback to shuffledns if output still empty
            if self.file_has_content(out_file):
                return
            self.logger.warning("puredns produced no output — falling back to shuffledns/massdns")

        if self.available.get("shuffledns"):
            cmd = (
                f"shuffledns -d {self._q(domain)} -w {self._q(wl)} "
                f"-r {self._q(self.resolvers)} "
                f"-t {BRUTE_THREADS} "
                f"-silent "
                f"-o {self._q(out_file)}"
            )
            self.run_cmd(cmd, "shuffledns bruteforce")
            if self.file_has_content(out_file):
                return

        if self.available.get("massdns"):
            self._brute_via_massdns(domain, wl, out_file)
        elif not self.available.get("puredns") and not self.available.get("shuffledns"):
            print(f"{Fore.YELLOW}      [~] No brute tool found. Skip.")

    def _brute_via_massdns(self, domain: str, wordlist: str, out_file: str):
        """
        FIX: massdns newer versions — output format changed.
        -o S = simple text: fqdn A ip  (some versions use JSON)
        """
        tmp_fqdn = self._tmpfile(f"fqdn_{domain}.txt")
        tmp_out  = self._tmpfile(f"massdns_{domain}.txt")

        if self.file_has_content(wordlist):
            with open(wordlist, encoding="utf-8", errors="replace") as fin, open(tmp_fqdn, "w") as fout:
                for line in fin:
                    prefix = line.strip()
                    if not prefix:
                        continue
                    if not re.match(r"^[a-z0-9-]{1,63}$", prefix, re.IGNORECASE):
                        continue
                    fout.write(f"{prefix}.{domain}\n")
        self.run_cmd(
            f"massdns -r {self._q(self.resolvers)} -t A -o S {self._q(tmp_fqdn)} -w {self._q(tmp_out)} --quiet",
            "massdns bruteforce"
        )
        resolved = []
        if self.file_has_content(tmp_out):
            with open(tmp_out, encoding="utf-8", errors="replace") as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts:
                        continue
                    host = parts[0].rstrip(".").lower()
                    if host == domain or host.endswith(f".{domain}"):
                        resolved.append(host)
        self._write_unique_sorted_lines(out_file, resolved)

    def _run_permutation(self, domain: str, known_subs: str, d_dir: str, out_file: str):
        """
        FIX: alterx needs subdomain PREFIXES, not FQDNs.
        Input: api, dev, staging  (nahi: api.example.com)
        """
        perm_raw     = self._tmpfile(f"perm_raw_{domain}.txt")
        perm_resolved = self._tmpfile(f"perm_resolved_{domain}.txt")

        # FIX: Extract just prefixes (strip domain suffix)
        prefix_file = self._tmpfile(f"prefixes_{domain}.txt")
        if self.file_has_content(known_subs):
            with open(known_subs) as fin, open(prefix_file, "w") as fout:
                for line in fin:
                    line = line.strip().lower()
                    if not line:
                        continue
                    # Strip domain suffix to get prefix
                    prefix = line.replace(f".{domain}", "").replace(domain, "")
                    prefix = prefix.strip(".")
                    if prefix and "." not in prefix:  # only simple prefixes
                        fout.write(prefix + "\n")

        if not self.file_has_content(prefix_file):
            self.logger.info("No prefixes for alterx — skipping permutation")
            return

        self.run_cmd(
            f"alterx -enrich -silent -d {self._q(domain)} -l {self._q(prefix_file)} -o {self._q(perm_raw)}",
            "alterx permutations"
        )

        perm_raw_count = self.count_lines(perm_raw)
        if not perm_raw_count:
            return
        print(f"      Permutations generated: {Fore.GREEN}{perm_raw_count}")

        if self.available.get("puredns"):
            self.run_cmd(
                f"puredns resolve {self._q(perm_raw)} -r {self._q(self.resolvers)} -q -w {self._q(out_file)}",
                "Resolving permutations (puredns)"
            )
        elif self.available.get("shuffledns"):
            self.run_cmd(
                f"shuffledns -list {self._q(perm_raw)} -r {self._q(self.resolvers)} -t {BRUTE_THREADS} "
                f"-silent -o {self._q(out_file)}",
                "Resolving permutations (shuffledns)"
            )
        else:
            self.run_cmd(
                f"dnsx -l {self._q(perm_raw)} -silent -a -t {THREADS_DNSX} -o {self._q(perm_resolved)}",
            )
            self.extract_domains_from_dnsx(perm_resolved, out_file)

    # ── PHASE 1b: RECURSIVE BRUTEFORCE ────────────────────────────────────────
    def phase1b_recursive_brute(self, domain: str, d_dir: str, resolved: str) -> str:
        if not RECURSIVE_BRUTE or not self.wordlist or not self._phase_enabled("recursive"):
            return resolved

        if not self.force and self._phase_is_done(d_dir, "recursive"):
            print(f"{Fore.YELLOW}  [~] Phase 1b already done, skipping.")
            return self._get_resolved_path(d_dir)

        t0 = self.phase_timer("PHASE 1b: RECURSIVE BRUTEFORCING")
        print(f"      Top {RECURSIVE_TOP_N} subdomains pe recursive brute...")

        top_subs = []
        if self.file_has_content(resolved):
            with open(resolved) as f:
                all_subs = [l.strip() for l in f if l.strip()]
            # prioritize_subdomains — admin/api/dev wale pehle
            top_subs = prioritize_subdomains(all_subs)[:RECURSIVE_TOP_N]

        recursive_all = f"{d_dir}/recursive_subs.txt"

        for sub in top_subs:
            # FIX: unique temp file per subdomain using session tmpdir
            safe_sub = re.sub(r"[^a-zA-Z0-9_-]", "_", sub)
            sub_out  = self._tmpfile(f"rec_{safe_sub}.txt")
            self._run_brute(sub, sub_out)
            if self.file_has_content(sub_out):
                count = self.count_lines(sub_out)
                if count > 0:
                    print(f"      {Fore.GREEN}+{count}{Fore.WHITE} → {sub}")
                # Scope check before merging
                valid_lines = []
                with open(sub_out) as f:
                    for line in f:
                        line = line.strip()
                        if line and self.scope.in_scope(line):
                            valid_lines.append(line)
                if valid_lines:
                    with open(recursive_all, "a") as f:
                        f.write("\n".join(valid_lines) + "\n")

        if self.file_has_content(recursive_all):
            merged = f"{d_dir}/resolved_subs_final.txt"
            total = self._merge_unique(resolved, recursive_all, out=merged)
            rec_count = self.count_lines(recursive_all)
            print(f"      Recursive new subs: {Fore.GREEN}{rec_count} | Total: {Fore.GREEN}{total}")
            self.phase_done(t0)
            self._mark_phase_done(d_dir, "recursive")
            return merged

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "recursive")
        return resolved

    # ── PHASE 2: PORT SCAN + PROBING ──────────────────────────────────────────
    def phase2_port_and_probe(self, domain: str, d_dir: str, resolved: str) -> tuple:
        if not self._phase_enabled("probe"):
            return f"{d_dir}/live.txt", f"{d_dir}/live_200.txt"
        if not self.force and self._phase_is_done(d_dir, "probe"):
            live_file = f"{d_dir}/live.txt"
            live_200  = f"{d_dir}/live_200.txt"
            return live_file, live_200

        t0 = self.phase_timer("PHASE 2: PORT SCAN + PORT-WISE PROBING")
        port_file = f"{d_dir}/open_ports.txt"
        ports_dir = f"{d_dir}/ports"
        os.makedirs(ports_dir, exist_ok=True)

        # ── 2a. Port Scanning ────────────────────────────────────────────────
        self.run_cmd(
            f"naabu -l {resolved} -p {NAABU_PORTS} -silent "
            f"-t {THREADS_NAABU} -o {port_file}",
            "Port scanning (naabu)"
        )
        total_open = self.count_lines(port_file)
        print(f"      Open port:host combos: {Fore.GREEN}{total_open}")

        # ── 2b. Port-wise Breakdown ───────────────────────────────────────────
        port_map: dict = {}
        if self.file_has_content(port_file):
            with open(port_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or ":" not in line:
                        continue
                    parts = line.rsplit(":", 1)
                    if len(parts) == 2:
                        host, port = parts[0].strip(), parts[1].strip()
                        if port.isdigit():
                            port_map.setdefault(port, []).append(host)

        port_summary_file = f"{d_dir}/port_summary.txt"
        print(f"\n{Fore.YELLOW}      ── Port Breakdown ──")
        with open(port_summary_file, "w") as psf:
            psf.write(f"Port breakdown for {domain}\n{'='*50}\n\n")
            for port in sorted(port_map.keys(), key=lambda x: int(x) if x.isdigit() else 9999):
                hosts = sorted(set(port_map[port]))
                count = len(hosts)
                label = INTERESTING_PORTS.get(port, "")
                is_std = port in STANDARD_PORTS

                per_port_file = f"{ports_dir}/hosts_port_{port}.txt"
                with open(per_port_file, "w") as ppf:
                    ppf.write("\n".join(hosts) + "\n")

                if not is_std and port in INTERESTING_PORTS:
                    color, flag = Fore.RED, " ◄ INTERESTING"
                elif not is_std:
                    color, flag = Fore.YELLOW, ""
                else:
                    color, flag = Fore.WHITE, ""

                desc = f"  ({label})" if label else ""
                print(f"      {color}:{port}{desc}{flag}{Fore.WHITE}  — {count} host(s)")
                for h in hosts[:5]:
                    print(f"          {Fore.CYAN}{h}")
                if count > 5:
                    print(f"          {Fore.CYAN}... aur {count-5} aur")

                psf.write(f"Port {port}{desc} — {count} hosts{flag}\n")
                for h in hosts:
                    psf.write(f"  {h}\n")
                psf.write("\n")

        # ── 2c. httpx Probe ──────────────────────────────────────────────────
        live_file = f"{d_dir}/live.txt"
        live_200  = f"{d_dir}/live_200.txt"
        input_for_httpx = port_file if self.file_has_content(port_file) else resolved

        self.run_cmd(
            f"httpx -l {self._q(input_for_httpx)} -silent -t {THREADS_HTTPX} "
            f"-sc -td -title -web-server -content-length -cdn -follow-redirects "
            f"-o {self._q(live_file)}",
            "HTTP probing (all ports)"
        )

        # FIX: live_200 — httpx output format: URL [SC] [...]
        self._extract_httpx_200_urls(live_file, live_200)

        live_count = self.count_lines(live_file)
        ok_count   = self.count_lines(live_200)
        print(f"\n      Live responses: {Fore.GREEN}{live_count}")
        print(f"      200 OK:         {Fore.GREEN}{ok_count}")

        # ── 2d. Per-port live files ───────────────────────────────────────────
        print(f"\n{Fore.YELLOW}      ── Live Services by Port ──")
        port_live: dict = {}
        if self.file_has_content(live_file):
            with open(live_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    url_part = line.split()[0]
                    detected_port = self._extract_port_from_url(url_part)
                    port_live.setdefault(detected_port, []).append(line)

        for port, entries in sorted(port_live.items(),
                                     key=lambda x: int(x[0]) if x[0].isdigit() else 9999):
            port_live_file = f"{ports_dir}/live_port_{port}.txt"
            with open(port_live_file, "w") as f:
                f.write("\n".join(e.split()[0] for e in entries) + "\n")

            ok_entries = [e for e in entries if "[200]" in e]
            label = INTERESTING_PORTS.get(port, "")
            desc  = f" ({label})" if label else ""
            flag  = f"{Fore.RED} ◄◄" if port in INTERESTING_PORTS and port not in STANDARD_PORTS else ""

            print(f"      :{port}{desc}{flag}{Fore.WHITE}  "
                  f"— {Fore.GREEN}{len(entries)}{Fore.WHITE} live, "
                  f"{Fore.GREEN}{len(ok_entries)}{Fore.WHITE} x 200 OK")

            if port not in STANDARD_PORTS and entries:
                for e in entries[:3]:
                    parts = e.split()
                    url   = parts[0]
                    sc    = parts[1] if len(parts) > 1 else ""
                    title = " ".join(parts[3:]) if len(parts) > 3 else ""
                    sc_color = (Fore.GREEN if "[200]" in sc
                                else Fore.YELLOW if "[30" in sc
                                else Fore.RED)
                    print(f"          {Fore.CYAN}{url} {sc_color}{sc}{Fore.WHITE} {title}")

        # ── 2e. Non-standard port 200 OK — Discord alert ─────────────────────
        nonstd_live = f"{d_dir}/nonstandard_live.txt"
        if self.file_has_content(live_file):
            self._extract_nonstandard_live_entries(live_file, nonstd_live)
            ns_count = self.count_lines(nonstd_live)
            if ns_count > 0:
                print(f"\n{Fore.RED}      🎯 NON-STANDARD PORT LIVE: {ns_count}")
                self.notify_discord(
                    f"[{domain}] {ns_count} non-standard port services! See {nonstd_live}"
                )

        # ── 2f. VHost Bruteforce ─────────────────────────────────────────────
        if VHOST_BRUTE and self.file_has_content(live_200):
            self._run_vhost_brute(domain, d_dir, live_200)

        # ── 2g. Technology Fingerprinting ────────────────────────────────────
        if self.available.get("wappalyzergo") and self.file_has_content(live_200):
            self.run_cmd(
                f"wappalyzergo -f {live_200} -o {d_dir}/evidence/technologies.json 2>/dev/null",
                "Technology fingerprinting"
            )

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "probe")
        return live_file, live_200

    def _extract_port_from_url(self, url: str) -> str:
        """URL se port extract karo."""
        try:
            p = urlparse(url)
            if p.port:
                return str(p.port)
            return "443" if p.scheme == "https" else "80"
        except Exception:
            return "80"

    def _run_vhost_brute(self, domain: str, d_dir: str, live_200: str):
        """
        FIX: ffuf output parsing improved, proper JSON handling.
        """
        if not self.available.get("ffuf"):
            print(f"{Fore.YELLOW}      [~] ffuf not found, vhost skip.")
            return

        wl = VHOST_WORDLIST if os.path.exists(VHOST_WORDLIST) else self.wordlist
        if not wl:
            return

        evidence = f"{d_dir}/evidence"
        vhost_out = f"{evidence}/vhosts.txt"
        print(f"{Fore.CYAN}  [*] VHost bruteforce (ffuf)...")

        targets = []
        if self.file_has_content(live_200):
            with open(live_200) as f:
                targets = [l.strip() for l in f if l.strip()][:5]

        found_total = 0
        for target in targets:
            tmp_out = self._tmpfile(f"vhost_{hashlib.md5(target.encode()).hexdigest()[:8]}.json")
            self.run_cmd(
                f"ffuf -u {target} -H 'Host: FUZZ.{domain}' "
                f"-w {wl} -mc 200,301,302,403 "
                f"-fs 0 -t 50 -s "
                f"-o {tmp_out} -of json 2>/dev/null",
            )
            if self.file_has_content(tmp_out):
                try:
                    with open(tmp_out) as jf:
                        data = json.load(jf)
                    results = data.get("results", [])
                    for r in results:
                        vhost = r.get("input", {}).get("FUZZ", "")
                        if vhost and self.scope.in_scope(f"{vhost}.{domain}"):
                            with open(vhost_out, "a") as vf:
                                vf.write(f"{vhost}.{domain}\n")
                    found_total += len(results)
                except (json.JSONDecodeError, KeyError) as e:
                    self.logger.warning(f"ffuf JSON parse error: {e}")

        if found_total > 0:
            print(f"{Fore.RED}      🏠 VHOSTS: {found_total}")
            self.notify_discord(f"[{domain}] {found_total} virtual hosts!")
        else:
            print(f"      VHosts: none found")

    # ── PHASE 3: HISTORICAL URLS ───────────────────────────────────────────────
    def phase3_historical_urls(self, domain: str, d_dir: str) -> str:
        if not self._phase_enabled("history"):
            return f"{d_dir}/historical_urls.txt"
        if not self.force and self._phase_is_done(d_dir, "history"):
            return f"{d_dir}/historical_urls.txt"

        t0 = self.phase_timer("PHASE 3: HISTORICAL URLS")
        hist_file = f"{d_dir}/historical_urls.txt"

        self.run_cmd(
            f"gau {domain} --mc 200,301,302 --threads 5 -o {hist_file}",
            "GAU"
        )
        if self.available.get("waybackurls"):
            wb = self.run_cmd_list(["waybackurls", domain], "Waybackurls")
            if wb:
                mode = "a" if self.file_has_content(hist_file) else "w"
                with open(hist_file, mode) as f:
                    f.write(wb + "\n")

        if self.file_has_content(hist_file):
            with open(hist_file, encoding="utf-8", errors="replace") as f:
                self._write_unique_sorted_lines(hist_file, [line.strip() for line in f])
        print(f"      Historical URLs: {Fore.GREEN}{self.count_lines(hist_file)}")
        self.phase_done(t0)
        self._mark_phase_done(d_dir, "history")
        return hist_file

    # ── PHASE 4: SCAN + CRAWL ─────────────────────────────────────────────────
    def phase4_scan_crawl(self, domain: str, d_dir: str, live_200: str, hist_file: str) -> str:
        if not self._phase_enabled("scan"):
            return f"{d_dir}/all_endpoints.txt"
        if not self.force and self._phase_is_done(d_dir, "scan"):
            return f"{d_dir}/all_endpoints.txt"

        t0 = self.phase_timer("PHASE 4: SCAN + CRAWL")
        evidence  = f"{d_dir}/evidence"
        endpoints = f"{d_dir}/endpoints.txt"

        # Nuclei templates update (once per session)
        if not hasattr(self, "_nuclei_updated"):
            self._update_nuclei_templates()
            self._nuclei_updated = True

        # Nuclei — SmartNuclei se smart command build karo
        _nuclei = SmartNuclei(rate_limit=NUCLEI_RATE_LIMIT, deep=False)
        nuclei_cmd = _nuclei.build_cmd(
            targets_file=self._q(live_200),
            output_file=f"{evidence}/vulns.txt",
            severity="critical,high,medium"
        )
        # Priority CVEs bhi alag run karo
        nuclei_cve_cmd = _nuclei.build_cve_cmd(
            targets_file=self._q(live_200),
            output_file=f"{evidence}/vulns_cve.txt"
        )
        self.run_cmd(nuclei_cmd, "Nuclei smart scan (critical/high/medium)")
        self.run_cmd(nuclei_cve_cmd, "Nuclei priority CVEs")
        vuln_count = self.count_lines(f"{evidence}/vulns.txt") + self.count_lines(f"{evidence}/vulns_cve.txt")
        if vuln_count > 0:
            print(f"{Fore.RED}      🔥 VULNS: {vuln_count}")
            self.notify_discord(f"[{domain}] Nuclei: {vuln_count} critical/high!")

        # Katana crawl
        self.run_cmd(
            f"katana -list {live_200} -jc -d {KATANA_DEPTH} -kf all -silent -o {endpoints}",
            f"Katana (depth={KATANA_DEPTH})"
        )

        # Merge endpoints + historical
        merged = f"{d_dir}/all_endpoints.txt"
        total = self._merge_unique(endpoints, hist_file, out=merged)
        print(f"      Total endpoints: {Fore.GREEN}{total}")

        # Screenshots
        # FIX: gowitness v3 API — old --disable-db flag removed
        if self.available.get("gowitness"):
            gowitness_cmd = (
                f"gowitness scan file -f {live_200} "
                f"--threads {THREADS_GOWITNESS} "
                f"--screenshot-path {evidence}/screenshots"
            )
            # Fallback for older gowitness
            result = self.run_cmd_list(["gowitness", "--version"])
            if result and "v2" in result.lower():
                gowitness_cmd = (
                    f"gowitness file -f {live_200} "
                    f"--threads {THREADS_GOWITNESS} "
                    f"--screenshot-path {evidence}/screenshots --disable-db"
                )
            self.run_cmd(gowitness_cmd, "Screenshots (gowitness)")

        # Subdomain Takeover
        if self.available.get("subzy"):
            resolved_path = self._get_resolved_path(d_dir)
            self.run_cmd(
                f"subzy run --targets {resolved_path} --hide-fails "
                f"--output {evidence}/takeover.txt",
                "Subdomain Takeover (subzy)"
            )
            tc = self.count_lines(f"{evidence}/takeover.txt")
            if tc > 0:
                print(f"{Fore.RED}      💀 TAKEOVER: {tc}")
                self.notify_discord(f"[{domain}] {tc} takeover candidates!")
        else:
            print(f"{Fore.YELLOW}      [~] subzy not found — takeover skip.")

        # Param Discovery
        if PARAM_DISCOVERY and self.available.get("paramspider") and self.file_has_content(live_200):
            self._run_param_discovery(domain, d_dir, live_200, merged)

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "scan")
        return merged

    def _run_param_discovery(self, domain: str, d_dir: str, live_200: str, merged: str):
        """paramspider se parameter discovery."""
        print(f"{Fore.CYAN}  [*] Param discovery (paramspider)...")
        param_out = f"{d_dir}/evidence/params.txt"
        self.run_cmd(
            f"paramspider -d {domain} --quiet -o {param_out} 2>/dev/null",
            timeout=300
        )
        if self.file_has_content(param_out):
            total = self._merge_unique(merged, param_out, out=merged)
            print(f"      After param discovery: {Fore.GREEN}{total} endpoints")

    def _extract_subjs_urls(self, live_200: str, js_urls: str):
        js_raw = self.run_cmd(
            f"subjs -i {self._q(live_200)} -c 20",
            "Extracting JS URLs",
            allow_exit_codes=(0, 1)
        )
        if not js_raw:
            # Compatibility fallback for older subjs builds
            js_raw = self.run_cmd(
                f"cat {self._q(live_200)} | subjs -c 20",
                "Extracting JS URLs (fallback)",
                allow_exit_codes=(0, 1)
            )
        values = js_raw.splitlines() if js_raw else []
        self._write_unique_sorted_lines(js_urls, values)

    def _hunt_js_secrets_python(self, js_urls_file: str, out_file: str):
        """Python-based JS secret hunt to avoid shell/xargs injection."""
        regex = re.compile(
            r'(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|'
            r'password|passwd|private[_-]?key|aws[_-]?secret|client[_-]?secret|'
            r'stripe[_-]?key|sendgrid|twilio|github[_-]?token|firebase)'
            r'[\s:=\'"]+([A-Za-z0-9/+_.=-]{16,})',
            re.IGNORECASE
        )
        findings = set()
        if not self.file_has_content(js_urls_file):
            return
        with open(js_urls_file, encoding="utf-8", errors="replace") as f:
            urls = [line.strip() for line in f if line.strip()][:200]
        for u in urls:
            try:
                r = self._http.get(u, timeout=10, verify=False, allow_redirects=True)
                if r.status_code >= 400:
                    continue
                body = r.text[:1_000_000]
                for m in regex.finditer(body):
                    key = m.group(0)[:220]
                    findings.add(f"{u} :: {key}")
            except Exception:
                continue
        self._write_unique_sorted_lines(out_file, sorted(findings))

    # ── PHASE 5: JS SECRET HUNTING ─────────────────────────────────────────────
    def phase5_js_secrets(self, domain: str, d_dir: str, live_200: str):
        if not self._phase_enabled("js"):
            return
        if not self.force and self._phase_is_done(d_dir, "js"):
            return

        if not self.available.get("subjs"):
            print(f"{Fore.YELLOW}      [~] subjs not found — JS analysis skip.")
            return
        if not self.file_has_content(live_200):
            print(f"{Fore.YELLOW}      [~] No live_200 input — JS analysis skip.")
            return

        t0 = self.phase_timer("PHASE 5: JS SECRET HUNTING")
        evidence = f"{d_dir}/evidence"
        js_urls  = f"{d_dir}/js_urls.txt"

        self._extract_subjs_urls(live_200, js_urls)
        js_count = self.count_lines(js_urls)
        print(f"      JS files: {Fore.GREEN}{js_count}")

        if self.file_has_content(js_urls):
            secrets_file = f"{evidence}/js_secrets.txt"
            self._hunt_js_secrets_python(js_urls, secrets_file)
            sc = self.count_lines(secrets_file)
            if sc > 0:
                print(f"{Fore.RED}      🔑 SECRETS: {sc}")
                self.notify_discord(f"[{domain}] {sc} potential secrets in JS!")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "js")

    # ── PHASE 6: DATA MINING ──────────────────────────────────────────────────
    def phase6_data_mining(self, domain: str, d_dir: str, live_200: str, merged_endpoints: str):
        """
        FIX: live_200 parameter now properly passed from caller (was using hardcoded path before).
        """
        if not self._phase_enabled("mine"):
            return
        if not self.force and self._phase_is_done(d_dir, "mine"):
            return
        if not self.file_has_content(merged_endpoints):
            print(f"{Fore.YELLOW}      [~] endpoints input missing — data mining skip.")
            return

        t0 = self.phase_timer("PHASE 6: DATA MINING (GF + CORS + 403 BYPASS)")
        evidence = f"{d_dir}/evidence"

        # GF patterns
        for pattern, out_rel in GF_PATTERNS.items():
            out_abs = f"{d_dir}/{out_rel}"
            self.run_cmd(
                f"gf {self._q(pattern)} {self._q(merged_endpoints)} > {self._q(out_abs)} 2>/dev/null",
                f"GF: {pattern}",
                allow_exit_codes=(0, 1)
            )
            count = self.count_lines(out_abs)
            if count > 0:
                print(f"        {pattern}: {Fore.GREEN}{count} params")

        # CORS check
        if self.available.get("corsy"):
            self.run_cmd(
                f"corsy -i {live_200} -t 10 --headers 'User-Agent: Mozilla' "
                f"-o {evidence}/cors.txt 2>/dev/null",
                "CORS check (corsy)"
            )
        else:
            # FIX: use passed live_200 param, not hardcoded path
            self.run_cmd(
                f"httpx -l {self._q(live_200)} -silent "
                f"-H 'Origin: https://evil.com' "
                f"-match-regex 'Access-Control-Allow-Origin: https://evil.com' "
                f"-o {self._q(evidence + '/cors.txt')} 2>/dev/null",
                "Basic CORS check (httpx)"
            )

        # 403 Bypass
        targets_403 = self._tmpfile(f"403_{domain}.txt")
        self._extract_403_urls(f"{d_dir}/live.txt", targets_403)
        if self.file_has_content(targets_403):
            # Bypass403 class — full 19-header + path + verb bypass
            bc = Bypass403.run(
                targets_file=targets_403,
                output_file=f"{evidence}/403_bypass.txt",
                engine=self._http,
                max_targets=cfg.max_403_targets,
            )
            if bc > 0:
                print(f"{Fore.RED}      🚪 403 BYPASSED: {bc}")
                self.notify_discord(f"[{domain}] {bc} 403 bypasses!")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "mine")

    def _run_403_bypass(self, targets_file: str, out_file: str):
        """
        FIX: Python-based 403 bypass — proper header handling, no bash quoting bugs.
        """
        bypass_headers = [
            {"X-Original-URL": "/"},
            {"X-Forwarded-For": "127.0.0.1"},
            {"X-Custom-IP-Authorization": "127.0.0.1"},
            {"X-Rewrite-URL": "/"},
            {"X-Real-IP": "127.0.0.1"},
            {"X-Host": "localhost"},
            {"X-Originating-IP": "127.0.0.1"},
        ]
        bypass_paths = [
            "/%2f/", "/./", "//", "/%252f/", "/..;/",
        ]

        urls = []
        with open(targets_file) as f:
            urls = [l.strip() for l in f if l.strip()]

        bypassed = []

        for url in urls[:50]:  # Max 50 targets
            for headers in bypass_headers:
                try:
                    r = self._http.get(url, headers=headers, timeout=8,
                                    allow_redirects=False)
                    if r.status_code == 200:
                        hname = list(headers.keys())[0]
                        entry = f"BYPASS [{hname}]: {url}"
                        bypassed.append(entry)
                        print(f"      {Fore.RED}{entry}")
                        break
                except Exception:
                    continue

            # Path-based bypass
            for suffix in bypass_paths:
                try:
                    test_url = url.rstrip("/") + suffix
                    r = self._http.get(test_url, timeout=8, allow_redirects=False)
                    if r.status_code == 200:
                        entry = f"BYPASS [path:{suffix}]: {url}"
                        bypassed.append(entry)
                        break
                except Exception:
                    continue

        if bypassed:
            with open(out_file, "w") as f:
                f.write("\n".join(bypassed) + "\n")

    # ── PHASE 7: CLOUD ASSET ENUM ─────────────────────────────────────────────
    def phase7_cloud_enum(self, domain: str, d_dir: str):
        if not CLOUD_ENUM_ENABLED or not self._phase_enabled("cloud"):
            return
        if not self.force and self._phase_is_done(d_dir, "cloud"):
            return

        t0 = self.phase_timer("PHASE 7: CLOUD ASSET ENUMERATION")
        evidence = f"{d_dir}/evidence"
        cloud_out = f"{evidence}/cloud_assets.txt"

        # S3 bucket permutations from domain name
        base = domain.split(".")[0]
        bucket_names = [
            base, f"{base}-dev", f"{base}-prod", f"{base}-staging",
            f"{base}-backup", f"{base}-assets", f"{base}-static",
            f"{base}-media", f"{base}-data", f"{base}-files",
            f"{base}-public", f"{base}-private", f"{base}-cdn",
        ]

        print(f"{Fore.CYAN}  [*] Checking S3/GCS/Azure buckets...")
        found_buckets = []

        for bucket in bucket_names:
            # S3
            s3_urls = [
                f"https://{bucket}.s3.amazonaws.com",
                f"https://s3.amazonaws.com/{bucket}",
            ]
            for url in s3_urls:
                try:
                    r = self._http.get(url, timeout=5, allow_redirects=False)
                    if r.status_code in (200, 403):  # 403 = exists but private
                        status = "OPEN" if r.status_code == 200 else "PRIVATE"
                        entry = f"S3[{status}]: {url}"
                        found_buckets.append(entry)
                        color = Fore.RED if status == "OPEN" else Fore.YELLOW
                        print(f"      {color}🪣 {entry}")
                except Exception:
                    continue

            # GCS
            gcs_url = f"https://storage.googleapis.com/{bucket}"
            try:
                r = self._http.get(gcs_url, timeout=5, allow_redirects=False)
                if r.status_code in (200, 403):
                    status = "OPEN" if r.status_code == 200 else "PRIVATE"
                    entry = f"GCS[{status}]: {gcs_url}"
                    found_buckets.append(entry)
                    print(f"      {Fore.RED}🪣 {entry}")
            except Exception:
                pass

        if found_buckets:
            with open(cloud_out, "w") as f:
                f.write("\n".join(found_buckets) + "\n")
            print(f"      Cloud assets found: {Fore.RED}{len(found_buckets)}")
            self.notify_discord(f"[{domain}] {len(found_buckets)} cloud assets!")
        else:
            print(f"      Cloud assets: none found")

        # cloud_enum tool (if available)
        if self.available.get("cloud_enum"):
            self.run_cmd(
                f"cloud_enum -k {domain.split('.')[0]} "
                f"--disable-azure-checks "  # often too noisy
                f"-b {cloud_out}",
                "cloud_enum", timeout=180
            )

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "cloud")

    # ── PHASE 8: GITHUB DORKING ───────────────────────────────────────────────
    def phase8_github_dork(self, domain: str, d_dir: str):
        """
        GitHub public search API se accidentally leaked secrets dhundna.
        Sirf public repos — authorized bug bounty recon ke liye.
        Token: GP_GITHUB_TOKEN env var mein set karo.
        """
        if not self._phase_enabled("github"):
            return
        if not self.force and self._phase_is_done(d_dir, "github"):
            return
        if not cfg.github_token:
            print(f"{Fore.YELLOW}  [~] Phase 8 skip — GP_GITHUB_TOKEN not set in .env")
            return

        t0 = self.phase_timer("PHASE 8: GITHUB DORKING (public repos)")
        evidence  = f"{d_dir}/evidence"
        out_file  = f"{evidence}/github_leaks.txt"
        org       = domain.split(".")[0]   # e.g. example.com → example

        headers = {
            "Authorization": f"token {cfg.github_token}",
            "Accept":        "application/vnd.github.v3+json",
            "User-Agent":    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        }

        # ── Search queries — public repo leaks ke liye standard dorks ──────
        # Sirf wahi patterns jo real bounties mein kaam aate hain
        DORKS = [
            # Secrets & credentials
            f'"{domain}" password',
            f'"{domain}" secret',
            f'"{domain}" api_key',
            f'"{domain}" apikey',
            f'"{domain}" api_secret',
            f'"{domain}" token',
            f'"{domain}" access_token',
            f'"{domain}" auth_token',
            f'"{domain}" client_secret',
            f'"{domain}" private_key',
            # .env files
            f'"{domain}" filename:.env',
            f'"{org}" filename:.env',
            # Config files with creds
            f'"{domain}" filename:config.yml',
            f'"{domain}" filename:config.json',
            f'"{domain}" filename:settings.py',
            f'"{domain}" filename:database.yml',
            f'"{domain}" filename:.npmrc',
            f'"{domain}" filename:wp-config.php',
            # Connection strings
            f'"{domain}" DB_PASSWORD',
            f'"{domain}" DATABASE_URL',
            f'"{domain}" JDBC',
            f'"{domain}" mongodb+srv',
            # Internal endpoints leak
            f'"{domain}" internal',
            f'"{domain}" staging',
            f'"{domain}" preprod',
            # AWS / cloud
            f'"{org}" AWS_SECRET_ACCESS_KEY',
            f'"{org}" AWS_ACCESS_KEY_ID',
            f'"{org}" s3.amazonaws.com',
            # SSH / private keys
            f'"{org}" BEGIN RSA PRIVATE KEY',
            f'"{org}" BEGIN EC PRIVATE KEY',
            f'"{org}" BEGIN OPENSSH PRIVATE KEY',
        ]

        # Regex patterns — found content mein actual secret match karne ke liye
        SECRET_PATTERNS = [
            (r'(?i)password\s*[=:]\s*["\']?([^\s"\']{6,})',      "password"),
            (r'(?i)api[_-]?key\s*[=:]\s*["\']?([A-Za-z0-9_\-]{16,})', "api_key"),
            (r'(?i)secret\s*[=:]\s*["\']?([A-Za-z0-9_\-]{16,})', "secret"),
            (r'(?i)token\s*[=:]\s*["\']?([A-Za-z0-9_\-\.]{16,})', "token"),
            (r'AKIA[0-9A-Z]{16}',                                  "aws_access_key"),
            (r'(?i)aws.{0,20}secret.{0,20}[=:]\s*["\']?([A-Za-z0-9/+=]{40})', "aws_secret"),
            (r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', "private_key"),
            (r'(?i)mongodb(?:\+srv)?://[^\s"\']+',                 "mongodb_uri"),
            (r'(?i)postgres(?:ql)?://[^\s"\']+',                   "postgres_uri"),
            (r'(?i)mysql://[^\s"\']+',                             "mysql_uri"),
            (r'(?i)redis://[^\s"\']+',                             "redis_uri"),
            (r'ghp_[A-Za-z0-9]{36}',                              "github_token"),
            (r'ghs_[A-Za-z0-9]{36}',                              "github_app_token"),
            (r'(?i)slack.{0,10}xox[baprs]-[A-Za-z0-9\-]+',       "slack_token"),
            (r'(?i)stripe.{0,10}sk_live_[A-Za-z0-9]{24,}',       "stripe_key"),
            (r'(?i)sendgrid.{0,10}SG\.[A-Za-z0-9_\-]{22,}',      "sendgrid_key"),
            (r'(?i)twilio.{0,20}SK[A-Za-z0-9]{32}',              "twilio_key"),
        ]
        compiled_patterns = [(re.compile(p), name) for p, name in SECRET_PATTERNS]

        findings = []
        seen_urls = set()
        rate_hit  = 0

        print(f"{Fore.CYAN}  [*] GitHub dorking — {len(DORKS)} queries, org: {org}")

        for i, dork in enumerate(DORKS):
            # GitHub API rate limit — unauthenticated: 10/min, authenticated: 30/min
            # 2.5s delay taaki 30/min ke andar rahein
            if i > 0:
                time.sleep(2.5 + random.uniform(0.3, 1.0))

            try:
                resp = requests.get(
                    "https://api.github.com/search/code",
                    headers=headers,
                    params={"q": dork, "per_page": 30},
                    timeout=20,
                )
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"GitHub search error [{dork[:40]}]: {e}")
                continue

            if resp.status_code == 401:
                print(f"{Fore.RED}  [!] GitHub token invalid ya expired — phase abort")
                break

            if resp.status_code == 403:
                rate_hit += 1
                retry_after = int(resp.headers.get("Retry-After", 60))
                print(f"{Fore.YELLOW}  [~] GitHub rate limit — waiting {retry_after}s...")
                time.sleep(retry_after + 5)
                if rate_hit >= 3:
                    print(f"{Fore.YELLOW}  [~] 3x rate limit — GitHub dork abort kar rahe hain")
                    break
                continue

            if resp.status_code != 200:
                self.logger.warning(f"GitHub search HTTP {resp.status_code} for: {dork[:40]}")
                continue

            try:
                data = resp.json()
            except ValueError:
                continue

            items = data.get("items", [])
            if not items:
                continue

            # Remaining rate limit check
            remaining = int(resp.headers.get("X-RateLimit-Remaining", 99))
            if remaining < 3:
                reset_ts  = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait_secs = max(0, reset_ts - int(time.time())) + 5
                print(f"{Fore.YELLOW}  [~] Rate limit low — sleeping {wait_secs}s")
                time.sleep(wait_secs)

            for item in items:
                html_url = item.get("html_url", "")
                raw_url  = html_url.replace(
                    "github.com", "raw.githubusercontent.com"
                ).replace("/blob/", "/")

                if html_url in seen_urls:
                    continue
                seen_urls.add(html_url)

                repo_name = item.get("repository", {}).get("full_name", "unknown")
                file_path = item.get("path", "")

                # File content fetch karke patterns match karo
                matched_secrets = []
                try:
                    time.sleep(random.uniform(0.3, 0.8))
                    raw_resp = requests.get(
                        raw_url, headers=headers, timeout=12
                    )
                    if raw_resp.status_code == 200:
                        content = raw_resp.text[:50_000]   # 50KB cap
                        for pattern, pname in compiled_patterns:
                            matches = pattern.findall(content)
                            for m in matches[:3]:   # max 3 per pattern per file
                                val = m if isinstance(m, str) else m[0] if m else ""
                                val = val[:80].strip()
                                if val and len(val) >= 6:
                                    matched_secrets.append(f"{pname}: {val}")
                except Exception:
                    pass

                entry = {
                    "dork":    dork,
                    "repo":    repo_name,
                    "file":    file_path,
                    "url":     html_url,
                    "secrets": matched_secrets,
                }
                findings.append(entry)

                # Console print
                secret_str = ""
                if matched_secrets:
                    secret_str = f" → {Fore.RED}{matched_secrets[0]}"
                print(f"      {Fore.YELLOW}[GH]{Fore.WHITE} {repo_name}/{file_path}{secret_str}")

        # ── Save results ──────────────────────────────────────────────────────
        if findings:
            # Human-readable txt
            with open(out_file, "w") as f:
                f.write(f"GitHub Dorking Results — {domain}\n")
                f.write(f"Scan time: {datetime.datetime.now().isoformat()}\n")
                f.write("=" * 60 + "\n\n")
                for idx, find in enumerate(findings, 1):
                    f.write(f"[{idx}] Repo:  {find['repo']}\n")
                    f.write(f"     File:  {find['file']}\n")
                    f.write(f"     URL:   {find['url']}\n")
                    f.write(f"     Dork:  {find['dork']}\n")
                    if find["secrets"]:
                        f.write(f"     *** SECRETS FOUND ***\n")
                        for s in find["secrets"]:
                            f.write(f"       - {s}\n")
                    f.write("\n")

            # JSON bhi save karo — program mein report submit karne ke liye
            json_out = f"{evidence}/github_leaks.json"
            with open(json_out, "w") as f:
                json.dump({
                    "domain":   domain,
                    "org":      org,
                    "ts":       datetime.datetime.now().isoformat(),
                    "total":    len(findings),
                    "findings": findings,
                }, f, indent=2)

            # High value findings — sirf jinmein actual secrets mile
            hv = [x for x in findings if x["secrets"]]
            print(f"\n{Fore.GREEN}      GitHub findings:  {len(findings)}")
            if hv:
                print(f"{Fore.RED}      *** Secrets matched: {len(hv)} files ***")
                self.notify_discord(
                    f"[{domain}] GitHub dork: {len(hv)} files mein secrets mili! "
                    f"Check {out_file}"
                )
        else:
            print(f"      GitHub: koi findings nahi")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "github")


    # ── PHASE 9: SUBDOMAIN TAKEOVER CHECK ────────────────────────────────────
    def phase9_takeover_check(self, domain: str, d_dir: str, resolved: str):
        """
        CNAME dangling check — subdomain takeover vulnerability.
        Resolved subdomains ke CNAME records check karo — agar service defunct
        hai toh takeover possible hai. Standard bug bounty finding.
        """
        if not self._phase_enabled("takeover"):
            return
        if not self.force and self._phase_is_done(d_dir, "takeover"):
            return
        if not self.file_has_content(resolved):
            print(f"{Fore.YELLOW}  [~] Phase 9 skip — resolved subdomains nahi hain (enum phase pehle chalao)")
            self._mark_phase_done(d_dir, "takeover")
            return

        t0 = self.phase_timer("PHASE 9: SUBDOMAIN TAKEOVER CHECK")
        evidence = f"{d_dir}/evidence"
        out_file = f"{evidence}/takeover_candidates.txt"

        # 25+ services — CNAME fingerprints jo takeover ke liye known hain
        TAKEOVER_FINGERPRINTS = {
            "github.io":                    "There isn't a GitHub Pages site here",
            "herokuapp.com":                "No such app",
            "s3.amazonaws.com":             "NoSuchBucket",
            "storage.googleapis.com":       "NoSuchBucket",
            "azurewebsites.net":            "404 Web Site not found",
            "cloudapp.net":                 "404 Web Site not found",
            "trafficmanager.net":           "404 Web Site not found",
            "cloudfront.net":               "The request could not be satisfied",
            "fastly.net":                   "Fastly error: unknown domain",
            "shopify.com":                  "Sorry, this shop is currently unavailable",
            "myshopify.com":                "Sorry, this shop is currently unavailable",
            "statuspage.io":                "Better luck next time",
            "helpscoutdocs.com":            "No settings were found",
            "freshdesk.com":                "There is no helpdesk here",
            "zendesk.com":                  "Help Center Closed",
            "ghost.io":                     "The thing you were looking for is no longer here",
            "tumblr.com":                   "There's nothing here",
            "wordpress.com":                "Do you want to register",
            "surge.sh":                     "project not found",
            "bitbucket.io":                 "Repository not found",
            "unbounce.com":                 "The requested URL was not found",
            "pantheon.io":                  "The gods are wise",
            "getresponse.com":              "With GetResponse Landing Pages",
            "feedpress.me":                 "The feed has not been found",
            "readme.io":                    "Project doesnt exist",
            "intercom.io":                  "This page is reserved for artistic masterpieces",
            "fly.io":                       "404 Not Found",
            "render.com":                   "There is no Render app deployed at this URL",
        }

        # subzy already hai — use karo agar available
        if self.available.get("subzy"):
            self.run_cmd(
                f"subzy run --targets {self._q(resolved)} "
                f"--output {self._q(out_file)} --hide-fails --concurrency 20",
                "Takeover check (subzy)"
            )
        else:
            # Manual CNAME + HTTP fingerprint check
            print(f"{Fore.CYAN}  [*] Manual CNAME takeover check...")
            candidates = []

            with open(resolved) as f:
                subdomains = [l.strip() for l in f if l.strip()]

            def check_sub(sub):
                hits = []
                # CNAME lookup
                try:
                    result = subprocess.run(
                        ["dig", "+short", "CNAME", sub],
                        capture_output=True, text=True, timeout=8
                    )
                    cname = result.stdout.strip().rstrip(".")
                    if not cname:
                        return hits

                    # Kaunsi service pe point kar raha hai
                    matched_service = None
                    for service_domain in TAKEOVER_FINGERPRINTS:
                        if service_domain in cname:
                            matched_service = service_domain
                            break

                    if not matched_service:
                        return hits

                    # HTTP se fingerprint confirm karo
                    for scheme in ["https", "http"]:
                        try:
                            r = self._http.get(
                                f"{scheme}://{sub}",
                                timeout=8,
                                allow_redirects=True,
                            )
                            body = r.text[:5000]
                            fingerprint = TAKEOVER_FINGERPRINTS[matched_service]
                            if fingerprint.lower() in body.lower():
                                hits.append(
                                    f"TAKEOVER [{matched_service}]: {sub} "
                                    f"→ CNAME: {cname}"
                                )
                            break
                        except Exception:
                            continue
                except Exception:
                    pass
                return hits

            with ThreadPoolExecutor(max_workers=30) as ex:
                futures = {ex.submit(check_sub, s): s for s in subdomains}
                for fut in as_completed(futures):
                    try:
                        hits = fut.result()
                        for h in hits:
                            candidates.append(h)
                            print(f"      {Fore.RED}*** {h}")
                    except Exception:
                        pass

            if candidates:
                with open(out_file, "w") as f:
                    f.write("\n".join(candidates) + "\n")

        count = self.count_lines(out_file)
        print(f"      Takeover candidates: {Fore.RED if count else Fore.GREEN}{count}")
        self.phase_done(t0)
        self._mark_phase_done(d_dir, "takeover")

    # ── PHASE 10: ASN / IP RANGE ENUM ─────────────────────────────────────────
    def phase10_asn_enum(self, domain: str, d_dir: str):
        """
        Target company ke ASN se IP ranges nikalna.
        Bade programs mein scope mein unallocated IPs bhi hoti hain.
        asnmap tool use karta hai — standard recon.
        """
        if not self._phase_enabled("asn"):
            return
        if not self.force and self._phase_is_done(d_dir, "asn"):
            return
        if not self.available.get("asnmap"):
            print(f"{Fore.YELLOW}  [~] Phase 10 skip — asnmap nahi mila")
            print(f"      Install: go install github.com/projectdiscovery/asnmap/cmd/asnmap@latest")
            return

        t0 = self.phase_timer("PHASE 10: ASN / IP RANGE ENUM")
        evidence = f"{d_dir}/evidence"
        out_file = f"{evidence}/asn_ranges.txt"

        self.run_cmd(
            f"asnmap -d {self._q(domain)} -silent -o {self._q(out_file)}",
            "ASN ranges (asnmap)"
        )

        count = self.count_lines(out_file)
        print(f"      IP ranges found: {Fore.GREEN}{count}")

        # Agar ranges mili toh httpx se quick probe — live IPs dhundo
        if count > 0 and count <= 50:   # bahut bade ranges skip karo
            ip_live = f"{evidence}/asn_live_hosts.txt"
            self.run_cmd(
                f"httpx -l {self._q(out_file)} -silent -t 50 -sc "
                f"-follow-redirects -o {self._q(ip_live)}",
                "ASN live host probe"
            )
            ip_count = self.count_lines(ip_live)
            print(f"      Live IPs (ASN): {Fore.GREEN}{ip_count}")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "asn")

    # ── PHASE 11: WAYBACK JS DIFFING ──────────────────────────────────────────
    def phase11_js_diff(self, domain: str, d_dir: str):
        """
        Historical JS files (Wayback Machine) vs current JS compare karo.
        Deleted endpoints, old API versions jo abhi bhi live hain — yahan se
        real bounties milti hain.
        """
        if not self._phase_enabled("jsdiff"):
            return
        if not self.force and self._phase_is_done(d_dir, "jsdiff"):
            return

        t0 = self.phase_timer("PHASE 11: WAYBACK JS DIFFING")
        evidence  = f"{d_dir}/evidence"
        out_file  = f"{evidence}/js_diff_endpoints.txt"
        js_dir    = f"{d_dir}/js_snapshots"
        os.makedirs(js_dir, exist_ok=True)

        # Step 1: Wayback se JS URLs nikalo
        print(f"{Fore.CYAN}  [*] Wayback JS URLs fetching...")
        try:
            # CDX API — mimetype filter se sirf JS files, last 5 years
            r = requests.get(
                "https://web.archive.org/cdx/search/cdx",
                params={
                    "url":        f"*.{domain}/*.js",
                    "output":     "text",
                    "fl":         "original,timestamp",
                    "collapse":   "urlkey",
                    "limit":      "300",
                    "filter":     ["statuscode:200", "mimetype:application/javascript"],
                    "from":       "20200101",
                },
                timeout=30,
            )
            if r.status_code == 200 and r.text.strip():
                # format: url timestamp — sirf URL lo
                raw_lines = r.text.strip().splitlines()
                wayback_urls = list(set(
                    line.split()[0] for line in raw_lines if line.strip()
                ))
            else:
                # Fallback — bina mimetype filter ke try karo
                r2 = requests.get(
                    "https://web.archive.org/cdx/search/cdx",
                    params={
                        "url":      f"*.{domain}/*.js",
                        "output":   "text",
                        "fl":       "original",
                        "collapse": "urlkey",
                        "limit":    "200",
                        "filter":   "statuscode:200",
                    },
                    timeout=30,
                )
                wayback_urls = list(set(r2.text.strip().splitlines())) if r2.status_code == 200 and r2.text.strip() else []
        except Exception as e:
            self.logger.warning(f"Wayback JS fetch error: {e}")
            wayback_urls = []

        print(f"      Wayback JS URLs: {Fore.GREEN}{len(wayback_urls)}")
        if not wayback_urls:
            self.phase_done(t0)
            self._mark_phase_done(d_dir, "jsdiff")
            return

        # Step 2: Current live JS files nikalo (phase5 ka output reuse)
        current_js_file = f"{d_dir}/evidence/js_files.txt"
        current_urls    = []
        if os.path.exists(current_js_file):
            with open(current_js_file) as f:
                current_urls = [l.strip() for l in f if l.strip()]

        # Wayback URLs se path nikalo — current site pe check karo
        wayback_paths = set()
        for url in wayback_urls:
            try:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(url)
                wayback_paths.add(parsed.path)
            except Exception:
                pass

        current_paths = set()
        for url in current_urls:
            try:
                parsed = urlparse(url)
                current_paths.add(parsed.path)
            except Exception:
                pass

        # Deleted paths — wayback mein hai lekin current mein nahi
        deleted_paths = wayback_paths - current_paths
        print(f"      Deleted JS paths: {Fore.YELLOW}{len(deleted_paths)}")

        # Step 3: Deleted JS files fetch karo aur endpoints extract karo
        endpoint_re = re.compile(
            r'["\'/](/(?:api|v[0-9]+|rest|graphql|admin|internal|auth|user|account)[a-zA-Z0-9/_\-]{2,100})["\'/]',
            re.IGNORECASE
        )
        secret_re = re.compile(
            r'(?i)(?:api_?key|secret|token|password|auth)\s*[:=]\s*[A-Za-z0-9_\-]{10,}'
        )

        found_endpoints = set()
        found_secrets   = []
        checked = 0

        for wb_url in wayback_urls[:80]:   # max 80 files check
            try:
                time.sleep(random.uniform(0.3, 0.8))
                # Wayback archived version fetch karo
                # Correct Wayback archived URL format
                wb_fetch = f"https://web.archive.org/web/20230101000000*/{wb_url}"
                r = requests.get(wb_fetch, timeout=12)
                if r.status_code != 200 or len(r.text) < 100:
                    continue
                js_content = r.text[:100_000]   # 100KB cap

                # Endpoints extract
                for match in endpoint_re.findall(js_content):
                    found_endpoints.add(match)

                # Secrets extract
                for match in secret_re.findall(js_content):
                    if len(match) >= 10:
                        found_secrets.append(f"{wb_url} → {match[:60]}")

                checked += 1
            except Exception:
                continue

        print(f"      JS files checked: {Fore.GREEN}{checked}")
        print(f"      Unique endpoints: {Fore.GREEN}{len(found_endpoints)}")
        if found_secrets:
            print(f"      *** Secrets in old JS: {Fore.RED}{len(found_secrets)} ***")

        # Save results
        if found_endpoints or found_secrets:
            with open(out_file, "w") as f:
                f.write(f"JS Diff Analysis — {domain}\n")
                f.write(f"Wayback JS: {len(wayback_urls)} | Checked: {checked}\n")
                f.write(f"Deleted paths: {len(deleted_paths)}\n\n")
                if found_endpoints:
                    f.write("── ENDPOINTS (historical) ──\n")
                    for ep in sorted(found_endpoints):
                        f.write(f"  {ep}\n")
                if found_secrets:
                    f.write("\n── SECRETS IN OLD JS ──\n")
                    for s in found_secrets:
                        f.write(f"  {s}\n")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "jsdiff")

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    def generate_summary(self, domain: str, d_dir: str):
        evidence    = f"{d_dir}/evidence"
        nonstd_live = f"{d_dir}/nonstandard_live.txt"

        # FIX: resolved path — pick correct one
        resolved_path = self._get_resolved_path(d_dir)

        summary = {
            "Subdomains (raw)":       self.count_lines(f"{d_dir}/raw_subs.txt"),
            "Subdomains (brute)":     self.count_lines(f"{d_dir}/brute_subs.txt"),
            "Subdomains (permut.)":   self.count_lines(f"{d_dir}/perm_subs.txt"),
            "Subdomains (recursive)": self.count_lines(f"{d_dir}/recursive_subs.txt"),
            "Subdomains (resolved)":  self.count_lines(resolved_path),
            "Open port combos":       self.count_lines(f"{d_dir}/open_ports.txt"),
            "Non-std port services":  self.count_lines(nonstd_live),
            "VHosts found":           self.count_lines(f"{evidence}/vhosts.txt"),
            "Live hosts":             self.count_lines(f"{d_dir}/live.txt"),
            "200 OK":                 self.count_lines(f"{d_dir}/live_200.txt"),
            "Endpoints (total)":      self.count_lines(f"{d_dir}/all_endpoints.txt"),
            "Vulns (nuclei)":         self.count_lines(f"{evidence}/vulns.txt"),
            "XSS params":             self.count_lines(f"{evidence}/xss.txt"),
            "SQLi params":            self.count_lines(f"{evidence}/sqli.txt"),
            "SSRF params":            self.count_lines(f"{evidence}/ssrf.txt"),
            "SSTI params":            self.count_lines(f"{evidence}/ssti.txt"),
            "Open Redirect":          self.count_lines(f"{evidence}/open_redirect.txt"),
            "LFI params":             self.count_lines(f"{evidence}/lfi.txt"),
            "Takeover candidates":    self.count_lines(f"{evidence}/takeover.txt"),
            "JS Secrets":             self.count_lines(f"{evidence}/js_secrets.txt"),
            "403 Bypassed":           self.count_lines(f"{evidence}/403_bypass.txt"),
            "CORS issues":            self.count_lines(f"{evidence}/cors.txt"),
            "Cloud assets":           self.count_lines(f"{evidence}/cloud_assets.txt"),
            "GitHub leaks (files)":   self.count_lines(f"{evidence}/github_leaks.txt"),
            "Takeover candidates":    self.count_lines(f"{evidence}/takeover_candidates.txt"),
            "ASN IP ranges":          self.count_lines(f"{evidence}/asn_ranges.txt"),
            "ASN live hosts":         self.count_lines(f"{evidence}/asn_live_hosts.txt"),
            "JS diff endpoints":      self.count_lines(f"{evidence}/js_diff_endpoints.txt"),
        }

        summary_data = {
            "domain":    domain,
            "timestamp": datetime.datetime.now().isoformat(),
            "stats":     summary
        }

        with open(f"{d_dir}/summary.json", "w") as f:
            json.dump(summary_data, f, indent=2)

        # HTML report
        self._generate_html_report(domain, d_dir, summary_data)

        HIGH_VALUE = {
            "Vulns (nuclei)", "JS Secrets", "403 Bypassed",
            "Takeover candidates", "VHosts found", "Non-std port services",
            "Cloud assets", "SSTI params", "GitHub leaks (files)",
            "ASN live hosts", "JS diff endpoints",
        }

        print(f"\n{Fore.MAGENTA}{'═'*52}")
        print(f"{Fore.MAGENTA}  SUMMARY: {domain}")
        print(f"{'═'*52}{Style.RESET_ALL}")
        for k, v in summary.items():
            if k in HIGH_VALUE:
                color = Fore.RED if v > 0 else Fore.WHITE
            else:
                color = Fore.GREEN if v > 0 else Fore.WHITE
            print(f"  {k:<28} {color}{v}{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'═'*52}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}HTML report: {d_dir}/report.html{Style.RESET_ALL}")

    def _generate_html_report(self, domain: str, d_dir: str, data: dict):
        """Minimal HTML report generate karo."""
        stats = data.get("stats", {})
        ts    = data.get("timestamp", "")

        rows = ""
        HIGH_VALUE = {
            "Vulns (nuclei)", "JS Secrets", "403 Bypassed",
            "Takeover candidates", "VHosts found", "Non-std port services",
            "Cloud assets",
        }
        for k, v in stats.items():
            cls = "high" if (k in HIGH_VALUE and v > 0) else ("ok" if v > 0 else "zero")
            rows += f'<tr class="{cls}"><td>{k}</td><td>{v}</td></tr>\n'

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Ghost Protocol — {domain}</title>
<style>
  body {{ font-family: monospace; background:#0d0d0d; color:#ccc; padding:2rem; }}
  h1   {{ color:#ff4444; }}
  h2   {{ color:#ffaa00; }}
  table {{ border-collapse:collapse; width:60%; margin-top:1rem; }}
  th,td {{ padding:0.4rem 1rem; border:1px solid #333; text-align:left; }}
  th   {{ background:#1a1a1a; color:#ff4444; }}
  .high {{ background:#3d0000; color:#ff6666; font-weight:bold; }}
  .ok  {{ color:#66ff66; }}
  .zero {{ color:#555; }}
</style>
</head>
<body>
<h1>🔥 GHOST PROTOCOL v10.0</h1>
<h2>Target: {domain}</h2>
<p>Scan time: {ts}</p>
<table>
  <tr><th>Metric</th><th>Count</th></tr>
  {rows}
</table>
</body>
</html>"""

        with open(f"{d_dir}/report.html", "w") as f:
            f.write(html)

    # ── crt.sh ────────────────────────────────────────────────────────────────
    def get_crt_sh(self, domain: str, sub_file: str):
        """crt.sh — wildcard + multi-SAN certificates handle karo. 429 pe retry."""
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=25)
                if r.status_code == 429:
                    wait = 10 * (attempt + 1)
                    self.logger.warning(f"crt.sh 429 — waiting {wait}s (attempt {attempt+1})")
                    time.sleep(wait)
                    continue
                if r.status_code == 200:
                    names = set()
                    for entry in r.json():
                        for name in entry.get("name_value", "").splitlines():
                            name = name.strip().lstrip("*.").lower()
                            if name and re.match(r'^[a-zA-Z0-9._-]+$', name):
                                if self.scope.in_scope(name):
                                    names.add(name)
                    with open(sub_file, "a") as f:
                        f.write("\n".join(names) + "\n")
                    self.logger.info(f"crt.sh: {len(names)} subs for {domain}")
                    return
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"crt.sh failed for {domain}: {e}")
                break
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"crt.sh JSON parse failed for {domain}: {e}")
                break

    # ── Master Controller ──────────────────────────────────────────────────────
    def process_target(self, domain: str):
        """Ek domain ka poora pipeline."""
        d_dir = f"{self.base_dir}/{self._safe_dirname(domain)}"

        # Scope validation
        if not self.scope.in_scope(domain):
            print(f"{Fore.RED}[!] {domain} — OUT OF SCOPE. Skipping.")
            return

        if self.is_already_scanned(domain):
            print(f"{Fore.YELLOW}[~] {domain} — already complete (resume mode). Use --force to rescan.")
            return

        print(f"\n{Fore.MAGENTA}{'='*55}")
        print(f"  [#] DEEP SCANNING: {domain}")
        print(f"{'='*55}{Style.RESET_ALL}")
        start_time = time.time()

        os.makedirs(f"{d_dir}/evidence/screenshots", exist_ok=True)

        try:
            resolved = self.phase1_subdomain_enum(domain, d_dir)
            resolved = self.phase1b_recursive_brute(domain, d_dir, resolved)
            live_file, live_200 = self.phase2_port_and_probe(domain, d_dir, resolved)

            if not self.file_has_content(live_200):
                print(f"{Fore.RED}  [!] No live 200 OK hosts for {domain}. Deeper phases skip.")
            else:
                hist_file = self.phase3_historical_urls(domain, d_dir)
                merged    = self.phase4_scan_crawl(domain, d_dir, live_200, hist_file)
                self.phase5_js_secrets(domain, d_dir, live_200)
                # FIX: pass live_200 properly — was using hardcoded path before
                self.phase6_data_mining(domain, d_dir, live_200, merged)
            # Cloud + GitHub + Takeover + ASN + JS Diff — live_200 pe depend nahi
            self.phase7_cloud_enum(domain, d_dir)
            self.phase8_github_dork(domain, d_dir)
            # resolved file exist na kare toh fallback path
            _resolved = resolved if resolved and self.file_has_content(resolved) else self._get_resolved_path(d_dir)
            self.phase9_takeover_check(domain, d_dir, _resolved)
            self.phase10_asn_enum(domain, d_dir)
            self.phase11_js_diff(domain, d_dir)

        except Exception as e:
            self.logger.error(f"Pipeline error for {domain}: {e}", exc_info=True)
            print(f"{Fore.RED}  [!] Error in {domain} pipeline: {e}")

        self.generate_summary(domain, d_dir)
        self.mark_scan_complete(domain, d_dir)
        elapsed = round(time.time() - start_time, 1)
        print(f"\n{Fore.GREEN}  [✔] {domain} — Done in {elapsed}s → {d_dir}{Style.RESET_ALL}")

    def start(self):
        banner = f"""
{Fore.RED}  ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
{Fore.RED}  ██╔════╝██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
{Fore.YELLOW}  ██║  ███╗███████║██║   ██║███████╗   ██║
{Fore.YELLOW}  ██║   ██║██╔══██║██║   ██║╚════██║   ██║
{Fore.GREEN}  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║
{Fore.GREEN}   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝
{Fore.CYAN}       PROTOCOL v10.0 — Bug Bounty Edition
{Fore.WHITE}       Targets: {len(self.targets)} | Session: {self.session_id}
{Fore.YELLOW}       Wordlist: {self.wordlist or "NOT FOUND — bruteforce skip"}
{Fore.YELLOW}       Phases:   {', '.join(self.phases)}
{Fore.YELLOW}       Dry Run:  {self.dry_run}
        """
        print(banner)
        with ThreadPoolExecutor(max_workers=MAX_DOMAINS_PARALLEL) as executor:
            futures = {executor.submit(self.process_target, t): t for t in self.targets}
            for future in as_completed(futures):
                t = futures[future]
                try:
                    future.result()
                except Exception as e:
                    print(f"{Fore.RED}[!] {t} failed: {e}")

        # Cleanup temp dir
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        print(f"\n{Fore.MAGENTA}[!!!] ALL DONE. Results: {self.base_dir}/{Style.RESET_ALL}")


# ─── CLI ───────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ghost Protocol v10.0 — Bug Bounty Deep Recon",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("targets", help="targets.txt — ek line par ek domain")
    parser.add_argument(
        "--scope", default="",
        help="scope.txt — in-scope domains/wildcards (optional)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Commands print karo, execute mat karo"
    )
    parser.add_argument(
        "--phases", default=",".join(PHASE_MARKERS.keys()),
        help=f"Comma-separated phases to run. Available: {','.join(PHASE_MARKERS.keys())}"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Already scanned domains ko bhi rescan karo"
    )
    parser.add_argument(
        "--skip-nuclei-update", action="store_true",
        help="Nuclei template auto-update skip karo"
    )
    parser.add_argument(
        "--output-dir", default="",
        help="Output directory (resume/re-run friendly). Default: timestamped folder"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    phases = [p.strip() for p in args.phases.split(",") if p.strip() in PHASE_MARKERS]
    if not phases:
        print(f"{Fore.RED}[!] No valid phases selected. Use: {','.join(PHASE_MARKERS.keys())}")
        sys.exit(1)

    recon = DeepRecon(
        target_file=args.targets,
        scope_file=args.scope,
        dry_run=args.dry_run,
        phases=phases,
        skip_nuclei_update=args.skip_nuclei_update,
        output_dir=args.output_dir,
        force=args.force,
    )

    if args.force and args.output_dir:
        # Force mode: scan_complete markers hata do
        for t in recon.targets:
            marker = f"{recon.base_dir}/{recon._safe_dirname(t)}/.scan_complete"
            if os.path.exists(marker):
                os.remove(marker)

    recon.start()
