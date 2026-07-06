# Ghost Protocol v14.1 — Deep Recon Engine

> A comprehensive, multi-phase bug bounty reconnaissance automation tool built for professional hunters.

```
Author  : Anshuman Jha
Handle  : @anshu19981
Certs   : OSCP+ | eJPT
Platform: Bugcrowd | HackerOne
```

---

## Overview

Ghost Protocol is a single-file Python recon engine designed for bug bounty hunting and authorized penetration testing. It orchestrates 11 sequential reconnaissance phases — from passive subdomain enumeration to JavaScript diff monitoring — and consolidates all findings into a severity-sorted `findings.json` and a rich HTML report.

Key design goals:

- **No silent misses** — every phase uses fallback logic; a failed optional tool never kills the pipeline
- **Stealth-first** — built-in rate limiting, UA rotation, proxy pool, and adaptive backoff on 429s
- **Resume-safe** — per-phase markers allow interrupted scans to restart from where they left off
- **Triage-ready output** — normalized `findings.json` with severity labels plugs directly into downstream tools or AI analysis

---

## Features at a Glance

| Phase | Name | What it does |
|-------|------|-------------|
| `enum` | Subdomain Enumeration | subfinder + assetfinder + amass + crt.sh + wayback |
| `recursive` | Recursive Brute-force | alterx permutations → puredns/shuffledns/massdns |
| `probe` | Port Scan & HTTP Probe | naabu port scan → httpx enrichment (IP, CNAME, favicon hash, tech) |
| `history` | Historical URLs | gau + waybackurls — passive URL corpus |
| `scan` | Vuln Scan & Crawl | nuclei (fast + CVE mode) + katana JS-aware crawl + param discovery |
| `js` | JS Secret Hunting | katana JS URL extraction → trufflehog (verified) + regex patterns |
| `mine` | Data Mining | gf pattern extraction (XSS/SQLi/SSRF/LFI/RCE/IDOR) + 403 bypass engine |
| `cloud` | Cloud Asset Enum | S3/GCS/Azure bucket permutations (3× naming variants) |
| `github` | GitHub Dorking | Paginated code search via GitHub API for secrets and internal endpoints |
| `takeover` | Subdomain Takeover | subzy + nuclei takeover templates — 40+ fingerprints |
| `asn` | ASN Enumeration | asnmap → naabu → httpx — full IP range coverage |
| `jsdiff` | JS Diff Monitoring | Detects new endpoints and secrets added in redeployed JS bundles |

---

## Requirements

### Python

