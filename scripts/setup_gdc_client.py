#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import sys
import urllib.request
import zipfile
from pathlib import Path

VERSION = "2.3.0"

# Official binaries + md5sums listed on the GDC Data Transfer Tool page.
# Installation method: download the respective binary distribution and unzip. :contentReference[oaicite:2]{index=2}
DISTROS = {
    "linux_x64": {
        "label": "Ubuntu x64",
        "url": "https://gdc.cancer.gov/system/files/public/file/gdc-client_2.3_Ubuntu_x64-py3.8-ubuntu-20.04.zip",
        "md5": "18591d74de07cdcd396dab71c52663da",
        "exe": "gdc-client",
    },
    "windows_x64": {
        "label": "Windows x64",
        "url": "https://gdc.cancer.gov/system/files/public/file/gdc-client_2.3_Windows_x64-py3.8-windows-2019.zip",
        "md5": "525ce44bb5f3f0624066b906c7dbdaf4",
        "exe": "gdc-client.exe",
    },
    "mac_intel_x64": {
        "label": "macOS x64 (Intel)",
        "url": "https://gdc.cancer.gov/system/files/public/file/gdc-client_2.3_OSX_x64-py3.8-macos-12.zip",
        "md5": "fee6a557d16a6c1a9388bd859224e638",
        "exe": "gdc-client",
    },
    "mac_silicon_arm64": {
        "label": "macOS (Apple Silicon)",
        "url": "https://gdc.cancer.gov/system/files/public/file/gdc-client_2.3_OSX_x64-py3.8-macos-14.zip",
        "md5": "56cca3594fa5fb47bc8297f5b6fd0e20",
        "exe": "gdc-client",
    },
}


def detect_platform_key() -> str:
    sysname = platform.system().lower()
    machine = platform.machine().lower()

    if sysname.startswith("win"):
        return "windows_x64"
    if sysname == "linux":
        return "linux_x64"
    if sysname == "darwin":
        # Best-effort detection: arm64 -> silicon, else intel
        if machine in ("arm64", "aarch64"):
            return "mac_silicon_arm64"
        return "mac_intel_x64"

    raise RuntimeError(f"Unsupported OS: {platform.system()} / {platform.machine()}")


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, dest.open("wb") as f:
        f.write(r.read())


def install(dest_root: Path) -> Path:
    key = detect_platform_key()
    cfg = DISTROS[key]

    out_dir = dest_root / "gdc-client" / VERSION / key
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / Path(cfg["url"]).name
    print(f"[INFO] Platform: {cfg['label']} ({key})")
    print(f"[INFO] Download: {cfg['url']}")
    print(f"[INFO] Target dir: {out_dir}")

    print("[INFO] Downloading zip...")
    download(cfg["url"], zip_path)

    got = md5_file(zip_path)
    if got != cfg["md5"]:
        raise RuntimeError(
            f"MD5 mismatch for {zip_path.name}\n"
            f"Expected: {cfg['md5']}\n"
            f"Got:      {got}"
        )
    print("[OK] MD5 verified.")

    print("[INFO] Extracting...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)

    exe_path = out_dir / cfg["exe"]
    if not exe_path.exists():
        # Sometimes the zip may include nested folders; try to locate it.
        matches = list(out_dir.rglob(cfg["exe"]))
        if not matches:
            raise RuntimeError(f"Executable not found after extraction: {cfg['exe']}")
        exe_path = matches[0]

    # Make executable on unix
    if exe_path.suffix != ".exe":
        exe_path.chmod(exe_path.stat().st_mode | 0o111)

    print(f"[OK] Installed: {exe_path}")
    return exe_path


def main() -> None:
    p = argparse.ArgumentParser(
        description="Setup GDC Data Transfer Tool (gdc-client) from official binaries."
    )
    p.add_argument(
        "--install",
        action="store_true",
        help="Perform download + checksum verification + extraction (otherwise no-op).",
    )
    p.add_argument(
        "--dest",
        default="tools",
        help="Destination root folder (default: tools).",
    )
    args = p.parse_args()

    if not args.install:
        key = detect_platform_key()
        cfg = DISTROS[key]
        print("[NO-OP] Not installing (use --install to proceed).")
        print(f"[INFO] Would install {cfg['label']} (version {VERSION}) into: {Path(args.dest) / 'gdc-client' / VERSION / key}")
        sys.exit(0)

    exe = install(Path(args.dest))
    print("\nNext step:")
    print(f'  Use: "{exe}" --help')


if __name__ == "__main__":
    main()