# SharePoint / Stream (on SharePoint) Video Downloader

A dual‑mode (**CLI** or **GUI**) Python tool that downloads Microsoft Stream (on SharePoint) / SharePoint videos using **yt-dlp**.  
It supports cookies (Netscape `cookies.txt`) and includes heuristics to turn single media segment URLs into a proper `videomanifest` DASH URL.

> **Important:** Download videos only if you have the rights and permission to do so. Some org streams are DRM protected; this project will **not** bypass DRM.

---

## Features

- **Two modes at startup:** `1 - CLI` or `2 - GUI` (Tkinter)
- **GUI**: paste the URL, select a cookies file via **File Manager**, and optionally set a custom output name
- **CLI**: prompts you for URL, opens a **file manager** dialog to select cookies (with text fallback)
- **Auto‑manifest cleanup**: converts `videotranscode ... part=mediasegment` links to a clean `videomanifest` (DASH, `part=index`) when possible
- **yt-dlp** integration: robust fragment downloading and merging (to MP4 when possible)
- **Logging + progress**: visible progress in CLI and progress bar + log panel in GUI
- Cross‑platform: Windows, macOS, Linux (GUI requires Tkinter; see notes below)

---

 **New! Windows users (no Python needed):**
>
> **Download the prebuilt `.exe` from the Releases page**, unzip, and double‑click
> **`SharePointVideoDownloader.exe`**. The app opens directly in **GUI** mode.
>
> **How to use the EXE:**
> 1. Paste your SharePoint/Stream **video URL**.
> 2. *(Optional)* Click **Browse…** and select your **`cookies.txt`** (Netscape format) if your video needs authentication.
> 3. *(Optional)* Enter a **custom file name** (leave blank to use the video title).
> 4. Click **Download**. A bundled **`ffmpeg.exe`** is included in the release; if it’s missing,
>    place `ffmpeg.exe` in the same folder as the `.exe`.
>
> If Windows SmartScreen warns you, click **More info → Run anyway** (or build/sign it yourself).
>
> ---


A dual‑mode (**CLI** or **GUI**) Python tool that downloads Microsoft Stream (on SharePoint) / SharePoint videos using **yt-dlp**.  
It supports cookies (Netscape `cookies.txt`) and includes heuristics to turn single media segment URLs into a proper `videomanifest` DASH URL.

> **Important:** Download videos only if you have the rights and permission to do so. Some org streams are DRM protected; this project will **not** bypass DRM.

---

## Features

- **Two modes at startup:** `1 - CLI` or `2 - GUI` (Tkinter)
- **GUI**: paste the URL, select a cookies file via **File Manager**, and optionally set a custom output name
- **CLI**: prompts you for URL, opens a **file manager** dialog to select cookies (with text fallback)
- **Auto‑manifest cleanup**: converts `videotranscode ... part=mediasegment` links to a clean `videomanifest` (DASH, `part=index`) when possible
- **yt-dlp** integration: robust fragment downloading and merging (to MP4 when possible)
- **Logging + progress**: visible progress in CLI and progress bar + log panel in GUI
- Cross‑platform: Windows, macOS, Linux (GUI requires Tkinter; see notes below)

---

## Project Layout

```
sharepoint.py                 # Dual-mode entry (CLI/GUI)
requirements.txt              # Pip requirements
```

---

## Prerequisites

- **Python 3.9+**
- **pip** for installing Python packages
- **ffmpeg** installed and on PATH (yt-dlp uses it to merge media)
- For **GUI** on Linux: system Tk bindings (e.g., `python3-tk`)

### Install Python and pip

- Windows: Install from https://www.python.org/ (check "Add Python to PATH" during setup).
- macOS: Use the official installer or a package manager (e.g., Homebrew).
- Linux: Use your distro packages (e.g., `sudo apt-get install python3 python3-pip`).

### Install ffmpeg

#### Windows (several options)

**Option A: winget (recommended on Win10/11):**
```powershell
winget install --id=FFmpeg.FFmpeg -e
```
> If that ID does not exist on your system, try: `winget search ffmpeg` to find the available package name.

**Option B: Chocolatey:**
```powershell
choco install ffmpeg
```
> If Chocolatey is not installed, see https://chocolatey.org/install

**Option C: Manual download:**
1. Download a static build of ffmpeg (zip).
2. Extract it, e.g., `C:\ffmpeg\bin\ffmpeg.exe`.
3. Add the `bin` folder to your **PATH** environment variable.

Verify:
```powershell
ffmpeg -version
```

#### Linux

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Fedora:**
```bash
sudo dnf install ffmpeg
```
> On some Fedora setups you may need to enable RPM Fusion repositories.

**Arch/Manjaro:**
```bash
sudo pacman -S ffmpeg
```

Verify:
```bash
ffmpeg -version
```

#### macOS

With Homebrew:
```bash
brew install ffmpeg
```

