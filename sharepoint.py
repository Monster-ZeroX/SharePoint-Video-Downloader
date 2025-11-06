#!/usr/bin/env python3
"""
sharepoint.py
---------------------------
Dual-mode (CLI or GUI) downloader for Microsoft Stream (on SharePoint) / SharePoint video URLs using yt-dlp.

- Polished GUI with header, accent color, and logo
- Browse to select cookies file (Netscape cookies.txt)
- Optional custom output name
- Auto-fixes common mediasegment URLs to videomanifest when possible
"""

import os
import sys
import time
import shutil
import threading
import logging
import base64
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

# Third-party
try:
    import yt_dlp as ytdlp
except Exception as e:
    print("[ERROR] yt-dlp is not installed. Run: pip install yt-dlp", file=sys.stderr)
    raise

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception:
    tk = None
    ttk = None
    filedialog = None
    messagebox = None

LOG = logging.getLogger("sp_yt_dlp_gui")
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

# Embedded PNG logo (base64). Not the official MS SharePoint logo; just a friendly S icon.
LOGO_PNG_B64 = "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"

ACCENT = "#036C70"   # teal
BG_DARK = "#02484B"  # darker teal
BG = "#F7FAFB"       # light background
FG = "#0B2F2F"       # dark text

def which_ffmpeg():
    return shutil.which("ffmpeg")

def clean_to_videomanifest(url: str):
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path
        q_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))

        if ".svc.ms" in host and "transform" in path:
            provider = None
            docid = None
            for k, v in list(q_pairs.items()):
                kl = k.lower()
                if kl == "provider":
                    provider = v
                elif kl == "docid":
                    docid = v
            if not provider or not docid:
                return (url, False, "Missing provider/docId; cannot auto-build a manifest. Capture videomanifest via DevTools.")
            new_q = {"provider": provider, "docId": docid, "format": "dash", "part": "index"}
            new_path = "/transform/videomanifest"
            new_url = urlunparse((parsed.scheme, parsed.netloc, new_path, "", urlencode(new_q), ""))
            return (new_url, True, "Converted mediasegment URL to videomanifest (DASH index).")

        if "videomanifest" in path:
            keep = {}
            for k, v in parse_qsl(parsed.query, keep_blank_values=True):
                kl = k.lower()
                if kl in ("provider", "docid", "format", "part"):
                    keep[k] = v
            if keep.get("format", "").lower() != "dash":
                keep["format"] = "dash"
            if "part" not in keep:
                keep["part"] = "index"
            new_url = urlunparse((parsed.scheme, parsed.netloc, path, "", urlencode(keep), ""))
            if new_url != url:
                return (new_url, True, "Trimmed manifest params and enforced format=dash, part=index.")
            return (url, False, "URL already looks like a usable videomanifest.")
        return (url, False, "Non-mediap pipeline URL; using as-is.")
    except Exception as e:
        return (url, False, "Manifest cleanup skipped: %s" % e)

class YTDLogger:
    def __init__(self, log_func=None):
        self.log_func = log_func or (lambda s: print(s, flush=True))

    def debug(self, msg):
        if isinstance(msg, bytes):
            msg = msg.decode("utf-8", "ignore")
        self.log_func(str(msg))

    def info(self, msg):
        self.debug(msg)

    def warning(self, msg):
        self.debug("[WARN] " + str(msg))

    def error(self, msg):
        self.debug("[ERROR] " + str(msg))

def make_outtmpl(custom_name: str | None):
    if custom_name:
        name = custom_name.strip()
        if not name:
            return "%(title).150B [%(id)s].%(ext)s"
        if "." not in os.path.basename(name):
            return name + ".%(ext)s"
        return name
    return "%(title).150B [%(id)s].%(ext)s"

def run_yt_dlp(url: str, cookiefile: str | None, custom_name: str | None, log_cb=None, prog_cb=None):
    logger = YTDLogger(log_cb)

    def hook(d):
        if prog_cb is None:
            return
        try:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                percent = (downloaded / total * 100.0) if total else 0.0
                speed = d.get("speed")
                eta = d.get("eta")
                prog_cb(percent, speed, eta)
            elif d.get("status") == "finished":
                prog_cb(100.0, None, 0)
        except Exception:
            pass

    ffmpeg = which_ffmpeg()
    ydl_opts = {
        "outtmpl": make_outtmpl(custom_name),
        "merge_output_format": "mp4",
        "concurrent_fragment_downloads": 8,
        "noprogress": True,
        "quiet": True,
        "logger": logger,
        "progress_hooks": [hook],
        "retries": 10,
        "fragment_retries": 10,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        },
    }
    if ffmpeg:
        ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg)
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile

    fixed_url, changed, reason = clean_to_videomanifest(url)
    if log_cb:
        log_cb("[INFO] " + reason)
        if changed:
            log_cb("[INFO] Using manifest: " + fixed_url)

    with ytdlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(fixed_url, download=True)
        outfile = None
        if info and isinstance(info, dict):
            rd = info.get("requested_downloads")
            if rd:
                outfile = rd[0].get("filepath")
        return outfile