```
Python 3.9+
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

```
# requirements.txt
requests
colorama
```

> Ghost Protocol has no other Python dependencies. All heavy lifting is done by external Go/binary tools.

### Required Tools

These tools **must** be installed and in `$PATH`. Ghost Protocol will exit at startup if any are missing.

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

### Optional Tools

Missing optional tools are skipped gracefully — the phase continues without them.

| Tool | Purpose |
|------|---------|
| `amass` | Additional passive subdomain sources |
| `waybackurls` | Supplementary Wayback URL fetch |
| `subjs` | Additional JS URL extraction |
| `corsy` | CORS misconfiguration detection |
| `subzy` | Subdomain takeover fingerprinting |
| `puredns` / `shuffledns` / `massdns` | DNS brute-force resolution |
| `alterx` | Subdomain permutation generation |
| `ffuf` | Directory/parameter fuzzing |
| `gowitness` | Screenshot capture for live hosts |
| `paramspider` | Parameter discovery |
| `wappalyzergo` | Technology fingerprinting |
| `cloud_enum` | Extended cloud asset enumeration |
| `asnmap` | ASN-to-IP-range mapping |
| `trufflehog` | Verified secret detection in JS files |

> **Brute-force note:** At least one of `puredns`, `shuffledns`, or `massdns` is needed for the `recursive` phase. If none are found, that phase is silently skipped.

### GF Patterns

The `mine` phase uses gf patterns. Install the community patterns:

```bash
mkdir -p ~/.gf
git clone https://github.com/1ndianl33t/Gf-Patterns /tmp/gf-patterns
cp /tmp/gf-patterns/*.json ~/.gf/
```

---

## Installation

```bash
# Clone or copy the script
git clone https://github.com/anshu19981/ghost-protocol
cd ghost-protocol

# Install Python dependencies
pip install requests colorama

# Install all required Go tools (see Requirements above)
# Then verify:
python3 ghost_protocol_v14.py --help
```

---

## Configuration

Ghost Protocol reads configuration from environment variables or a `.env` file in the working directory.

### .env File

Create a `.env` file alongside the script:

```bash
# Discord webhook for real-time alerts (optional)
GP_DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR/WEBHOOK

# GitHub personal access token — enables GitHub dorking (phase 8)
# Scope required: read:user, public_repo (read-only)
GP_GITHUB_TOKEN=ghp_XXXXXXXXXXXXXXXX

# Proxy list file — one proxy per line (http://user:pass@host:port)
GP_PROXY_FILE=/path/to/proxies.txt

# Rate limiting
GP_BACKOFF_429=30.0        # Seconds to back off on HTTP 429
GP_BASE_DELAY=0.3          # Base delay between requests (seconds)

# Scan tuning
GP_MAX_403=100             # Max URLs to attempt 403 bypass on
GP_MAX_JS=300              # Max JS files to scan for secrets
GP_NUCLEI_FAST_ONLY=0      # 1 = skip CVE templates (faster scans)

# Custom User-Agent pool file
GP_UA_FILE=~/.ghost_protocol/user_agents.txt

# Favicon hashing (extra request per host — off by default)
GP_FAVICON=1               # Enable favicon hashing
```

> All `.env` variables can also be exported as shell environment variables. Shell environment takes precedence over `.env`.

---

## Usage

```
python3 ghost_protocol_v14.py <targets.txt> [OPTIONS]
```

### Positional Argument

```
targets.txt     Path to a file containing one domain per line.
                Example:
                  example.com
                  sub.example.com
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--scope <file>` | — | Path to a scope file containing allowed domains/wildcards. Subdomains outside scope are filtered. |
| `--output-dir <dir>` | Auto (timestamped) | Use a fixed output directory. Enables safe re-runs and resuming. |
| `--phases <list>` | All phases | Comma-separated list of phases to run. See phase names below. |
| `--passive` | Off | Passive-only mode — skips brute-force, port scanning, and active probing. OSINT recon only. |
| `--dry-run` | Off | Print all commands that would run without executing them. Useful for auditing. |
| `--force` | Off | Re-scan domains that already have a `.scan_complete` marker. |
| `--skip-nuclei-update` | Off | Skip automatic nuclei template update on startup. |
| `--rate-limit <N>` | 150 | Global requests/second cap applied to httpx, katana, and nuclei. Lower = stealthier. |
| `--sweep-workers <N>` | 15 | Parallel worker threads for 403 bypass, cloud enum, and JS secret sweeps. |
| `--favicon` | Off | Enable favicon hashing in httpx (mmh3 hash → asset clustering). Adds one extra request per host. |
| `--katana-scope <mode>` | `rdn` | Katana crawl scope: `rdn` (root domain, follows sibling subdomains), `fqdn` (exact host only), `dn`. |
| `--github-pages <N>` | 3 | Number of pages to fetch per GitHub dork query (100 results/page). |

### Available Phase Names

```
enum        Subdomain enumeration (passive)
recursive   Recursive DNS brute-force with permutations
probe       Port scanning + HTTP probing + tech detection
history     Historical URL collection (gau/wayback)
scan        Nuclei vulnerability scan + Katana crawl
js          JavaScript secret hunting (trufflehog + regex)
mine        Data mining: gf patterns + 403 bypass engine
cloud       Cloud storage asset enumeration (S3/GCS/Azure)
github      GitHub code search dorking
takeover    Subdomain takeover detection
asn         ASN enumeration → IP range scanning
jsdiff      JS diff monitoring for new endpoints/secrets
```

---

## Examples

### Basic full scan

```bash
echo "example.com" > targets.txt
python3 ghost_protocol_v14.py targets.txt
```

### Multiple targets with scope enforcement

```bash
python3 ghost_protocol_v14.py targets.txt --scope scope.txt
```

### Passive-only recon (no active scanning)

```bash
python3 ghost_protocol_v14.py targets.txt --passive
```

### Run specific phases only

```bash
# Only subdomain enum + probe
python3 ghost_protocol_v14.py targets.txt --phases enum,probe

# Only secret hunting phases
python3 ghost_protocol_v14.py targets.txt --phases js,github,jsdiff
```

### Resume an interrupted scan

```bash
# Pass the same --output-dir from the previous run
python3 ghost_protocol_v14.py targets.txt --output-dir DEEP_RECON_20240115_143022
```

### Stealth mode (slow, low-noise)

```bash
python3 ghost_protocol_v14.py targets.txt --rate-limit 30 --passive
```

### Dry run — preview commands without executing

```bash
python3 ghost_protocol_v14.py targets.txt --dry-run
```

### Force rescan of already-completed targets

```bash
python3 ghost_protocol_v14.py targets.txt --output-dir PREVIOUS_SESSION --force
```

---

## Output Structure

Ghost Protocol creates one directory per target domain inside the session directory.

```
DEEP_RECON_<SESSION_ID>/
│
├── SESSION_FINDINGS.json       ← All targets merged, severity-sorted
├── index.html                  ← Multi-target dashboard
│
└── example.com/
    ├── findings.json           ← Normalized findings — PRIMARY TRIAGE FILE
    ├── summary.json            ← Stat counts for all evidence files
    ├── report.html             ← Cyberpunk HTML report with copy buttons
    ├── recon.log               ← Full debug log for this domain
    │
    ├── raw_subs.txt            ← Raw passive subdomains
    ├── brute_subs.txt          ← DNS brute-force results
    ├── perm_subs.txt           ← Permutation-based subdomains
    ├── recursive_subs.txt      ← Recursive brute subdomains
    ├── resolved.txt            ← DNS-resolved subdomains
    ├── live.txt                ← Live HTTP hosts (key probed fields)
    ├── live_all.txt            ← Live hosts — all status codes
    ├── live_200.txt            ← 200 OK hosts only
    ├── nonstandard_live.txt    ← Hosts on non-standard ports
    ├── open_ports.txt          ← host:port pairs from naabu
    ├── all_endpoints.txt       ← All discovered URLs (crawl + history)
    ├── favicon_clusters.txt    ← Hosts grouped by favicon hash (pivot signal)
    ├── infra_map.txt           ← IP/CNAME infrastructure map
    │
    └── evidence/
        ├── vulns.txt           ← Nuclei vulnerability hits
        ├── vulns_cve.txt       ← Nuclei CVE hits
        ├── xss.txt             ← XSS parameter candidates (gf)
        ├── sqli.txt            ← SQLi parameter candidates (gf)
        ├── ssrf.txt            ← SSRF parameter candidates (gf)
        ├── ssti.txt            ← SSTI parameter candidates (gf)
        ├── lfi.txt             ← LFI parameter candidates (gf)
        ├── rce.txt             ← RCE parameter candidates (gf)
        ├── idor.txt            ← IDOR parameter candidates (gf)
        ├── open_redirect.txt   ← Open redirect candidates (gf)
        ├── debug.txt           ← Debug/logic parameter candidates (gf)
        ├── js_secrets.txt      ← Regex-detected secrets in JS ([high-signal] tagged)
        ├── trufflehog_js.txt   ← Verified secrets from live JS (trufflehog)
        ├── trufflehog_wayback_js.txt ← Verified secrets from Wayback JS
        ├── 403_bypass.txt      ← Successful 403/401 bypass attempts
        ├── cors.txt            ← CORS misconfiguration hits
        ├── vhosts.txt          ← Virtual hosts discovered
        ├── takeover_candidates.txt ← Subdomain takeover candidates
        ├── cloud_assets.txt    ← Accessible cloud storage buckets
        ├── github_leaks.txt    ← GitHub code search findings
        ├── asn_ranges.txt      ← IP ranges from ASN lookup
        ├── asn_open_ports.txt  ← Open ports from ASN IP scanning
        ├── asn_live_hosts.txt  ← Live hosts from ASN IP ranges
        └── js_diff_endpoints.txt ← New endpoints found via JS diff
```

### findings.json Schema

The primary triage file. Every finding follows this structure:

```json
{
  "target": "example.com",
  "timestamp": "2024-01-15T14:30:22.123456",
  "total_findings": 42,
  "by_severity": {
    "critical": 1,
    "high": 5,
    "medium": 12,
    "low": 8,
    "info": 16
  },
  "findings": [
    {
      "target": "example.com",
      "type": "nuclei",
      "severity": "critical",
      "source": "vulns.txt",
      "detail": "[CVE-2024-XXXX] [http] [critical] https://api.example.com/..."
    }
  ]
}
```

**Finding types:** `nuclei`, `subdomain-takeover`, `secret-verified`, `secret-high-signal`, `secret-unverified`, `403-bypass`, `cors-misconfig`, `github-leak`, `cloud-asset`, `nonstd-service`, `favicon-cluster`

**Severity levels:** `critical` → `high` → `medium` → `low` → `info`

---

## Architecture

Ghost Protocol is a single-file build composed of four internal modules:

### GhostConfig
Loads all configuration from environment variables and `.env`. Provides proxy dict helpers and a safe dump method for logging (credentials masked).

### StealthEngine
Per-domain rate-limited HTTP client wrapping `requests`. Features:
- User-Agent rotation from configurable pool
- Rotating proxy pool with per-proxy health tracking
- Adaptive backoff on HTTP 429 (respects `Retry-After` header)
- Per-domain request delay with jitter

### SmartNuclei
Nuclei command builder that selects appropriate template sets and flags based on scan mode (fast vs. deep vs. CVE-only). Automatically updates templates on startup unless `--skip-nuclei-update` is set.

### Bypass403
A 19-technique 403/401 bypass engine running concurrently via `ThreadPoolExecutor`. Techniques include header injection (`X-Forwarded-For`, `X-Original-URL`, `X-Rewrite-URL`, etc.), path variants (`//`, `/%2f`, `/.`), and HTTP verb tampering.

---

## Discord Notifications

Set `GP_DISCORD_WEBHOOK` in `.env` to receive real-time alerts. Ghost Protocol sends notifications at key phase milestones:

- Nuclei critical/high findings
- JavaScript secrets detected
- Subdomain takeover candidates
- Virtual hosts discovered
- 403 bypasses found
- Cloud assets accessible
- GitHub leaks found
- ASN live IP counts

---

## Triage Workflow

After a scan completes, work the output in this order:

```
1. SESSION_FINDINGS.json        → Cross-target severity overview
2. findings.json (per domain)   → Per-target normalized findings
3. evidence/trufflehog_*.txt    → Verified secrets — report immediately
4. evidence/takeover_candidates.txt → Claim and verify
5. evidence/vulns.txt           → Nuclei confirmed vulnerabilities
6. evidence/403_bypass.txt      → Manually verify each bypass
7. evidence/cors.txt            → Check with auth cookies
8. evidence/github_leaks.txt    → Validate keys before reporting
9. evidence/js_secrets.txt      → [high-signal] entries first
10. evidence/xss.txt / sqli.txt → Manual validation in Burp
```

---

## Responsible Use

Ghost Protocol is intended exclusively for:

- Authorized bug bounty programs (in-scope targets only)
- Penetration testing engagements with written authorization
- Security research in controlled/lab environments

Unauthorized use against systems you do not have explicit permission to test is illegal. The author assumes no liability for misuse.

---

## License

For personal bug bounty and authorized security research use only.

---

*Ghost Protocol v14.1 — Built by Anshuman Jha*
