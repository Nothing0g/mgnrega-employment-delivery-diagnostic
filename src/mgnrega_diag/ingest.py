"""Load canonical CSV/XLSX exports and validate without silently repairing data."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .schema import (
    ALL_METRIC_COLUMNS,
    IDENTIFIER_COLUMNS,
    OPTIONAL_METRIC_COLUMNS,
    REQUIRED_METRIC_COLUMNS,
    TRANSITION_FY_TOKENS,
)


@dataclass
class ValidationResult:
    data: pd.DataFrame
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def normalize_header(name: object) -> str:
    """Normalize typography only; do not guess ambiguous source field names."""
    value = str(name).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def read_source(source: str | Path | BinaryIO, filename: str | None = None) -> pd.DataFrame:
    """Read a local CSV or Excel file. Input files are never downloaded automatically."""
    inferred = filename or (str(source) if isinstance(source, (str, Path)) else "source.csv")
    suffix = Path(inferred).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(source, sep=None, engine="python")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(source)
    raise ValueError(
        "Supported software input formats are .csv, .xlsx and .xls. "
        "This does not establish the government portal's export format."
    )


def canonicalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize case, spaces and punctuation; field meaning must be mapped by the user."""
    data = frame.copy()
    data.columns = [normalize_header(col) for col in data.columns]
    duplicates = data.columns[data.columns.duplicated()].tolist()
    if duplicates:
        raise ValueError(f"Column names collide after normalization: {duplicates}")
    return data


def validate_panel(frame: pd.DataFrame) -> ValidationResult:
    original = frame.copy()
    original.columns = [normalize_header(col) for col in original.columns]
    data = canonicalize_columns(original)
    errors: list[str] = []
    warnings: list[str] = []

    required = IDENTIFIER_COLUMNS + REQUIRED_METRIC_COLUMNS
    missing = [column for column in required if column not in data.columns]
    if missing:
        errors.append(
            "Missing required canonical columns: " + ", ".join(missing)
            + ". Review source headers and map them explicitly; the pipeline will not infer ambiguous fields."
        )
        return ValidationResult(data=data, errors=errors, warnings=warnings)

    for column in OPTIONAL_METRIC_COLUMNS:
        if column not in data.columns:
            data[column] = pd.NA
            warnings.append(f"Optional field '{column}' is not present; related indicators will be unavailable.")

    for key in IDENTIFIER_COLUMNS:
        data[key] = data[key].astype("string").str.strip()
        if data[key].isna().any() or data[key].eq("").any():
            errors.append(f"'{key}' contains blank values.")

    for column in ALL_METRIC_COLUMNS:
        source_values = original[column] if column in original.columns else None
        data[column] = pd.to_numeric(data[column], errors="coerce")
        if source_values is not None:
            bad = source_values.notna() & data[column].isna()
            if bad.any():
                errors.append(f"'{column}' contains {int(bad.sum())} non-numeric nonblank value(s).")
        if data[column].dropna().lt(0).any():
            errors.append(f"'{column}' contains negative values; counts and expenditure must not be negative.")
        missing_count = int(data[column].isna().sum())
        if missing_count:
            level = "Required" if column in REQUIRED_METRIC_COLUMNS else "Optional"
            warnings.append(f"{level} field '{column}' is missing in {missing_count} of {len(data)} row(s); values remain missing and are not imputed.")

    if not data.empty and data.duplicated(IDENTIFIER_COLUMNS, keep=False).any():
        examples = data.loc[data.duplicated(IDENTIFIER_COLUMNS, keep=False), IDENTIFIER_COLUMNS].head(3)
        errors.append(
            "Duplicate state-district-FY keys found; aggregate or disambiguate records before analysis. Examples: "
            + str(examples.to_dict("records"))
        )

    for fy_value in data["fy"].dropna().astype(str):
        if any(token in fy_value for token in TRANSITION_FY_TOKENS):
            warnings.append(
                "FY 2026-27 includes the 1 July 2026 transition from MGNREGA to the VB-G RAM G Act; do not interpret it as a clean MGNREGA year."
            )
            break

    provided = data["households_provided"]
    demanded = data["households_demanded"]
    if (provided > demanded).fillna(False).any():
        warnings.append(
            "Some records report households provided above households demanded. This can reflect revisions, timing or non-aligned source definitions; inspect before interpreting a fulfilment ratio."
        )

    if (data["households_100_days"] > provided).fillna(False).any():
        warnings.append("Some records report 100-day households above households provided; check definitions, coverage and revisions.")

    total = data["persondays_generated"]
    for group_col in ("women_persondays", "sc_persondays", "st_persondays"):
        if (data[group_col] > total).fillna(False).any():
            warnings.append(f"Some records have {group_col} greater than total person-days; check whether source units and periods match.")
    group_sum = data[["sc_persondays", "st_persondays"]].sum(axis=1, min_count=1)
    if (group_sum > total).fillna(False).any():
        warnings.append("SC plus ST person-days exceed total person-days in some records; verify subgroup definitions and units.")

    if data.empty:
        warnings.append("The source file contains no data rows.")
    if data["fy"].nunique(dropna=True) > 1:
        warnings.append("Multiple financial years are present; confirm periods are comparable and that FY keys are consistent.")

    return ValidationResult(data=data, errors=errors, warnings=list(dict.fromkeys(warnings)))
