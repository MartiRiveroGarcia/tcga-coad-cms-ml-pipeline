#!/usr/bin/env python3
"""Download GDC files from a manifest using gdc-client (auto-installs if missing)."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from src.gdc_utils import ensure_gdc_client, repo_root


def default_manifest_path() -> Path:
    """Find the newest GDC manifest file in data/metadata/."""
    md_dir = repo_root() / "data" / "metadata"
    candidates = sorted(md_dir.glob("gdc_manifest*.txt"))
    if not candidates:
        raise FileNotFoundError(
            f"No GDC manifest found in {md_dir}. "
            "Place your manifest there (e.g., gdc_manifest.<date>.txt) or pass --manifest."
        )
    return candidates[-1]


def main() -> None:
    root = repo_root()

    p = argparse.ArgumentParser(
        description="Download GDC files from a manifest into data/raw using gdc-client."
    )
    p.add_argument(
        "--manifest",
        default=None,
        help="Path to GDC manifest TSV. If omitted, uses the newest gdc_manifest*.txt in data/metadata/.",
    )
    p.add_argument(
        "--out",
        default=str(root / "data" / "raw" / "gdc"),
        help="Output directory for downloaded files (default: data/raw/gdc).",
    )
    p.add_argument(
        "--tools",
        default=str(root / "tools"),
        help="Tools directory where gdc-client is installed (default: tools).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be executed without downloading.",
    )
    args = p.parse_args()

    manifest = Path(args.manifest) if args.manifest else default_manifest_path()
    out_dir = Path(args.out)
    tools_dir = Path(args.tools)

    if not manifest.exists():
        print(f"[ERROR] Manifest not found: {manifest}", file=sys.stderr)
        sys.exit(2)

    if args.dry_run:
        print("[DRY-RUN] No install, no download.")
        print(f"  Manifest: {manifest}")
        print(f"  Output:   {out_dir}")
        print(f"  Tools:    {tools_dir}")
        sys.exit(0)

    gdc_client = ensure_gdc_client(tools_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(gdc_client), "download", "-m", str(manifest), "-d", str(out_dir)]
    print(f"[INFO] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
