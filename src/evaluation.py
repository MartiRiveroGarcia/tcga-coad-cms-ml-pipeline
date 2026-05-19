"""Evaluation utilities for CMS classification models.

This module provides functions to load trained models, compute metrics on
the test set, generate visualisations, and persist the evaluation report.

Design contract
---------------
- All functions receive fitted models and test data; they never retrain.
- Figures are saved to disk and also returned so callers can display them.
- Metrics follow sklearn conventions: macro averages treat all classes equally,
  weighted averages account for class imbalance.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.base import BaseEstimator
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

CMS_ORDER: list[str] = ["CMS1", "CMS2", "CMS3", "CMS4"]
CMS_PALETTE: dict[str, str] = {
    "CMS1": "#E41A1C",
    "CMS2": "#377EB8",
    "CMS3": "#4DAF4A",
    "CMS4": "#FF7F00",
}
MODEL_DISPLAY_NAMES: dict[str, str] = {
    "logistic_regression": "Logistic Regression",
    "random_forest": "Random Forest",
    "svm": "SVM (linear)",
}
# Colors for the three models in comparison plots
MODEL_COLORS: list[str] = ["#4292c6", "#41ab5d", "#e6550d"]


# ── Loading ───────────────────────────────────────────────────────────────────

def load_models(models_dir: Path) -> dict[str, BaseEstimator]:
    """Load all trained .joblib model files from *models_dir*.

    Parameters
    ----------
    models_dir:
        Directory containing logistic_regression.joblib, random_forest.joblib,
        and svm.joblib produced by scripts/train.py.

    Returns
    -------
    Dictionary mapping model name to fitted estimator.
    """
    models: dict[str, BaseEstimator] = {}
    for key in MODEL_DISPLAY_NAMES:
        path = models_dir / f"{key}.joblib"
        if not path.exists():
            raise FileNotFoundError(
                f"Model file not found: {path}\n"
                "Run `python scripts/train.py` first."
            )
        models[key] = joblib.load(path)
        logger.info("Loaded %s from %s", key, path)
    return models


# ── Metrics ───────────────────────────────────────────────────────────────────

def evaluate_model(
    model: BaseEstimator,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict:
    """Compute classification metrics for a single model on the test set.

    Parameters
    ----------
    model:
        Fitted sklearn estimator with a predict() method.
    X_test:
        Feature matrix (samples × genes, log2-transformed).
    y_test:
        True CMS labels for the test set.

    Returns
    -------
    Dictionary with keys: accuracy, f1_macro, f1_weighted, per_class, y_pred.
    per_class maps each CMS label to precision, recall, f1 and support.
    """
    y_pred = model.predict(X_test)
    report = classification_report(
        y_test, y_pred,
        labels=CMS_ORDER,
        target_names=CMS_ORDER,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 6),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 6),
        "f1_weighted": round(float(f1_score(y_test, y_pred, average="weighted", zero_division=0)), 6),
        "per_class": {
            cms: {
                "precision": round(float(report[cms]["precision"]), 4),
                "recall":    round(float(report[cms]["recall"]), 4),
                "f1":        round(float(report[cms]["f1-score"]), 4),
                "support":   int(report[cms]["support"]),
            }
            for cms in CMS_ORDER
        },
        "y_pred": y_pred.tolist(),
    }


def build_benchmark_table(results: dict[str, dict]) -> pd.DataFrame:
    """Build a summary DataFrame comparing all models side by side.

    Parameters
    ----------
    results:
        Dictionary mapping model name to the dict returned by evaluate_model().

    Returns
    -------
    DataFrame indexed by model display name with one column per metric.
    """
    rows = []
    for key, metrics in results.items():
        row: dict = {"Model": MODEL_DISPLAY_NAMES[key]}
        row["Accuracy"]    = metrics["accuracy"]
        row["F1 macro"]    = metrics["f1_macro"]
        row["F1 weighted"] = metrics["f1_weighted"]
        for cms in CMS_ORDER:
            row[f"F1 {cms}"] = metrics["per_class"][cms]["f1"]
        rows.append(row)
    return pd.DataFrame(rows).set_index("Model")


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_confusion_matrix(
    model: BaseEstimator,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    title: str,
    output_path: Path | None = None,
) -> plt.Figure:
    """Plot a colour-coded confusion matrix for one model.

    Parameters
    ----------
    model:
        Fitted estimator.
    X_test, y_test:
        Test features and true labels.
    title:
        Figure title (typically includes the model name).
    output_path:
        If provided, the figure is saved there.

    Returns
    -------
    Matplotlib Figure.
    """
    y_pred = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred, labels=CMS_ORDER)

    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    sns.heatmap(
        cm,
        annot=True, fmt="d", cmap="Blues",
        xticklabels=CMS_ORDER, yticklabels=CMS_ORDER,
        linewidths=0.5, linecolor="#ddd",
        annot_kws={"size": 13},
        ax=ax,
    )
    ax.set_xlabel("Predicció", fontsize=11)
    ax.set_ylabel("Real", fontsize=11)
    ax.set_title(title, fontsize=12, pad=10)
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info("Confusion matrix saved to %s", output_path)
    return fig


def plot_metrics_comparison(
    results: dict[str, dict],
    output_path: Path | None = None,
) -> plt.Figure:
    """Grouped bar chart comparing accuracy and F1 macro across all models.

    Parameters
    ----------
    results:
        Dict mapping model name to evaluate_model() output.
    output_path:
        If provided, saves the figure.

    Returns
    -------
    Matplotlib Figure.
    """
    model_keys = list(results.keys())
    display_names = [MODEL_DISPLAY_NAMES[k] for k in model_keys]

    accuracies = [results[k]["accuracy"] for k in model_keys]
    f1_macros  = [results[k]["f1_macro"]  for k in model_keys]

    x     = np.arange(len(model_keys))
    width = 0.35

    fig, ax = plt.subplots(figsize=(9, 5))
    bars1 = ax.bar(x - width / 2, accuracies, width,
                   label="Accuracy", color="#4292c6", alpha=0.85)
    bars2 = ax.bar(x + width / 2, f1_macros,  width,
                   label="F1 macro", color="#41ab5d", alpha=0.85)

    for bar in list(bars1) + list(bars2):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.007,
            f"{bar.get_height():.3f}",
            ha="center", va="bottom", fontsize=9,
        )

    ax.set_ylim(0, 1.15)
    ax.set_xticks(x)
    ax.set_xticklabels(display_names, fontsize=11)
    ax.set_ylabel("Score")
    ax.set_title("Comparativa de models: Accuracy i F1 macro (test set)")
    ax.legend(fontsize=10)
    ax.axhline(y=1.0, color="#ccc", linestyle="--", linewidth=0.8)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info("Metrics comparison saved to %s", output_path)
    return fig


def plot_f1_per_class(
    results: dict[str, dict],
    output_path: Path | None = None,
) -> plt.Figure:
    """Grouped bar chart showing F1-score per CMS subtype for each model.

    This plot reveals which subtypes are easy or hard for each classifier
    — particularly useful for comparing CMS3 performance.

    Parameters
    ----------
    results:
        Dict mapping model name to evaluate_model() output.
    output_path:
        If provided, saves the figure.

    Returns
    -------
    Matplotlib Figure.
    """
    model_keys = list(results.keys())
    display_names = [MODEL_DISPLAY_NAMES[k] for k in model_keys]

    x     = np.arange(len(CMS_ORDER))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 5))
    for i, (key, name, color) in enumerate(
        zip(model_keys, display_names, MODEL_COLORS)
    ):
        f1_values = [results[key]["per_class"][cms]["f1"] for cms in CMS_ORDER]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, f1_values, width,
                      label=name, color=color, alpha=0.85)
        for bar, val in zip(bars, f1_values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.012,
                f"{val:.2f}",
                ha="center", va="bottom", fontsize=8,
            )

    ax.set_ylim(0, 1.20)
    ax.set_xticks(x)
    ax.set_xticklabels(CMS_ORDER, fontsize=11)
    ax.set_ylabel("F1-score")
    ax.set_title("F1-score per subtipus CMS i model (test set)")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info("F1 per class saved to %s", output_path)
    return fig


# ── Persistence ───────────────────────────────────────────────────────────────

def save_evaluation_report(
    results: dict[str, dict],
    output_path: Path,
) -> None:
    """Save evaluation metrics to a JSON file.

    y_pred arrays are excluded; only aggregate metrics and per_class dicts
    are persisted.

    Parameters
    ----------
    results:
        Dict mapping model name to evaluate_model() output.
    output_path:
        Destination path for the JSON file.
    """
    report = {
        key: {k: v for k, v in metrics.items() if k != "y_pred"}
        for key, metrics in results.items()
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2))
    logger.info("Evaluation report saved to %s", output_path)
