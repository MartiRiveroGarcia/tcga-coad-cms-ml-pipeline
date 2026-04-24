"""Preprocessing functions for TCGA-COAD RNA-seq expression data.

This module implements the full preprocessing pipeline:
- Load and parse raw STAR-Counts expression files
- Build a unified expression matrix (genes x samples)
- Clean: remove QC rows, filter to protein-coding genes
- Deduplicate samples (FFPE, metastatic, recurrence, duplicates)
- Attach CMS consensus labels (Guinney et al. 2015)
- Stratified train/test split (before any data-dependent transforms)
- Filter low-count genes (fit on train, apply to both)
- Log2(x+1) transformation
- Save processed outputs
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# ── Constants ───────────────────────────────────────────────────────────────
RANDOM_SEED: int = 42
TEST_SIZE: float = 0.2
MIN_COUNT_THRESHOLD: int = 10
MIN_SAMPLE_FRACTION: float = 0.2

# Rows produced by STAR that are alignment metadata, not genes
QC_ROW_PREFIXES: tuple[str, ...] = (
    "N_unmapped",
    "N_multimapping",
    "N_noFeature",
    "N_ambiguous",
)

# Column in cms_labels_public_all.txt that holds the final consensus label
CMS_LABEL_COLUMN: str = "CMS_final_network_plus_RFclassifier_in_nonconsensus_samples"
VALID_CMS_LABELS: frozenset[str] = frozenset({"CMS1", "CMS2", "CMS3", "CMS4"})


# ── Step 0: Load metadata ──────────────────────────────────────────────────

def load_sample_sheet(path: Path) -> pd.DataFrame:
    """Load the GDC sample sheet and normalise column names to snake_case.

    Returns a DataFrame with columns:
        file_id, file_name, data_category, data_type, project_id,
        case_id, sample_id, tissue_type, tumor_descriptor,
        specimen_type, preservation_method
    """
    df = pd.read_csv(path, sep="\t", dtype=str)
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    logger.info("Sample sheet loaded: %d rows from %s", len(df), path.name)
    return df


def load_cms_labels(path: Path) -> pd.DataFrame:
    """Load CMS consensus labels from the Synapse public file.

    Filters to TCGA samples with valid CMS labels (CMS1-4).
    Returns a DataFrame with columns: case_id, cms_label.
    """
    df = pd.read_csv(path, sep="\t", dtype=str)

    # Keep only TCGA rows
    df = df[df["dataset"] == "tcga"].copy()
    logger.info("CMS file: %d TCGA samples total", len(df))

    # Use the final consensus column
    df = df.rename(columns={"sample": "case_id", CMS_LABEL_COLUMN: "cms_label"})
    df = df[["case_id", "cms_label"]]

    # Keep only valid labels (CMS1-4), discard NOLBL and UNK
    before = len(df)
    df = df[df["cms_label"].isin(VALID_CMS_LABELS)].copy()
    logger.info(
        "CMS labels: %d with valid label (dropped %d NOLBL/UNK)",
        len(df),
        before - len(df),
    )
    return df


# ── Step 1: Build expression matrix ────────────────────────────────────────

def load_single_expression_file(file_path: Path) -> tuple[pd.Series, pd.DataFrame]:
    """Read one STAR-Counts TSV and return the unstranded counts + gene info.

    Returns:
        counts: Series indexed by gene_id with unstranded counts.
        gene_info: DataFrame with columns gene_id, gene_name, gene_type.
    """
    df = pd.read_csv(
        file_path,
        sep="\t",
        comment="#",
        usecols=["gene_id", "gene_name", "gene_type", "unstranded"],
        dtype={"gene_id": str, "gene_name": str, "gene_type": str, "unstranded": "Int64"},
    )
    counts = df.set_index("gene_id")["unstranded"]
    gene_info = df[["gene_id", "gene_name", "gene_type"]].copy()
    return counts, gene_info


def build_expression_matrix(
    raw_dir: Path,
    sample_sheet: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a genes-x-samples expression matrix from individual STAR-Counts files.

    Iterates over UUID directories in raw_dir, reads each expression file,
    and concatenates them into a single matrix.

    Returns:
        expression_matrix: DataFrame with gene_id as index, case_id as columns.
        gene_info: DataFrame mapping gene_id -> gene_name, gene_type.
    """
    # Map file_id (UUID directory name) -> case_id
    file_to_case = dict(zip(sample_sheet["file_id"], sample_sheet["case_id"]))

    all_counts: dict[str, pd.Series] = {}
    gene_info: pd.DataFrame | None = None
    uuid_dirs = sorted(raw_dir.iterdir())

    for i, uuid_dir in enumerate(uuid_dirs):
        if not uuid_dir.is_dir():
            continue

        # Find the .tsv expression file inside the UUID directory
        tsv_files = list(uuid_dir.glob("*.rna_seq.augmented_star_gene_counts.tsv"))
        if not tsv_files:
            logger.warning("No expression file in %s, skipping", uuid_dir.name)
            continue

        file_id = uuid_dir.name
        case_id = file_to_case.get(file_id)
        if case_id is None:
            logger.warning("UUID %s not in sample sheet, skipping", file_id)
            continue

        counts, gi = load_single_expression_file(tsv_files[0])

        # Use file_id as column key (case_id may have duplicates at this stage)
        all_counts[file_id] = counts

        if gene_info is None:
            gene_info = gi

        if (i + 1) % 50 == 0:
            logger.info("Loaded %d / %d files...", i + 1, len(uuid_dirs))

    expression_matrix = pd.DataFrame(all_counts)
    logger.info(
        "Expression matrix built: %d genes x %d files",
        expression_matrix.shape[0],
        expression_matrix.shape[1],
    )
    assert gene_info is not None, "No expression files found"
    return expression_matrix, gene_info


