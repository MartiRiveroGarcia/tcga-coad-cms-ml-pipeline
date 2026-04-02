"""Dimensionality reduction and visualisation utilities for TCGA-COAD RNA-seq data.

This module provides functions to:
- Fit and apply PCA on training data
- Plot explained variance (scree plot)
- Scatter plots of principal components coloured by CMS label
- UMAP projection for non-linear visualisation

Design contract
---------------
All functions that *fit* a model (PCA, UMAP) receive only training data.
Test data is always *transformed* using the model fitted on train — never
fitted separately — to avoid data leakage.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

# CMS colour palette — consistent across all plots in the project
CMS_PALETTE: dict[str, str] = {
    "CMS1": "#E41A1C",  # Red
    "CMS2": "#377EB8",  # Blue
    "CMS3": "#4DAF4A",  # Green
    "CMS4": "#FF7F00",  # Orange
}


# ── PCA ───────────────────────────────────────────────────────────────────────

def fit_pca(X_train: pd.DataFrame, n_components: int = 50) -> PCA:
    """Fit PCA on training data.

    Parameters
    ----------
    X_train:
        Expression matrix, samples as rows and genes as columns.
        Must already be log2-transformed and filtered.
    n_components:
        Number of principal components to compute.
        50 is a reasonable upper bound for RNA-seq data.

    Returns
    -------
    Fitted sklearn PCA object.
    """
    pca = PCA(n_components=n_components, random_state=42)
    pca.fit(X_train)
    return pca


def apply_pca(pca: PCA, X: pd.DataFrame) -> pd.DataFrame:
    """Project samples into PCA space using a previously fitted model.

    Parameters
    ----------
    pca:
        PCA object fitted on training data.
    X:
        Expression matrix to project (train or test).

    Returns
    -------
    DataFrame with shape (n_samples, n_components),
    columns named PC1, PC2, ..., PCn.
    """
    components = pca.transform(X)
    column_names = [f"PC{i + 1}" for i in range(components.shape[1])]
    return pd.DataFrame(components, index=X.index, columns=column_names)


# ── Plots ─────────────────────────────────────────────────────────────────────

def plot_explained_variance(
    pca: PCA,
    n_components: int = 30,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Scree plot: variance explained by each principal component.

    Shows both individual (bars) and cumulative (line) explained variance.
    Useful to decide how many components capture most of the signal.

    Parameters
    ----------
    pca:
        Fitted PCA object.
    n_components:
        How many components to display (default: 30).
    output_path:
        If provided, saves the figure to this path.

    Returns
    -------
    matplotlib Figure.
    """
    n = min(n_components, pca.n_components_)
    individual = pca.explained_variance_ratio_[:n] * 100
    cumulative = np.cumsum(individual)

    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Bars: individual variance per component
    ax1.bar(range(1, n + 1), individual, color="#377EB8", alpha=0.7, label="Individual")
    ax1.set_xlabel("Principal component")
    ax1.set_ylabel("Explained variance (%)", color="#377EB8")
    ax1.tick_params(axis="y", labelcolor="#377EB8")

    # Line: cumulative variance
    ax2 = ax1.twinx()
    ax2.plot(range(1, n + 1), cumulative, color="#E41A1C", marker="o",
             markersize=3, linewidth=2, label="Cumulative")
    ax2.set_ylabel("Cumulative explained variance (%)", color="#E41A1C")
    ax2.tick_params(axis="y", labelcolor="#E41A1C")
    ax2.axhline(80, color="#E41A1C", linestyle="--", alpha=0.4, label="80% threshold")

    ax1.set_title("PCA — Explained variance per component")
    fig.tight_layout()

    if output_path is not None:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


