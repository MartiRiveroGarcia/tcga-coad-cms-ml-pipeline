"""Model training utilities for TCGA-COAD CMS classification.

This module provides functions to load preprocessed data, train three
sklearn classifiers (Logistic Regression, Random Forest, SVM), and
persist the fitted models to disk.

Design contract
---------------
- All models use the same RANDOM_SEED and class_weight='balanced'.
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
LR_SOLVER: str = "lbfgs"
LR_MULTI_CLASS: str = "multinomial"

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
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Load the four processed CSV files produced by scripts/preprocess.py.

    Parameters
    ----------
    processed_dir:
        Path to the directory containing X_train.csv, X_test.csv,
        y_train.csv and y_test.csv.

    Returns
    -------
    X_train, X_test:
        Feature matrices (samples × genes, log2-transformed).
        Row index is the case_id; columns are gene_ids.
    y_train, y_test:
        CMS label Series (index=case_id, values in {CMS1, CMS2, CMS3, CMS4}).
    """
    logger.info("Loading processed data from %s", processed_dir)

    X_train = pd.read_csv(processed_dir / "X_train.csv", index_col=0)
    X_test = pd.read_csv(processed_dir / "X_test.csv", index_col=0)

    # y files are saved as single-column DataFrames; squeeze to Series
    y_train = pd.read_csv(processed_dir / "y_train.csv", index_col=0).squeeze("columns")
    y_test = pd.read_csv(processed_dir / "y_test.csv", index_col=0).squeeze("columns")

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
) -> LogisticRegression:
    """Fit a multinomial Logistic Regression classifier.

    Uses the lbfgs solver with L2 regularisation and class balancing.
    max_iter is set to 5000 because the default (100) rarely converges
    on datasets with thousands of features.

    Parameters
    ----------
    X_train:
        Feature matrix (samples × genes, log2-transformed).
    y_train:
        CMS class labels aligned with X_train rows.

    Returns
    -------
    Fitted LogisticRegression estimator.
    """
    model = LogisticRegression(
        solver=LR_SOLVER,
        multi_class=LR_MULTI_CLASS,
        max_iter=LR_MAX_ITER,
        class_weight=CLASS_WEIGHT,
        random_state=RANDOM_SEED,
    )
    model.fit(X_train, y_train)
    return model


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
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

    Returns
    -------
    Fitted RandomForestClassifier estimator.
    """
    model = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        max_features=RF_MAX_FEATURES,
        class_weight=CLASS_WEIGHT,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def train_svm(
    X_train: pd.DataFrame,
    y_train: pd.Series,
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

    Returns
    -------
    Fitted SVC estimator.
    """
    model = SVC(
        kernel=SVM_KERNEL,
        max_iter=SVM_MAX_ITER,
        probability=SVM_PROBABILITY,
        class_weight=CLASS_WEIGHT,
        random_state=RANDOM_SEED,
    )
    model.fit(X_train, y_train)
    return model


# ── Orchestration ─────────────────────────────────────────────────────────────

def train_all_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
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
        model = trainer(X_train, y_train)
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
