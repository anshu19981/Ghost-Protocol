#!/usr/bin/env python3
"""
Ghost Protocol v11 — GUI v2
Ultra-polished cyberpunk interface

Requirements:
    pip install customtkinter
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import threading
import os
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    HAS_CTK = True
except ImportError:
    HAS_CTK = False
    print("[!] customtkinter not found — run: pip install customtkinter")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
# COLOR SYSTEM
# ═══════════════════════════════════════════════════════════════════

C = {
    "bg":       "#090d12",
    "bg2":      "#0d1117",
    "bg3":      "#161b22",
    "bg4":      "#1c2128",
    "bg5":      "#21262d",
    "border":   "#30363d",
    "border2":  "#3d444d",
    "text":     "#e6edf3",
    "text2":    "#8b949e",
    "text3":    "#484f58",
    "green":    "#39d353",
    "green_dk": "#238636",
    "red":      "#f85149",
    "red_dk":   "#da3633",
    "yellow":   "#e3b341",
    "cyan":     "#58a6ff",
    "cyan_dk":  "#1f6feb",
    "purple":   "#bc8cff",
    "orange":   "#ffa657",
    "teal":     "#2dd4bf",
    "pink":     "#f778ba",
}

FONT_MONO   = ("JetBrains Mono", 10)
FONT_MONO_S = ("JetBrains Mono", 9)
FONT_MONO_L = ("JetBrains Mono", 12, "bold")
FONT_TITLE  = ("JetBrains Mono", 18, "bold")
FONT_BADGE  = ("JetBrains Mono", 11, "bold")

# ═══════════════════════════════════════════════════════════════════
# PHASE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

PHASES = [
    "enum", "recursive", "probe", "history",
    "scan", "js", "mine", "cloud",
    "github", "takeover", "asn", "jsdiff",
]

PHASE_META = {
    "enum":      {"label": "Subdomain Enum",   "short": "ENUM",  "color": C["cyan"],   "icon": "◈"},
    "recursive": {"label": "Recursive Brute",  "short": "RECUR", "color": C["purple"], "icon": "↻"},
    "probe":     {"label": "Port + Probe",     "short": "PROBE", "color": C["orange"], "icon": "⬡"},
    "history":   {"label": "Historical URLs",  "short": "HIST",  "color": C["teal"],   "icon": "⊕"},
    "scan":      {"label": "Nuclei Scan",      "short": "SCAN",  "color": C["red"],    "icon": "◎"},
    "js":        {"label": "JS Secrets",       "short": "JS",    "color": C["yellow"], "icon": "⟨⟩"},
    "mine":      {"label": "Data Mining",      "short": "MINE",  "color": C["green"],  "icon": "◆"},
    "cloud":     {"label": "Cloud Enum",       "short": "CLOUD", "color": C["cyan"],   "icon": "☁"},
    "github":    {"label": "GitHub Dorking",   "short": "GITHU", "color": C["purple"], "icon": "⦿"},
    "takeover":  {"label": "Takeover Check",   "short": "TAKEO", "color": C["red"],    "icon": "⚑"},
    "asn":       {"label": "ASN Enum",         "short": "ASN",   "color": C["orange"], "icon": "⊞"},
    "jsdiff":    {"label": "JS Diff",          "short": "JSDIF", "color": C["yellow"], "icon": "Δ"},
}

PASSIVE_PHASES = {"enum", "cloud", "github"}

# Phase status states
ST_IDLE    = "idle"
ST_RUNNING = "running"
ST_DONE    = "done"
ST_SKIP    = "skip"
ST_ERROR   = "error"

STATUS_STYLE = {
    ST_IDLE:    {"fg": C["text3"],  "bg": C["bg4"],  "char": "○"},
    ST_RUNNING: {"fg": C["yellow"], "bg": C["bg4"],  "char": "◉"},
    ST_DONE:    {"fg": C["green"],  "bg": C["bg4"],  "char": "✓"},
    ST_SKIP:    {"fg": C["text3"],  "bg": C["bg4"],  "char": "–"},
    ST_ERROR:   {"fg": C["red"],    "bg": C["bg4"],  "char": "✗"},
}


# ═══════════════════════════════════════════════════════════════════
# HELPER WIDGETS
# ═══════════════════════════════════════════════════════════════════

class SectionHeader(ctk.CTkFrame):
    """Styled section header with horizontal rule."""
    def __init__(self, parent, title, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        tk.Label(self, text=title, font=("JetBrains Mono", 8, "bold"),
                 fg=C["text3"], bg=C["bg3"]).pack(side="left")
        tk.Frame(self, bg=C["border"], height=1).pack(
            side="left", fill="x", expand=True, padx=(8, 0), pady=1)


class PhaseCard(tk.Frame):
    """Single phase status card in the tracker strip."""
    def __init__(self, parent, phase_key, **kwargs):
        meta = PHASE_META[phase_key]
        super().__init__(parent, bg=C["bg4"], padx=6, pady=4, **kwargs)
        self.phase_key = phase_key

        self.icon_lbl = tk.Label(self, text=meta["icon"],
                                  font=("JetBrains Mono", 10),
                                  fg=C["text3"], bg=C["bg4"])
        self.icon_lbl.pack()

        self.name_lbl = tk.Label(self, text=meta["short"],
                                  font=("JetBrains Mono", 7, "bold"),
                                  fg=C["text3"], bg=C["bg4"])
        self.name_lbl.pack()

        self.status_lbl = tk.Label(self, text="○",
                                    font=("JetBrains Mono", 8),
                                    fg=C["text3"], bg=C["bg4"])
        self.status_lbl.pack()

        self.time_lbl = tk.Label(self, text="",
                                  font=("JetBrains Mono", 7),
                                  fg=C["text3"], bg=C["bg4"])
        self.time_lbl.pack()

        self._start_time = None

    def set_status(self, state, elapsed=None):
        st = STATUS_STYLE[state]
        meta = PHASE_META[self.phase_key]
        color = meta["color"] if state == ST_RUNNING else (
            C["green"] if state == ST_DONE else (
            C["red"]   if state == ST_ERROR else C["text3"]))
        self.icon_lbl.config(fg=color)
        self.name_lbl.config(fg=color)
        self.status_lbl.config(text=st["char"], fg=color)
        if elapsed:
            self.time_lbl.config(text=f"{elapsed:.0f}s", fg=C["text3"])

    def start_timer(self):
        self._start_time = time.time()

    def get_elapsed(self):
        if self._start_time:
            return time.time() - self._start_time
        return 0.0


class ToastNotification(tk.Toplevel):
    """Brief toast popup."""
    def __init__(self, parent, message, color=C["green"]):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=C["bg4"])
        tk.Label(self, text=f"  {message}  ",
                 font=FONT_MONO, fg=color, bg=C["bg4"],
                 padx=12, pady=8).pack()
        # Position bottom-right of parent
        px = parent.winfo_x() + parent.winfo_width() - 300
        py = parent.winfo_y() + parent.winfo_height() - 80
        self.geometry(f"+{px}+{py}")
        self.after(2500, self.destroy)


# ═══════════════════════════════════════════════════════════════════
# MAIN GUI CLASS
# ═══════════════════════════════════════════════════════════════════

class GhostProtocolGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Ghost Protocol v11")
        self.root.geometry("1300x820")
        self.root.configure(bg=C["bg"])
        self.root.minsize(1000, 650)

        # State
        self.process      = None
        self.running      = False
        self.phase_vars   = {}
        self.phase_cards  = {}
        self.phase_states = {p: ST_IDLE for p in PHASES}
        self.phase_timers = {p: None for p in PHASES}
        self._current_phase = None
        self._elapsed_start = None
        self._elapsed_after = None

        # Tkinter vars
        self.output_dir   = tk.StringVar()
        self.targets_file = tk.StringVar()
        self.scope_file   = tk.StringVar()
        self.script_path  = tk.StringVar(
            value=str(Path(__file__).parent / "ghost_protocol_v11.py"))
        self.dry_run      = tk.BooleanVar(value=False)
        self.passive_mode = tk.BooleanVar(value=False)
        self.force_mode   = tk.BooleanVar(value=False)
        self.skip_nuclei  = tk.BooleanVar(value=False)

        # Log filter state
        self._log_filter      = "all"   # all | errors | warnings | info
        self._search_query    = ""
        self._all_log_lines   = []      # (text, tag) pairs

        # Summary counters
        self._summary = {
            "subs": "—", "live": "—", "vulns": "—",
            "js": "—", "gh": "—", "cloud": "—", "takeover": "—",
        }

        self._build_ui()
        self._try_load_fonts()

    # ─────────────────────────────────────────────────────────────
    # FONT SETUP
    # ─────────────────────────────────────────────────────────────

    def _try_load_fonts(self):
        """Fall back gracefully if JetBrains Mono not installed."""
        import tkinter.font as tkf
        available = tkf.families()
        if "JetBrains Mono" not in available:
            # Fall back to Courier
            global FONT_MONO, FONT_MONO_S, FONT_MONO_L, FONT_TITLE, FONT_BADGE
            FONT_MONO   = ("Courier", 10)
            FONT_MONO_S = ("Courier", 9)
            FONT_MONO_L = ("Courier", 12, "bold")
            FONT_TITLE  = ("Courier", 18, "bold")
            FONT_BADGE  = ("Courier", 11, "bold")

    # ─────────────────────────────────────────────────────────────
    # UI CONSTRUCTION
    # ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_titlebar()
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")
        self._build_main_area()
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")
        self._build_stats_bar()
        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")
        self._build_bottom_bar()

    # ── Title Bar ────────────────────────────────────────────────

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=C["bg"], pady=10)
        bar.pack(fill="x", padx=20)

        # Logo / title
        left_bar = tk.Frame(bar, bg=C["bg"])
        left_bar.pack(side="left")

        tk.Label(left_bar, text="⬡ GHOST PROTOCOL",
                 font=FONT_TITLE, fg=C["cyan"], bg=C["bg"]).pack(side="left")
        tk.Label(left_bar, text=" v11",
                 font=("JetBrains Mono", 14, "bold"),
                 fg=C["text3"], bg=C["bg"]).pack(side="left", pady=2)
        tk.Label(left_bar, text="  Bug Bounty Recon Engine",
                 font=FONT_MONO_S, fg=C["text3"], bg=C["bg"]).pack(
                 side="left", padx=12, pady=4)

        # Right side: status + timer
        right_bar = tk.Frame(bar, bg=C["bg"])
        right_bar.pack(side="right")

        self.timer_lbl = tk.Label(right_bar, text="00:00:00",
                                   font=FONT_MONO_S, fg=C["text3"], bg=C["bg"])
        self.timer_lbl.pack(side="right", padx=12)

        self.status_dot = tk.Label(right_bar, text="● IDLE",
                                    font=("JetBrains Mono", 11, "bold"),
                                    fg=C["text3"], bg=C["bg"])
        self.status_dot.pack(side="right")

    # ── Main Area (left + right) ─────────────────────────────────

    def _build_main_area(self):
        pane = tk.PanedWindow(self.root, orient="horizontal",
                               bg=C["border"], sashwidth=4,
                               sashrelief="flat", handlepad=0)
        pane.pack(fill="both", expand=True)

        left  = tk.Frame(pane, bg=C["bg3"])
        right = tk.Frame(pane, bg=C["bg"])

        pane.add(left,  minsize=300, width=360)
        pane.add(right, minsize=500)

        self._build_left_panel(left)
        self._build_right_panel(right)

    # ── LEFT PANEL ───────────────────────────────────────────────

    def _build_left_panel(self, parent):
        # Scrollable canvas
        canvas = tk.Canvas(parent, bg=C["bg3"], highlightthickness=0)
        vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                            bg=C["bg4"], troughcolor=C["bg3"],
                            highlightthickness=0, bd=0)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=C["bg3"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=canvas.winfo_width())

        inner.bind("<Configure>", _resize)
        canvas.bind("<Configure>", _resize)
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

        p = {"padx": 16, "pady": 3}

        # ── Target Config ─────────────────────────────────────
        self._section(inner, "TARGET CONFIG")

        self._file_row(inner, "Targets file",   self.targets_file,
                       "Select targets.txt", [("Text", "*.txt"), ("All", "*")])
        self._file_row(inner, "Scope file",     self.scope_file,
                       "Select scope.txt",   [("Text", "*.txt"), ("All", "*")])
        self._dir_row (inner, "Output dir",     self.output_dir)
        self._file_row(inner, "Script path",    self.script_path,
                       "Select ghost_protocol_v11.py", [("Python", "*.py")])

        # ── Phases ────────────────────────────────────────────
        self._section(inner, "PHASES")

        phase_grid = tk.Frame(inner, bg=C["bg3"])
        phase_grid.pack(fill="x", **p)

        for i, phase in enumerate(PHASES):
            var = tk.BooleanVar(value=True)
            self.phase_vars[phase] = var
            meta = PHASE_META[phase]

            row_f = tk.Frame(phase_grid, bg=C["bg3"])
            row_f.grid(row=i//2, column=i%2, sticky="ew", padx=2, pady=1)

            cb = tk.Checkbutton(
                row_f, text=f"{meta['icon']}  {meta['label']}",
                variable=var,
                bg=C["bg3"], fg=meta["color"],
                selectcolor=C["bg4"],
                activebackground=C["bg3"],
                activeforeground=meta["color"],
                font=FONT_MONO_S,
                cursor="hand2",
                anchor="w",
            )
            cb.pack(side="left", fill="x")

        # Quick-select row
        qf = tk.Frame(inner, bg=C["bg3"])
        qf.pack(fill="x", padx=16, pady=(6, 2))
        for label, cmd, color in [
            ("All",          self._select_all,     C["text2"]),
            ("None",         self._select_none,    C["text2"]),
            ("Passive only", self._select_passive, C["cyan"]),
        ]:
            tk.Button(qf, text=label, command=cmd,
                      **self._btn(C["bg5"], color)).pack(side="left", padx=2)

        # ── Options ───────────────────────────────────────────
        self._section(inner, "OPTIONS")

        opts = [
            ("Dry run (no execution)",  self.dry_run,      C["yellow"]),
            ("Passive mode",            self.passive_mode, C["cyan"]),
            ("Force rescan",            self.force_mode,   C["orange"]),
            ("Skip nuclei update",      self.skip_nuclei,  C["text2"]),
        ]
        for label, var, color in opts:
            f = tk.Frame(inner, bg=C["bg3"])
            f.pack(fill="x", padx=16, pady=1)
            tk.Checkbutton(f, text=label, variable=var,
                           bg=C["bg3"], fg=color,
                           selectcolor=C["bg4"],
                           activebackground=C["bg3"],
                           activeforeground=color,
                           font=FONT_MONO_S, cursor="hand2").pack(anchor="w")

        # padding at bottom
        tk.Frame(inner, bg=C["bg3"], height=20).pack()

    # ── RIGHT PANEL ──────────────────────────────────────────────

    def _build_right_panel(self, parent):
        # ── Log toolbar ──────────────────────────────────────
        toolbar = tk.Frame(parent, bg=C["bg3"])
        toolbar.pack(fill="x")

        # Filter buttons
        self._filter_btns = {}
        filter_bar = tk.Frame(toolbar, bg=C["bg3"])
        filter_bar.pack(side="left", padx=8, pady=6)

        for tag, label in [("all","ALL"), ("errors","ERR"), ("warnings","WARN"), ("info","INFO")]:
            is_active = (tag == "all")
            btn = tk.Button(
                filter_bar, text=label,
                command=lambda t=tag: self._set_filter(t),
                font=("JetBrains Mono", 8, "bold"),
                bg=C["cyan_dk"] if is_active else C["bg5"],
                fg=C["text"] if is_active else C["text3"],
                relief="flat", padx=8, pady=3,
                cursor="hand2",
                activebackground=C["bg5"], activeforeground=C["text"],
            )
            btn.pack(side="left", padx=1)
            self._filter_btns[tag] = btn

        # Search bar
        search_frame = tk.Frame(toolbar, bg=C["bg3"])
        search_frame.pack(side="left", padx=8, fill="x", expand=True)

        tk.Label(search_frame, text="⌕", font=("JetBrains Mono", 12),
                 fg=C["text3"], bg=C["bg3"]).pack(side="left", padx=4)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                bg=C["bg4"], fg=C["text"],
                                insertbackground=C["cyan"],
                                relief="flat", font=FONT_MONO_S,
                                highlightthickness=1,
                                highlightcolor=C["cyan_dk"],
                                highlightbackground=C["border"])
        search_entry.pack(side="left", fill="x", expand=True, ipady=4)

        tk.Button(search_frame, text="✕",
                  command=lambda: self.search_var.set(""),
                  **self._btn(C["bg3"], C["text3"])).pack(side="left", padx=4)

        # Right buttons
        right_btns = tk.Frame(toolbar, bg=C["bg3"])
        right_btns.pack(side="right", padx=8)

        tk.Button(right_btns, text="Save log", command=self._save_log,
                  **self._btn(C["bg5"], C["text2"])).pack(side="right", padx=2, pady=4)
        tk.Button(right_btns, text="Clear",    command=self._clear_log,
                  **self._btn(C["bg5"], C["text2"])).pack(side="right", padx=2, pady=4)

        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x")

        # ── Log area ─────────────────────────────────────────
        self.log_text = tk.Text(
            parent,
            bg=C["bg"], fg=C["text"],
            font=FONT_MONO_S,
            insertbackground=C["cyan"],
            selectbackground=C["bg5"],
            relief="flat", bd=0,
            wrap="word", state="disabled",
            spacing1=1, spacing3=1,
        )
        log_vsb = tk.Scrollbar(parent, orient="vertical",
                                command=self.log_text.yview,
                                bg=C["bg4"], troughcolor=C["bg3"],
                                highlightthickness=0, bd=0)
        self.log_text.configure(yscrollcommand=log_vsb.set)
        log_vsb.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        self._setup_log_tags()

        # ── Phase Tracker Strip ───────────────────────────────
        self._build_phase_tracker(parent.master
                                   if hasattr(parent, "master") else parent)

    def _build_phase_tracker(self, parent):
        """Phase cards row below the log."""
        # We pack this into the right panel frame
        # Find right panel's real parent by traversing
        # Actually simpler: add to root's bottom area above stats
        tracker_outer = tk.Frame(self.root, bg=C["bg3"])
        # We'll insert this before stats — handled via pack order in _build_ui
        # But since we're called after, we just insert it now
        # (It will appear between log and stats)
        tracker_outer.pack(fill="x")

        tk.Frame(tracker_outer, bg=C["border"], height=1).pack(fill="x")
        tracker_inner = tk.Frame(tracker_outer, bg=C["bg3"])
        tracker_inner.pack(fill="x", pady=4, padx=8)

        tk.Label(tracker_inner, text="PHASES ",
                 font=("JetBrains Mono", 7, "bold"),
                 fg=C["text3"], bg=C["bg3"]).pack(side="left", padx=(4, 8))

        for phase in PHASES:
            card = PhaseCard(tracker_inner, phase)
            card.pack(side="left", padx=3)
            self.phase_cards[phase] = card

        self._tracker_outer = tracker_outer

    # ── Stats Bar ────────────────────────────────────────────────

    def _build_stats_bar(self):
        stats_frame = tk.Frame(self.root, bg=C["bg2"], pady=6)
        stats_frame.pack(fill="x")

        self.stat_labels = {}

        items = [
            ("Subdomains", "subs",     C["cyan"]),
            ("Live Hosts", "live",     C["green"]),
            ("Vulns",      "vulns",    C["red"]),
            ("Secrets",    "secrets",  C["orange"]),
            ("JS Secrets", "js",       C["yellow"]),
            ("GitHub",     "gh",       C["purple"]),
            ("Cloud",      "cloud",    C["teal"]),
            ("Takeover",   "takeover", C["red"]),
        ]

        for i, (label, key, color) in enumerate(items):
            if i > 0:
                tk.Frame(stats_frame, bg=C["border"], width=1).pack(
                    side="left", fill="y", pady=4)

            cell = tk.Frame(stats_frame, bg=C["bg2"])
            cell.pack(side="left", padx=18, pady=2)

            tk.Label(cell, text=label.upper(),
                     font=("JetBrains Mono", 7), fg=C["text3"],
                     bg=C["bg2"]).pack()

            lbl = tk.Label(cell, text="—",
                           font=("JetBrains Mono", 13, "bold"),
                           fg=color, bg=C["bg2"])
            lbl.pack()
            self.stat_labels[key] = (lbl, color)

    # ── Bottom Bar ───────────────────────────────────────────────

    def _build_bottom_bar(self):
        bar = tk.Frame(self.root, bg=C["bg2"], pady=8)
        bar.pack(fill="x")

        # START button
        self.start_btn = tk.Button(
            bar, text="▶  START SCAN",
            command=self._start_scan,
            font=("JetBrains Mono", 11, "bold"),
            bg=C["green_dk"], fg="#ffffff",
            relief="flat", padx=22, pady=8,
            cursor="hand2",
            activebackground=C["green"],
            activeforeground=C["bg"],
        )
        self.start_btn.pack(side="left", padx=(16, 4))

        # STOP button
        self.stop_btn = tk.Button(
            bar, text="■  STOP",
            command=self._stop_scan,
            font=("JetBrains Mono", 11, "bold"),
            bg=C["bg5"], fg=C["red"],
            relief="flat", padx=20, pady=8,
            cursor="hand2",
            state="disabled",
            activebackground=C["bg4"],
            activeforeground=C["red"],
        )
        self.stop_btn.pack(side="left", padx=4)

        # Progress bar (manual using Canvas)
        self.progress_canvas = tk.Canvas(bar, bg=C["bg4"],
                                          height=6, width=220,
                                          highlightthickness=0)
        self.progress_canvas.pack(side="left", padx=16, pady=8)
        self._progress_rect = self.progress_canvas.create_rectangle(
            0, 0, 0, 6, fill=C["cyan"], outline="")
        self._progress_pos   = 0
        self._progress_dir   = 1
        self._progress_after = None

        # Command preview with copy button
        cmd_outer = tk.Frame(bar, bg=C["bg2"])
        cmd_outer.pack(side="left", fill="x", expand=True, padx=4)

        self.cmd_label = tk.Label(
            cmd_outer, text="",
            font=("JetBrains Mono", 8),
            fg=C["text3"], bg=C["bg2"],
            anchor="w", justify="left",
        )
        self.cmd_label.pack(side="left", fill="x", expand=True)

        self.copy_btn = tk.Button(
            cmd_outer, text="⎘",
            command=self._copy_command,
            **self._btn(C["bg4"], C["text3"])
        )
        self.copy_btn.pack(side="right", padx=4)
        self._last_cmd = ""

    # ─────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────

    def _section(self, parent, title):
        f = tk.Frame(parent, bg=C["bg3"])
        f.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(f, text=title, font=("JetBrains Mono", 7, "bold"),
                 fg=C["text3"], bg=C["bg3"]).pack(side="left")
        tk.Frame(f, bg=C["border"], height=1).pack(
            side="left", fill="x", expand=True, padx=8)

    def _file_row(self, parent, label, var, dlg_title, filetypes):
        f = tk.Frame(parent, bg=C["bg3"])
        f.pack(fill="x", padx=16, pady=2)
        tk.Label(f, text=label, font=FONT_MONO_S,
                 fg=C["text2"], bg=C["bg3"], width=14, anchor="w").pack(side="left")
        e = tk.Entry(f, textvariable=var, bg=C["bg4"], fg=C["text"],
                     insertbackground=C["cyan"], relief="flat",
                     font=FONT_MONO_S, highlightthickness=1,
                     highlightcolor=C["cyan_dk"],
                     highlightbackground=C["border"])
        e.pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f, text="…",
                  command=lambda: var.set(
                      filedialog.askopenfilename(
                          title=dlg_title, filetypes=filetypes) or var.get()),
                  **self._btn(C["bg5"], C["text2"])).pack(side="left", padx=2)

    def _dir_row(self, parent, label, var):
        f = tk.Frame(parent, bg=C["bg3"])
        f.pack(fill="x", padx=16, pady=2)
        tk.Label(f, text=label, font=FONT_MONO_S,
                 fg=C["text2"], bg=C["bg3"], width=14, anchor="w").pack(side="left")
        e = tk.Entry(f, textvariable=var, bg=C["bg4"], fg=C["text"],
                     insertbackground=C["cyan"], relief="flat",
                     font=FONT_MONO_S, highlightthickness=1,
                     highlightcolor=C["cyan_dk"],
                     highlightbackground=C["border"])
        e.pack(side="left", fill="x", expand=True, ipady=3)
        tk.Button(f, text="…",
                  command=lambda: var.set(
                      filedialog.askdirectory(
                          title="Select output dir") or var.get()),
                  **self._btn(C["bg5"], C["text2"])).pack(side="left", padx=2)

    def _btn(self, bg, fg):
        return dict(bg=bg, fg=fg, relief="flat",
                    font=FONT_MONO_S, padx=8, pady=3,
                    cursor="hand2",
                    activebackground=C["bg4"],
                    activeforeground=C["text"])

    def _select_all(self):
        for v in self.phase_vars.values(): v.set(True)

    def _select_none(self):
        for v in self.phase_vars.values(): v.set(False)

    def _select_passive(self):
        self._select_none()
        for p in PASSIVE_PHASES: self.phase_vars[p].set(True)
        self.passive_mode.set(True)

    # ─────────────────────────────────────────────────────────────
    # LOG SYSTEM
    # ─────────────────────────────────────────────────────────────

    def _setup_log_tags(self):
        self.log_text.tag_config("green",   foreground=C["green"])
        self.log_text.tag_config("red",     foreground=C["red"])
        self.log_text.tag_config("yellow",  foreground=C["yellow"])
        self.log_text.tag_config("cyan",    foreground=C["cyan"])
        self.log_text.tag_config("purple",  foreground=C["purple"])
        self.log_text.tag_config("orange",  foreground=C["orange"])
        self.log_text.tag_config("teal",    foreground=C["teal"])
        self.log_text.tag_config("dim",     foreground=C["text3"])
        self.log_text.tag_config("text",    foreground=C["text"])
        self.log_text.tag_config("phase",   foreground=C["cyan"],
                                 font=("JetBrains Mono", 10, "bold"))

    def _classify_line(self, line):
        """Return (tag, category) for a line."""
        s = line.strip()

        # Errors / criticals
        if any(k in line for k in ("[!]", "ERROR", "CRITICAL", "fatal")):
            return "red", "errors"

        # Warnings / skips / rate limits
        if any(k in line for k in ("[~]", "WARNING", "WARN")):
            # Distinguish skip (just yellow/info) vs rate-limit warnings
            return "yellow", "warnings"

        # Phase headers  ── PHASE N: TITLE ──
        if "PHASE" in line and ("──" in line or "─" in line):
            return "phase", "info"

        # Section separators
        if any(k in line for k in ("═══", "───", "━━━", "===", "────")):
            return "phase", "info"

        # Success lines
        if s.startswith("[✔]") or "Done in" in line or "✔" in line or "ALL DONE" in line:
            return "green", "info"

        # GitHub dorking results
        if s.startswith("[GH]") or "GitHub findings:" in line:
            return "purple", "info"

        # High-value findings — secrets, bypasses, takeovers
        if any(k in line for k in ("*** Secrets", "Secrets matched", "BYPASS", "private_key", "api_key", "secret")):
            return "orange", "errors"

        # Cloud / bucket findings
        if any(k in line for k in ("🪣", "GCS[", "S3[", "AZURE[", "Cloud assets found")):
            return "teal", "info"

        # Dry run commands
        if "[DRY]" in line:
            return "yellow", "info"

        # Info markers
        if s.startswith("[*]"):
            return "cyan", "info"

        # Summary block header
        if "SUMMARY:" in line or "SUMMARY" in line and "═" in line:
            return "phase", "info"

        # Timer lines
        if s.startswith("⏱"):
            return "dim", "info"

        return "dim", "info"

    def _append_log(self, line):
        tag, category = self._classify_line(line)
        self._all_log_lines.append((line, tag, category))

        # Phase detection
        self._detect_phase_change(line)

        # Summary update
        self._update_summary(line)

        # Render if matches current filter + search
        if self._should_show(line, category):
            self._render_line(line, tag)

    def _render_line(self, line, tag):
        self.log_text.config(state="normal")
        self.log_text.insert("end", line, tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _log(self, text, tag="dim"):
        self._all_log_lines.append((text, tag, "info"))
        if self._should_show(text, "info"):
            self._render_line(text, tag)

    def _should_show(self, line, category):
        if self._log_filter != "all" and category != self._log_filter:
            return False
        if self._search_query:
            return self._search_query.lower() in line.lower()
        return True

    def _set_filter(self, ftype):
        self._log_filter = ftype
        for tag, btn in self._filter_btns.items():
            active = (tag == ftype)
            btn.config(
                bg=C["cyan_dk"] if active else C["bg5"],
                fg=C["text"]    if active else C["text3"],
            )
        self._redraw_log()

    def _on_search_change(self, *args):
        self._search_query = self.search_var.get()
        self._redraw_log()

    def _redraw_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        for line, tag, category in self._all_log_lines:
            if self._should_show(line, category):
                self.log_text.insert("end", line, tag)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self._all_log_lines.clear()
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All", "*")],
            initialfile=f"gp_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                for line, _, _ in self._all_log_lines:
                    f.write(line)
            ToastNotification(self.root, f"Log saved → {Path(path).name}")

    # ─────────────────────────────────────────────────────────────
    # PHASE TRACKING
    # ─────────────────────────────────────────────────────────────

    # ── Actual output format from ghost_protocol_v11.py ──────────────
    # Phase headers:  ── PHASE 1: SUBDOMAIN ENUMERATION ──
    #                 ── PHASE 1b: RECURSIVE BRUTEFORCING ──
    # Phase done:     ⏱  3.1s   (timer line at end of each phase)
    # Phase skip:     [~] Phase 9 skip — ...
    # ─────────────────────────────────────────────────────────────────
    _PHASE_HEADER_MAP = {
        # (substring in upper-case line) → phase key
        "SUBDOMAIN ENUM":       "enum",
        "RECURSIVE BRUTE":      "recursive",
        "PORT SCAN":            "probe",
        "PORT-WISE PROB":       "probe",
        "HISTORICAL URL":       "history",
        "NUCLEI SCAN":          "scan",
        "JS SECRET":            "js",
        "DATA MINING":          "mine",
        "CLOUD ASSET":          "cloud",
        "GITHUB DORK":          "github",
        "TAKEOVER":             "takeover",
        "ASN":                  "asn",
        "WAYBACK JS":           "jsdiff",
        "JS DIFF":              "jsdiff",
    }
    # Phase number → key (fallback if keyword not matched)
    _PHASE_NUM_MAP = {
        "1": "enum", "1B": "recursive",
        "2": "probe", "3": "history",
        "4": "scan",  "5": "js",
        "6": "mine",  "7": "cloud",
        "8": "github","9": "takeover",
        "10": "asn",  "11": "jsdiff",
    }
    # Skip line: "[~] Phase 9 skip"
    _PHASE_SKIP_NUM = {
        "9": "takeover", "4": "scan", "5": "js",
        "6": "mine",     "2": "probe","3": "history",
    }

    def _detect_phase_change(self, line):
        """Detect phase transitions from ghost_protocol_v11 actual output."""
        import re
        stripped = line.strip()
        up = stripped.upper()

        # ── Phase header line: ── PHASE N[b]: TITLE ── ────────────
        if "PHASE" in up and ("──" in stripped or "─" in stripped):
            # Try keyword match first (most reliable)
            matched = None
            for keyword, phase_key in self._PHASE_HEADER_MAP.items():
                if keyword in up:
                    matched = phase_key
                    break
            # Fallback: extract phase number
            if not matched:
                m = re.search(r'PHASE\s+(\d+[Bb]?)', up)
                if m:
                    matched = self._PHASE_NUM_MAP.get(m.group(1).upper())

            if matched:
                # Close previous running phase
                if self._current_phase and self._current_phase != matched:
                    if self.phase_states.get(self._current_phase) == ST_RUNNING:
                        self._set_phase_status(self._current_phase, ST_DONE)
                self._set_phase_status(matched, ST_RUNNING)
            return

        # ── Phase done: ⏱  Xs at end of a phase ──────────────────
        if stripped.startswith("⏱") and self._current_phase:
            # Extract elapsed from "⏱  3.1s"
            m = re.search(r'([\d.]+)s', stripped)
            elapsed = float(m.group(1)) if m else None
            phase = self._current_phase
            if self.phase_states.get(phase) == ST_RUNNING:
                card = self.phase_cards.get(phase)
                self.phase_states[phase] = ST_DONE
                if card:
                    self.root.after(0, card.set_status, ST_DONE, elapsed)
                self._current_phase = None
            return

        # ── Skip line: [~] Phase N skip ───────────────────────────
        if "[~]" in stripped and "skip" in stripped.lower():
            m = re.search(r'[Pp]hase\s+(\d+)', stripped)
            if m:
                phase = self._PHASE_SKIP_NUM.get(m.group(1))
                if phase:
                    self._set_phase_status(phase, ST_SKIP)
            return

        # ── Error line ─────────────────────────────────────────────
        if any(k in stripped for k in ("[!]", "ERROR", "CRITICAL")):
            if self._current_phase:
                if "phase" in stripped.lower() or "scan" in stripped.lower():
                    self._set_phase_status(self._current_phase, ST_ERROR)

    def _set_phase_status(self, phase, state):
        if phase not in self.phase_cards:
            return
        card = self.phase_cards[phase]
        if state == ST_RUNNING:
            card.start_timer()
            self._current_phase = phase
            # Mark previous phases done
            idx = PHASES.index(phase)
            for p in PHASES[:idx]:
                if self.phase_states[p] == ST_RUNNING:
                    self._set_phase_status(p, ST_DONE)
        elapsed = card.get_elapsed() if state in (ST_DONE, ST_ERROR) else None
        self.phase_states[phase] = state
        self.root.after(0, card.set_status, state, elapsed)

    def _reset_phase_states(self):
        for phase in PHASES:
            self.phase_states[phase] = ST_IDLE
            if phase in self.phase_cards:
                self.phase_cards[phase].set_status(ST_IDLE)
                self.phase_cards[phase]._start_time = None

    def _mark_selected_phases_idle(self):
        for phase, var in self.phase_vars.items():
            if not var.get():
                self._set_phase_status(phase, ST_SKIP)

    # ─────────────────────────────────────────────────────────────
    # SUMMARY STATS
    # ─────────────────────────────────────────────────────────────

    def _update_summary(self, line):
        """
        Parse both live output lines AND final SUMMARY block.

        Live patterns (during scan):
          Resolved: 0 (-0 wildcards/dead)
          200 OK:         0           ← multiple spaces
          Cloud assets found: 1
          GitHub findings:  183       ← extra space
          *** Secrets matched: 38 files ***

        Final SUMMARY block (space-separated columns):
          Subdomains (resolved)        0
          200 OK                       0
          Vulns (nuclei)               0
          JS Secrets                   0
          GitHub leaks (files)         884
          Cloud assets                 1
          Takeover candidates          0
        """
        import re

        def _n(s):
            """Extract first integer from string, return as str."""
            m = re.search(r'\d+', s)
            return m.group(0) if m else None

        def _post(key, val_str, color_pos, color_zero=None):
            n = _n(val_str)
            if n is None:
                return
            color = color_pos if int(n) > 0 else (color_zero or C["text3"])
            self.root.after(0, self._set_stat, key, n, color)

        try:
            s = line.strip()

            # ── Live: Resolved ────────────────────────────────────
            if s.startswith("Resolved:"):
                _post("subs", s.split("Resolved:")[1], C["cyan"])

            # ── Live: 200 OK:   N ─────────────────────────────────
            elif re.match(r'200 OK:\s+\d', s):
                _post("live", re.split(r'200 OK:\s+', s)[1], C["green"])

            # ── Live: Cloud assets found ──────────────────────────
            elif "Cloud assets found:" in s:
                _post("cloud", s.split("Cloud assets found:")[1], C["teal"])

            # ── Live: GitHub findings ─────────────────────────────
            elif re.match(r'\s*GitHub findings:', line):
                _post("gh", re.split(r'GitHub findings:\s*', s)[1], C["purple"])

            # ── Live: Secrets matched ─────────────────────────────
            elif "Secrets matched:" in s:
                _post("secrets", s.split("Secrets matched:")[1], C["orange"])

            # ── Live: Takeover candidates ─────────────────────────
            elif "Takeover candidates:" in s:
                _post("takeover", s.split("Takeover candidates:")[1], C["orange"])

            # ── Final SUMMARY block lines (2+ spaces between key/val)
            elif re.search(r'\s{2,}\d+\s*$', s):
                val = s.split()[-1]
                su = s.upper()

                if "SUBDOMAINS (RESOLVED)" in su or "SUBDOMAINS (TOTAL)" in su:
                    _post("subs",     val, C["cyan"])
                elif re.match(r'200 OK\s*$', s.split()[-2] if len(s.split()) >= 2 else ""):
                    _post("live",     val, C["green"])
                elif "200 OK" in su and len(s.split()) <= 4:
                    _post("live",     val, C["green"])
                elif "VULNS (NUCLEI)" in su:
                    _post("vulns",    val, C["red"])
                elif "JS SECRETS" in su:
                    _post("js",       val, C["yellow"])
                elif "GITHUB LEAKS" in su or "GITHUB FINDINGS" in su:
                    _post("gh",       val, C["purple"])
                elif "CLOUD ASSETS" in su:
                    _post("cloud",    val, C["teal"])
                elif "TAKEOVER CANDIDATES" in su:
                    _post("takeover", val, C["orange"])
                elif "LIVE HOSTS" in su or ("LIVE" in su and "200" in su):
                    _post("live",     val, C["green"])

        except Exception:
            pass

    def _set_stat(self, key, value, color):
        if key in self.stat_labels:
            lbl, _ = self.stat_labels[key]
            lbl.config(text=str(value), fg=color)
            # Quick flash animation
            def flash(n=0):
                if n < 4:
                    lbl.config(fg=C["text"] if n % 2 == 0 else color)
                    self.root.after(80, flash, n + 1)
                else:
                    lbl.config(fg=color)
            flash()

    def _reset_stats(self):
        for key, (lbl, color) in self.stat_labels.items():
            lbl.config(text="—", fg=color)

    # ─────────────────────────────────────────────────────────────
    # SCAN CONTROL
    # ─────────────────────────────────────────────────────────────

    def _build_command(self):
        script  = self.script_path.get()
        targets = self.targets_file.get()

        if not script or not os.path.exists(script):
            messagebox.showerror("Error",
                "ghost_protocol_v11.py nahi mila — path check karo")
            return None
        if not targets or not os.path.exists(targets):
            messagebox.showerror("Error", "Targets file select karo pehle")
            return None

        selected = [p for p, v in self.phase_vars.items() if v.get()]
        if not selected:
            messagebox.showerror("Error", "Kam se kam ek phase select karo")
            return None

        cmd = [sys.executable, script, targets,
               "--phases", ",".join(selected)]

        if self.scope_file.get():   cmd += ["--scope",      self.scope_file.get()]
        if self.output_dir.get():   cmd += ["--output-dir", self.output_dir.get()]
        if self.dry_run.get():      cmd.append("--dry-run")
        if self.passive_mode.get(): cmd.append("--passive")
        if self.force_mode.get():   cmd.append("--force")
        if self.skip_nuclei.get(): cmd.append("--skip-nuclei-update")

        return cmd

    def _start_scan(self):
        cmd = self._build_command()
        if not cmd:
            return

        self.running = True
        self._last_cmd = " ".join(cmd)
        self._reset_stats()
        self._reset_phase_states()
        self._mark_selected_phases_idle()
        self._clear_log()

        self._set_status("RUNNING", C["yellow"])
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._start_progress()
        self._start_elapsed()

        short_cmd = self._last_cmd[:100] + ("…" if len(self._last_cmd) > 100 else "")
        self.cmd_label.config(text=short_cmd)

        ts = datetime.now().strftime("%H:%M:%S")
        self._log(f"[{ts}] Scan started\n", "dim")
        self._log(f"CMD: {self._last_cmd}\n\n", "dim")

        thread = threading.Thread(target=self._run_process, args=(cmd,), daemon=True)
        thread.start()

    def _run_process(self, cmd):
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                encoding="utf-8", errors="replace",
            )
            for line in self.process.stdout:
                if not self.running:
                    break
                self.root.after(0, self._append_log, line)

            self.process.wait()
            rc = self.process.returncode
            self.root.after(0, self._scan_done, rc)
        except Exception as e:
            self.root.after(0, self._log, f"\n[ERROR] {e}\n", "red")
            self.root.after(0, self._scan_done, -1)

    def _stop_scan(self):
        self.running = False
        if self.process:
            try: self.process.terminate()
            except Exception: pass
        self._scan_done(None)
        self._log("\n[STOPPED by user]\n", "yellow")

    def _scan_done(self, returncode):
        self.running = False
        self._stop_progress()
        self._stop_elapsed()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

        # Mark any still-running phases as done/error
        for phase, state in self.phase_states.items():
            if state == ST_RUNNING:
                self._set_phase_status(phase,
                    ST_DONE if returncode == 0 else ST_ERROR)

        if returncode == 0:
            self._set_status("DONE ✓", C["green"])
            self._log("\n[✔] Scan complete!\n", "green")
            ToastNotification(self.root, "✔ Scan complete!", C["green"])
        elif returncode is None:
            self._set_status("STOPPED", C["yellow"])
        else:
            self._set_status(f"ERROR ({returncode})", C["red"])
            ToastNotification(self.root, f"✗ Scan failed (rc={returncode})", C["red"])

    # ─────────────────────────────────────────────────────────────
    # PROGRESS + TIMER
    # ─────────────────────────────────────────────────────────────

    def _start_progress(self):
        self._progress_pos = 0
        self._progress_dir = 1
        self._animate_progress()

    def _animate_progress(self):
        if not self.running:
            return
        W = 220
        bar_w = 50
        self._progress_pos += self._progress_dir * 3
        if self._progress_pos + bar_w >= W:
            self._progress_dir = -1
        if self._progress_pos <= 0:
            self._progress_dir = 1
        self.progress_canvas.coords(
            self._progress_rect,
            self._progress_pos, 0,
            self._progress_pos + bar_w, 6,
        )
        self._progress_after = self.root.after(20, self._animate_progress)

    def _stop_progress(self):
        if self._progress_after:
            self.root.after_cancel(self._progress_after)
        self.progress_canvas.coords(self._progress_rect, 0, 0, 0, 6)

    def _start_elapsed(self):
        self._elapsed_start = time.time()
        self._tick_elapsed()

    def _tick_elapsed(self):
        if not self.running:
            return
        elapsed = int(time.time() - self._elapsed_start)
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60
        self.timer_lbl.config(text=f"{h:02d}:{m:02d}:{s:02d}", fg=C["text2"])
        self._elapsed_after = self.root.after(1000, self._tick_elapsed)

    def _stop_elapsed(self):
        if self._elapsed_after:
            self.root.after_cancel(self._elapsed_after)

    # ─────────────────────────────────────────────────────────────
    # MISC
    # ─────────────────────────────────────────────────────────────

    def _set_status(self, text, color):
        self.status_dot.config(text=f"● {text}", fg=color)

    def _copy_command(self):
        if self._last_cmd:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._last_cmd)
            ToastNotification(self.root, "Command copied!", C["cyan"])

    def on_close(self):
        if self.running:
            self._stop_scan()
        self.root.destroy()


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.configure(bg=C["bg"])

    # Try to set icon
    try:
        root.iconbitmap(default="ghost.ico")
    except Exception:
        pass

    app = GhostProtocolGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
