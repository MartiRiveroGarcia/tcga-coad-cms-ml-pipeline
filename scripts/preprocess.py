#!/usr/bin/env python3
"""Preprocess TCGA-COAD RNA-seq data for CMS classification.

Pipeline steps (in order):
  1. Load sample sheet + CMS labels
  2. Build expression matrix from raw STAR-Counts files
  3. Remove QC rows (N_unmapped, etc.)
  4. Filter to protein-coding genes
  5. Deduplicate samples (FFPE, metastatic, recurrence, duplicates)
  6. Attach CMS labels, drop unlabeled samples
  7. Stratified train/test split (80/20, seed=42)
  8. Filter low-count genes (fit on train, apply to both)
  9. Log2(x+1) transformation
 10. Save to data/processed/

Usage:
    python scripts/preprocess.py
    python scripts/preprocess.py --dry-run
    python scripts/preprocess.py --seed 123 --test-size 0.3
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.gdc_utils import repo_root
from src.preprocessing import (
    RANDOM_SEED,
    TEST_SIZE,
    MIN_COUNT_THRESHOLD,
    MIN_SAMPLE_FRACTION,
    attach_labels,
    build_expression_matrix,
    deduplicate_samples,
    filter_low_count_genes,
    filter_protein_coding,
    load_cms_labels,
    load_sample_sheet,
    log_transform,
    remove_qc_rows,
    save_processed_data,
    split_train_test,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def default_sample_sheet(metadata_dir: Path) -> Path:
    """Find the newest GDC sample sheet in the metadata directory."""
    candidates = sorted(metadata_dir.glob("gdc_sample_sheet*.tsv"))
    if not candidates:
        raise FileNotFoundError(f"No sample sheet found in {metadata_dir}")
    return candidates[-1]


def default_cms_labels(metadata_dir: Path) -> Path:
    """Find the CMS labels file in the metadata directory."""
    path = metadata_dir / "cms_labels_public_all.txt"
    if not path.exists():
        raise FileNotFoundError(
            f"CMS labels not found: {path}\n"
            "Download from Synapse (syn4978511) and place in data/metadata/"
        )
    return path


def main() -> None:
    root = repo_root()

    parser = argparse.ArgumentParser(
        description="Preprocess TCGA-COAD RNA-seq data for CMS classification.",
    )
    parser.add_argument(
        "--raw-dir",
        default=str(root / "data" / "raw" / "gdc"),
        help="Directory with UUID subdirectories containing expression files.",
    )
    parser.add_argument(
        "--metadata-dir",
        default=str(root / "data" / "metadata"),
        help="Directory with sample sheet and CMS labels.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(root / "data" / "processed"),
        help="Output directory for processed data.",
    )
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed.")
    parser.add_argument("--test-size", type=float, default=TEST_SIZE, help="Test set fraction.")
    parser.add_argument(
        "--min-count", type=int, default=MIN_COUNT_THRESHOLD,
        help="Minimum count threshold for gene filtering.",
    )
    parser.add_argument(
        "--min-fraction", type=float, default=MIN_SAMPLE_FRACTION,
        help="Minimum fraction of samples that must meet the count threshold.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print configuration without executing.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    metadata_dir = Path(args.metadata_dir)
    output_dir = Path(args.output_dir)

    if args.dry_run:
        print("[DRY-RUN] Configuration:")
        print(f"  Raw data:    {raw_dir}")
        print(f"  Metadata:    {metadata_dir}")
        print(f"  Output:      {output_dir}")
        print(f"  Seed:        {args.seed}")
        print(f"  Test size:   {args.test_size}")
        print(f"  Min count:   {args.min_count}")
        print(f"  Min fraction:{args.min_fraction}")
        sys.exit(0)

    logger.info("=== TCGA-COAD Preprocessing Pipeline ===")

    # Step 0: Load metadata
    sample_sheet = load_sample_sheet(default_sample_sheet(metadata_dir))
    cms_labels = load_cms_labels(default_cms_labels(metadata_dir))

    # Step 1: Build expression matrix
    expression_matrix, gene_info = build_expression_matrix(raw_dir, sample_sheet)

    # Step 2: Remove QC rows
    expression_matrix = remove_qc_rows(expression_matrix)

    # Step 3: Filter protein-coding genes
    expression_matrix = filter_protein_coding(expression_matrix, gene_info)

    # Step 4: Deduplicate samples
    expression_matrix = deduplicate_samples(expression_matrix, sample_sheet)

    # Step 5: Attach CMS labels
    expression_matrix, labels = attach_labels(expression_matrix, cms_labels)

    # Step 6: Train/test split (BEFORE data-dependent transforms)
    X_train, X_test, y_train, y_test = split_train_test(
        expression_matrix, labels,
        test_size=args.test_size,
        random_seed=args.seed,
    )

    # Step 7: Filter low-count genes (fit on train, apply to both)
    X_train, X_test, kept_genes = filter_low_count_genes(
        X_train, X_test,
        min_count=args.min_count,
        min_fraction=args.min_fraction,
    )

    # Step 8: Log2(x+1) transformation
    X_train, X_test = log_transform(X_train, X_test)

    # Step 9: Save outputs
    preprocessing_params = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": args.seed,
        "test_size": args.test_size,
        "min_count_threshold": args.min_count,
        "min_sample_fraction": args.min_fraction,
        "raw_files_found": len(list(raw_dir.iterdir())),
        "samples_after_dedup": expression_matrix.shape[1],
        "samples_with_cms_labels": len(labels),
        "train_samples": len(y_train),
        "test_samples": len(y_test),
        "genes_initial": gene_info.shape[0],
        "genes_after_protein_coding": expression_matrix.shape[0],
        "genes_after_low_count_filter": len(kept_genes),
        "transform": "log2(x + 1)",
        "cms_distribution_train": y_train.value_counts().to_dict(),
        "cms_distribution_test": y_test.value_counts().to_dict(),
    }

    save_processed_data(
        output_dir, X_train, X_test, y_train, y_test,
        gene_info, kept_genes, preprocessing_params,
    )

    logger.info("=== Preprocessing complete ===")
    logger.info("Output: %s", output_dir)
    logger.info("Train: %d samples x %d genes", X_train.shape[0], X_train.shape[1])
    logger.info("Test:  %d samples x %d genes", X_test.shape[0], X_test.shape[1])


if __name__ == "__main__":
    main()
