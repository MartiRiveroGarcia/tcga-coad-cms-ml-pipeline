#!/usr/bin/env python3
"""Stage 4 — Train classification models for CMS subtype prediction.

Loads preprocessed data from data/processed/, trains three sklearn
classifiers (Logistic Regression, Random Forest, SVM), saves the fitted
models to data/models/, and writes a training log with hyperparameters
and sanity-check metrics.

Also trains the same three models on the 'minimal' dataset
(pre-low-count-filter, pre-log2) and saves predictions and evaluation
metrics for downstream comparison.

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
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.evaluation import evaluate_model, save_evaluation_report
from src.gdc_utils import repo_root
from src.models import (
    CLASS_WEIGHT,
    LR_MAX_ITER,
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

# Minimal dataset suffix and output column names for predictions CSV
_MINIMAL_SUFFIX = "_minimal_no_lowexpr_no_log2"
_MINIMAL_PRED_COLUMNS = {
    "logistic_regression": "logistic_regression_minimal",
    "random_forest": "random_forest_minimal",
    "svm": "svm_linear_minimal",
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
        "--results-dir",
        default=str(root / "results"),
        help="Output directory for predictions and evaluation reports.",
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
    results_dir = Path(args.results_dir)
    selected = list(_TRAINERS.keys()) if args.model == "all" else [args.model]

    logger.info("── Stage 4: Model training ──────────────────────────────")
    logger.info("  processed-dir : %s", processed_dir)
    logger.info("  output-dir    : %s", output_dir)
    logger.info("  results-dir   : %s", results_dir)
    logger.info("  models        : %s", ", ".join(selected))
    logger.info("  random seed   : %d", RANDOM_SEED)

    if args.dry_run:
        logger.info("Dry-run mode — exiting without training.")
        sys.exit(0)

    # ── Load full dataset ─────────────────────────────────────────────────────
    X_train, _X_test, y_train, _y_test = load_processed_data(processed_dir)
    logger.info("Full dataset loaded — %d samples x %d genes", X_train.shape[0], X_train.shape[1])

    cms_distribution = y_train.value_counts().sort_index().to_dict()
    logger.info("CMS distribution in train: %s", cms_distribution)

    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Train each selected model (full, balanced) ────────────────────────────
    log_models: dict[str, dict] = {}

    for name in selected:
        trainer, hyperparameters = _TRAINERS[name]
        logger.info("Training %s ...", name)
        t0 = time.perf_counter()
        model = trainer(X_train, y_train)
        elapsed = time.perf_counter() - t0

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

    # ── Train unbalanced variants (class_weight=None) — needed for H6 ─────────
    logger.info("── Training unbalanced variants (class_weight=None) ─────")
    log_models_unbalanced: dict[str, dict] = {}

    for name in selected:
        trainer, hyperparameters = _TRAINERS[name]
        logger.info("Training %s (unbalanced) ...", name)
        t0 = time.perf_counter()
        model_unbal = trainer(X_train, y_train, class_weight=None)
        elapsed = time.perf_counter() - t0

        train_accuracy = float(model_unbal.score(X_train, y_train))
        logger.info(
            "  %s (unbalanced) — train accuracy: %.4f, time: %.1f s",
            name,
            train_accuracy,
            elapsed,
        )

        output_file = f"{name}_unbalanced.joblib"
        save_model(model_unbal, output_dir / output_file)

        unbal_hyperparameters = {**hyperparameters, "class_weight": None}
        log_models_unbalanced[name] = {
            "hyperparameters": unbal_hyperparameters,
            "train_accuracy": round(train_accuracy, 6),
            "training_time_seconds": round(elapsed, 2),
            "output_file": output_file,
        }

    # ── Train minimal dataset models ──────────────────────────────────────────
    logger.info("── Loading minimal dataset ────────────────────────────────")
    X_train_min, X_test_min, y_train_min, y_test_min = load_processed_data(
        processed_dir, suffix=_MINIMAL_SUFFIX
    )
    logger.info(
        "Minimal dataset loaded — X_train: %d samples x %d genes, X_test: %d samples x %d genes",
        X_train_min.shape[0], X_train_min.shape[1],
        X_test_min.shape[0], X_test_min.shape[1],
    )

    logger.info("── Training models on minimal dataset ─────────────────────")
    log_models_minimal: dict[str, dict] = {}
    trained_minimal: dict[str, object] = {}

    for name in selected:
        trainer, hyperparameters = _TRAINERS[name]
        logger.info("Training %s (minimal) ...", name)
        t0 = time.perf_counter()
        model_min = trainer(X_train_min, y_train_min)
        elapsed = time.perf_counter() - t0

        train_accuracy = float(model_min.score(X_train_min, y_train_min))
        logger.info(
            "  %s (minimal) — train accuracy: %.4f, time: %.1f s",
            name,
            train_accuracy,
            elapsed,
        )

        output_file = f"{name}{_MINIMAL_SUFFIX}.joblib"
        save_model(model_min, output_dir / output_file)
        logger.info("  Model saved: %s", output_dir / output_file)

        trained_minimal[name] = model_min
        log_models_minimal[name] = {
            "hyperparameters": hyperparameters,
            "train_accuracy": round(train_accuracy, 6),
            "training_time_seconds": round(elapsed, 2),
            "output_file": output_file,
        }

    logger.info("Models minimal entrenats: %s", ", ".join(selected))

    # ── Evaluate minimal models and save predictions ──────────────────────────
    logger.info("── Generating predictions and metrics (minimal) ─────────")
    results_dir.mkdir(parents=True, exist_ok=True)

    eval_results: dict[str, dict] = {}
    pred_columns: dict[str, list] = {}

    for name in selected:
        model_min = trained_minimal[name]
        metrics = evaluate_model(model_min, X_test_min, y_test_min)  # type: ignore[arg-type]
        col = _MINIMAL_PRED_COLUMNS[name]
        pred_columns[col] = metrics["y_pred"]
        eval_results[name] = metrics

        logger.info(
            "  %-32s  accuracy=%.4f  F1_macro=%.4f  F1_weighted=%.4f",
            f"{name} (minimal)",
            metrics["accuracy"],
            metrics["f1_macro"],
            metrics["f1_weighted"],
        )

    # Save predictions CSV
    preds_df = pd.DataFrame(
        {"sample_id": X_test_min.index, "y_true": y_test_min.values}
        | {col: pred_columns[col] for col in _MINIMAL_PRED_COLUMNS.values()
           if col in pred_columns}
    )
    preds_path = results_dir / f"predictions{_MINIMAL_SUFFIX}.csv"
    preds_df.to_csv(preds_path, index=False)
    logger.info("Prediccions guardades: %s", preds_path)

    # Save evaluation report JSON
    report_path = results_dir / f"evaluation_report{_MINIMAL_SUFFIX}.json"
    save_evaluation_report(eval_results, report_path)
    logger.info("Mètriques guardades: %s", report_path)

    # ── Write training log (all variants) ────────────────────────────────────
    training_log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": RANDOM_SEED,
        "train_samples": int(X_train.shape[0]),
        "train_genes": int(X_train.shape[1]),
        "cms_distribution_train": {k: int(v) for k, v in cms_distribution.items()},
        "models": log_models,
        "models_unbalanced": log_models_unbalanced,
        "models_minimal": {
            "train_samples": int(X_train_min.shape[0]),
            "train_genes": int(X_train_min.shape[1]),
            "models": log_models_minimal,
        },
    }

    log_path = output_dir / "training_log.json"
    log_path.write_text(json.dumps(training_log, indent=2))
    logger.info("Training log saved to %s", log_path)

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("── Summary ──────────────────────────────────────────────")
    logger.info("  Full dataset models:")
    for name, info in log_models.items():
        logger.info(
            "    %-24s  train_acc=%.4f  time=%.1f s",
            name,
            info["train_accuracy"],
            info["training_time_seconds"],
        )
    logger.info("  Minimal dataset models:")
    for name, info in log_models_minimal.items():
        logger.info(
            "    %-24s  train_acc=%.4f  time=%.1f s",
            name,
            info["train_accuracy"],
            info["training_time_seconds"],
        )
    logger.info("Models saved to %s", output_dir)
    logger.info("Results saved to %s", results_dir)


if __name__ == "__main__":
    main()
