#!/usr/bin/env python3
"""
sp_sharepoint_yt_dlp_gui.py
---------------------------
Dual-mode (CLI or GUI) downloader for Microsoft Stream (on SharePoint) / SharePoint video URLs using yt-dlp.

Features
- Start-up prompt: choose CLI or GUI.
- GUI with fields to paste the URL, select a cookies.txt file via a file manager (Netscape format), and an optional custom output file name.
- CLI flow that also pops a file manager to choose the cookies file (with a manual fallback).
- Heuristics to convert "videotranscode/mediasegment" links into a clean "videomanifest" DASH index URL (provider+docId preserved).
- Progress bar/status updates in GUI and clear logging in CLI.
- Outputs MP4 when merging is possible (requires ffmpeg installed and on PATH).

Notes
- If your link looks like a single segment (contains part=mediasegment/segmentTime), grab the real videomanifest from DevTools -> Network if auto-conversion fails.
- This script will not bypass DRM.

Requirements
- Python 3.9+
- pip install yt-dlp
- ffmpeg installed and on PATH (yt-dlp uses it for merging/fragment downloads)
"""

import os
import sys
import time
import shutil
import threading
import logging
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

# Third-party
try:
    import yt_dlp as ytdlp
except Exception as e:
    print("[ERROR] yt-dlp is not installed. Run: pip install yt-dlp", file=sys.stderr)
    raise

# GUI imports (lazy so CLI works on headless systems)
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

def which_ffmpeg():
    return shutil.which("ffmpeg")

def clean_to_videomanifest(url: str):
    """
    Heuristically convert a SharePoint 'videotranscode/mediasegment' URL to a 'videomanifest' DASH index URL.
    Return (new_url, changed, reason)
    """
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path
        q_pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))

        # Convert svc.ms/transform/videotranscode -> /transform/videomanifest
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
            new_q = {
                "provider": provider,
                "docId": docid,
                "format": "dash",
                "part": "index"
            }
            new_path = "/transform/videomanifest"
            new_url = urlunparse((parsed.scheme, parsed.netloc, new_path, "", urlencode(new_q), ""))
            return (new_url, True, "Converted mediasegment URL to videomanifest (DASH index).")

        # Already a videomanifest -> trim extra query args; enforce format=dash&part=index
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
        # If no extension, let yt-dlp choose ext
        if "." not in os.path.basename(name):
            return name + ".%(ext)s"
        return name
    return "%(title).150B [%(id)s].%(ext)s"

def run_yt_dlp(url: str, cookiefile: str | None, custom_name: str | None, log_cb=None, prog_cb=None):
    """
    Run yt-dlp with optional cookie file and custom output name.
    log_cb: function(str) -> None for logs.
    prog_cb: function(percent, speed, eta) -> None for progress updates.
    """
    logger = YTDLogger(log_cb)

    def hook(d):
        if prog_cb is None:
            return
        try:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                percent = (downloaded / total * 100.0) if total else 0.0
                speed = d.get("speed")  # bytes/s
                eta = d.get("eta")  # seconds
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
        "noprogress": True,   # we handle progress via hook
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

    # Clean mediasegment URLs if needed
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
        self.title("SharePoint / Stream (on SharePoint) Downloader")
        self.geometry("720x480")
        self.minsize(640, 420)

        self.url_var = tk.StringVar()
        self.cookies_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Idle")
        self.percent_var = tk.DoubleVar(value=0.0)

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 8}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # URL
        ttk.Label(frm, text="Video URL (videomanifest preferred):").grid(row=0, column=0, sticky="w", **pad)
        url_entry = ttk.Entry(frm, textvariable=self.url_var)
        url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", **pad)

        # Cookies
        ttk.Label(frm, text="Cookies file (Netscape format, optional):").grid(row=2, column=0, sticky="w", **pad)
        cookies_entry = ttk.Entry(frm, textvariable=self.cookies_var)
        cookies_entry.grid(row=3, column=0, columnspan=2, sticky="ew", **pad)
        ttk.Button(frm, text="Browse...", command=self._browse_cookies).grid(row=3, column=2, sticky="ew", **pad)

        # Custom name
        ttk.Label(frm, text="Custom output name (optional, no ext to auto-pick):").grid(row=4, column=0, sticky="w", **pad)
        name_entry = ttk.Entry(frm, textvariable=self.name_var)
        name_entry.grid(row=5, column=0, columnspan=3, sticky="ew", **pad)

        # Progress
        self.pbar = ttk.Progressbar(frm, orient="horizontal", mode="determinate", variable=self.percent_var, maximum=100.0)
        self.pbar.grid(row=6, column=0, columnspan=3, sticky="ew", **pad)

        self.status_label = ttk.Label(frm, textvariable=self.status_var)
        self.status_label.grid(row=7, column=0, columnspan=3, sticky="w", **pad)

        # Log box
        self.log = tk.Text(frm, height=10, wrap="word")
        self.log.grid(row=8, column=0, columnspan=3, sticky="nsew", **pad)
        self.log.configure(state="disabled")

        # Buttons
        btn_row = ttk.Frame(frm)
        btn_row.grid(row=9, column=0, columnspan=3, sticky="ew", **pad)
        ttk.Button(btn_row, text="Download", command=self._start_download_thread).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Quit", command=self.destroy).pack(side="right", padx=6)

        # grid weights
        frm.columnconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(2, weight=0)
        frm.rowconfigure(8, weight=1)

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
    """
    Try to open a file manager dialog for cookies.txt.
    If Tkinter isn't available (headless), fallback to manual input.
    """
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
    # fallback
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
