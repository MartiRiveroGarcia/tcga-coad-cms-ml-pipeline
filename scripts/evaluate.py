#!/usr/bin/env python3
"""Stage 5 — Evaluate trained CMS classification models on the test set.

Loads the three fitted models from data/models/, evaluates them on the
held-out test set in data/processed/, generates comparison figures, and
writes a JSON evaluation report.

Usage
-----
    python scripts/evaluate.py
    python scripts/evaluate.py --dry-run
    python scripts/evaluate.py --models-dir data/models --output-dir results
    python scripts/evaluate.py --figures-dir figures
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — no display required

from src.gdc_utils import repo_root
from src.evaluation import (
    MODEL_DISPLAY_NAMES,
    build_benchmark_table,
    evaluate_model,
    load_models,
    plot_confusion_matrix,
    plot_f1_per_class,
    plot_metrics_comparison,
    save_evaluation_report,
)
from src.models import load_processed_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Evaluate CMS classification models on the held-out test set.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--processed-dir",
        default=str(root / "data" / "processed"),
        help="Directory with X_train.csv, X_test.csv, y_train.csv, y_test.csv.",
    )
    parser.add_argument(
        "--models-dir",
        default=str(root / "data" / "models"),
        help="Directory containing .joblib model files produced by scripts/train.py.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(root / "results"),
        help="Output directory for evaluation_report.json.",
    )
    parser.add_argument(
        "--figures-dir",
        default=str(root / "figures"),
        help="Output directory for all generated figures.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration and exit without evaluating.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    processed_dir = Path(args.processed_dir)
    models_dir    = Path(args.models_dir)
    output_dir    = Path(args.output_dir)
    figures_dir   = Path(args.figures_dir)

    logger.info("── Stage 5: Model evaluation ────────────────────────────")
    logger.info("  processed-dir : %s", processed_dir)
    logger.info("  models-dir    : %s", models_dir)
    logger.info("  output-dir    : %s", output_dir)
    logger.info("  figures-dir   : %s", figures_dir)

    if args.dry_run:
        logger.info("Dry-run mode — exiting without evaluating.")
        sys.exit(0)

    # ── Load data and models ──────────────────────────────────────────────────
    _X_train, X_test, _y_train, y_test = load_processed_data(processed_dir)
    logger.info(
        "Test set — %d samples × %d genes, classes: %s",
        X_test.shape[0],
        X_test.shape[1],
        sorted(y_test.unique()),
    )

    models = load_models(models_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # ── Evaluate each model ───────────────────────────────────────────────────
    results: dict[str, dict] = {}
    for name, model in models.items():
        logger.info("Evaluating %s ...", name)
        metrics = evaluate_model(model, X_test, y_test)
        results[name] = metrics
        logger.info(
            "  %-24s  accuracy=%.4f  F1_macro=%.4f  F1_weighted=%.4f",
            name,
            metrics["accuracy"],
            metrics["f1_macro"],
            metrics["f1_weighted"],
        )

    # ── Confusion matrices (one per model) ───────────────────────────────────
    for name, model in models.items():
        display = MODEL_DISPLAY_NAMES[name]
        fig_path = figures_dir / f"confusion_matrix_{name}.png"
        plot_confusion_matrix(
            model,
            X_test,
            y_test,
            title=f"Matriu de confusió — {display}",
            output_path=fig_path,
        )
        logger.info("Confusion matrix saved: %s", fig_path)

    # ── Comparison figures ────────────────────────────────────────────────────
    plot_metrics_comparison(
        results,
        output_path=figures_dir / "metrics_comparison.png",
    )
    logger.info("Metrics comparison saved: %s", figures_dir / "metrics_comparison.png")

    plot_f1_per_class(
        results,
        output_path=figures_dir / "f1_per_class.png",
    )
    logger.info("F1 per class saved: %s", figures_dir / "f1_per_class.png")

    # ── Benchmark table ───────────────────────────────────────────────────────
    table = build_benchmark_table(results)
    logger.info("\nBenchmark table:\n%s", table.to_string())

    # ── Save JSON report ──────────────────────────────────────────────────────
    report_path = output_dir / "evaluation_report.json"
    save_evaluation_report(results, report_path)
    logger.info("Evaluation report saved: %s", report_path)

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("── Summary ──────────────────────────────────────────────")
    logger.info("  %-24s  %-10s  %-10s  %s", "Model", "Accuracy", "F1 macro", "F1 weighted")
    logger.info("  %s", "-" * 60)
    for name, metrics in results.items():
        logger.info(
            "  %-24s  %-10.4f  %-10.4f  %.4f",
            name,
            metrics["accuracy"],
            metrics["f1_macro"],
            metrics["f1_weighted"],
        )
    logger.info("Figures saved to %s", figures_dir)
    logger.info("Report saved to %s", report_path)


if __name__ == "__main__":
    main()
