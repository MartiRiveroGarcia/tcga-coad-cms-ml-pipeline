#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import subprocess
import sys
from pathlib import Path

VERSION = "2.3.0"

EXE_NAME = {
    "linux_x64": "gdc-client",
    "windows_x64": "gdc-client.exe",
    "mac_intel_x64": "gdc-client",
    "mac_silicon_arm64": "gdc-client",
}


def detect_platform_key() -> str:
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


def repo_root() -> Path:
    # scripts/ is inside repo root
    return Path(__file__).resolve().parents[1]


def default_manifest_path() -> Path:
    md_dir = repo_root() / "data" / "metadata"
    candidates = sorted(md_dir.glob("gdc_manifest*.txt"))
    if not candidates:
        raise FileNotFoundError(
            f"No GDC manifest found in {md_dir}. "
            "Place your manifest there (e.g., gdc_manifest.<date>.txt) or pass --manifest."
        )
    # pick the last one (usually newest by name)
    return candidates[-1]


def find_gdc_client(tools_dir: Path) -> Path:
    key = detect_platform_key()
    exe = EXE_NAME[key]

    candidate = tools_dir / "gdc-client" / VERSION / key / exe
    if candidate.exists():
        return candidate

    # Fallback in case zip extracted into nested folder(s)
    version_root = tools_dir / "gdc-client" / VERSION / key
    if version_root.exists():
        matches = list(version_root.rglob(exe))
        if matches:
            return matches[0]

    raise FileNotFoundError(
        f"gdc-client not found under: {tools_dir}/gdc-client/{VERSION}/{key}/\n"
        f"Run: python scripts/setup_gdc_client.py --install"
    )


def ensure_gdc_client(tools_dir: Path) -> Path:
    try:
        return find_gdc_client(tools_dir)
    except FileNotFoundError:
        # Auto-install using our setup script
        setup_script = Path(__file__).resolve().parent / "setup_gdc_client.py"
        if not setup_script.exists():
            raise FileNotFoundError(f"Missing installer script: {setup_script}")

        print("[INFO] gdc-client not found. Installing via setup_gdc_client.py --install ...")
        subprocess.run(
            [sys.executable, str(setup_script), "--install", "--dest", str(tools_dir)],
            check=True,
        )
        # Try again after install
        return find_gdc_client(tools_dir)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Download GDC files from a manifest into data/raw using gdc-client (auto-installs if missing)."
    )
    p.add_argument(
        "--manifest",
        default=None,
        help="Path to GDC manifest TSV. If omitted, uses the newest gdc_manifest*.txt in data/metadata/.",
    )
    p.add_argument(
        "--out",
        default=str(repo_root() / "data" / "raw" / "gdc"),
        help="Output directory for downloaded files (default: data/raw/gdc).",
    )
    p.add_argument(
        "--tools",
        default=str(repo_root() / "tools"),
        help="Tools directory where gdc-client is installed (default: tools).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be executed (no install, no download).",
    )
    args = p.parse_args()

    manifest = Path(args.manifest) if args.manifest else default_manifest_path()
    out_dir = Path(args.out)
    tools_dir = Path(args.tools)

    if not manifest.exists():
        print(f"[ERROR] Manifest not found: {manifest}", file=sys.stderr)
        sys.exit(2)

    key = detect_platform_key()
    exe = EXE_NAME[key]
    expected = tools_dir / "gdc-client" / VERSION / key / exe

    if args.dry_run:
        print("[DRY-RUN] No install, no download.")
        print(f"[INFO] Manifest: {manifest}")
        print(f"[INFO] Output:   {out_dir}")
        print(f"[INFO] Tools:    {tools_dir}")
        print(f"[INFO] Expected gdc-client path: {expected}")
        print("Command (after install):")
        print(f"  {expected} download -m {manifest} -d {out_dir}")
        sys.exit(0)

    gdc_client = ensure_gdc_client(tools_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(gdc_client), "download", "-m", str(manifest), "-d", str(out_dir)]
    print("[INFO] Downloading with:")
    print("  " + " ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()