# ── Step 2: Remove QC rows ─────────────────────────────────────────────────

def remove_qc_rows(expression_matrix: pd.DataFrame) -> pd.DataFrame:
    """Remove STAR alignment QC rows (N_unmapped, N_multimapping, etc.)."""
    qc_mask = expression_matrix.index.isin(QC_ROW_PREFIXES)
    n_removed = qc_mask.sum()
    result = expression_matrix[~qc_mask]
    logger.info("Removed %d QC rows (N_unmapped, etc.)", n_removed)
    return result


# ── Step 3: Filter protein-coding genes ─────────────────────────────────────

def filter_protein_coding(
    expression_matrix: pd.DataFrame,
    gene_info: pd.DataFrame,
) -> pd.DataFrame:
    """Keep only protein-coding genes based on GENCODE annotation."""
    protein_coding_ids = gene_info.loc[
        gene_info["gene_type"] == "protein_coding", "gene_id"
    ]
    before = expression_matrix.shape[0]
    result = expression_matrix.loc[
        expression_matrix.index.isin(protein_coding_ids)
    ]
    logger.info(
        "Protein-coding filter: %d -> %d genes (removed %d)",
        before,
        result.shape[0],
        before - result.shape[0],
    )
    return result


# ── Step 4: Deduplicate samples ─────────────────────────────────────────────

