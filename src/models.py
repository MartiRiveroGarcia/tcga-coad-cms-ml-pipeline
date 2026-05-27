"""Model training utilities for TCGA-COAD CMS classification.

This module provides functions to load preprocessed data, train three
sklearn classifiers (Logistic Regression, Random Forest, SVM), and
persist the fitted models to disk.

Design contract
---------------
- All models use the same RANDOM_SEED.
- class_weight defaults to 'balanced' to compensate for CMS3 minority class;
  pass class_weight=None to train unbalanced variants (used for H6 statistical test).
- Each train_* function receives only training data. Test data is never
  seen during training — evaluation happens in a separate stage.
- No hyperparameter search is performed here; that is stage 5.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

RANDOM_SEED: int = 42

# LogisticRegression hyperparameters
LR_MAX_ITER: int = 5000       # default 100 fails to converge on 15k features
LR_SOLVER: str = "saga"        # Cython solver, random_state-controlled, cross-platform deterministic

# RandomForestClassifier hyperparameters
RF_N_ESTIMATORS: int = 500
RF_MAX_FEATURES: str = "sqrt"  # standard choice for classification tasks

# SVC hyperparameters
SVM_KERNEL: str = "linear"     # linear kernel excels when n_features >> n_samples
SVM_MAX_ITER: int = -1         # unlimited iterations (SVC default, made explicit)
SVM_PROBABILITY: bool = True   # enables predict_proba via Platt scaling (stage 6)

# Shared
CLASS_WEIGHT: str = "balanced"  # compensates for CMS3 minority (43/296 train samples)


# ── Data loading ──────────────────────────────────────────────────────────────

def load_processed_data(
    processed_dir: Path,
    suffix: str = "",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Load the four processed CSV files produced by scripts/preprocess.py.

    Parameters
    ----------
    processed_dir:
        Path to the directory containing the processed CSV files.
    suffix:
        Optional filename suffix to select a dataset variant, e.g.
        "_minimal_no_lowexpr_no_log2". Empty string loads the default
        full-pipeline files (X_train.csv, X_test.csv, etc.).

    Returns
    -------
    X_train, X_test:
        Feature matrices (samples × genes).
        Row index is the case_id; columns are gene_ids.
    y_train, y_test:
        CMS label Series (index=case_id, values in {CMS1, CMS2, CMS3, CMS4}).
    """
    logger.info("Loading processed data from %s (suffix=%r)", processed_dir, suffix or "none")

    X_train = pd.read_csv(processed_dir / f"X_train{suffix}.csv", index_col=0)
    X_test = pd.read_csv(processed_dir / f"X_test{suffix}.csv", index_col=0)

    # y files are saved as single-column DataFrames; squeeze to Series
    y_train = pd.read_csv(processed_dir / f"y_train{suffix}.csv", index_col=0).squeeze("columns")
    y_test = pd.read_csv(processed_dir / f"y_test{suffix}.csv", index_col=0).squeeze("columns")

    logger.info(
        "Loaded — X_train: %s, X_test: %s, y_train: %s, y_test: %s",
        X_train.shape,
        X_test.shape,
        y_train.shape,
        y_test.shape,
    )
    return X_train, X_test, y_train, y_test


# ── Training functions ────────────────────────────────────────────────────────

