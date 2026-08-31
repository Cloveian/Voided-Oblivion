#!/usr/bin/env python3
"""Run a local preview of the MkDocs site.

Same shape as the engineering-notebook preview script (auto-create venv,
install requirements, port fallback, auto-open browser, banner), with two
differences for this repo:

  * No nav generation. The nav in mkdocs.yml is a *reading path* - it encodes
    the order these decisions were actually made and which ones got reopened.
    That can't be derived from filenames, so it stays hand-written.

  * A link check runs before serving. These docs are dense with cross-links
    into specific headings, and renaming a heading during a rewrite breaks
    them silently. The report prints what's broken, then serves anyway - it
    never blocks the preview mid-edit.

No CLI args required.
"""

import os
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
VENV = ROOT / ".venv"
PYTHON = VENV / "bin" / "python"
MKDOCS = VENV / "bin" / "mkdocs"

ANCHOR_RE = re.compile(r"does not contain an anchor|there is no such anchor")


def find_free_port(start: int = 8001, end: int = 8020) -> int:
    """Return the first free TCP port on 127.0.0.1 in [start, end]."""
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No free port found in {start}-{end}")


def open_browser_later(url: str, delay: float = 2.0) -> None:
    def _open() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()


def check_links() -> None:
    """Build once and report broken cross-links. Never fatal."""
    print("Checking links...")
    result = subprocess.run(
        [str(MKDOCS), "build", "--site-dir", str(ROOT / "site")],
        capture_output=True,
        text=True,
    )
    lines = (result.stderr + result.stdout).splitlines()

    anchors = [ln.split("-", 1)[-1].strip() for ln in lines if ANCHOR_RE.search(ln)]
    warnings = [
        ln.split("-", 1)[-1].strip()
        for ln in lines
        if ln.startswith("WARNING") and not ANCHOR_RE.search(ln)
    ]

    if not anchors and not warnings:
        print("  all links resolve")
        return

    if anchors:
        print(f"\n  {len(anchors)} broken anchor(s) - a heading was renamed or removed:")
        for item in anchors:
            print(f"    - {item}")
    if warnings:
        print(f"\n  {len(warnings)} warning(s):")
        for item in warnings:
            print(f"    - {item}")
    print()


def main() -> int:
    os.chdir(ROOT)

    if not VENV.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)

    subprocess.run(
        [str(PYTHON), "-m", "pip", "install", "-q", "-r", "requirements.txt"],
        check=True,
    )

    check_links()

    port = find_free_port(8001, 8020)
    url = f"http://127.0.0.1:{port}"

    banner = (
        "\n"
        "==================================================\n"
        "  Voided Oblivion - MkDocs preview\n"
        f"    root : {ROOT}\n"
        f"    port : {port}\n"
        f"    url  : {url}\n"
        "==================================================\n"
    )
    print(banner)

    open_browser_later(url)

    return subprocess.run(
        [str(MKDOCS), "serve", "--dev-addr", f"127.0.0.1:{port}"]
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
