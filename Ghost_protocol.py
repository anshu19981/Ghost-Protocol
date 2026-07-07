#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         GHOST PROTOCOL v14.2 — DEEP RECON ENGINE                ║
║              Bug Bounty Hunter Edition                           ║
╠══════════════════════════════════════════════════════════════════╣
║  NEW in v14.2 (post-review hardening):                          ║
║  ✔ Wildcard-DNS filter (tool-agnostic) — recursive brute ab     ║
║    massdns fallback ke wildcard FPs nahi rakhta (211→real).      ║
║  ✔ JS secret [unverified] branch pe value-shape gate — route    ║
║    strings / func-refs (e.g. "/reset_password/") ab drop.        ║
║  ✔ asnmap timeout 900s→120s (graceful skip, 15-min hang gaya).  ║
║  ✔ "wildcards/dead" label → "unresolved" (accurate).            ║
║                                                                  ║
║  FIXED in v14.1 (review hardening):                             ║
║  ✔ httpx enrichment ab graceful — agar favicon/ip/cname/loc    ║
║    flags fail (purana build) aur output khali, to core-flag     ║
║    fallback probe. Warna saare live hosts silently gayab ho     ║
║    jaate the → pura pipeline dead. Ab kabhi nahi.               ║
║  ✔ -favicon default OFF (--favicon / GP_FAVICON=1) — extra      ║
║    req/host, bade scope pe mehenga tha.                         ║
║  ✔ katana scope-lock default 'rdn' (root domain, configurable)  ║
║    'fqdn' se badla — wildcard programs mein sibling in-scope     ║
║    subs ab follow honge, warna miss ho rahe the.                ║
║  ✔ GitHub dork pagination (100/page, GITHUB_MAX_PAGES tak).     ║
║    Pehle sirf 30 (page 1) — 30+ result wale dork ki findings    ║
║    miss ho rahi thi. 401/rate-limit pe clean abort.             ║
╠══════════════════════════════════════════════════════════════════╣
║  NEW in v14.0 (yield + stealth + speed):                       ║
║  ✔ Go-tools ab rate-limited: httpx -rl, naabu -rate, katana    ║
║    -rl/-c/-fs fqdn. StealthEngine sirf Python govern karta tha; ║
║    asli traffic to in tools se. Ab polite + kam block.          ║
║  ✔ httpx enriched: -favicon (mmh3 hash → asset clustering /     ║
║    hidden-origin pivot), -ip -cname (infra map), -location.     ║
║  ✔ favicon_clusters.txt + infra_map.txt — naye pivot artifacts. ║
║  ✔ Parallelized sweeps: 403-bypass, cloud-enum, JS-secret hunt  ║
║    (ThreadPoolExecutor, SWEEP_WORKERS) — ghanton ka kaam min.   ║
║  ✔ Cloud enum: 3x bucket permutations + Azure blob check.       ║
║  ✔ JS secrets: high-signal token shapes (Google/AWS/GitHub/     ║
║    Slack/Stripe/JWT/OpenAI/GitLab…) [high-signal] tag → medium. ║
║  ✔ Substring status-bucket FP bugs khatam (nonstd-live,         ║
║    200-count) — ab poora status_code-derived.                   ║
║  ✔ Rich cyberpunk HTML report — findings render + copy buttons. ║
║  ✔ SESSION_FINDINGS.json + index.html — multi-target roll-up    ║
║    dashboard (triage / team workflow).                          ║
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
║  CHANGED in v13.0 (more BB findings, fewer silent misses):      ║
║  ✔ P0 FIX: deep pipeline ab live_ALL pe (200+30x+401+403),      ║
║            sirf 200 pe nahi — 403/401/redirect hosts ab scan     ║
║            hote hain. 403-bypass engine ab all-403 targets pe    ║
║            actually chalta hai.                                   ║
║  ✔ P0 FIX: httpx -json parsing — status_code field se reliable  ║
║            bucketing. Pehle '[200]'/'[403]' substring match      ║
║            content-length se collide hota tha (false buckets).   ║
║  ✔ FIX: Phase 3 (gau/wayback) ab unconditional — passive hai,   ║
║         live host na ho tab bhi historical URLs aate hain.       ║
║  ✔ NEW: findings.json — normalized, severity-sorted, triage-    ║
║         ready aggregate of all evidence (team workflow).         ║
║  ✔ TUNE: gau --mc filter hata diya (401/403 historical bhi),    ║
║          nuclei -mhe 30 (dead hosts drop), regex secrets ko      ║
║          [unverified] tag (trufflehog verified se alag).         ║
╠══════════════════════════════════════════════════════════════════╣
║  MERGED + WIRED in v12.0 (single-file build):                   ║
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

from collections import defaultdict
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
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
import socket
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
    from dotenv import load_dotenv  # noqa: F811 — re-import inside try for availability check
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
            with self._lock:
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
        verify: bool     = False,
        **kwargs
    ) -> Optional[requests.Response]:

        # FIX: `verify` ab named param hai. Pehle koi caller verify=False bhejta
        # (e.g. _hunt_js_secrets_python) toh wo **kwargs mein chala jaata tha aur
        # neeche self._session.request(..., verify=False, **kwargs) mein DUPLICATE
        # keyword ban ke TypeError raise karta tha — jise except Exception swallow
        # kar leta tha. Result: har JS URL silently skip, regex secret hunt = 0.
        # Defensive: kahin aur se bhi galti se aaye toh pop kar do.
        kwargs.pop("verify", None)

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
                    verify        = verify,
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
    "build":    2, "deploy":  2,
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
        import shlex as _shlex
        if self.deep:
            skip_tags = ",".join(self.SKIP_TAGS)
            return (
                f"nuclei -l {targets_file} "
                f"-severity {severity} "
                f"-etags {skip_tags} "
                f"-rl {self.rate_limit} "
                f"-mhe 30 "          # max-host-error: dead host 30 fails ke baad drop
                f"-silent -no-color "
                f"-o {_shlex.quote(output_file)}"
            )
        else:
            fast_tags = ",".join(self.FAST_IMPACT_TAGS)
            skip_tags = ",".join(self.SKIP_TAGS)
            custom_flag = (
                f"-t {_shlex.quote(NUCLEI_CUSTOM_TEMPLATES)} "
                if os.path.isdir(NUCLEI_CUSTOM_TEMPLATES) else ""
            )
            return (
                f"nuclei -l {targets_file} "
                f"-severity {severity} "
                f"-tags {fast_tags} "
                f"-etags {skip_tags} "
                f"{custom_flag}"
                f"-rl {self.rate_limit} "
                f"-mhe 30 "          # max-host-error: dead host 30 fails ke baad drop
                f"-silent -no-color "
                f"-o {_shlex.quote(output_file)}"
            )

    def build_cve_cmd(self, targets_file: str, output_file: str) -> str:
        """
        Recent critical CVEs ke liye targeted scan.
        Fast + high-value.
        """
        import shlex as _shlex
        template_ids = ",".join(self.PRIORITY_CVE_TEMPLATES)
        return (
            f"nuclei -l {targets_file} "
            f"-id {template_ids} "
            f"-rl {self.rate_limit} "
            f"-silent -no-color "
            f"-o {_shlex.quote(output_file)}"
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
        workers: int     = 12,
    ) -> int:
        """
        Full 403 bypass sweep — v14: parallelized.
        Har URL independent hai aur StealthEngine (per-domain rate state + proxy
        pool) thread-safe hai, isliye ThreadPoolExecutor safe + bahut fast hai.
        Returns: number of bypasses found.
        """
        urls = []
        try:
            with open(targets_file) as f:
                urls = [l.strip() for l in f if l.strip()][:max_targets]
        except FileNotFoundError:
            return 0
        if not urls:
            return 0

        bypassed = []
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(cls._try_url, url, engine, timeout): url
                       for url in urls}
            for fut in as_completed(futures):
                url = futures[fut]
                try:
                    found = fut.result()
                except Exception:
                    found = []
                if found:
                    bypassed.extend(found)
                    # Print main thread mein — interleave se bachne ke liye
                    print(f"      {Fore.RED}{'─'*3} 403 BYPASS FOUND: {url}")
                    for b in found:
                        print(f"          {Fore.RED}{b}")

        if bypassed:
            with open(output_file, "w") as f:
                f.write("\n".join(sorted(set(bypassed))) + "\n")

        return len(set(bypassed))

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

# ── v14: External-tool rate limiting (Go tools ke liye — StealthEngine sirf
#         Python requests govern karta tha; asli traffic to in tools se aata hai).
#         Politeness + WAF/rate-limit evasion. .env se override karo.
HTTPX_RATE_LIMIT     = os.getenv("GP_HTTPX_RL",    "150")   # httpx -rl (req/sec)
NAABU_RATE           = os.getenv("GP_NAABU_RATE",  "1000")  # naabu -rate (pkt/sec)
KATANA_RATE_LIMIT    = os.getenv("GP_KATANA_RL",   "150")   # katana -rl (req/sec)
KATANA_CONCURRENCY   = os.getenv("GP_KATANA_C",    "10")    # katana -c
# v14: Python-side sweeps ki parallelism (StealthEngine thread-safe hai)
SWEEP_WORKERS        = int(os.getenv("GP_SWEEP_WORKERS", "15"))