def deduplicate_samples(
    expression_matrix: pd.DataFrame,
    sample_sheet: pd.DataFrame,
) -> pd.DataFrame:
    """Remove FFPE, metastatic, recurrence samples and resolve duplicates.

    Deduplication strategy:
    1. Remove FFPE samples (preservation_method == "FFPE")
    2. Remove non-primary samples (tumor_descriptor != "Primary")
    3. For patients with multiple remaining files, keep the one
       with the highest total count (more sequencing depth).

    After deduplication, columns are renamed from file_id to case_id.
    """
    file_to_case = dict(zip(sample_sheet["file_id"], sample_sheet["case_id"]))
    current_files = set(expression_matrix.columns)

    # 1. Remove FFPE
    ffpe_files = set(
        sample_sheet.loc[sample_sheet["preservation_method"] == "FFPE", "file_id"]
    )
    ffpe_to_remove = ffpe_files & current_files
    logger.info("FFPE samples removed: %d", len(ffpe_to_remove))

    # 2. Remove non-primary (metastatic, recurrence)
    non_primary_files = set(
        sample_sheet.loc[sample_sheet["tumor_descriptor"] != "Primary", "file_id"]
    )
    non_primary_to_remove = non_primary_files & current_files
    logger.info("Non-primary samples removed: %d", len(non_primary_to_remove))

    # Apply removals
    to_remove = ffpe_to_remove | non_primary_to_remove
    result = expression_matrix.drop(columns=to_remove, errors="ignore")

    # 3. Resolve remaining duplicates (same case_id, multiple files)
    # Map remaining file_ids to case_ids
    remaining_file_to_case: dict[str, str] = {}
    for file_id in result.columns:
        case_id = file_to_case.get(file_id, file_id)
        remaining_file_to_case[file_id] = case_id

    # Find case_ids with multiple files
    case_to_files: dict[str, list[str]] = {}
    for file_id, case_id in remaining_file_to_case.items():
        case_to_files.setdefault(case_id, []).append(file_id)

    duplicates_resolved = 0
    files_to_drop: list[str] = []
    for case_id, file_ids in case_to_files.items():
        if len(file_ids) <= 1:
            continue
        # Keep the file with highest total count (most sequencing depth)
        total_counts = {fid: result[fid].sum() for fid in file_ids}
        best_file = max(total_counts, key=total_counts.get)  # type: ignore[arg-type]
        for fid in file_ids:
            if fid != best_file:
                files_to_drop.append(fid)
                duplicates_resolved += 1

    result = result.drop(columns=files_to_drop, errors="ignore")
    logger.info("Duplicate files resolved: %d (kept highest depth)", duplicates_resolved)

    # Rename columns from file_id to case_id
    result.columns = [file_to_case.get(fid, fid) for fid in result.columns]

    logger.info("After deduplication: %d samples", result.shape[1])
    return result


# ── Step 5: Attach CMS labels ──────────────────────────────────────────────

def attach_labels(
    expression_matrix: pd.DataFrame,
    cms_labels: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Inner-join expression matrix with CMS labels on case_id.

    Returns:
        filtered_matrix: Expression matrix with only labeled samples.
        labels: Series mapping case_id -> cms_label.
    """
    # expression_matrix has case_ids as columns; transpose for easy join
    labeled_cases = set(cms_labels["case_id"])
    matching_columns = [c for c in expression_matrix.columns if c in labeled_cases]

    before = expression_matrix.shape[1]
    filtered_matrix = expression_matrix[matching_columns]

    # Build labels series aligned with matrix columns
    label_map = dict(zip(cms_labels["case_id"], cms_labels["cms_label"]))
    labels = pd.Series(
        {case_id: label_map[case_id] for case_id in filtered_matrix.columns},
        name="cms_label",
    )

    logger.info(
        "CMS label join: %d -> %d samples (dropped %d without label)",
        before,
        len(matching_columns),
        before - len(matching_columns),
    )
    logger.info("CMS distribution: %s", labels.value_counts().to_dict())
    return filtered_matrix, labels


# ── Step 6: Train/test split ───────────────────────────────────────────────

def split_train_test(
    expression_matrix: pd.DataFrame,
    labels: pd.Series,
    test_size: float = TEST_SIZE,
    random_seed: int = RANDOM_SEED,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Stratified train/test split preserving CMS class proportions.

    The expression matrix has genes as rows and samples as columns.
    We transpose to samples-as-rows for sklearn, then transpose back.

    Returns X_train, X_test (genes x samples), y_train, y_test.
    """
    # Transpose: samples as rows for sklearn
    X = expression_matrix.T  # (samples, genes)
    y = labels

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_seed,
        stratify=y,
    )

    logger.info("Train/test split: %d train, %d test (seed=%d)", len(y_train), len(y_test), random_seed)
    logger.info("Train CMS distribution: %s", y_train.value_counts().to_dict())
    logger.info("Test CMS distribution: %s", y_test.value_counts().to_dict())

    # Keep as samples-as-rows (ML convention)
    return X_train, X_test, y_train, y_test