Verify:
```bash
ffmpeg -version
```

### (Linux) Tkinter for GUI

If the GUI complains that Tk/Tkinter is missing, install it:

- **Debian/Ubuntu:**
  ```bash
  sudo apt install python3-tk
  ```
- **Fedora:**
  ```bash
  sudo dnf install python3-tkinter
  ```
- **Arch:**
  ```bash
  sudo pacman -S tk
  ```

---

## Installation (Python deps)

Clone your repo and install requirements:

```bash
# From your project directory
pip install -r requirements.txt
```

This installs:
- `yt-dlp`

> `ffmpeg` is **not** a Python package; install it using OS-specific steps above.

---

## Usage

### Start the tool (dual-mode)

```bash
python sharepoint.py
```

You will be prompted:

```
Choose mode:
  1 - CLI
  2 - GUI
```

Pick **2** for the GUI or **1** for CLI.

---

### GUI mode

1. **Video URL**: Paste your SharePoint/Stream URL.\ 

   **First, paste your SharePoint link into the app. If it doesn’t work, try this:**
    
   - Ideally paste the **videomanifest** URL copied from DevTools → Network (filter for `videomanifest`).  
   - If you paste a `videotranscode ... part=mediasegment` link, the app will attempt to convert it automatically to a `videomanifest` (DASH) index URL.

3. **Cookies file (optional)**: Click **Browse...** to open a File Manager and pick your `cookies.txt` file (Netscape format).  
   - If you need cookies, export with a browser extension (e.g., a [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc?pli=1) exporter).

4. **Custom output name (optional)**: Provide a filename (without extension to auto-pick). Leave blank to use the original video title.

5. Click **Download**. Progress will appear in the bar; logs show details. When done, the final path is printed in the log.

**Notes on cookies**:
- Many SharePoint/Teams/Stream pages require authenticated access. Supplying a **fresh** cookies file is often the difference between success and a `403` error.
- Your organization policies may prevent downloads or apply DRM. This tool will not bypass DRM.

---

### CLI mode

```text
=== SharePoint / Stream (on SharePoint) downloader (yt-dlp) ===
Video URL: https://... (paste your link)
Use cookies file? [y/N]: y
# A file manager dialog opens to select cookies.txt (fallback: manual path entry)
Custom output name (optional, no extension to auto-pick): 
[##########----------] 50.0%
...
[OK] Finished.
```

- The CLI also tries to open a **file manager** to pick `cookies.txt`. If Tkinter is unavailable (headless), it falls back to a text prompt for the path.
- Output filename defaults to the source title: `%(title).150B [%(id)s].%(ext)s`. If you enter a custom name without extension, the extension is auto-selected.

---

## Where to find the right URL
**First, paste your SharePoint link into the app. If it doesn’t work, try this:**

- Open the video in your browser.
- Press **F12** → **Network** tab → reload the page.
- Filter by **`videomanifest`** and copy that URL.  
- If you only see `videotranscode ... part=mediasegment` URLs, grab the entry that looks like the **manifest/index** (often contains `videomanifest` and `format=dash`).

This tool will attempt to convert a `mediasegment` link to a `videomanifest` index using `provider` and `docId` query parameters, but the **original manifest** is the most reliable.

---

## Troubleshooting

- **HTTP 401/403**: Your cookies are invalid/expired, or you do not have permission. Export a **fresh** `cookies.txt` while logged in and try again.
- **"DRM protected"** or streams that refuse to download: Some org videos use DRM; this tool will not circumvent DRM.
- **"ffmpeg not found"**: Install ffmpeg and ensure it is on your PATH (see install section). Then verify with `ffmpeg -version`.
- **GUI does not open**: On Linux, install Tk (`python3-tk` / `tk`). In headless/server environments, use CLI mode.
- **Stuck at a segment URL**: Make sure you’re feeding a **videomanifest** URL. Use DevTools → Network to copy it.
- **Slow downloads**: Corporate networks or throttling can limit speed. Try again, use a wired connection, or run off-hours.

---

## Privacy & Legal

- This tool is for **personal/educational** use on videos you are authorized to access.
- Respect your organization’s policies. Do **not** distribute copyrighted or confidential content.
- The authors and contributors are **not** responsible for misuse.

---

## Development

- Lint/format (optional): `ruff`, `black`
- Build/test on Windows/macOS/Linux
- PRs welcome for:
  - Additional cookie flows (e.g., `--cookies-from-browser` integration in GUI)
  - Better manifest detection and error hints
  - Localization and accessibility

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)**.

- See the full license text in [LICENSE](LICENSE).
- When contributing code, you agree to license your contributions under GPL-3.0.
- If you distribute binaries, you must provide corresponding source or a written offer, per the GPL terms.

```text
SharePoint / Stream Downloader
Copyright (C) 2025 Monster-ZeroX

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

```