# ── v14.2 tuning ────────────────────────────────────────────────────────────────
# favicon probe har host pe ek EXTRA /favicon.ico request maarta hai (~2x volume).
# Bade scope pe mehenga — default OFF, --favicon ya GP_FAVICON=1 se on.
FAVICON_ENABLED      = os.getenv("GP_FAVICON", "0") == "1"
# katana scope-lock strategy: 'rdn' (root domain — *.example.com wildcard programs
# ke liye behtar, sibling subs follow honge) vs 'fqdn' (exact host — tightest) vs
# 'dn' (domain name). Default rdn — most BB scopes root-domain wildcard hote hain.
KATANA_FIELD_SCOPE   = os.getenv("GP_KATANA_SCOPE", "rdn")
# GitHub dork pagination — kitne pages tak jaao (100/page). 0/1 = sirf first page.
GITHUB_MAX_PAGES     = int(os.getenv("GP_GITHUB_PAGES", "3"))

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
    "asnmap", "trufflehog",
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
                 force: bool = False,
                 passive: bool = False):
        self.targets      = self._load_targets(target_file)
        self.session_id   = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        self.base_dir     = os.path.abspath(output_dir) if output_dir else f"DEEP_RECON_{self.session_id}"
        self.dry_run      = dry_run
        self.phases       = phases or list(PHASE_MARKERS.keys())
        # FIX v12: explicit --passive flag, not inferred from phases list.
        # Agar koi --phases enum,cloud,github kare toh passive nahi hona chahiye.
        self._passive_mode = passive
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

        # FIX: nuclei template update guard — MAX_DOMAINS_PARALLEL>1 hone par
        # do threads ek saath update chala dete the (race). Lock se ek hi baar.
        self._nuclei_lock = threading.Lock()
        self._nuclei_updated = False

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
            with open(RESOLVERS_FILE, encoding="utf-8", errors="replace") as fh:
                count = sum(1 for _ in fh)
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
                # FIX v12: self._http — consistent stealth across all HTTP calls
                r = self._http.get(url, timeout=30)
                if r is not None and r.status_code == 200 and len(r.text) > 500:
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
        # Use self._http — retry + proxy + UA rotation
        for attempt in range(3):
            try:
                r = self._http.post(
                    DISCORD_WEBHOOK_URL,
                    json={"content": f"🚨 **GHOST PROTOCOL ALERT**\n```{message}```"},
                    timeout=10,
                )
                if r and r.status_code in (200, 204):
                    return
                if r and r.status_code == 429:
                    retry_after = int(r.headers.get("Retry-After", 5))
                    time.sleep(retry_after)
                    continue
                # Non-429, non-success — break out, no point retrying
                break
            except Exception as e:
                self.logger.warning(f"Discord notify attempt {attempt+1} failed: {e}")
                time.sleep(2)

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

    def _parse_httpx_json(self, json_file: str, live_file: str,
                          live_200: str, live_all: str):
        """
        v13: httpx -json output parse karo — status_code field se RELIABLE bucketing.
        Purana substring approach ('[200]' in line) content-length se collide hota tha.

        Produces:
          live_file → clean text  : url [status] [server] title   (downstream display)
          live_200  → url-only    : sirf status == 200
          live_all  → url-only    : koi bhi HTTP response (200/30x/401/403/5xx) = full surface
        """
        # v14: record ab dict — favicon/ip/cname/location bhi capture
        records = []
        favicon_map: dict = {}   # favicon_hash → [urls]
        if self.file_has_content(json_file):
            with open(json_file, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    url = obj.get("url") or obj.get("input") or ""
                    if not url:
                        continue
                    raw_sc = obj.get("status_code", obj.get("status-code", 0))
                    try:
                        sc = int(raw_sc)
                    except (TypeError, ValueError):
                        sc = 0
                    server = obj.get("webserver") or obj.get("web_server") or ""
                    title  = (obj.get("title") or "").replace("\n", " ").strip()
                    fav    = str(obj.get("favicon") or obj.get("favicon_hash") or "").strip()
                    ip     = obj.get("host") or obj.get("ip") or ""
                    cname  = obj.get("cname") or []
                    if isinstance(cname, list):
                        cname = ",".join(cname)
                    location = obj.get("location") or ""
                    rec = {"url": url, "sc": sc, "server": server, "title": title,
                           "favicon": fav, "ip": ip, "cname": cname, "location": location}
                    records.append(rec)
                    if fav and fav not in ("0", "-", "None"):
                        favicon_map.setdefault(fav, []).append(url)

        # Clean text live.txt — status hamesha doosra field, content-length yahan nahi
        with open(live_file, "w") as f:
            for r in records:
                sb = f" [{r['server']}]" if r["server"] else ""
                tb = f" {r['title']}" if r["title"] else ""
                f.write(f"{r['url']} [{r['sc']}]{sb}{tb}\n")

        self._write_unique_sorted_lines(live_200, [r["url"] for r in records if r["sc"] == 200])
        # live_all: koi bhi real HTTP response. sc>0 matlab httpx ne status report kiya.
        self._write_unique_sorted_lines(live_all, [r["url"] for r in records if r["sc"] > 0])
        # FIX: 403/401 bucket status_code se reliably. (auth-walled surface = bypass gold)
        d_dir_base = os.path.dirname(live_all) or "."
        live_403 = os.path.join(d_dir_base, "live_403.txt")
        self._write_unique_sorted_lines(live_403, [r["url"] for r in records if r["sc"] in (401, 403)])

        # v14 FIX: non-standard-port live — root pe reliably likho (status-derived).
        # Pehle _extract_nonstandard_live_entries live.txt pe '[200]' substring
        # match karta tha (title/server collision → false bucket). Ab structured.
        nonstd = []
        for r in records:
            if r["sc"] <= 0:
                continue
            port = self._extract_port_from_url(r["url"])
            if port not in STANDARD_PORTS:
                sb = f" [{r['server']}]" if r["server"] else ""
                tb = f" {r['title']}" if r["title"] else ""
                nonstd.append(f"{r['url']} [{r['sc']}]{sb}{tb}")
        self._write_unique_sorted_lines(os.path.join(d_dir_base, "nonstandard_live.txt"), nonstd)

        # v14: favicon clustering — ek hi hash 2+ hosts pe = same app / possible
        # hidden origin / staging clone. BB pivoting ka high-signal artifact.
        evidence_dir = os.path.join(d_dir_base, "evidence")
        os.makedirs(evidence_dir, exist_ok=True)
        clusters = {h: u for h, u in favicon_map.items() if len(set(u)) >= 2}
        if clusters:
            with open(os.path.join(evidence_dir, "favicon_clusters.txt"), "w") as f:
                for h, urls in sorted(clusters.items(), key=lambda x: -len(set(x[1]))):
                    f.write(f"# favicon hash {h} — {len(set(urls))} hosts\n")
                    for u in sorted(set(urls)):
                        f.write(f"  {u}\n")
                    f.write("\n")

        # v14: IP/CNAME infra map — asset ownership + shared-host pivoting
        infra_lines = []
        for r in records:
            if r["ip"] or r["cname"]:
                infra_lines.append(f"{r['url']}\t{r['ip']}\t{r['cname']}")
        if infra_lines:
            self._write_unique_sorted_lines(os.path.join(evidence_dir, "infra_map.txt"), infra_lines)

    def _extract_httpx_200_urls(self, live_file: str, out_file: str):
        # LEGACY (v13 mein replace by _parse_httpx_json) — retained for compatibility
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
              f"({Fore.RED}-{dead} unresolved{Fore.WHITE})")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, phase)
        return resolved

    def _get_resolved_path(self, d_dir: str) -> str:
        """FIX: Correct resolved path — final ya regular, jo bhi exist kare."""
        final = f"{d_dir}/resolved_subs_final.txt"
        regular = f"{d_dir}/resolved_subs.txt"
        return final if self.file_has_content(final) else regular

    def _resolve_hosts(self, hosts: list) -> dict:
        """Resolve hosts → {host: set(ips)} via dnsx (socket fallback)."""
        mapping: dict = {}
        hosts = [h for h in hosts if h]
        if not hosts:
            return mapping
        if self.available.get("dnsx"):
            tag     = random.randint(100000, 999999)
            tmp_in  = self._tmpfile(f"wc_in_{tag}.txt")
            tmp_out = self._tmpfile(f"wc_out_{tag}.txt")
            self._write_unique_sorted_lines(tmp_in, hosts)
            rflag = ""
            if getattr(self, "resolvers", "") and os.path.exists(self.resolvers):
                rflag = f"-r {self._q(self.resolvers)} "
            self.run_cmd(
                f"dnsx -l {self._q(tmp_in)} -silent -a -resp {rflag}"
                f"-t {THREADS_DNSX} -o {self._q(tmp_out)}",
                timeout=180,
            )
            if self.file_has_content(tmp_out):
                with open(tmp_out, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        m = re.match(r"^(\S+)\s+\[([0-9a-fA-F:.]+)\]", line.strip())
                        if m:
                            host = m.group(1).rstrip(".").lower()
                            mapping.setdefault(host, set()).add(m.group(2))
        else:
            for h in hosts:
                try:
                    for info in socket.getaddrinfo(h, None):
                        mapping.setdefault(h.lower(), set()).add(info[4][0])
                except Exception:
                    pass
        return mapping

    def _detect_wildcard_ips(self, parent: str) -> set:
        """Random labels resolve karo — agar resolve hue to parent wildcard hai.
        Returns wildcard IP set (khaali = wildcard nahi)."""
        alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
        probes = [
            f"{''.join(random.choice(alphabet) for _ in range(16))}.{parent}"
            for _ in range(3)
        ]
        wc: set = set()
        for ips in self._resolve_hosts(probes).values():
            wc |= ips
        return wc

    def _filter_wildcards(self, out_file: str, parent: str):
        """Tool-agnostic wildcard filter — jo hosts SIRF wildcard IP pe resolve
        karte hain unhe drop karo. massdns/kisi bhi fallback ke FPs saaf."""
        if not self.file_has_content(out_file):
            return
        wc_ips = self._detect_wildcard_ips(parent)
        if not wc_ips:
            return  # wildcard domain nahi — kuch filter nahi karna
        with open(out_file, encoding="utf-8", errors="replace") as f:
            hosts = [l.strip().lower() for l in f if l.strip()]
        if not hosts:
            return
        mapping = self._resolve_hosts(hosts)
        kept, dropped = [], 0
        for h in hosts:
            ips = mapping.get(h, set())
            if ips and ips <= wc_ips:      # sirf wildcard IP pe resolve → junk
                dropped += 1
                continue
            kept.append(h)
        if dropped:
            self._write_unique_sorted_lines(out_file, kept)
            print(f"      {Fore.RED}-{dropped}{Fore.WHITE} wildcard FPs filtered ({parent})")

    def _run_brute(self, domain: str, out_file: str):
        self._run_brute_chain(domain, out_file)
        # v14.2: wildcard filter — massdns/kisi bhi tool ke wildcard FPs hatao
        self._filter_wildcards(out_file, domain)

    def _run_brute_chain(self, domain: str, out_file: str):
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
            return f"{d_dir}/live.txt", f"{d_dir}/live_200.txt", f"{d_dir}/live_all.txt"
        if not self.force and self._phase_is_done(d_dir, "probe"):
            live_file = f"{d_dir}/live.txt"
            live_200  = f"{d_dir}/live_200.txt"
            live_all  = f"{d_dir}/live_all.txt"
            return live_file, live_200, live_all

        t0 = self.phase_timer("PHASE 2: PORT SCAN + PORT-WISE PROBING")
        port_file = f"{d_dir}/open_ports.txt"
        ports_dir = f"{d_dir}/ports"
        os.makedirs(ports_dir, exist_ok=True)

        # ── 2a. Port Scanning ────────────────────────────────────────────────
        self.run_cmd(
            f"naabu -l {self._q(resolved)} -p {NAABU_PORTS} -silent "
            f"-t {THREADS_NAABU} -rate {NAABU_RATE} -o {self._q(port_file)}",
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

        # ── 2c. httpx Probe (JSON mode — reliable status parsing) ─────────────
        # FIX v13: -json output use karo. Pehle text format mein "[200]"/"[403]"
        # substring match content-length se collide hota tha (e.g. content-length=200
        # → galat 200-OK bucket). Ab status_code field se positionally parse karte hain.
        live_file = f"{d_dir}/live.txt"      # clean text: url [status] [server] title
        live_200  = f"{d_dir}/live_200.txt"  # strict 200 only
        live_all  = f"{d_dir}/live_all.txt"  # 200 + 30x + 401 + 403 + … = full attack surface
        live_json = self._tmpfile(f"httpx_{domain}.jsonl")
        input_for_httpx = port_file if self.file_has_content(port_file) else resolved

        # v14.2: enriched probe WITH graceful degradation.
        # -favicon (mmh3 hash → asset clustering) har host pe extra request maarta
        # hai — isliye FAVICON_ENABLED ke peeche gated. -ip -cname (infra map),
        # -location (redirect chains). CRITICAL: agar httpx build mein koi enrichment
        # flag support nahi (purana version), to enriched run khali output degा →
        # saare live hosts "gayab" → pura pipeline dead (silent). Isse bachne ke liye:
        # enriched output khali AND input mein hosts hain → plain flags se dobara probe.
        input_has_hosts = self.file_has_content(input_for_httpx)
        fav_flag = "-favicon " if FAVICON_ENABLED else ""
        enriched = (
            f"httpx -l {self._q(input_for_httpx)} -silent -t {THREADS_HTTPX} "
            f"-rl {HTTPX_RATE_LIMIT} "
            f"-sc -td -title -web-server -content-length -cdn -follow-redirects "
            f"{fav_flag}-ip -cname -location -json -o {self._q(live_json)}"
        )
        self.run_cmd(enriched, "HTTP probing (all ports, JSON, enriched)")

        if not self.file_has_content(live_json) and input_has_hosts and not self.dry_run:
            # Enrichment flags ne kaam nahi kiya (version mismatch ya genuine 0 live).
            # Core flags se dobara — findings kabhi silently na khoyein.
            self.logger.warning(
                "Enriched httpx produced no output — retrying with core flags "
                "(favicon/ip/cname/location enrichment skipped this run)."
            )
            print(f"{Fore.YELLOW}      [~] Enriched probe empty — core-flag fallback...")
            plain = (
                f"httpx -l {self._q(input_for_httpx)} -silent -t {THREADS_HTTPX} "
                f"-rl {HTTPX_RATE_LIMIT} "
                f"-sc -title -web-server -content-length -follow-redirects "
                f"-json -o {self._q(live_json)}"
            )
            self.run_cmd(plain, "HTTP probing (core-flag fallback)")

        self._parse_httpx_json(live_json, live_file, live_200, live_all)

        live_count = self.count_lines(live_file)
        ok_count   = self.count_lines(live_200)
        all_count  = self.count_lines(live_all)
        print(f"\n      Live responses: {Fore.GREEN}{live_count}")
        print(f"      200 OK:         {Fore.GREEN}{ok_count}")
        print(f"      Live (all SC):  {Fore.GREEN}{all_count}{Fore.WHITE} "
              f"← pipeline ab ispe chalega (403/401/30x bhi)")

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

            # v14 FIX: status token (parts[1] == '[200]') se count, na ki whole-line
            # substring — warna title/server mein '[200]' ho toh false count.
            ok_entries = [e for e in entries
                          if len(e.split()) > 1 and e.split()[1] == "[200]"]
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

        # ── 2e. Non-standard port live — Discord alert ───────────────────────
        # v14: nonstandard_live.txt ab _parse_httpx_json status-derived likhta hai
        # (200 + 401/403/30x bhi — weird port pe koi bhi live service interesting).
        nonstd_live = f"{d_dir}/nonstandard_live.txt"
        ns_count = self.count_lines(nonstd_live)
        if ns_count > 0:
            print(f"\n{Fore.RED}      🎯 NON-STANDARD PORT LIVE: {ns_count}")
            self.notify_discord(
                f"[{domain}] {ns_count} non-standard port services! See {nonstd_live}"
            )

        # ── 2f. VHost Bruteforce ─────────────────────────────────────────────
        # v13: live_all use karo — 403/401 hosts ke peeche bhi vhosts ho sakte hain
        if VHOST_BRUTE and self.file_has_content(live_all):
            self._run_vhost_brute(domain, d_dir, live_all)

        # ── 2g. Technology Fingerprinting ────────────────────────────────────
        if self.available.get("wappalyzergo") and self.file_has_content(live_all):
            self.run_cmd(
                f"wappalyzergo -f {self._q(live_all)} -o {self._q(d_dir + '/evidence/technologies.json')} 2>/dev/null",
                "Technology fingerprinting"
            )

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "probe")
        return live_file, live_200, live_all

    def _extract_port_from_url(self, url: str) -> str:
        """URL se port extract karo."""
        try:
            p = urlparse(url)
            if p.port:
                return str(p.port)
            return "443" if p.scheme == "https" else "80"
        except Exception:
            return "80"

    def _run_vhost_brute(self, domain: str, d_dir: str, live_urls: str):
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
        if self.file_has_content(live_urls):
            with open(live_urls) as f:
                targets = [l.strip() for l in f if l.strip()][:5]

        found_total = 0
        for target in targets:
            tmp_out = self._tmpfile(f"vhost_{hashlib.md5(target.encode()).hexdigest()[:8]}.json")
            self.run_cmd(
                f"ffuf -u {target} -H 'Host: FUZZ.{domain}' "
                f"-w {self._q(wl)} -mc 200,301,302,403 "
                f"-fs 0 -t 50 -s "
                f"-o {self._q(tmp_out)} -of json 2>/dev/null",
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
            print("      VHosts: none found")

    # ── PHASE 3: HISTORICAL URLS ───────────────────────────────────────────────
    def phase3_historical_urls(self, domain: str, d_dir: str) -> str:
        if not self._phase_enabled("history"):
            return f"{d_dir}/historical_urls.txt"
        if not self.force and self._phase_is_done(d_dir, "history"):
            return f"{d_dir}/historical_urls.txt"

        t0 = self.phase_timer("PHASE 3: HISTORICAL URLS")
        hist_file = f"{d_dir}/historical_urls.txt"

        # v13: --mc filter hata diya — recon mein 401/403/404 historical endpoints bhi
        # valuable hote hain (purane admin paths, deprecated API routes). Sab le aao.
        # FIX: --subs add kiya — iske bina gau sirf apex domain ke URLs deta hai,
        # subdomains (api., admin., dev.) ke historical endpoints chhoot jaate the.
        self.run_cmd(
            f"gau {self._q(domain)} --subs --threads 5 -o {self._q(hist_file)}",
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
    def phase4_scan_crawl(self, domain: str, d_dir: str, live_urls: str, hist_file: str) -> str:
        if not self._phase_enabled("scan"):
            return f"{d_dir}/all_endpoints.txt"
        if not self.force and self._phase_is_done(d_dir, "scan"):
            return f"{d_dir}/all_endpoints.txt"

        t0 = self.phase_timer("PHASE 4: SCAN + CRAWL")
        evidence  = f"{d_dir}/evidence"
        endpoints = f"{d_dir}/endpoints.txt"

        # Nuclei templates update (once per session, thread-safe)
        with self._nuclei_lock:
            if not self._nuclei_updated:
                self._update_nuclei_templates()
                self._nuclei_updated = True

        # Nuclei — SmartNuclei se smart command build karo
        _nuclei = SmartNuclei(rate_limit=NUCLEI_RATE_LIMIT, deep=False)
        nuclei_cmd = _nuclei.build_cmd(
            targets_file=self._q(live_urls),
            output_file=f"{evidence}/vulns.txt",
            severity="critical,high,medium"
        )
        # Priority CVEs bhi alag run karo
        nuclei_cve_cmd = _nuclei.build_cve_cmd(
            targets_file=self._q(live_urls),
            output_file=f"{evidence}/vulns_cve.txt"
        )
        self.run_cmd(nuclei_cmd, "Nuclei smart scan (critical/high/medium)")
        self.run_cmd(nuclei_cve_cmd, "Nuclei priority CVEs")
        vuln_count = self.count_lines(f"{evidence}/vulns.txt") + self.count_lines(f"{evidence}/vulns_cve.txt")
        if vuln_count > 0:
            print(f"{Fore.RED}      🔥 VULNS: {vuln_count}")
            self.notify_discord(f"[{domain}] Nuclei: {vuln_count} critical/high!")

        # Katana crawl
        # v14.2: -rl (polite rate) + -c (concurrency) + -fs {scope} (scope-lock —
        # crawler ko off-scope wander karne se roko; BB mein off-scope = report reject).
        # Default 'rdn' (root domain) — *.example.com wildcard programs mein sibling
        # in-scope subdomains bhi follow honge. 'fqdn' se sirf exact host (too tight).
        self.run_cmd(
            f"katana -list {self._q(live_urls)} -jc -d {KATANA_DEPTH} -kf all "
            f"-rl {KATANA_RATE_LIMIT} -c {KATANA_CONCURRENCY} -fs {self._q(KATANA_FIELD_SCOPE)} "
            f"-silent -o {self._q(endpoints)}",
            f"Katana (depth={KATANA_DEPTH}, scope={KATANA_FIELD_SCOPE})"
        )

        # Merge endpoints + historical
        merged = f"{d_dir}/all_endpoints.txt"
        total = self._merge_unique(endpoints, hist_file, out=merged)
        print(f"      Total endpoints: {Fore.GREEN}{total}")

        # Screenshots
        # FIX: gowitness v3 API — old --disable-db flag removed
        if self.available.get("gowitness"):
            gowitness_cmd = (
                f"gowitness scan file -f {self._q(live_urls)} "
                f"--threads {THREADS_GOWITNESS} "
                f"--screenshot-path {self._q(evidence + '/screenshots')}"
            )
            # Fallback for older gowitness
            result = self.run_cmd_list(["gowitness", "--version"])
            if result and "v2" in result.lower():
                gowitness_cmd = (
                    f"gowitness file -f {self._q(live_urls)} "
                    f"--threads {THREADS_GOWITNESS} "
                    f"--screenshot-path {self._q(evidence + '/screenshots')} --disable-db"
                )
            self.run_cmd(gowitness_cmd, "Screenshots (gowitness)")

        # FIX v12: subzy Phase 4 se remove — Phase 9 dedicated takeover phase hai
        # Duplicate work tha aur alag output files mein save hota tha (takeover.txt vs takeover_candidates.txt)
        # Phase 9 mein subzy properly run hota hai with correct output path

        # Param Discovery
        if PARAM_DISCOVERY and self.available.get("paramspider") and self.file_has_content(live_urls):
            self._run_param_discovery(domain, d_dir, live_urls, merged)

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "scan")
        return merged

    def _run_param_discovery(self, domain: str, d_dir: str, live_urls: str, merged: str):
        """paramspider se parameter discovery."""
        print(f"{Fore.CYAN}  [*] Param discovery (paramspider)...")
        param_out = f"{d_dir}/evidence/params.txt"
        self.run_cmd(
            f"paramspider -d {self._q(domain)} --quiet -o {self._q(param_out)} 2>/dev/null",
            timeout=300
        )
        if self.file_has_content(param_out):
            total = self._merge_unique(merged, param_out, out=merged)
            print(f"      After param discovery: {Fore.GREEN}{total} endpoints")

    def _extract_subjs_urls(self, live_urls: str, js_urls: str):
        js_raw = self.run_cmd(
            f"subjs -i {self._q(live_urls)} -c 20",
            "Extracting JS URLs",
            allow_exit_codes=(0, 1)
        )
        if not js_raw:
            # Compatibility fallback for older subjs builds
            js_raw = self.run_cmd(
                f"cat {self._q(live_urls)} | subjs -c 20",
                "Extracting JS URLs (fallback)",
                allow_exit_codes=(0, 1)
            )
        values = js_raw.splitlines() if js_raw else []
        self._write_unique_sorted_lines(js_urls, values)

    # v14: keyword-context regex (medium confidence — [unverified])
    _JS_KV_REGEX = re.compile(
        r'(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|'
        r'password|passwd|private[_-]?key|aws[_-]?secret|client[_-]?secret|'
        r'stripe[_-]?key|sendgrid|twilio|github[_-]?token|firebase)'
        r'[\s:=\'"]+([A-Za-z0-9/+_.=-]{16,})',
        re.IGNORECASE
    )
    # v14: standalone high-signal token shapes (low-FP — [high-signal]).
    # Ye providers ke fixed formats hain, keyword context ki zaroorat nahi.
    _JS_HIGH_SIGNAL = [
        (re.compile(r'AIza[0-9A-Za-z_\-]{35}'),                      "google_api_key"),
        (re.compile(r'AKIA[0-9A-Z]{16}'),                           "aws_access_key_id"),
        (re.compile(r'gh[pousr]_[0-9A-Za-z]{36}'),                  "github_token"),
        (re.compile(r'xox[baprs]-[0-9A-Za-z\-]{10,}'),              "slack_token"),
        (re.compile(r'sk_live_[0-9A-Za-z]{24,}'),                   "stripe_secret_live"),
        (re.compile(r'rk_live_[0-9A-Za-z]{24,}'),                   "stripe_restricted_live"),
        (re.compile(r'SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}'), "sendgrid_key"),
        (re.compile(r'sk-[A-Za-z0-9]{20,}T3BlbkFJ[A-Za-z0-9]{20,}'),"openai_key"),
        (re.compile(r'glpat-[0-9A-Za-z_\-]{20}'),                   "gitlab_pat"),
        (re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'), "private_key"),
        (re.compile(r'eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}'), "jwt"),
        (re.compile(r'AC[a-z0-9]{32}'),                             "twilio_sid"),
        (re.compile(r'[0-9a-f]{32}-us[0-9]{1,2}'),                  "mailchimp_key"),
    ]

    @staticmethod
    def _is_probable_secret(val: str) -> bool:
        """Keyword-context matches ke liye value-shape gate — route strings,
        function/property refs, aur non-secret literals kill karta hai."""
        val = val.strip().strip('\'"').strip()
        if len(val) < 12:
            return False
        if val[0] in "/.#?" or val.startswith("../"):          # routes / paths
            return False
        if re.fullmatch(r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+", val):  # a.b.c ref
            return False
        if val.lower() in {
            "true", "false", "null", "undefined", "password", "changeme",
            "reset-password", "reset_password", "example", "your_api_key",
        }:
            return False
        has_upper = any(c.isupper() for c in val)
        has_lower = any(c.islower() for c in val)
        has_digit = any(c.isdigit() for c in val)
        is_hex      = bool(re.fullmatch(r"[0-9a-fA-F]{16,}", val))
        is_tokenish = bool(re.fullmatch(r"[A-Za-z0-9_\-]{20,}", val)) and has_digit \
                      and (has_upper or has_lower)
        return is_hex or is_tokenish or (has_upper and has_lower and has_digit and len(val) >= 16)

    def _hunt_js_secrets_python(self, js_urls_file: str, out_file: str):
        """
        Python-based JS secret hunt (shell/xargs injection se bachne ke liye).
        v14: parallelized (SWEEP_WORKERS) + high-signal token patterns.
        """
        if not self.file_has_content(js_urls_file):
            return
        with open(js_urls_file, encoding="utf-8", errors="replace") as f:
            urls = [line.strip() for line in f if line.strip()][:300]
        if not urls:
            return

        def _scan_one(u: str) -> list:
            out = []
            try:
                r = self._http.get(u, timeout=10, allow_redirects=True)
                if r is None or r.status_code >= 400:
                    return out
                body = r.text[:1_500_000]
            except Exception:
                return out
            # High-signal standalone tokens — low FP
            for rx, name in self._JS_HIGH_SIGNAL:
                for m in rx.findall(body):
                    val = (m if isinstance(m, str) else (m[0] if m else ""))[:120]
                    if val:
                        out.append(f"[high-signal] {name} :: {u} :: {val}")
            # Keyword-context — medium confidence
            for m in self._JS_KV_REGEX.finditer(body):
                val = m.group(1) if m.lastindex else ""
                if not self._is_probable_secret(val):
                    continue
                out.append(f"[unverified] {u} :: {m.group(0)[:200]}")
            return out

        findings = set()
        with ThreadPoolExecutor(max_workers=SWEEP_WORKERS) as ex:
            for res in ex.map(_scan_one, urls):
                findings.update(res)

        # High-signal upar aaye — triage friendly
        self._write_unique_sorted_lines(
            out_file,
            sorted(findings, key=lambda x: (not x.startswith("[high-signal]"), x))
        )

    def _run_trufflehog(self, scan_dir: str, out_file: str, label: str = "") -> int:
        """
        TruffleHog v3 — filesystem scan on a directory of JS/text files.

        TruffleHog v3 install:
          curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin
          OR: go install github.com/trufflesecurity/trufflehog/v3@latest

        Returns: number of verified/unverified secrets found.
        """
        if not self.available.get("trufflehog"):
            return 0
        if not os.path.isdir(scan_dir):
            return 0

        th_raw = self._tmpfile(f"trufflehog_{os.path.basename(scan_dir)}.jsonl")

        # TruffleHog v3 filesystem scan
        # --only-verified  : sirf confirmed secrets (low FP) — comment out agar aur chahiye
        # --json           : machine-readable JSONL output
        # --no-update      : startup mein update skip karo (faster)
        cmd = (
            f"trufflehog filesystem {self._q(scan_dir)} "
            f"--json --no-update "
            f"2>/dev/null > {self._q(th_raw)}"
        )
        self.run_cmd(cmd, f"TruffleHog scan{' (' + label + ')' if label else ''}", timeout=300)

        # Parse JSONL output
        findings = []
        verified_count   = 0
        unverified_count = 0

        if self.file_has_content(th_raw):
            with open(th_raw, encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    detector  = obj.get("DetectorName", "Unknown")
                    verified  = obj.get("Verified", False)
                    raw_val   = obj.get("Raw", "") or obj.get("RawV2", "")
                    redacted  = obj.get("Redacted", "")

                    # Source file path extract karo
                    src_meta = obj.get("SourceMetadata", {})
                    file_path = ""
                    for src_type in ["Filesystem", "Github", "URL"]:
                        data = src_meta.get("Data", {}).get(src_type, {})
                        file_path = (
                            data.get("file") or data.get("link") or
                            data.get("repository") or ""
                        )
                        if file_path:
                            break

                    # Display value — redacted agar available, warna raw truncated
                    display_val = redacted if redacted else (raw_val[:60] + "..." if len(raw_val) > 60 else raw_val)
                    verified_str = f"{Fore.RED}[VERIFIED]" if verified else f"{Fore.YELLOW}[unverified]"
                    short_path   = os.path.basename(file_path) if file_path else "?"

                    entry = {
                        "detector":  detector,
                        "verified":  verified,
                        "value":     display_val,
                        "file":      file_path,
                        "raw":       raw_val[:200],
                    }
                    findings.append(entry)

                    if verified:
                        verified_count += 1
                    else:
                        unverified_count += 1

                    print(
                        f"      {verified_str} {Fore.WHITE}{detector}"
                        f"{Fore.CYAN}  [{short_path}]"
                        f"  {Fore.WHITE}{display_val[:50]}"
                    )

        if findings:
            # Save human-readable + JSON
            txt_lines = []
            for idx, f in enumerate(findings, 1):
                v_tag = "*** VERIFIED ***" if f["verified"] else "unverified"
                txt_lines.append(
                    f"[{idx}] {v_tag} | {f['detector']} | {f['file']}\n"
                    f"      Value: {f['value']}\n"
                )
            self._write_unique_sorted_lines(out_file, txt_lines)

            json_out = out_file.replace(".txt", ".json")
            with open(json_out, "w") as jf:
                json.dump({
                    "total":      len(findings),
                    "verified":   verified_count,
                    "unverified": unverified_count,
                    "findings":   findings,
                }, jf, indent=2)

        return len(findings)

    # ── PHASE 5: JS SECRET HUNTING ─────────────────────────────────────────────
    def phase5_js_secrets(self, domain: str, d_dir: str, live_urls: str):
        if not self._phase_enabled("js"):
            return
        if not self.force and self._phase_is_done(d_dir, "js"):
            return
        if not self.file_has_content(live_urls):
            print(f"{Fore.YELLOW}      [~] No live_urls input — JS analysis skip.")
            return

        t0 = self.phase_timer("PHASE 5: JS SECRET HUNTING")
        evidence = f"{d_dir}/evidence"
        js_urls  = f"{d_dir}/js_urls.txt"

        # FIX v12: subjs nahi hai toh Python fallback use karo — phase skip nahi karo
        if self.available.get("subjs"):
            self._extract_subjs_urls(live_urls, js_urls)
        else:
            print(f"{Fore.YELLOW}      [~] subjs not found — katana JS extraction use kar rahe hain")
            # katana JS link extraction fallback
            self.run_cmd(
                f"katana -list {self._q(live_urls)} -jc -d 2 -kf all -silent "
                f"-ef css,font,woff,woff2,png,jpg,gif,svg,ico "
                f"| grep '\\.js' > {self._q(js_urls)} 2>/dev/null",
                allow_exit_codes=(0, 1)
            )
            if not self.file_has_content(js_urls):
                # Last fallback: httpx pe grep karo JS links ke liye
                # FIX: -match-regex deprecated → -mr (newer httpx), v12 fix yahan reh gaya tha
                self.run_cmd(
                    f"httpx -l {self._q(live_urls)} -silent -mr '\\.js([?#]|$)' "
                    f"-o {self._q(js_urls)} 2>/dev/null",
                    allow_exit_codes=(0, 1)
                )

        js_count = self.count_lines(js_urls)
        print(f"      JS files: {Fore.GREEN}{js_count}")

        if self.file_has_content(js_urls):
            # Save copy for phase11 (js_diff) — evidence/js_files.txt
            shutil.copy2(js_urls, f"{evidence}/js_files.txt")

            # ── Step A: Python regex-based hunt ──────────────────────────
            secrets_file = f"{evidence}/js_secrets.txt"
            self._hunt_js_secrets_python(js_urls, secrets_file)
            regex_sc = self.count_lines(secrets_file)

            # ── Step B: TruffleHog scan (700+ detectors, verified secrets)
            th_findings = 0
            if self.available.get("trufflehog"):
                # JS files ko locally download karo — trufflehog filesystem scan ke liye
                js_download_dir = self._tmpfile(f"js_dl_{domain}")
                os.makedirs(js_download_dir, exist_ok=True)
                print(f"{Fore.CYAN}  [*] Downloading JS files for TruffleHog scan...")

                downloaded = 0
                with open(js_urls, encoding="utf-8", errors="replace") as f:
                    urls_to_dl = [l.strip() for l in f if l.strip()][:150]

                def _dl_js(url):
                    try:
                        r = self._http.get(url, timeout=10, allow_redirects=True)
                        if r and r.status_code == 200 and len(r.text) > 50:
                            # URL se safe filename banao
                            fname = re.sub(r'[^a-zA-Z0-9_.-]', '_', url)[-120:] + ".js"
                            fpath = os.path.join(js_download_dir, fname)
                            with open(fpath, "w", encoding="utf-8", errors="replace") as fout:
                                fout.write(r.text)
                            return True
                    except Exception:
                        pass
                    return False

                with ThreadPoolExecutor(max_workers=20) as ex:
                    results = list(ex.map(_dl_js, urls_to_dl))
                downloaded = sum(results)
                print(f"      Downloaded: {Fore.GREEN}{downloaded} JS files")

                if downloaded > 0:
                    th_out = f"{evidence}/trufflehog_js.txt"
                    th_findings = self._run_trufflehog(
                        js_download_dir, th_out, label="live JS"
                    )
                    # Cleanup downloaded JS files (can be large)
                    shutil.rmtree(js_download_dir, ignore_errors=True)
            else:
                print(f"{Fore.YELLOW}      [~] trufflehog not found — install: "
                      f"curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin")

            # ── Combined results ──────────────────────────────────────────
            total_sc = regex_sc + th_findings
            if total_sc > 0:
                print(f"{Fore.RED}      🔑 SECRETS: {total_sc} "
                      f"(regex: {regex_sc}, trufflehog: {th_findings})")
                self.notify_discord(
                    f"[{domain}] 🔑 {total_sc} secrets in JS! "
                    f"(regex:{regex_sc}, trufflehog:{th_findings})"
                )
            else:
                print("      JS Secrets: none found")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "js")

    # ── PHASE 6: DATA MINING ──────────────────────────────────────────────────
    def phase6_data_mining(self, domain: str, d_dir: str, live_urls: str, merged_endpoints: str):
        """
        FIX: live_urls parameter now properly passed from caller (was using hardcoded path before).
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
                f"corsy -i {self._q(live_urls)} -t 10 --headers 'User-Agent: Mozilla' "
                f"-o {self._q(evidence + '/cors.txt')} 2>/dev/null",
                "CORS check (corsy)"
            )
        else:
            # FIX v12: -match-regex deprecated → -mr (newer httpx versions)
            self.run_cmd(
                f"httpx -l {self._q(live_urls)} -silent "
                f"-H 'Origin: https://evil.com' "
                f"-mr 'Access-Control-Allow-Origin: https://evil.com' "
                f"-o {self._q(evidence + '/cors.txt')} 2>/dev/null",
                "Basic CORS check (httpx)"
            )

        # 403 Bypass
        targets_403 = self._tmpfile(f"403_{domain}.txt")
        # FIX: prefer reliable live_403.txt (status_code-derived). Agar wo na ho
        # (purana run / probe phase skip) toh legacy substring extractor pe fallback.
        live_403_file = f"{d_dir}/live_403.txt"
        if self.file_has_content(live_403_file):
            shutil.copy2(live_403_file, targets_403)
        else:
            self._extract_403_urls(f"{d_dir}/live.txt", targets_403)
        if self.file_has_content(targets_403):
            # Bypass403 class — full 19-header + path + verb bypass
            bc = Bypass403.run(
                targets_file=targets_403,
                output_file=f"{evidence}/403_bypass.txt",
                engine=self._http,
                max_targets=cfg.max_403_targets,
                workers=SWEEP_WORKERS,
            )
            if bc > 0:
                print(f"{Fore.RED}      🚪 403 BYPASSED: {bc}")
                self.notify_discord(f"[{domain}] {bc} 403 bypasses!")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "mine")

    # ── PHASE 7: CLOUD ASSET ENUM ─────────────────────────────────────────────
    def phase7_cloud_enum(self, domain: str, d_dir: str):
        if not CLOUD_ENUM_ENABLED or not self._phase_enabled("cloud"):
            return
        if not self.force and self._phase_is_done(d_dir, "cloud"):
            return

        t0 = self.phase_timer("PHASE 7: CLOUD ASSET ENUMERATION")
        evidence = f"{d_dir}/evidence"
        cloud_out = f"{evidence}/cloud_assets.txt"

        # S3 bucket permutations from domain name — v14: expanded suffix list
        base = domain.split(".")[0]
        _SUFFIXES = [
            "", "-dev", "-prod", "-production", "-staging", "-stage", "-test",
            "-qa", "-uat", "-backup", "-backups", "-bak", "-assets", "-static",
            "-media", "-data", "-files", "-uploads", "-public", "-private",
            "-cdn", "-images", "-img", "-logs", "-config", "-internal",
            "-app", "-web", "-api", "-storage", "-archive", "-tmp",
        ]
        # dot- aur plain- dono naming conventions
        bucket_names = []
        for s in _SUFFIXES:
            bucket_names.append(f"{base}{s}")
            if s:
                bucket_names.append(f"{base}{s.replace('-', '.')}")
                bucket_names.append(f"{s.lstrip('-')}-{base}")
        bucket_names = sorted(set(bucket_names))

        print(f"{Fore.CYAN}  [*] Checking S3/GCS/Azure buckets ({len(bucket_names)} names, parallel)...")

        def _check_bucket(bucket: str) -> list:
            """Ek bucket name ke saare provider variants check karo."""
            hits = []
            probes = [
                ("S3",  f"https://{bucket}.s3.amazonaws.com"),
                ("S3",  f"https://s3.amazonaws.com/{bucket}"),
                ("GCS", f"https://storage.googleapis.com/{bucket}"),
                # Azure blob — {account}.blob.core.windows.net (container list attempt)
                ("AZ",  f"https://{re.sub(r'[^a-z0-9]', '', bucket.lower())}.blob.core.windows.net/?comp=list"),
            ]
            for provider, url in probes:
                try:
                    r = self._http.get(url, timeout=6, allow_redirects=False)
                    if r is None:
                        continue
                    # 200 = listable/open, 403 = exists-but-private (still a valid asset)
                    if r.status_code in (200, 403):
                        status = "OPEN" if r.status_code == 200 else "PRIVATE"
                        hits.append((provider, status, url))
                except Exception:
                    continue
            return hits

        found_buckets = []
        with ThreadPoolExecutor(max_workers=SWEEP_WORKERS) as ex:
            futures = {ex.submit(_check_bucket, b): b for b in bucket_names}
            for fut in as_completed(futures):
                try:
                    for provider, status, url in fut.result():
                        entry = f"{provider}[{status}]: {url}"
                        found_buckets.append(entry)
                        color = Fore.RED if status == "OPEN" else Fore.YELLOW
                        print(f"      {color}🪣 {entry}")
                except Exception:
                    continue

        found_buckets = sorted(set(found_buckets))
        if found_buckets:
            with open(cloud_out, "w") as f:
                f.write("\n".join(found_buckets) + "\n")
            print(f"      Cloud assets found: {Fore.RED}{len(found_buckets)}")
            self.notify_discord(f"[{domain}] {len(found_buckets)} cloud assets!")
        else:
            print("      Cloud assets: none found")

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

        # v14.2: pagination — GitHub search 100/page deta hai aur max 1000 results
        # (10 pages). Pehle sirf 30 (first page) le raha tha → 30+ result wale dork
        # ki findings miss. GITHUB_MAX_PAGES tak jaao, chhoti page pe ruk jaao.
        PER_PAGE  = 100
        max_pages = max(1, GITHUB_MAX_PAGES)
        abort_all = False   # 401/rate-exhaust pe pura phase rok do

        for i, dork in enumerate(DORKS):
            if abort_all:
                break
            # GitHub search API: authenticated 30 req/min. Har page ek request hai.
            for page in range(1, max_pages + 1):
                # Har search request ke beech throttle (30/min ke andar)
                if not (i == 0 and page == 1):
                    time.sleep(2.5 + random.uniform(0.3, 1.0))

                try:
                    # self._http — UA rotation + proxy pool + adaptive backoff
                    resp = self._http.get(
                        "https://api.github.com/search/code",
                        headers=headers,
                        params={"q": dork, "per_page": PER_PAGE, "page": page},
                        timeout=20,
                    )
                except Exception as e:
                    self.logger.warning(f"GitHub search error [{dork[:40]}] p{page}: {e}")
                    break   # is dork ki agli pages chhod do

                if resp is None:
                    self.logger.warning(f"GitHub search: no response [{dork[:40]}] p{page}")
                    break

                if resp.status_code == 401:
                    print(f"{Fore.RED}  [!] GitHub token invalid ya expired — phase abort")
                    abort_all = True
                    break

                if resp.status_code == 403:
                    # Rate limit (primary/secondary). Retry-After ya reset tak wait.
                    rate_hit += 1
                    retry_after = int(resp.headers.get(
                        "Retry-After",
                        max(0, int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                            - int(time.time())) + 5
                    ))
                    print(f"{Fore.YELLOW}  [~] GitHub rate limit — waiting {retry_after}s...")
                    time.sleep(min(retry_after, 120) + 2)
                    if rate_hit >= 3:
                        print(f"{Fore.YELLOW}  [~] 3x rate limit — GitHub dork abort")
                        abort_all = True
                        break
                    # same page dobara try karne ke liye loop mat todo — bas continue
                    # (page increment nahi hua, but simplicity ke liye next page pe jao)
                    continue

                if resp.status_code != 200:
                    self.logger.warning(f"GitHub search HTTP {resp.status_code}: {dork[:40]} p{page}")
                    break

                try:
                    data = resp.json()
                except ValueError:
                    break

                items = data.get("items", [])
                if not items:
                    break   # is dork ke aur pages nahi

                # Remaining rate limit — proactive sleep
                remaining = int(resp.headers.get("X-RateLimit-Remaining", 99))
                if remaining < 3:
                    reset_ts  = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                    wait_secs = max(0, reset_ts - int(time.time())) + 5
                    print(f"{Fore.YELLOW}  [~] Rate limit low — sleeping {wait_secs}s")
                    time.sleep(min(wait_secs, 90))

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
                        raw_resp = self._http.get(raw_url, headers=headers, timeout=12)
                        if raw_resp is not None and raw_resp.status_code == 200:
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

                    secret_str = ""
                    if matched_secrets:
                        secret_str = f" → {Fore.RED}{matched_secrets[0]}"
                    print(f"      {Fore.YELLOW}[GH]{Fore.WHITE} {repo_name}/{file_path}{secret_str}")

                # Last page? (fewer than PER_PAGE = no more results)
                if len(items) < PER_PAGE:
                    break

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
                        f.write("     *** SECRETS FOUND ***\n")
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
            print("      GitHub: koi findings nahi")

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
                            if r is None:
                                continue
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
            print("      Install: go install github.com/projectdiscovery/asnmap/cmd/asnmap@latest")
            return

        t0 = self.phase_timer("PHASE 10: ASN / IP RANGE ENUM")
        evidence = f"{d_dir}/evidence"
        out_file = f"{evidence}/asn_ranges.txt"

        self.run_cmd(
            f"asnmap -d {self._q(domain)} -silent -o {self._q(out_file)}",
            "ASN ranges (asnmap)",
            timeout=120,
        )

        count = self.count_lines(out_file)
        print(f"      IP ranges found: {Fore.GREEN}{count}")

        # FIX v12: naabu port scan pehle, phir httpx probe — sirf httpx se bohot kuch miss ho jaata tha
        if count > 0 and count <= 50:   # bahut bade ranges skip karo
            ip_ports_file = f"{evidence}/asn_open_ports.txt"
            ip_live       = f"{evidence}/asn_live_hosts.txt"

            # Step 1: naabu — IP ranges mein open ports dhundo
            self.run_cmd(
                f"naabu -l {self._q(out_file)} -p {NAABU_PORTS} "
                f"-silent -t {THREADS_NAABU} -rate {NAABU_RATE} -o {self._q(ip_ports_file)}",
                "ASN port scan (naabu)"
            )
            asn_ports = self.count_lines(ip_ports_file)
            print(f"      ASN open ports: {Fore.GREEN}{asn_ports}")

            # Step 2: httpx probe — live + fingerprint
            input_for_httpx = ip_ports_file if self.file_has_content(ip_ports_file) else out_file
            self.run_cmd(
                f"httpx -l {self._q(input_for_httpx)} -silent -t 50 -sc "
                f"-title -web-server -follow-redirects -o {self._q(ip_live)}",
                "ASN live host probe (httpx)"
            )
            ip_count = self.count_lines(ip_live)
            print(f"      Live IPs (ASN): {Fore.GREEN}{ip_count}")
            if ip_count > 0:
                self.notify_discord(f"[{domain}] ASN: {ip_count} live IPs from IP ranges!")

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
            # FIX v12: self._http — stealth fetch
            r = self._http.get(
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
            if r and r.status_code == 200 and r.text.strip():
                raw_lines = r.text.strip().splitlines()
                wayback_urls = list(set(
                    line.split()[0] for line in raw_lines if line.strip()
                ))
            else:
                # Fallback — bina mimetype filter ke
                r2 = self._http.get(
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
                wayback_urls = (
                    list(set(r2.text.strip().splitlines()))
                    if r2 and r2.status_code == 200 and r2.text.strip()
                    else []
                )
        except Exception as e:
            self.logger.warning(f"Wayback JS fetch error: {e}")
            wayback_urls = []

        print(f"      Wayback JS URLs: {Fore.GREEN}{len(wayback_urls)}")
        if not wayback_urls:
            self.phase_done(t0)
            self._mark_phase_done(d_dir, "jsdiff")
            return

        # Step 2: Current live JS files nikalo
        # FIX v12: phase5 js_urls.txt path — evidence/js_files.txt bhi check karo (Phase5 copies both)
        current_js_file = f"{d_dir}/js_urls.txt"
        if not os.path.exists(current_js_file):
            current_js_file = f"{d_dir}/evidence/js_files.txt"
        current_urls = []
        if os.path.exists(current_js_file):
            with open(current_js_file) as f:
                current_urls = [l.strip() for l in f if l.strip()]

        # Wayback URLs se path nikalo — current site pe check karo
        wayback_paths = set()
        for url in wayback_urls:
            parsed = urlparse(url)
            if parsed.path:
                wayback_paths.add(parsed.path)

        current_paths = set()
        for url in current_urls:
            parsed = urlparse(url)
            if parsed.path:
                current_paths.add(parsed.path)

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
                # FIX v12 CRITICAL: * hataao — * CDX wildcard hai, content URL mein nahi hota
                # Galat: /web/20230101000000*/{url}  ← yeh 400/404 deta tha
                # Sahi:  /web/2/{url}               ← latest available snapshot fetch karta hai
                wb_fetch = f"https://web.archive.org/web/2/{wb_url}"
                # FIX v12: self._http use karo — stealth + retry
                r = self._http.get(wb_fetch, timeout=15)
                if not r or r.status_code != 200 or len(r.text) < 100:
                    continue
                js_content = r.text[:100_000]   # 100KB cap

                # Save snapshot to disk — TruffleHog filesystem scan ke liye
                fname = re.sub(r'[^a-zA-Z0-9_.-]', '_', wb_url)[-100:] + ".js"
                snap_path = os.path.join(js_dir, fname)
                try:
                    with open(snap_path, "w", encoding="utf-8", errors="replace") as sf:
                        sf.write(js_content)
                except Exception:
                    pass

                # Endpoints extract
                for match in endpoint_re.findall(js_content):
                    found_endpoints.add(match)

                # Regex secrets extract
                for match in secret_re.findall(js_content):
                    if len(match) >= 10:
                        found_secrets.append(f"{wb_url} → {match[:60]}")

                checked += 1
            except Exception:
                continue

        print(f"      JS files checked: {Fore.GREEN}{checked}")
        print(f"      Unique endpoints: {Fore.GREEN}{len(found_endpoints)}")
        if found_secrets:
            print(f"      Regex secrets (old JS): {Fore.YELLOW}{len(found_secrets)}")

        # ── TruffleHog scan on downloaded Wayback JS snapshots ────────────────
        th_jsdiff = 0
        if self.available.get("trufflehog"):
            snap_count = len([f for f in os.listdir(js_dir) if f.endswith(".js")])
            if snap_count > 0:
                print(f"{Fore.CYAN}  [*] TruffleHog scan — {snap_count} Wayback JS snapshots...")
                th_out_jsdiff = f"{evidence}/trufflehog_wayback_js.txt"
                th_jsdiff = self._run_trufflehog(js_dir, th_out_jsdiff, label="Wayback JS")
                if th_jsdiff > 0:
                    print(f"{Fore.RED}      🔑 TruffleHog (Wayback): {th_jsdiff} secrets!")
                    self.notify_discord(
                        f"[{domain}] 🔑 TruffleHog: {th_jsdiff} secrets in historical JS!"
                    )

        total_secrets = len(found_secrets) + th_jsdiff
        if total_secrets > 0:
            print(f"{Fore.RED}      *** Total secrets in old JS: {total_secrets} "
                  f"(regex:{len(found_secrets)}, trufflehog:{th_jsdiff}) ***")

        # Save results
        if found_endpoints or found_secrets or th_jsdiff:
            with open(out_file, "w") as f:
                f.write(f"JS Diff Analysis — {domain}\n")
                f.write(f"Wayback JS: {len(wayback_urls)} | Checked: {checked}\n")
                f.write(f"Deleted paths: {len(deleted_paths)}\n")
                f.write(f"TruffleHog findings: {th_jsdiff}\n\n")
                if found_endpoints:
                    f.write("── ENDPOINTS (historical) ──\n")
                    for ep in sorted(found_endpoints):
                        f.write(f"  {ep}\n")
                if found_secrets:
                    f.write("\n── REGEX SECRETS IN OLD JS ──\n")
                    for s in found_secrets:
                        f.write(f"  {s}\n")
                if th_jsdiff > 0:
                    f.write(f"\n── TRUFFLEHOG FINDINGS → see {evidence}/trufflehog_wayback_js.txt ──\n")

        self.phase_done(t0)
        self._mark_phase_done(d_dir, "jsdiff")

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    def _aggregate_findings(self, domain: str, d_dir: str) -> int:
        """
        v13: Sari bikhri findings ko ek normalized findings.json mein collect karo.
        Triage, dedup-across-targets, aur dusre tools mein import easy ho jaata hai.

        Schema (list of):
          {target, type, severity, source, detail}
        Severity: critical | high | medium | low | info
        """
        evidence = f"{d_dir}/evidence"
        findings = []
        _SEV = {"critical", "high", "medium", "low", "info"}

        def _read_lines(path):
            if not self.file_has_content(path):
                return []
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    return [l.strip() for l in f if l.strip()]
            except Exception:
                return []

        def _add(ftype, severity, source, lines):
            for ln in lines:
                findings.append({
                    "target":   domain,
                    "type":     ftype,
                    "severity": severity,
                    "source":   source,
                    "detail":   ln[:500],
                })

        # ── Nuclei — severity line se parse karo: [id] [proto] [sev] url ──────
        for nf in (f"{evidence}/vulns.txt", f"{evidence}/vulns_cve.txt"):
            for ln in _read_lines(nf):
                sev = "info"
                for tok in re.findall(r"\[([a-z]+)\]", ln.lower()):
                    if tok in _SEV:
                        sev = tok
                        break
                findings.append({
                    "target": domain, "type": "nuclei", "severity": sev,
                    "source": os.path.basename(nf), "detail": ln[:500],
                })

        # ── High-confidence buckets ──────────────────────────────────────────
        _add("subdomain-takeover", "high",   "takeover_candidates.txt",
             _read_lines(f"{evidence}/takeover_candidates.txt"))
        _add("secret-verified",    "high",   "trufflehog_js.txt",
             _read_lines(f"{evidence}/trufflehog_js.txt"))
        _add("secret-verified",    "high",   "trufflehog_wayback_js.txt",
             _read_lines(f"{evidence}/trufflehog_wayback_js.txt"))
        _add("403-bypass",         "medium", "403_bypass.txt",
             _read_lines(f"{evidence}/403_bypass.txt"))
        _add("cors-misconfig",     "medium", "cors.txt",
             _read_lines(f"{evidence}/cors.txt"))
        _add("github-leak",        "medium", "github_leaks.txt",
             _read_lines(f"{evidence}/github_leaks.txt"))
        # secret (regex) — v14: [high-signal] provider tokens medium, baaki low
        _js_secret_lines = _read_lines(f"{evidence}/js_secrets.txt")
        _add("secret-high-signal", "medium", "js_secrets.txt",
             [l for l in _js_secret_lines if l.startswith("[high-signal]")])
        _add("secret-unverified",  "low",    "js_secrets.txt",
             [l for l in _js_secret_lines if not l.startswith("[high-signal]")])
        _add("cloud-asset",        "info",   "cloud_assets.txt",
             _read_lines(f"{evidence}/cloud_assets.txt"))
        _add("nonstd-service",     "info",   "nonstandard_live.txt",
             _read_lines(f"{d_dir}/nonstandard_live.txt"))
        # v14: favicon clusters — same-app / hidden-origin pivoting signal
        _add("favicon-cluster",    "info",   "favicon_clusters.txt",
             [l for l in _read_lines(f"{evidence}/favicon_clusters.txt")
              if l.startswith("#")])

        # Severity ke hisaab se sort — critical pehle
        _order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        findings.sort(key=lambda x: _order.get(x["severity"], 9))

        out = {
            "target":         domain,
            "timestamp":      datetime.datetime.now().isoformat(),
            "total_findings": len(findings),
            "by_severity": {
                s: sum(1 for f in findings if f["severity"] == s) for s in _SEV
            },
            "findings": findings,
        }
        with open(f"{d_dir}/findings.json", "w") as f:
            json.dump(out, f, indent=2)

        actionable = sum(1 for f in findings if f["severity"] in ("critical", "high", "medium"))
        if actionable:
            print(f"  {Fore.RED}★ Actionable findings (crit/high/med): {actionable}"
                  f"{Style.RESET_ALL} → {d_dir}/findings.json")
        return len(findings)

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
            "Live (all SC)":          self.count_lines(f"{d_dir}/live_all.txt"),
            "200 OK":                 self.count_lines(f"{d_dir}/live_200.txt"),
            "Endpoints (total)":      self.count_lines(f"{d_dir}/all_endpoints.txt"),
            "Vulns (nuclei)":         self.count_lines(f"{evidence}/vulns.txt") + self.count_lines(f"{evidence}/vulns_cve.txt"),
            "XSS params":             self.count_lines(f"{evidence}/xss.txt"),
            "SQLi params":            self.count_lines(f"{evidence}/sqli.txt"),
            "SSRF params":            self.count_lines(f"{evidence}/ssrf.txt"),
            "SSTI params":            self.count_lines(f"{evidence}/ssti.txt"),
            "Open Redirect":          self.count_lines(f"{evidence}/open_redirect.txt"),
            "LFI params":             self.count_lines(f"{evidence}/lfi.txt"),
            # FIX v12: duplicate key bug — ek hi "Takeover candidates" key hona chahiye
            # Phase 9 ka output (takeover_candidates.txt) correct hai
            # Phase 4 se subzy remove kar diya — ek hi jagah ab
            "Takeover candidates":    self.count_lines(f"{evidence}/takeover_candidates.txt"),
            "JS Secrets":             self.count_lines(f"{evidence}/js_secrets.txt"),
            "TruffleHog (live JS)":   self.count_lines(f"{evidence}/trufflehog_js.txt"),
            "TruffleHog (Wayback)":   self.count_lines(f"{evidence}/trufflehog_wayback_js.txt"),
            "403 Bypassed":           self.count_lines(f"{evidence}/403_bypass.txt"),
            "CORS issues":            self.count_lines(f"{evidence}/cors.txt"),
            "Cloud assets":           self.count_lines(f"{evidence}/cloud_assets.txt"),
            "GitHub leaks (files)":   self.count_lines(f"{evidence}/github_leaks.txt"),
            "ASN IP ranges":          self.count_lines(f"{evidence}/asn_ranges.txt"),
            "ASN open ports":         self.count_lines(f"{evidence}/asn_open_ports.txt"),
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

        # v13: normalized findings.json — triage-ready, severity-sorted
        self._aggregate_findings(domain, d_dir)

        # HTML report
        self._generate_html_report(domain, d_dir, summary_data)

        HIGH_VALUE = {
            "Vulns (nuclei)", "JS Secrets", "403 Bypassed",
            "Takeover candidates", "VHosts found", "Non-std port services",
            "Cloud assets", "SSTI params", "GitHub leaks (files)",
            "ASN live hosts", "JS diff endpoints",
            "TruffleHog (live JS)", "TruffleHog (Wayback)",
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

    @staticmethod
    def _html_escape(s: str) -> str:
        return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    def _generate_html_report(self, domain: str, d_dir: str, data: dict):
        """v14: rich cyberpunk HTML report — findings.json render karta hai."""
        stats = data.get("stats", {})
        ts    = data.get("timestamp", "")

        # findings.json load karo (aggregate pehle chal chuka hai)
        findings, by_sev = [], {}
        fj = f"{d_dir}/findings.json"
        if self.file_has_content(fj):
            try:
                with open(fj, encoding="utf-8", errors="replace") as f:
                    fdata = json.load(f)
                findings = fdata.get("findings", [])
                by_sev   = fdata.get("by_severity", {})
            except Exception:
                pass

        esc = self._html_escape
        SEV_ORDER = ["critical", "high", "medium", "low", "info"]

        # Severity chips
        chips = ""
        for s in SEV_ORDER:
            c = by_sev.get(s, 0)
            chips += (f'<span class="chip sev-{s}">{s.upper()}: {c}</span>')

        # Findings rows (grouped severity order)
        _ord = {s: i for i, s in enumerate(SEV_ORDER)}
        findings_sorted = sorted(findings, key=lambda x: _ord.get(x.get("severity"), 9))
        frows = ""
        for f in findings_sorted:
            sev = f.get("severity", "info")
            detail = esc(f.get("detail", ""))
            frows += (
                f'<tr class="row-{sev}">'
                f'<td><span class="sev-tag sev-{sev}">{sev.upper()}</span></td>'
                f'<td>{esc(f.get("type",""))}</td>'
                f'<td class="src">{esc(f.get("source",""))}</td>'
                f'<td class="detail"><code>{detail}</code>'
                f'<button class="copy" onclick="cp(this)" data-v="{detail}">⧉</button></td>'
                f'</tr>\n'
            )
        if not frows:
            frows = '<tr><td colspan="4" class="zero">No normalized findings.</td></tr>'

        # Stats rows
        HIGH_VALUE = {
            "Vulns (nuclei)", "JS Secrets", "403 Bypassed",
            "Takeover candidates", "VHosts found", "Non-std port services",
            "Cloud assets", "GitHub leaks (files)",
            "TruffleHog (live JS)", "TruffleHog (Wayback)",
        }
        srows = ""
        for k, v in stats.items():
            cls = "high" if (k in HIGH_VALUE and v > 0) else ("ok" if v > 0 else "zero")
            srows += f'<tr class="{cls}"><td>{esc(k)}</td><td>{v}</td></tr>\n'

        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ghost Protocol — {esc(domain)}</title>
<style>
  :root {{ --bg:#0a0a0f; --panel:#12121b; --line:#232336; --txt:#c8c8d4;
           --neon:#00ffe0; --pink:#ff2d78; --amber:#ffb000; }}
  * {{ box-sizing:border-box; }}
  body {{ font-family:'JetBrains Mono',Consolas,monospace; background:var(--bg);
          color:var(--txt); margin:0; padding:2rem; }}
  h1 {{ color:var(--pink); text-shadow:0 0 12px rgba(255,45,120,.5); margin:0 0 .2rem; letter-spacing:2px; }}
  h2 {{ color:var(--neon); font-weight:400; margin:.2rem 0 1rem; }}
  .meta {{ color:#6a6a86; font-size:.85rem; margin-bottom:1.2rem; }}
  .chip {{ display:inline-block; padding:.3rem .7rem; margin:.2rem .3rem .2rem 0;
           border-radius:4px; font-size:.8rem; font-weight:700; border:1px solid var(--line); }}
  .sev-critical {{ background:#2a0010; color:#ff3b6b; border-color:#ff3b6b; }}
  .sev-high     {{ background:#2a0d00; color:#ff7a2d; border-color:#ff7a2d; }}
  .sev-medium   {{ background:#2a2200; color:#ffb000; border-color:#ffb000; }}
  .sev-low      {{ background:#001f2a; color:#38c6ff; border-color:#38c6ff; }}
  .sev-info     {{ background:#141420; color:#8a8aa5; border-color:#3a3a52; }}
  h3 {{ color:var(--amber); border-bottom:1px solid var(--line); padding-bottom:.4rem; margin-top:2rem; }}
  table {{ border-collapse:collapse; width:100%; margin-top:.8rem; background:var(--panel); }}
  th,td {{ padding:.5rem .8rem; border:1px solid var(--line); text-align:left; vertical-align:top; font-size:.85rem; }}
  th {{ background:#16161f; color:var(--neon); position:sticky; top:0; }}
  .sev-tag {{ padding:.15rem .5rem; border-radius:3px; font-size:.7rem; font-weight:700; }}
  .detail code {{ color:#d7d7e6; word-break:break-all; }}
  .src {{ color:#7a7a96; font-size:.78rem; }}
  .copy {{ float:right; background:transparent; border:1px solid var(--line); color:var(--neon);
           cursor:pointer; border-radius:3px; padding:0 .4rem; margin-left:.4rem; }}
  .copy:hover {{ background:var(--neon); color:#000; }}
  .high {{ color:#ff6b8f; font-weight:700; }}
  .ok {{ color:#4dffa6; }} .zero {{ color:#4a4a5e; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:2rem; }}
  @media(max-width:800px){{ .grid{{grid-template-columns:1fr;}} }}
</style></head><body>
<h1>👻 GHOST PROTOCOL v14.2</h1>
<h2>{esc(domain)}</h2>
<div class="meta">Scan: {esc(ts)}</div>
<div>{chips}</div>

<h3>🎯 Findings (triage-ready)</h3>
<table>
  <tr><th>Sev</th><th>Type</th><th>Source</th><th>Detail</th></tr>
  {frows}
</table>

<h3>📊 Recon Stats</h3>
<table style="max-width:520px">
  <tr><th>Metric</th><th>Count</th></tr>
  {srows}
</table>

<script>
function cp(b){{
  navigator.clipboard.writeText(b.dataset.v).then(()=>{{
    const o=b.textContent; b.textContent='✓'; setTimeout(()=>b.textContent=o,900);
  }});
}}
</script>
</body></html>"""

        with open(f"{d_dir}/report.html", "w") as f:
            f.write(html)

    def _generate_session_report(self):
        """
        v14: Saare targets ki findings.json ko ek session-wide roll-up mein merge karo.
        Deta hai:
          SESSION_FINDINGS.json  — sab domains ki normalized findings, severity-sorted
          index.html             — top-level cyberpunk dashboard (per-target links + counts)
        """
        all_findings = []
        per_target   = {}   # domain → by_severity dict

        for domain in self.targets:
            d_dir = f"{self.base_dir}/{self._safe_dirname(domain)}"
            fj = f"{d_dir}/findings.json"
            if not self.file_has_content(fj):
                continue
            try:
                with open(fj, encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
            except Exception:
                continue
            per_target[domain] = data.get("by_severity", {})
            all_findings.extend(data.get("findings", []))

        SEV_ORDER = ["critical", "high", "medium", "low", "info"]
        _ord = {s: i for i, s in enumerate(SEV_ORDER)}
        all_findings.sort(key=lambda x: (_ord.get(x.get("severity"), 9),
                                         x.get("target", "")))

        totals = {s: sum(1 for f in all_findings if f.get("severity") == s)
                  for s in SEV_ORDER}

        with open(f"{self.base_dir}/SESSION_FINDINGS.json", "w") as f:
            json.dump({
                "session":        self.session_id,
                "timestamp":      datetime.datetime.now().isoformat(),
                "targets":        list(self.targets),
                "total_findings": len(all_findings),
                "by_severity":    totals,
                "per_target":     per_target,
                "findings":       all_findings,
            }, f, indent=2)

        # ── Dashboard index.html ──
        esc = self._html_escape
        chips = "".join(
            f'<span class="chip sev-{s}">{s.upper()}: {totals.get(s,0)}</span>'
            for s in SEV_ORDER
        )
        # per-target rows
        trows = ""
        for domain in sorted(per_target.keys()):
            bs = per_target[domain]
            rel = f"{self._safe_dirname(domain)}/report.html"
            counts = "".join(
                f'<span class="mini sev-{s}">{bs.get(s,0)}</span>' for s in SEV_ORDER
            )
            actionable = sum(bs.get(s, 0) for s in ("critical", "high", "medium"))
            trows += (
                f'<tr><td><a href="{esc(rel)}">{esc(domain)}</a></td>'
                f'<td>{counts}</td>'
                f'<td class="{"hot" if actionable else "cold"}">{actionable}</td></tr>\n'
            )
        # top actionable findings (crit/high/med) preview
        prev = ""
        for f in [x for x in all_findings
                  if x.get("severity") in ("critical", "high", "medium")][:100]:
            sev = f.get("severity", "info")
            prev += (
                f'<tr class="row-{sev}">'
                f'<td><span class="sev-tag sev-{sev}">{sev.upper()}</span></td>'
                f'<td>{esc(f.get("target",""))}</td>'
                f'<td>{esc(f.get("type",""))}</td>'
                f'<td class="detail"><code>{esc(f.get("detail",""))}</code></td></tr>\n'
            )
        if not prev:
            prev = '<tr><td colspan="4" class="zero">No actionable findings this session.</td></tr>'

        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ghost Protocol — Session {esc(self.session_id)}</title>
<style>
  :root {{ --bg:#0a0a0f; --panel:#12121b; --line:#232336; --txt:#c8c8d4;
           --neon:#00ffe0; --pink:#ff2d78; --amber:#ffb000; }}
  body {{ font-family:'JetBrains Mono',Consolas,monospace; background:var(--bg);
          color:var(--txt); margin:0; padding:2rem; }}
  h1 {{ color:var(--pink); text-shadow:0 0 14px rgba(255,45,120,.55); letter-spacing:2px; margin:0; }}
  .meta {{ color:#6a6a86; font-size:.85rem; margin:.4rem 0 1.2rem; }}
  .chip {{ display:inline-block; padding:.35rem .8rem; margin:.2rem .3rem .2rem 0; border-radius:4px;
           font-size:.85rem; font-weight:700; border:1px solid var(--line); }}
  .mini {{ display:inline-block; min-width:1.6rem; text-align:center; padding:.1rem .3rem;
           margin-right:.2rem; border-radius:3px; font-size:.72rem; font-weight:700; border:1px solid var(--line); }}
  .sev-critical {{ background:#2a0010; color:#ff3b6b; border-color:#ff3b6b; }}
  .sev-high {{ background:#2a0d00; color:#ff7a2d; border-color:#ff7a2d; }}
  .sev-medium {{ background:#2a2200; color:#ffb000; border-color:#ffb000; }}
  .sev-low {{ background:#001f2a; color:#38c6ff; border-color:#38c6ff; }}
  .sev-info {{ background:#141420; color:#8a8aa5; border-color:#3a3a52; }}
  h3 {{ color:var(--amber); border-bottom:1px solid var(--line); padding-bottom:.4rem; margin-top:2rem; }}
  table {{ border-collapse:collapse; width:100%; margin-top:.8rem; background:var(--panel); }}
  th,td {{ padding:.5rem .8rem; border:1px solid var(--line); text-align:left; font-size:.85rem; vertical-align:top; }}
  th {{ background:#16161f; color:var(--neon); }}
  a {{ color:var(--neon); text-decoration:none; }} a:hover {{ text-shadow:0 0 8px var(--neon); }}
  .sev-tag {{ padding:.15rem .5rem; border-radius:3px; font-size:.7rem; font-weight:700; }}
  .hot {{ color:#ff6b8f; font-weight:700; }} .cold {{ color:#4a4a5e; }}
  .detail code {{ color:#d7d7e6; word-break:break-all; }}
  .zero {{ color:#4a4a5e; }}
</style></head><body>
<h1>👻 GHOST PROTOCOL v14.2 — SESSION DASHBOARD</h1>
<div class="meta">Session {esc(self.session_id)} · {len(self.targets)} target(s) · {len(all_findings)} findings</div>
<div>{chips}</div>

<h3>🗂️ Targets</h3>
<table>
  <tr><th>Domain</th><th>C / H / M / L / I</th><th>Actionable</th></tr>
  {trows or '<tr><td colspan="3" class="zero">No target reports found.</td></tr>'}
</table>

<h3>🔥 Top Actionable Findings (crit / high / medium)</h3>
<table>
  <tr><th>Sev</th><th>Target</th><th>Type</th><th>Detail</th></tr>
  {prev}
</table>
</body></html>"""

        with open(f"{self.base_dir}/index.html", "w") as f:
            f.write(html)

        act = totals["critical"] + totals["high"] + totals["medium"]
        print(f"\n{Fore.MAGENTA}{'═'*52}")
        print(f"{Fore.MAGENTA}  SESSION ROLL-UP{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'═'*52}{Style.RESET_ALL}")
        print(f"  Total findings: {Fore.GREEN}{len(all_findings)}{Style.RESET_ALL} "
              f"| Actionable: {Fore.RED}{act}{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Dashboard: {self.base_dir}/index.html{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Merged JSON: {self.base_dir}/SESSION_FINDINGS.json{Style.RESET_ALL}")

    # ── crt.sh ────────────────────────────────────────────────────────────────
    def get_crt_sh(self, domain: str, sub_file: str):
        """crt.sh — wildcard + multi-SAN certificates handle karo. 429 pe retry."""
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        for attempt in range(3):
            try:
                r = self._http.get(url, timeout=25)
                if r is None:
                    self.logger.warning(f"crt.sh: no response for {domain} (attempt {attempt+1})")
                    time.sleep(5 * (attempt + 1))
                    continue
                if r.status_code == 429:
                    wait = 10 * (attempt + 1)
                    self.logger.warning(f"crt.sh 429 — waiting {wait}s (attempt {attempt+1})")
                    time.sleep(wait)
                    continue
                if r.status_code == 200:
                    try:
                        entries = r.json()
                    except (json.JSONDecodeError, ValueError) as e:
                        self.logger.warning(f"crt.sh JSON parse failed for {domain}: {e}")
                        break
                    names = set()
                    for entry in entries:
                        for name in entry.get("name_value", "").splitlines():
                            name = name.strip().lstrip("*.").lower()
                            if name and re.match(r'^[a-zA-Z0-9._-]+$', name):
                                if self.scope.in_scope(name):
                                    names.add(name)
                    with open(sub_file, "a") as f:
                        f.write("\n".join(names) + "\n")
                    self.logger.info(f"crt.sh: {len(names)} subs for {domain}")
                    return
            except Exception as e:
                self.logger.warning(f"crt.sh failed for {domain}: {e}")
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
            live_file, live_200, live_all = self.phase2_port_and_probe(domain, d_dir, resolved)

            # v13 FIX: Phase 3 (gau/wayback) PASSIVE hai — live host pe depend nahi.
            # Pehle ye live_200 ke peeche gated tha, isliye all-403/all-30x targets pe
            # historical URLs bhi gayab ho jaate the. Ab hamesha chalao.
            hist_file = self.phase3_historical_urls(domain, d_dir)

            # v13 FIX: deep pipeline ab live_ALL pe chalta hai (200 + 30x + 401 + 403…),
            # sirf 200 pe nahi. 403/401/redirect hosts BB gold hote hain — aur ironically
            # 403-bypass engine (phase6) tab kabhi chalta hi nahi tha jab target poora 403 ho.
            scan_input = None
            if self.file_has_content(live_all):
                scan_input = live_all
            elif self.file_has_content(hist_file):
                # Koi live host nahi mila par historical URLs hain — un par hi crawl/scan karo
                print(f"{Fore.YELLOW}  [~] {domain}: koi live host nahi, par historical "
                      f"URLs mile — unhi par deep phases chalenge.")
                scan_input = hist_file

            if scan_input:
                merged = self.phase4_scan_crawl(domain, d_dir, scan_input, hist_file)
                self.phase5_js_secrets(domain, d_dir, scan_input)
                self.phase6_data_mining(domain, d_dir, scan_input, merged)
            else:
                print(f"{Fore.RED}  [!] {domain}: na live host na historical URL. "
                      f"Crawl/scan/mine phases skip (cloud/github/takeover/asn phir bhi chalenge).")

            # Cloud + GitHub + Takeover + ASN + JS Diff — live hosts pe depend nahi
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
{Fore.CYAN}       PROTOCOL v14.2 — Bug Bounty Edition
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

        # v14: session-wide roll-up (SESSION_FINDINGS.json + index.html dashboard)
        try:
            self._generate_session_report()
        except Exception as e:
            self.logger.warning(f"Session report failed: {e}")

        # Cleanup temp dir + HTTP session
        shutil.rmtree(self._tmpdir, ignore_errors=True)
        try:
            self._http.close()
        except Exception:
            pass
        print(f"\n{Fore.MAGENTA}[!!!] ALL DONE. Results: {self.base_dir}/{Style.RESET_ALL}")


# ─── CLI ───────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ghost Protocol v14.2 — Bug Bounty Deep Recon",
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
        "--passive", action="store_true",
        help="Passive only mode — bruteforce/port scan skip (OSINT recon)"
    )
    parser.add_argument(
        "--output-dir", default="",
        help="Output directory (resume/re-run friendly). Default: timestamped folder"
    )
    parser.add_argument(
        "--rate-limit", default="", metavar="N",
        help="Global req/sec for httpx/katana/nuclei (stealth/polite). Default: 150"
    )
    parser.add_argument(
        "--sweep-workers", type=int, default=0, metavar="N",
        help="Parallel workers for 403-bypass/cloud/JS-secret sweeps. Default: 15"
    )
    parser.add_argument(
        "--favicon", action="store_true",
        help="httpx favicon hashing on karo (extra req/host — asset clustering)"
    )
    parser.add_argument(
        "--katana-scope", default="", choices=["", "rdn", "fqdn", "dn"],
        help="Katana crawl scope-lock: rdn (root, default) | fqdn (exact host) | dn"
    )
    parser.add_argument(
        "--github-pages", type=int, default=-1, metavar="N",
        help="GitHub dork max pages (100/page). Default: 3. 1 = first page only"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    phases = [p.strip() for p in args.phases.split(",") if p.strip() in PHASE_MARKERS]
    if not phases:
        print(f"{Fore.RED}[!] No valid phases selected. Use: {','.join(PHASE_MARKERS.keys())}")
        sys.exit(1)

    # v14: CLI overrides — command builders in globals runtime pe read karte hain
    if args.rate_limit and args.rate_limit.strip().isdigit():
        HTTPX_RATE_LIMIT  = args.rate_limit.strip()
        KATANA_RATE_LIMIT = args.rate_limit.strip()
        NUCLEI_RATE_LIMIT = args.rate_limit.strip()
    if args.sweep_workers and args.sweep_workers > 0:
        SWEEP_WORKERS = args.sweep_workers
    # v14.2 overrides
    if args.favicon:
        FAVICON_ENABLED = True
    if args.katana_scope:
        KATANA_FIELD_SCOPE = args.katana_scope
    if args.github_pages >= 0:
        GITHUB_MAX_PAGES = args.github_pages

    recon = DeepRecon(
        target_file=args.targets,
        scope_file=args.scope,
        dry_run=args.dry_run,
        phases=phases,
        skip_nuclei_update=args.skip_nuclei_update,
        output_dir=args.output_dir,
        force=args.force,
        passive=args.passive,
    )

    if args.force and args.output_dir:
        # Force mode: scan_complete markers hata do
        for t in recon.targets:
            marker = f"{recon.base_dir}/{recon._safe_dirname(t)}/.scan_complete"
            if os.path.exists(marker):
                os.remove(marker)

    recon.start()
