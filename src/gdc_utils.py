"""Shared utilities for GDC Data Transfer Tool: detection, installation, and lookup."""
from __future__ import annotations

import hashlib
import platform
import urllib.request
import zipfile
from pathlib import Path

GDC_CLIENT_VERSION = "2.3.0"

DISTROS: dict[str, dict[str, str]] = {
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


def repo_root() -> Path:
    """Return the repository root (parent of src/)."""
    return Path(__file__).resolve().parents[1]


def detect_platform_key() -> str:
    """Detect the current platform and return the corresponding DISTROS key."""
    sysname = platform.system().lower()
    machine = platform.machine().lower()

    if sysname.startswith("win"):
        return "windows_x64"
    if sysname == "linux":
        return "linux_x64"
    if sysname == "darwin":
        if machine in ("arm64", "aarch64"):
            return "mac_silicon_arm64"
        return "mac_intel_x64"

    raise RuntimeError(f"Unsupported OS: {platform.system()} / {platform.machine()}")


def _md5_file(path: Path) -> str:
    """Compute MD5 checksum of a file."""
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_file(url: str, dest: Path) -> None:
    """Download a URL to a local file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as r, dest.open("wb") as f:
        f.write(r.read())


def _extract_nested_zips(zip_path: Path, out_dir: Path) -> None:
    """Extract a zip file. If it contains nested zips, extract those too."""
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(out_dir)

    for nested_zip in out_dir.rglob("*.zip"):
        if nested_zip == zip_path:
            continue
        print(f"[INFO] Found nested zip: {nested_zip.name}, extracting...")
        with zipfile.ZipFile(nested_zip, "r") as z:
            z.extractall(nested_zip.parent)
        nested_zip.unlink()


def _find_executable(base_dir: Path, exe_name: str) -> Path:
    """Search for an executable inside a directory, filtering macOS artifacts."""
    matches = list(base_dir.rglob(exe_name))
    matches = [m for m in matches if "__MACOSX" not in m.parts and m.is_file()]
    if not matches:
        raise FileNotFoundError(
            f"Executable '{exe_name}' not found under: {base_dir}\n"
            f"Contents: {[str(p.relative_to(base_dir)) for p in base_dir.rglob('*') if p.is_file()]}"
        )
    return matches[0]


def install_gdc_client(tools_dir: Path) -> Path:
    """Download, verify and extract gdc-client for the current platform."""
    key = detect_platform_key()
    cfg = DISTROS[key]

    out_dir = tools_dir / "gdc-client" / GDC_CLIENT_VERSION / key
    out_dir.mkdir(parents=True, exist_ok=True)

    zip_path = out_dir / Path(cfg["url"]).name
    print(f"[INFO] Platform: {cfg['label']} ({key})")
    print(f"[INFO] Download: {cfg['url']}")
    print(f"[INFO] Target dir: {out_dir}")

    print("[INFO] Downloading zip...")
    _download_file(cfg["url"], zip_path)

    got = _md5_file(zip_path)
    if got != cfg["md5"]:
        zip_path.unlink()
        raise RuntimeError(
            f"MD5 mismatch for {zip_path.name}\n"
            f"Expected: {cfg['md5']}\n"
            f"Got:      {got}"
        )
    print("[OK] MD5 verified.")

    print("[INFO] Extracting...")
    _extract_nested_zips(zip_path, out_dir)
    zip_path.unlink(missing_ok=True)

    exe_path = _find_executable(out_dir, cfg["exe"])

    # Make executable on unix
    if exe_path.suffix != ".exe":
        exe_path.chmod(exe_path.stat().st_mode | 0o111)

    print(f"[OK] Installed: {exe_path}")
    return exe_path


def find_gdc_client(tools_dir: Path) -> Path:
    """Locate the gdc-client executable. Raises FileNotFoundError if missing."""
    key = detect_platform_key()
    exe_name = DISTROS[key]["exe"]
    version_dir = tools_dir / "gdc-client" / GDC_CLIENT_VERSION / key

    if not version_dir.exists():
        raise FileNotFoundError(
            f"gdc-client not found: {version_dir} does not exist.\n"
            f"Run: python scripts/download.py (it will auto-install)"
        )

    return _find_executable(version_dir, exe_name)


def ensure_gdc_client(tools_dir: Path) -> Path:
    """Return path to gdc-client, auto-installing if not found."""
    try:
        return find_gdc_client(tools_dir)
    except FileNotFoundError:
        print("[INFO] gdc-client not found. Installing...")
        return install_gdc_client(tools_dir)
