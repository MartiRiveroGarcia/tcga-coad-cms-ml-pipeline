#!/usr/bin/env python3
"""Stage 4 — Train classification models for CMS subtype prediction.

Loads preprocessed data from data/processed/, trains three sklearn
classifiers (Logistic Regression, Random Forest, SVM), saves the fitted
models to data/models/, and writes a training log with hyperparameters
and sanity-check metrics.

Usage
-----
    python scripts/train.py
    python scripts/train.py --dry-run
    python scripts/train.py --model random_forest
    python scripts/train.py --processed-dir data/processed --output-dir data/models
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.gdc_utils import repo_root
from src.models import (
    CLASS_WEIGHT,
    LR_MAX_ITER,
    LR_MULTI_CLASS,
    LR_SOLVER,
    RANDOM_SEED,
    RF_MAX_FEATURES,
    RF_N_ESTIMATORS,
    SVM_KERNEL,
    SVM_MAX_ITER,
    SVM_PROBABILITY,
    load_processed_data,
    save_model,
    train_logistic_regression,
    train_random_forest,
    train_svm,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Map model name → (train function, hyperparameters dict for the log)
_TRAINERS = {
    "logistic_regression": (
        train_logistic_regression,
        {
            "solver": LR_SOLVER,
            "multi_class": LR_MULTI_CLASS,
            "max_iter": LR_MAX_ITER,
            "class_weight": CLASS_WEIGHT,
            "random_state": RANDOM_SEED,
        },
    ),
    "random_forest": (
        train_random_forest,
        {
            "n_estimators": RF_N_ESTIMATORS,
            "max_features": RF_MAX_FEATURES,
            "class_weight": CLASS_WEIGHT,
            "random_state": RANDOM_SEED,
            "n_jobs": -1,
        },
    ),
    "svm": (
        train_svm,
        {
            "kernel": SVM_KERNEL,
            "max_iter": SVM_MAX_ITER,
            "probability": SVM_PROBABILITY,
            "class_weight": CLASS_WEIGHT,
            "random_state": RANDOM_SEED,
        },
    ),
}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Train CMS classification models on preprocessed RNA-seq data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--processed-dir",
        default=str(root / "data" / "processed"),
        help="Directory containing X_train.csv, X_test.csv, y_train.csv, y_test.csv.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(root / "data" / "models"),
        help="Output directory for .joblib model files and training_log.json.",
    )
    parser.add_argument(
        "--model",
        default="all",
        choices=["all", "logistic_regression", "random_forest", "svm"],
        help="Which model(s) to train.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print configuration and exit without training.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    processed_dir = Path(args.processed_dir)
    output_dir = Path(args.output_dir)
    selected = list(_TRAINERS.keys()) if args.model == "all" else [args.model]

    logger.info("── Stage 4: Model training ──────────────────────────────")
    logger.info("  processed-dir : %s", processed_dir)
    logger.info("  output-dir    : %s", output_dir)
    logger.info("  models        : %s", ", ".join(selected))
    logger.info("  random seed   : %d", RANDOM_SEED)

    if args.dry_run:
        logger.info("Dry-run mode — exiting without training.")
        sys.exit(0)

    # ── Load data ─────────────────────────────────────────────────────────────
    X_train, _X_test, y_train, _y_test = load_processed_data(processed_dir)

    cms_distribution = y_train.value_counts().sort_index().to_dict()
    logger.info("CMS distribution in train: %s", cms_distribution)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Train each selected model ─────────────────────────────────────────────
    import time

    log_models: dict[str, dict] = {}

    for name in selected:
        trainer, hyperparameters = _TRAINERS[name]
        logger.info("Training %s ...", name)
        t0 = time.perf_counter()
        model = trainer(X_train, y_train)
        elapsed = time.perf_counter() - t0

        # Sanity check: accuracy on training set
        train_accuracy = float(model.score(X_train, y_train))
        logger.info(
            "  %s — train accuracy: %.4f, time: %.1f s",
            name,
            train_accuracy,
            elapsed,
        )

        output_file = f"{name}.joblib"
        save_model(model, output_dir / output_file)

        log_models[name] = {
            "hyperparameters": hyperparameters,
            "train_accuracy": round(train_accuracy, 6),
            "training_time_seconds": round(elapsed, 2),
            "output_file": output_file,
        }

    # ── Write training log ────────────────────────────────────────────────────
    training_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "train_samples": int(X_train.shape[0]),
        "train_genes": int(X_train.shape[1]),
        "cms_distribution_train": {k: int(v) for k, v in cms_distribution.items()},
        "models": log_models,
    }

    log_path = output_dir / "training_log.json"
    log_path.write_text(json.dumps(training_log, indent=2))
    logger.info("Training log saved to %s", log_path)

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("── Summary ──────────────────────────────────────────────")
    for name, info in log_models.items():
        logger.info(
            "  %-24s  train_acc=%.4f  time=%.1f s",
            name,
            info["train_accuracy"],
            info["training_time_seconds"],
        )
    logger.info("Models saved to %s", output_dir)


if __name__ == "__main__":
    main()