# ---------------------- GUI ----------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SharePoint Video Downloader")
        self.configure(bg=BG)
        # Apply a modern-ish ttk theme if available
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Colors
        style.configure("Header.TFrame", background=ACCENT)
        style.configure("Header.TLabel", background=ACCENT, foreground="white", font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", background=ACCENT, foreground="#E6F2F2", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="white")
        style.configure("TLabel", background="white", foreground=FG, font=("Segoe UI", 10))
        style.configure("TEntry", padding=6)
        style.configure("Accent.TButton", foreground="white")
        style.map("Accent.TButton", background=[("!disabled", ACCENT), ("pressed", BG_DARK), ("active", "#05838A")], foreground=[("pressed","white"),("active","white")])
        style.configure("TButton", padding=6)

        self.url_var = tk.StringVar()
        self.cookies_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Idle")
        self.percent_var = tk.DoubleVar(value=0.0)

        self._logo_img = None
        self._build_ui()

    def _build_ui(self):
        padx, pady = 16, 12

        # Header
        header = ttk.Frame(self, style="Header.TFrame")
        header.pack(fill="x")
        # logo
        try:
            data = base64.b64decode(LOGO_PNG_B64)
            self._logo_img = tk.PhotoImage(data=data)
            logo_lbl = tk.Label(header, image=self._logo_img, bg=ACCENT)
            logo_lbl.pack(side="left", padx=16, pady=10)
        except Exception:
            tk.Label(header, text=" ", bg=ACCENT).pack(side="left", padx=16, pady=10)

        title_box = tk.Frame(header, bg=ACCENT)
        title_box.pack(side="left", padx=4, pady=10)
        ttk.Label(title_box, text="SharePoint / Stream Downloader", style="Header.TLabel").pack(anchor="w")
        ttk.Label(title_box, text="Powered by yt-dlp. Paste your URL, pick cookies, click Download.", style="SubHeader.TLabel").pack(anchor="w")

        # Card
        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=padx, pady=pady)

        # URL
        ttk.Label(card, text="Video URL (videomanifest preferred):").grid(row=0, column=0, sticky="w", padx=12, pady=(16, 4))
        url_entry = ttk.Entry(card, textvariable=self.url_var, width=10)
        url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=4)

        # Cookies
        ttk.Label(card, text="Cookies file (Netscape format, optional):").grid(row=2, column=0, sticky="w", padx=12, pady=(12, 4))
        cookies_entry = ttk.Entry(card, textvariable=self.cookies_var)
        cookies_entry.grid(row=3, column=0, sticky="ew", padx=12, pady=4)
        ttk.Button(card, text="Browse...", command=self._browse_cookies).grid(row=3, column=1, sticky="e", padx=12, pady=4)

        # Custom name
        ttk.Label(card, text="Custom output name (optional, no ext to auto-pick):").grid(row=4, column=0, sticky="w", padx=12, pady=(12, 4))
        name_entry = ttk.Entry(card, textvariable=self.name_var)
        name_entry.grid(row=5, column=0, columnspan=2, sticky="ew", padx=12, pady=4)

        # Progress + status
        self.pbar = ttk.Progressbar(card, orient="horizontal", mode="determinate", variable=self.percent_var, maximum=100.0)
        self.pbar.grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=(16, 4))

        self.status_label = tk.Label(card, textvariable=self.status_var, anchor="w", bg="white", fg=FG)
        self.status_label.grid(row=7, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))

        # Log box
        self.log = tk.Text(card, height=10, wrap="word", bg="#FAFEFF", fg="#1A2B2B", bd=0, highlightthickness=1, highlightbackground="#E2EBEE")
        self.log.grid(row=8, column=0, columnspan=2, sticky="nsew", padx=12, pady=(6, 12))
        self.log.configure(state="disabled")

        # Buttons row
        btn_row = tk.Frame(card, bg="white")
        btn_row.grid(row=9, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 16))
        ttk.Button(btn_row, text="Download", style="Accent.TButton", command=self._start_download_thread).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Quit", command=self.destroy).pack(side="left")

        # Grid weights for card
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)
        card.rowconfigure(8, weight=1)

        # Window min size
        self.minsize(720, 520)

    def _browse_cookies(self):
        try:
            path = filedialog.askopenfilename(
                title="Select cookies file (Netscape/Mozilla format)",
                filetypes=[("Cookies/Text", "*.txt;*.*"), ("All files", "*.*")],
            )
            if path:
                self.cookies_var.set(path)
        except Exception as e:
            messagebox.showwarning("File dialog error", str(e))

    def _append_log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_status(self, text):
        self.status_var.set(text)

    def _progress_cb(self, percent, speed, eta):
        def fmt_speed(s):
            if not s:
                return ""
            units = ["B/s","KB/s","MB/s","GB/s"]
            v = float(s)
            i = 0
            while v >= 1024.0 and i < len(units)-1:
                v /= 1024.0
                i += 1
            return f"{v:.1f} {units[i]}"
        def fmt_eta(e):
            if e is None:
                return ""
            m, s = divmod(int(e), 60)
            h, m = divmod(m, 60)
            if h: return f"{h}h {m}m {s}s"
            if m: return f"{m}m {s}s"
            return f"{s}s"

        self.after(0, lambda: (
            self.percent_var.set(percent),
            self._set_status(f"Downloading... {percent:5.1f}%  {fmt_speed(speed)}  ETA {fmt_eta(eta)}")
        ))

    def _log_cb(self, msg):
        self.after(0, lambda: self._append_log(str(msg)))

    def _start_download_thread(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Missing URL", "Please paste a SharePoint/Stream video URL.")
            return
        cookiefile = self.cookies_var.get().strip() or None
        custom_name = self.name_var.get().strip() or None
        self.percent_var.set(0.0)
        self._set_status("Starting...")
        self._append_log(f"URL: {url}")
        if cookiefile:
            self._append_log(f"Using cookies: {cookiefile}")

        t = threading.Thread(
            target=self._download_job,
            args=(url, cookiefile, custom_name),
            daemon=True
        )
        t.start()

    def _download_job(self, url, cookiefile, custom_name):
        try:
            outfile = run_yt_dlp(url, cookiefile, custom_name, log_cb=self._log_cb, prog_cb=self._progress_cb)
            self.after(0, lambda: self._set_status("Done."))
            self.after(0, lambda: self._append_log("[OK] Finished. File may be in current directory."))
            if outfile:
                self.after(0, lambda: self._append_log(f"[OK] Saved: {outfile}"))
        except ytdlp.utils.DownloadError as e:
            self.after(0, lambda: self._set_status("Error."))
            self.after(0, lambda: messagebox.showerror("yt-dlp error", str(e)))
        except Exception as e:
            self.after(0, lambda: self._set_status("Error."))
            self.after(0, lambda: messagebox.showerror("Unexpected error", str(e)))

# ---------------------- CLI ----------------------

def pick_cookies_cli():
    if filedialog is not None and tk is not None:
        try:
            root = tk.Tk()
            root.withdraw()
            root.lift()
            root.attributes("-topmost", True)
            root.after(200, lambda: root.attributes("-topmost", False))
            path = filedialog.askopenfilename(
                title="Select cookies file (Netscape/Mozilla format)",
                filetypes=[("Cookies/Text", "*.txt;*.*"), ("All files", "*.*")],
            )
            root.destroy()
            if path:
                print(f"[INFO] Selected cookies file: {path}")
                return path
        except Exception as e:
            print(f"[WARN] File dialog failed: {e}")
    path = input("Enter path to cookies file (or leave blank to skip): ").strip()
    return path or None

def cli_flow():
    print("=== SharePoint / Stream (on SharePoint) downloader (yt-dlp) ===")
    url = ""
    while not url:
        url = input("Video URL: ").strip().strip('"').strip("'")

    use_cookies = input("Use cookies file? [y/N]: ").strip().lower() == "y"
    cookiefile = None
    if use_cookies:
        cookiefile = pick_cookies_cli()

    custom_name = input("Custom output name (optional, no extension to auto-pick): ").strip() or None

    def log_cb(msg): print(msg)
    def prog_cb(p,s,e):
        bar = int(p/5)
        sys.stdout.write("\r[{}{}] {:5.1f}%".format("#"*bar, "-"*(20-bar), p))
        sys.stdout.flush()
        if p >= 100:
            print()

    try:
        outfile = run_yt_dlp(url, cookiefile, custom_name, log_cb=log_cb, prog_cb=prog_cb)
        print("\n[OK] Finished.")
        if outfile:
            print(f"Saved: {outfile}")
    except ytdlp.utils.DownloadError as e:
        print(f"\n[ERROR] yt-dlp failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[ABORTED] Interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)

# ---------------------- Entry ----------------------

def main():
    print("Choose mode:\n  1 - CLI\n  2 - GUI")
    mode = input("Enter 1 or 2: ").strip()
    if mode == "2":
        if tk is None:
            print("[ERROR] Tkinter is not available in this environment. Falling back to CLI.")
            cli_flow()
            return
        app = App()
        app.mainloop()
    else:
        cli_flow()

if __name__ == "__main__":
    main()

