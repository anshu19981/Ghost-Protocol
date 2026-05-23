markdown
# 👻 Ghost Protocol v12.0 — Deep Recon Engine

> **Bug Bounty Hunter Edition** — Single-file, production-ready recon automation for authorized penetration testing and bug bounty programs.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Version](https://img.shields.io/badge/Version-12.0-red?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Linux%20%2F%20macOS-lightgrey?style=flat-square)

---

## ⚠️ Legal Disclaimer

> This tool is intended **strictly for authorized security testing and bug bounty programs**.  
> Running it against systems you do not have explicit written permission to test is **illegal**.  
> The author is not responsible for any misuse or damage caused by this tool.  
> **Always stay in scope. Always have authorization.**

---

## 📖 What is Ghost Protocol?

Ghost Protocol is a **full-pipeline recon automation engine** built for bug bounty hunters and penetration testers. It chains together 11 recon phases — from passive subdomain enumeration all the way to Wayback JS diffing and GitHub dorking — into a single, resumable, stealth-aware workflow.

**Key design principles:**
- **Single file** — drop on any VPS and run, no module hell
- **Stealth-first** — adaptive rate limiting, UA rotation, proxy pool, per-domain backoff
- **Resume-aware** — phase markers mean a crash or Ctrl+C picks up exactly where it left off
- **Scope-safe** — wildcard + exclusion scope validation before any active scanning

---

## 🗺️ Recon Pipeline

```
Phase 1   →  Subdomain Enumeration     (crt.sh + subfinder + assetfinder + amass + brute)
Phase 1b  →  Recursive Bruteforce      (top N subdomains drilled deeper)
Phase 2   →  Port Scan + HTTP Probe    (naabu + httpx, per-port breakdown)
Phase 3   →  Historical URLs           (gau + waybackurls)
Phase 4   →  Scan + Crawl              (nuclei + katana + gowitness + paramspider)
Phase 5   →  JS Secret Hunting         (subjs + regex + TruffleHog 700+ detectors)
Phase 6   →  Data Mining               (gf patterns + CORS + 403 bypass)
Phase 7   →  Cloud Asset Enum         (S3 / GCS / Azure bucket bruteforce)
Phase 8   →  GitHub Dorking            (30+ dork queries + secret pattern matching)
Phase 9   →  Subdomain Takeover        (CNAME + HTTP fingerprint, 28 services)
Phase 10  →  ASN / IP Range Enum       (asnmap + naabu + httpx on IP ranges)
Phase 11  →  Wayback JS Diffing        (deleted endpoints + old secrets in historical JS)
```

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **StealthEngine** | UA rotation (24 real browser UAs), proxy pool with circuit breaker, adaptive per-domain backoff |
| **SmartNuclei** | Fast mode (high-signal tags only) + Priority CVE mode (Log4Shell, Spring4Shell, etc.) |
| **Bypass403** | 19 spoof headers + 14 path mutations + HTTP verb tampering |
| **TruffleHog v3** | 700+ secret detectors with verification on live JS + Wayback snapshots |
| **Priority Scanning** | `admin`, `api`, `dev`, `staging` subdomains always scanned first |
| **Discord Alerts** | Real-time webhook notifications for high-value findings |
| **HTML Report** | Auto-generated `report.html` + `summary.json` after each target |
| **Dry Run Mode** | Print all commands without executing — review before you run |
| **Per-phase Resume** | Crash or interrupt mid-scan, resume from the exact phase it stopped |

---

## 🔧 Requirements

### Python
```
Python 3.8+
```

### Python Dependencies
```bash
pip install colorama requests python-dotenv
```

### Required Tools
All of these must be in your `$PATH`:

| Tool | Install |
|------|---------|
| `subfinder` | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` |
| `assetfinder` | `go install github.com/tomnomnom/assetfinder@latest` |
| `httpx` | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` |
| `nuclei` | `go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest` |
| `katana` | `go install github.com/projectdiscovery/katana/cmd/katana@latest` |
| `gf` | `go install github.com/tomnomnom/gf@latest` |
| `dnsx` | `go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest` |
| `naabu` | `go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest` |
| `gau` | `go install github.com/lc/gau/v2/cmd/gau@latest` |

### Optional Tools (greatly expand coverage)

| Tool | Purpose | Install |
|------|---------|---------|
| `amass` | Passive enum | `go install github.com/owasp-amass/amass/v4/...@master` |
| `puredns` | DNS bruteforce (preferred) | `go install github.com/d3mondev/puredns/v2@latest` |
| `shuffledns` | DNS bruteforce (fallback) | `go install github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest` |
| `massdns` | DNS bruteforce (fallback) | [Build from source](https://github.com/blechschmidt/massdns) |
| `alterx` | Permutation bruteforce | `go install github.com/projectdiscovery/alterx/cmd/alterx@latest` |
| `waybackurls` | Historical URLs | `go install github.com/tomnomnom/waybackurls@latest` |
| `subjs` | JS URL extraction | `go install github.com/lc/subjs@latest` |
| `trufflehog` | Secret detection (700+ detectors) | `curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh \| sh -s -- -b /usr/local/bin` |
| `ffuf` | VHost bruteforce | `go install github.com/ffuf/ffuf/v2@latest` |
| `gowitness` | Screenshots | `go install github.com/sensepost/gowitness@latest` |
| `corsy` | CORS scanner | `pip install corsy` |
| `subzy` | Takeover check | `go install github.com/PentestPad/subzy@latest` |
| `asnmap` | ASN/IP range enum | `go install github.com/projectdiscovery/asnmap/cmd/asnmap@latest` |
| `paramspider` | Parameter discovery | `pip install paramspider` |
| `cloud_enum` | Cloud asset enum | `pip install cloud-enum` |
| `wappalyzergo` | Tech fingerprinting | `go install github.com/projectdiscovery/wappalyzergo/cmd/update-fingerprints@latest` |

### Wordlists
```bash
# Recommended — download SecLists
sudo apt install seclists
# OR
git clone https://github.com/danielmiessler/SecLists ~/wordlists/SecLists
```

Ghost Protocol auto-detects wordlists from these paths (in order):
```
~/wordlists/subdomains-top1million-110000.txt
/usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt
/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt
/usr/share/wordlists/dnsmap.txt
~/wordlists/dns_wordlist.txt
```

---

## 🚀 Quick Start

### 1. Clone and install
```bash
git clone https://github.com/yourusername/ghost-protocol.git
cd ghost-protocol
pip install colorama requests python-dotenv
```

### 2. Create your targets file
```bash
cat > targets.txt << EOF
example.com
another-target.com
EOF
```

### 3. (Optional) Configure via `.env`
```bash
cp .env.example .env
nano .env
```

### 4. Run
```bash
python3 ghost_protocol_v12.py targets.txt
```

---

## ⚙️ Configuration

Create a `.env` file in your working directory (or at `~/.ghost_protocol/.env`):

```env
# ── Discord Notifications ─────────────────────────────────────────
GP_DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR/WEBHOOK

# ── GitHub Dorking (Phase 8) ──────────────────────────────────────
GP_GITHUB_TOKEN=ghp_yourPersonalAccessTokenHere

# ── Proxy Settings (choose one) ───────────────────────────────────
# Single proxy
GP_PROXY=http://127.0.0.1:8080

# Proxy list file (one proxy per line)
GP_PROXY_FILE=~/proxies.txt

# BrightData rotating proxy
GP_BRIGHTDATA_USER=your_user
GP_BRIGHTDATA_PASS=your_password
GP_BRIGHTDATA_HOST=brd.superproxy.io:22225

# ── Rate Limiting ─────────────────────────────────────────────────
GP_BASE_DELAY=0.3          # Seconds between requests (default: 0.3)
GP_BACKOFF_429=30.0        # Backoff on 429 Too Many Requests (default: 30)

# ── Scan Tuning ───────────────────────────────────────────────────
GP_MAX_403=100             # Max targets for 403 bypass (default: 100)
GP_MAX_JS=300              # Max JS files to scan for secrets (default: 300)
GP_NUCLEI_FAST_ONLY=0      # 1 = skip deep nuclei scan (default: 0)

# ── Custom User-Agents ────────────────────────────────────────────
GP_UA_FILE=~/.ghost_protocol/user_agents.txt
```

---

## 📋 Usage

### Basic scan
```bash
python3 ghost_protocol_v12.py targets.txt
```

### With scope file (recommended for bug bounty)
```bash
python3 ghost_protocol_v12.py targets.txt --scope scope.txt
```

### Run specific phases only
```bash
# Passive recon only (no active scanning)
python3 ghost_protocol_v12.py targets.txt --phases enum,history,cloud,github

# Just re-run JS secrets and takeover after a previous full scan
python3 ghost_protocol_v12.py targets.txt --phases js,takeover --output-dir DEEP_RECON_20240101_1200
```

### Passive mode (OSINT only — no bruteforce, no port scan)
```bash
python3 ghost_protocol_v12.py targets.txt --passive
```

### Dry run (preview all commands before executing)
```bash
python3 ghost_protocol_v12.py targets.txt --dry-run
```

### Resume a previous scan
```bash
# Uses the same output dir — completed phases are skipped automatically
python3 ghost_protocol_v12.py targets.txt --output-dir DEEP_RECON_20240101_1200
```

### Force rescan (ignore resume markers)
```bash
python3 ghost_protocol_v12.py targets.txt --output-dir DEEP_RECON_20240101_1200 --force
```

### Skip nuclei template update (faster startup)
```bash
python3 ghost_protocol_v12.py targets.txt --skip-nuclei-update
```

---

## 📁 Scope File Format

```
# Wildcards — all subdomains of example.com
*.example.com

# Exact domain
example.com

# Explicit exclusion — never scan this
!internal.example.com
!staging.example.com
```

---

## 📂 Output Structure

```
DEEP_RECON_20240101_1200/
└── example.com/
    ├── raw_subs.txt              # All discovered subdomains (pre-resolution)
    ├── brute_subs.txt            # Bruteforced subdomains
    ├── perm_subs.txt             # Permutation-based subdomains (alterx)
    ├── recursive_subs.txt        # Recursive bruteforce results
    ├── resolved_subs.txt         # DNS-resolved subdomains
    ├── open_ports.txt            # host:port combos from naabu
    ├── port_summary.txt          # Human-readable port breakdown
    ├── live.txt                  # All live HTTP responses (httpx)
    ├── live_200.txt              # 200 OK URLs only
    ├── nonstandard_live.txt      # Live services on non-standard ports
    ├── historical_urls.txt       # GAU + Wayback URLs
    ├── all_endpoints.txt         # Merged crawled + historical endpoints
    ├── js_urls.txt               # Discovered JS file URLs
    ├── summary.json              # Machine-readable scan summary
    ├── report.html               # HTML report (open in browser)
    ├── recon.log                 # Full debug log
    └── evidence/
        ├── vulns.txt             # Nuclei findings (critical/high/medium)
        ├── vulns_cve.txt         # Priority CVE scan results
        ├── js_secrets.txt        # Regex-detected secrets in JS
        ├── trufflehog_js.txt     # TruffleHog findings (live JS)
        ├── trufflehog_wayback_js.txt  # TruffleHog findings (historical JS)
        ├── xss.txt               # XSS parameter candidates (gf)
        ├── sqli.txt              # SQLi parameter candidates (gf)
        ├── ssrf.txt              # SSRF parameter candidates (gf)
        ├── lfi.txt               # LFI parameter candidates (gf)
        ├── ssti.txt              # SSTI parameter candidates (gf)
        ├── rce.txt               # RCE parameter candidates (gf)
        ├── idor.txt              # IDOR parameter candidates (gf)
        ├── open_redirect.txt     # Open redirect candidates (gf)
        ├── cors.txt              # CORS misconfiguration findings
        ├── 403_bypass.txt        # Successful 403 bypasses
        ├── vhosts.txt            # Discovered virtual hosts
        ├── takeover_candidates.txt  # Subdomain takeover candidates
        ├── cloud_assets.txt      # S3/GCS/Azure buckets found
        ├── github_leaks.txt      # GitHub dorking findings
        ├── github_leaks.json     # GitHub findings (JSON)
        ├── asn_ranges.txt        # IP ranges from ASN lookup
        ├── asn_live_hosts.txt    # Live hosts in ASN ranges
        ├── js_diff_endpoints.txt # Endpoints found in historical JS
        ├── technologies.json     # Wappalyzer tech fingerprints
        └── screenshots/          # Gowitness screenshots
```

---

## 🔍 Available Phases

| Phase | Name | Description |
|-------|------|-------------|
| `enum` | Subdomain Enumeration | crt.sh, subfinder, assetfinder, amass, DNS brute, permutations |
| `recursive` | Recursive Bruteforce | Drill down into top priority subdomains |
| `probe` | Port Scan + HTTP Probe | naabu port scan + httpx probing all ports |
| `history` | Historical URLs | GAU + Waybackurls |
| `scan` | Scan + Crawl | Nuclei, Katana crawl, screenshots, param discovery |
| `js` | JS Secret Hunting | subjs + regex + TruffleHog on live JS files |
| `mine` | Data Mining | GF patterns, CORS check, 403 bypass |
| `cloud` | Cloud Asset Enum | S3/GCS/Azure bucket detection |
| `github` | GitHub Dorking | 30+ dork queries against public repos |
| `takeover` | Subdomain Takeover | CNAME dangling check (28 services) |
| `asn` | ASN Enum | IP range discovery + live host probe |
| `jsdiff` | Wayback JS Diffing | Historical JS comparison, deleted endpoints |

---

## 🛡️ Stealth Features

Ghost Protocol is built to avoid triggering WAFs and rate limiters:

- **24 real browser User-Agents** — Chrome, Firefox, Safari, Edge, mobile — with matching `Accept`, `Sec-Fetch-*`, and `sec-ch-ua` headers per browser family
- **Per-domain adaptive rate limiting** — each domain tracks its own request delay, backing off exponentially on 429 responses and recovering gradually on success
- **Proxy pool with circuit breaker** — dead proxies are automatically dead-listed for 5 minutes after 3 consecutive failures
- **Random jitter** — 0.1–1.2s jitter on every request to avoid pattern detection
- **Priority subdomain scanning** — high-value targets (`admin`, `api`, `dev`) hit first before rate limits kick in

---

## 📡 Discord Notifications

Set `GP_DISCORD_WEBHOOK` in your `.env` to get real-time alerts for:

- 🔥 Nuclei critical/high findings
- 🔑 JS secrets detected
- 🚪 403 bypass successes
- 🪣 Open S3/GCS/Azure buckets
- 🏠 Virtual hosts discovered
- ⚠️ Non-standard port live services
- 💀 Subdomain takeover candidates

---

## 🔑 403 Bypass Engine

The `Bypass403` class tests 3 layers of bypass techniques per URL:

**Layer 1 — Header-based (19 headers)**
```
X-Forwarded-For, X-Real-IP, X-Originating-IP, X-Remote-IP,
X-Remote-Addr, X-Client-IP, X-Custom-IP-Authorization,
X-Host, X-Forwarded-Host, X-Original-URL, X-Rewrite-URL,
X-Override-URL, X-ProxyUser-Ip, X-HTTP-Method-Override,
X-Forwarded-Proto, Referer (localhost trick), and more
```

**Layer 2 — Path manipulation (14 variants)**
```
double slash, dot-slash, trailing dot, semicolon (Tomcat),
null byte, double URL encoding, Unicode overlong,
path traversal wrapping, case switching, double path encoding
```

**Layer 3 — HTTP verb tampering**
```
HEAD, OPTIONS, TRACE, PUT, POST, PATCH
```

---

## 🧪 Nuclei Scan Modes

**Fast mode (default)** — high-signal templates only:
```
cve, exposures, misconfiguration, takeover, default-login,
exposed-panels, tokens, xss, sqli, ssrf, lfi, open-redirect,
xxe, rce, fileupload, deserialization
```

**Priority CVE mode** — always runs alongside fast mode:
```
Log4Shell (CVE-2021-44228), Exchange SSRF (CVE-2021-26855),
Spring4Shell (CVE-2022-22965), Confluence RCE (CVE-2022-26134),
Ivanti RCE (CVE-2024-21887), ConnectWise CVSS-10 (CVE-2024-1709),
and more
```

---

## 💡 Tips for Bug Bounty

**Large programs (500+ subdomains):**
```bash
# Run passive first to map scope, then active phases separately
python3 ghost_protocol_v12.py targets.txt --phases enum,recursive,history,cloud,github
python3 ghost_protocol_v12.py targets.txt --phases probe,scan,js,mine --output-dir 
```

**Quick triage on a new target:**
```bash
python3 ghost_protocol_v12.py targets.txt --phases enum,probe,scan --skip-nuclei-update
```

**OSINT-only (no active footprint):**
```bash
python3 ghost_protocol_v12.py targets.txt --passive --phases enum,history,cloud,github
```

**Custom nuclei templates:**
```bash
mkdir -p ~/.ghost_protocol/templates
# Drop your .yaml templates there — auto-loaded on every scan
```

---

## 📦 Installation Script

```bash
#!/bin/bash
# Install all Go tools at once
GO_TOOLS=(
    "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
    "github.com/tomnomnom/assetfinder@latest"
    "github.com/projectdiscovery/httpx/cmd/httpx@latest"
    "github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest"
    "github.com/projectdiscovery/katana/cmd/katana@latest"
    "github.com/tomnomnom/gf@latest"
    "github.com/projectdiscovery/dnsx/cmd/dnsx@latest"
    "github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
    "github.com/lc/gau/v2/cmd/gau@latest"
    "github.com/d3mondev/puredns/v2@latest"
    "github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest"
    "github.com/projectdiscovery/alterx/cmd/alterx@latest"
    "github.com/tomnomnom/waybackurls@latest"
    "github.com/lc/subjs@latest"
    "github.com/ffuf/ffuf/v2@latest"
    "github.com/sensepost/gowitness@latest"
    "github.com/PentestPad/subzy@latest"
    "github.com/projectdiscovery/asnmap/cmd/asnmap@latest"
    "github.com/owasp-amass/amass/v4/...@master"
)

for tool in "${GO_TOOLS[@]}"; do
    echo "[*] Installing $tool"
    go install "$tool"
done

# Python tools
pip install colorama requests python-dotenv paramspider corsy cloud-enum

# TruffleHog
curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin

echo "[✔] All tools installed"
```

---

## 🗂️ Changelog

### v12.0 (Production-Ready Pass)
- **CRITICAL FIX:** `dotenv` try/except was catching nothing — `GP_*` env vars silently ignored when `python-dotenv` not installed
- **CRITICAL FIX:** `notify_discord()` break misaligned — retry loop never executed
- **CRITICAL FIX:** `get_crt_sh()` duplicate unreachable `except` + missing `None` check causing `AttributeError` on timeout
- **CRITICAL FIX:** `ProxyPool.mark_success()` missing lock — thread-safety bug under concurrent scans
- **CRITICAL FIX:** Multiple `r.status_code` accesses without `None` guard across phases 5, 8, and `_detect_resolvers`
- **SECURITY FIX:** 13 unquoted shell variables across naabu, katana, gau, gowitness, ffuf, corsy, wappalyzergo, nuclei output paths — shell injection risk
- **BUG FIX:** Duplicate `"jenkins"` key in priority dict
- **BUG FIX:** Dead `_run_403_bypass()` method removed (superseded by `Bypass403` class)
- **CLEANUP:** Inline `import os/shutil` removed, 6× bare f-strings fixed, unused `deque` import removed

### v11.0
- Merged single-file build (gp_config + gp_stealth + gp_modules)
- GhostConfig, StealthEngine, SmartNuclei, Bypass403 all inlined

### v10.0
- Graceful Ctrl+C handler, per-phase resume markers, scope validation
- Nuclei auto-update, rate limit guard, duplicate-safe merges
- S3/GCS cloud enum, paramspider, wappalyzer-go, HTML report

---

## 🤝 Contributing

Pull requests welcome. Please:
1. Test against a target you own or have authorization for
2. Don't add dependencies that require separate installation beyond the tools listed above
3. Keep the single-file design intact

---