def train_logistic_regression(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    class_weight: str | None = CLASS_WEIGHT,
) -> LogisticRegression:
    """Fit a Logistic Regression classifier.

    Uses the saga solver with L2 regularisation and class balancing.
    saga is implemented in sklearn's own Cython code: its randomness is
    fully controlled by random_state (one sample drawn per update step),
    and its core arithmetic does not delegate large matrix products to
    BLAS. lbfgs was discarded because it calls BLAS routines whose
    floating-point accumulation order differs between OpenBLAS (Linux)
    and MKL (Windows), producing divergent results despite identical seeds.
    max_iter is set to 5000 because the default (100) rarely converges
    on datasets with thousands of features.

    Parameters
    ----------
    X_train:
        Feature matrix (samples × genes, log2-transformed).
    y_train:
        CMS class labels aligned with X_train rows.
    class_weight:
        Passed directly to LogisticRegression. Use 'balanced' (default)
        for production models or None to train an unbalanced variant.

    Returns
    -------
    Fitted LogisticRegression estimator.
    """
    model = LogisticRegression(
        solver=LR_SOLVER,
        max_iter=LR_MAX_ITER,
        class_weight=class_weight,
        random_state=RANDOM_SEED,
    )
    model.fit(X_train, y_train)
    return model


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    class_weight: str | None = CLASS_WEIGHT,
) -> RandomForestClassifier:
    """Fit a Random Forest classifier.

    Uses sqrt(n_features) as the number of features considered at each
    split, which is the standard recommendation for classification tasks.
    n_jobs=-1 parallelises tree building across all CPU cores; the result
    is deterministic because random_state is fixed.

    Parameters
    ----------
    X_train:
        Feature matrix (samples × genes, log2-transformed).
    y_train:
        CMS class labels aligned with X_train rows.
    class_weight:
        Passed directly to RandomForestClassifier. Use 'balanced' (default)
        for production models or None to train an unbalanced variant.

    Returns
    -------
    Fitted RandomForestClassifier estimator.
    """
    model = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        max_features=RF_MAX_FEATURES,
        class_weight=class_weight,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def train_svm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    class_weight: str | None = CLASS_WEIGHT,
) -> SVC:
    """Fit a linear Support Vector Machine classifier.

    A linear kernel is chosen because it performs well in high-dimensional
    feature spaces (15,625 genes >> 296 samples). probability=True enables
    Platt scaling so that predict_proba is available for ROC curve analysis
    in the evaluation stage.

    Parameters
    ----------
    X_train:
        Feature matrix (samples × genes, log2-transformed).
    y_train:
        CMS class labels aligned with X_train rows.
    class_weight:
        Passed directly to SVC. Use 'balanced' (default) for production
        models or None to train an unbalanced variant.

    Returns
    -------
    Fitted SVC estimator.
    """
    model = SVC(
        kernel=SVM_KERNEL,
        max_iter=SVM_MAX_ITER,
        probability=SVM_PROBABILITY,
        class_weight=class_weight,
        random_state=RANDOM_SEED,
    )
    model.fit(X_train, y_train)
    return model


# ── Orchestration ─────────────────────────────────────────────────────────────

def train_all_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    class_weight: str | None = CLASS_WEIGHT,
) -> tuple[dict[str, BaseEstimator], dict[str, Any]]:
    """Train all three classifiers and return them with timing metadata.

    Each model is trained independently on the same X_train and y_train,
    ensuring a fair comparison in the evaluation stage.

    Parameters
    ----------
    X_train:
        Feature matrix (samples × genes, log2-transformed).
    y_train:
        CMS class labels aligned with X_train rows.
    class_weight:
        Passed to all three classifiers. Use 'balanced' (default) for
        production models or None to train unbalanced variants.

    Returns
    -------
    models:
        Dictionary mapping model name to fitted estimator:
        ``{"logistic_regression": ..., "random_forest": ..., "svm": ...}``.
    timings:
        Dictionary mapping model name to elapsed training time in seconds.
    """
    trainers = {
        "logistic_regression": train_logistic_regression,
        "random_forest": train_random_forest,
        "svm": train_svm,
    }

    models: dict[str, BaseEstimator] = {}
    timings: dict[str, float] = {}

    for name, trainer in trainers.items():
        logger.info("Training %s ...", name)
        t0 = time.perf_counter()
        model = trainer(X_train, y_train, class_weight=class_weight)
        elapsed = time.perf_counter() - t0
        models[name] = model
        timings[name] = elapsed
        logger.info("  %s trained in %.1f s", name, elapsed)

    return models, timings


# ── Persistence ───────────────────────────────────────────────────────────────

def save_model(model: BaseEstimator, output_path: Path) -> None:
    """Persist a fitted sklearn estimator to disk using joblib.

    Parameters
    ----------
    model:
        Any fitted sklearn estimator.
    output_path:
        Full path for the .joblib file.
        Parent directories are created automatically if they do not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output_path)
    logger.info("Model saved to %s", output_path)
