# Ghost Protocol v11.0 — Deep Recon Engine


<img width="1918" height="980" alt="2026-05-22_13-27" src="https://github.com/user-attachments/assets/5a003fb2-2ad1-4699-9ac3-c47aa84186e2" />



**Ghost Protocol** is an advanced, high-performance automated reconnaissance framework designed specifically for bug bounty hunters. It integrates industry-standard security tools into a cohesive, modular pipeline to map target attack surfaces, detect misconfigurations, and identify critical vulnerabilities.

---

### 🚀 Key Features

* **Stealth & Adaptive Recon:** Features a built-in `StealthEngine` that handles rotating proxies, adaptive backoff for 429 rate-limiting, and dynamic User-Agent rotation.
* **Modular Pipeline:** Execute one or all of the 8 phases (Enum → Recursive Brute → Probe → Scan → JS Secrets → Data Mining → Cloud → GitHub Dorks) based on your needs.
* **Advanced 403 Bypass Engine:** A robust bypass module utilizing 19+ techniques, including header manipulation, verb tampering, and path mutation, to test WAF/gateway restrictions.
* **Smart Nuclei Integration:** Automatically prioritizes high-yield `FAST_IMPACT` templates while keeping `DEEP_SCAN` modules optional.
* **Asset Discovery:** Includes S3/GCS bucket enumeration and targeted GitHub Dorking to identify sensitive leaks and exposed assets.
* **GUI Interface:** Includes `ghost_gui_v2.py`, a `customtkinter` dashboard for module orchestration and real-time console monitoring.

---

### 🛠 Tools Included
Ghost Protocol acts as a powerful wrapper for the following tools:
`subfinder`, `assetfinder`, `httpx`, `nuclei`, `katana`, `gf`, `dnsx`, `naabu`, `gau`, `puredns`, `shuffledns`, `alterx`, `gowitness`, `paramspider`, `wappalyzergo`, `subzy`, `corsy`, `ffuf`.

---

### 📥 Setup & Installation

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/yourusername/ghost-protocol.git](https://github.com/yourusername/ghost-protocol.git)
    cd ghost-protocol
    ```

2.  **Environment Configuration:**
    Create a `.env` file in the root directory to configure your environment:
    ```bash
    GP_DISCORD_WEBHOOK=your_webhook_url
    GP_GITHUB_TOKEN=your_token
    GP_PROXY_FILE=~/.ghost_protocol/proxies.txt
    ```

3.  **Run:**
    * **CLI Mode:**
        ```bash
        python3 ghost_protocol_v11.py targets.txt --phases enum,scan,mine
        ```
    * **GUI Mode:**
        ```bash
        python3 ghost_gui_v2.py
        ```

---

### 📊 Pipeline Workflow

| Phase | Description |
| :--- | :--- |
| **Enum** | Passive & Active subdomain discovery (subfinder/alterx). |
| **Recursive** | Recursive bruteforcing on high-priority subdomains. |
| **Probe** | Naabu port scanning followed by HTTP status verification. |
| **Scan** | Nuclei vulnerability scanning and Katana web crawling. |
| **JS** | Mining JavaScript files for exposed API keys and secrets. |
| **Mine** | GF pattern matching, CORS checks, and 403 Bypass attempts. |
| **Cloud** | S3/GCS bucket enumeration for public/private assets. |
| **GitHub** | Organization-specific secret hunting via GitHub Dorking. |

---

### 🛡 Disclaimer
*This tool is intended for educational purposes and authorized security auditing only. The author assumes no responsibility for misuse or legal consequences. Always ensure you have explicit, written permission to test your target.*

---
*Engineered by an OSCP-certified security researcher to streamline attack surface management and vulnerability discovery.*