def plot_pca_scatter(
    pca_coords: pd.DataFrame,
    labels: pd.Series,
    pc_x: int = 1,
    pc_y: int = 2,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Scatter plot of two principal components coloured by CMS subtype.

    Parameters
    ----------
    pca_coords:
        DataFrame returned by apply_pca() (columns PC1, PC2, ...).
    labels:
        Series with CMS label for each sample, aligned with pca_coords index.
    pc_x, pc_y:
        Which principal components to plot on each axis (1-indexed).
    output_path:
        If provided, saves the figure.

    Returns
    -------
    matplotlib Figure.
    """
    col_x = f"PC{pc_x}"
    col_y = f"PC{pc_y}"

    fig, ax = plt.subplots(figsize=(8, 6))

    for cms, colour in CMS_PALETTE.items():
        mask = labels == cms
        ax.scatter(
            pca_coords.loc[mask, col_x],
            pca_coords.loc[mask, col_y],
            c=colour,
            label=cms,
            alpha=0.7,
            s=40,
            edgecolors="white",
            linewidths=0.3,
        )

    ax.set_xlabel(col_x)
    ax.set_ylabel(col_y)
    ax.set_title(f"PCA — {col_x} vs {col_y} coloured by CMS subtype")
    ax.legend(title="CMS subtype", bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()

    if output_path is not None:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


def plot_top_genes(
    pca: PCA,
    gene_names: pd.DataFrame,
    component: int = 1,
    top_n: int = 20,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """Bar plot of the genes with the highest absolute loading on a component.

    A gene's *loading* on a component measures how much it contributes to that
    direction of variance. High-loading genes are biologically informative.

    Parameters
    ----------
    pca:
        Fitted PCA object.
    gene_names:
        DataFrame with columns gene_id and gene_name.
    component:
        Which PC to inspect (1-indexed).
    top_n:
        Number of top genes to display.
    output_path:
        If provided, saves the figure.

    Returns
    -------
    matplotlib Figure.
    """
    loadings = pca.components_[component - 1]  # shape: (n_genes,)
    top_idx = np.argsort(np.abs(loadings))[::-1][:top_n]

    # Map gene indices to names
    id_to_name = dict(zip(gene_names["gene_id"], gene_names["gene_name"]))
    gene_ids = list(gene_names["gene_id"])

    top_ids = [gene_ids[i] for i in top_idx]
    top_names = [id_to_name.get(g, g) for g in top_ids]
    top_loadings = loadings[top_idx]

    colours = ["#E41A1C" if v > 0 else "#377EB8" for v in top_loadings]

    fig, ax = plt.subplots(figsize=(8, top_n * 0.35 + 1))
    ax.barh(range(top_n), top_loadings[::-1], color=colours[::-1])
    ax.set_yticks(range(top_n))
    ax.set_yticklabels(top_names[::-1], fontsize=8)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel(f"Loading on PC{component}")
    ax.set_title(f"Top {top_n} genes by absolute loading on PC{component}")
    fig.tight_layout()

    if output_path is not None:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


# ── UMAP ──────────────────────────────────────────────────────────────────────

def plot_umap_scatter(
    X: pd.DataFrame,
    labels: pd.Series,
    n_neighbors: int = 30,
    min_dist: float = 0.3,
    random_state: int = 42,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """UMAP projection of samples coloured by CMS subtype.

    UMAP (Uniform Manifold Approximation and Projection) is a non-linear
    dimensionality reduction algorithm. Unlike PCA, it can preserve local
    neighbourhood structure, making it better for visualising clusters.

    This function fits UMAP directly on the provided data (no separate
    train/test split needed for visualisation purposes).

    Parameters
    ----------
    X:
        Expression matrix (samples as rows).
    labels:
        CMS labels aligned with X index.
    n_neighbors:
        Controls how UMAP balances local vs global structure.
        Higher = more global, lower = more local.
    min_dist:
        Minimum distance between points in 2D space.
        Lower = tighter clusters.
    random_state:
        Seed for reproducibility.
    output_path:
        If provided, saves the figure.

    Returns
    -------
    matplotlib Figure.
    """
    try:
        import umap  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "umap-learn is required for UMAP plots. "
            "Install with: pip install umap-learn"
        ) from exc

    reducer = umap.UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state,
        n_components=2,
    )
    embedding = reducer.fit_transform(X.values)

    fig, ax = plt.subplots(figsize=(8, 6))
    for cms, colour in CMS_PALETTE.items():
        mask = labels.values == cms
        ax.scatter(
            embedding[mask, 0],
            embedding[mask, 1],
            c=colour,
            label=cms,
            alpha=0.7,
            s=40,
            edgecolors="white",
            linewidths=0.3,
        )

    ax.set_xlabel("UMAP 1")
    ax.set_ylabel("UMAP 2")
    ax.set_title("UMAP projection coloured by CMS subtype")
    ax.legend(title="CMS subtype", bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()

    if output_path is not None:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig
