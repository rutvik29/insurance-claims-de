"""Data profiling utilities for the insurance claims pipeline."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataProfiler:
    """Profile a DataFrame and produce a structured quality report."""

    def __init__(self) -> None:
        self._report: Dict[str, Any] = {}

    def profile(self, df: pd.DataFrame, name: str) -> Dict[str, Any]:
        """
        Profile a DataFrame.

        Args:
            df: Input DataFrame to profile.
            name: Logical name of the dataset (used as report key).

        Returns:
            Dictionary containing quality metrics.
        """
        logger.info("Profiling dataset '%s' with shape %s", name, df.shape)
        report: Dict[str, Any] = {
            "dataset": name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "duplicate_count": int(df.duplicated().sum()),
            "duplicate_pct": round(df.duplicated().mean() * 100, 2),
            "columns": {},
        }

        for col in df.columns:
            col_report: Dict[str, Any] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_pct": round(df[col].isna().mean() * 100, 2),
                "cardinality": int(df[col].nunique()),
            }

            if pd.api.types.is_numeric_dtype(df[col]):
                series = df[col].dropna()
                if len(series) > 0:
                    col_report.update(
                        {
                            "min": float(series.min()),
                            "max": float(series.max()),
                            "mean": round(float(series.mean()), 4),
                            "std": round(float(series.std()), 4),
                            "p25": float(series.quantile(0.25)),
                            "p75": float(series.quantile(0.75)),
                        }
                    )
            elif pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
                top_vals = df[col].value_counts().head(5).to_dict()
                col_report["top_values"] = {str(k): int(v) for k, v in top_vals.items()}

            report["columns"][col] = col_report

        self._report[name] = report
        logger.info(
            "Profile complete for '%s': %d rows, %d nulls total, %d duplicates",
            name,
            report["row_count"],
            sum(v["null_count"] for v in report["columns"].values()),
            report["duplicate_count"],
        )
        return report

    def check_referential_integrity(
        self,
        child_df: pd.DataFrame,
        parent_df: pd.DataFrame,
        child_key: str,
        parent_key: str,
        child_name: str,
        parent_name: str,
    ) -> Dict[str, Any]:
        """Check foreign key integrity between two DataFrames."""
        child_vals = set(child_df[child_key].dropna().unique())
        parent_vals = set(parent_df[parent_key].dropna().unique())
        orphans = child_vals - parent_vals
        result = {
            "check": f"{child_name}.{child_key} -> {parent_name}.{parent_key}",
            "orphan_count": len(orphans),
            "orphan_pct": round(len(orphans) / max(len(child_vals), 1) * 100, 2),
        }
        self._report.setdefault("referential_integrity", []).append(result)
        logger.info("RI check %s: %d orphan keys (%.1f%%)", result["check"], result["orphan_count"], result["orphan_pct"])
        return result

    def save_report(self, output_path: str) -> None:
        """Persist the accumulated profile report as JSON."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as fh:
            json.dump(self._report, fh, indent=2, default=str)
        logger.info("Profile report saved to %s", output_path)

    @property
    def report(self) -> Dict[str, Any]:
        """Return the full accumulated report."""
        return self._report