# ── Step 7: Filter low-count genes ─────────────────────────────────────────

def filter_low_count_genes(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    min_count: int = MIN_COUNT_THRESHOLD,
    min_fraction: float = MIN_SAMPLE_FRACTION,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Remove genes with low counts. Fit criteria on train, apply to both.

    A gene is kept if at least `min_fraction` of training samples
    have a count >= `min_count`.

    Returns filtered X_train, X_test, and the list of kept gene IDs.
    """
    # X_train has samples as rows, genes as columns
    n_train = X_train.shape[0]
    min_samples = int(n_train * min_fraction)

    # Count how many training samples meet the threshold per gene
    genes_above_threshold = (X_train >= min_count).sum(axis=0)
    keep_mask = genes_above_threshold >= min_samples
    kept_genes = list(X_train.columns[keep_mask])

    before = X_train.shape[1]
    X_train_filtered = X_train[kept_genes]
    X_test_filtered = X_test[kept_genes]

    # Build per-gene stats for all genes (used by the exploration notebook)
    expression_rate = genes_above_threshold / n_train
    gene_filter_stats = pd.DataFrame({
        "expression_rate": expression_rate,
        "passed_filter": keep_mask,
    })

    logger.info(
        "Low-count gene filter (count>=%d in >=%d%% of train): %d -> %d genes (removed %d)",
        min_count,
        int(min_fraction * 100),
        before,
        len(kept_genes),
        before - len(kept_genes),
    )
    return X_train_filtered, X_test_filtered, kept_genes, gene_filter_stats


# ── Step 8: Log transformation ──────────────────────────────────────────────

def log_transform(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Apply log2(x + 1) transformation to expression counts.

    This is a stateless, deterministic transformation — no parameters
    are fitted on the training set. The +1 avoids log(0) = -inf.
    """
    X_train_log = np.log2(X_train + 1)
    X_test_log = np.log2(X_test + 1)
    logger.info("Log2(x+1) transform applied. Value range: [%.2f, %.2f]",
                X_train_log.min().min(), X_train_log.max().max())
    return X_train_log, X_test_log


# ── Step 9: Save outputs ───────────────────────────────────────────────────

def save_processed_data(
    output_dir: Path,
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    gene_info: pd.DataFrame,
    kept_genes: list[str],
    gene_filter_stats: pd.DataFrame,
    params: dict[str, Any],
) -> None:
    """Save all processed data to CSV files and a JSON log.

    Output files:
        X_train.csv          — samples as rows, genes as columns (log2-transformed)
        X_test.csv           — same format
        y_train.csv          — case_id, cms_label
        y_test.csv           — case_id, cms_label
        gene_names.csv       — gene_id -> gene_name mapping for kept genes
        gene_filter_stats.csv — per-gene expression rate and filter decision
        preprocessing_log.json — full record of parameters and counts
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    X_train.to_csv(output_dir / "X_train.csv")
    X_test.to_csv(output_dir / "X_test.csv")
    y_train.to_csv(output_dir / "y_train.csv", header=True)
    y_test.to_csv(output_dir / "y_test.csv", header=True)

    # Gene names for interpretation (only kept genes)
    gene_names = gene_info[gene_info["gene_id"].isin(kept_genes)][["gene_id", "gene_name"]]
    gene_names.to_csv(output_dir / "gene_names.csv", index=False)

    # Per-gene filter statistics (all protein-coding genes, for notebook exploration)
    gene_filter_stats.to_csv(output_dir / "gene_filter_stats.csv")

    # Preprocessing log
    log_path = output_dir / "preprocessing_log.json"
    log_path.write_text(json.dumps(params, indent=2, ensure_ascii=False))

    logger.info("Saved processed data to %s (%d files)", output_dir, 7)
