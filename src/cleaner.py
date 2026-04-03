"""Data cleaning transformations for the insurance claims pipeline."""

import logging
import re
from typing import Dict, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Recognised date formats to attempt parsing
_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d", "%m/%d/%Y"]
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
_PROVINCE_MAP = {
    "alberta": "AB",
    "british columbia": "BC",
    "bc": "BC",
    "ontario": "ON",
    "on": "ON",
    "quebec": "QC",
    "qc": "QC",
    "manitoba": "MB",
    "mb": "MB",
    "saskatchewan": "SK",
    "sk": "SK",
    "nova scotia": "NS",
    "ns": "NS",
    "new brunswick": "NB",
    "nb": "NB",
    "newfoundland and labrador": "NL",
    "nl": "NL",
    "prince edward island": "PE",
    "pe": "PE",
    "pei": "PE",
}


def _parse_date_series(series: pd.Series) -> pd.Series:
    """Attempt multi-format date parsing; return ISO 8601 strings."""
    def _parse_single(val):
        if pd.isna(val):
            return np.nan
        val_str = str(val).strip()
        for fmt in _DATE_FORMATS:
            try:
                from datetime import datetime
                return datetime.strptime(val_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return np.nan  # unparseable

    return series.apply(_parse_single)


def _cap_outliers_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """Cap outliers using IQR method."""
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - factor * iqr, q3 + factor * iqr
    capped = series.clip(lower=lower, upper=upper)
    n_capped = int((series < lower).sum() + (series > upper).sum())
    logger.debug("IQR cap [%.2f, %.2f]: %d values capped", lower, upper, n_capped)
    return capped


def _log_step(name: str, before: int, after: int) -> None:
    logger.info("  [%s] rows before=%d  after=%d  delta=%d", name, before, after, before - after)


class DataCleaner:
    """Cleans raw insurance DataFrames, logging every transformation."""

    def __init__(self, iqr_factor: float = 1.5) -> None:
        self.iqr_factor = iqr_factor

    # ------------------------------------------------------------------
    def clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the customers DataFrame."""
        logger.info("=== Cleaning customers (input rows: %d) ===", len(df))
        df = df.copy()

        # 1. Remove duplicates
        before = len(df)
        df = df.drop_duplicates()
        _log_step("drop_duplicates", before, len(df))

        # 2. Standardise dates
        for col in ["dob", "signup_date"]:
            if col in df.columns:
                df[col] = _parse_date_series(df[col])

        # 3. Impute nulls
        for col in df.select_dtypes(include="number").columns:
            median = df[col].median()
            n_filled = int(df[col].isna().sum())
            df[col] = df[col].fillna(median)
            if n_filled:
                logger.info("  [impute_numeric] %s: filled %d nulls with median=%.4f", col, n_filled, median)

        for col in df.select_dtypes(include="object").columns:
            if df[col].isna().any():
                mode_val = df[col].mode(dropna=True)
                fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
                n_filled = int(df[col].isna().sum())
                df[col] = df[col].fillna(fill_val)
                logger.info("  [impute_categorical] %s: filled %d nulls with mode='%s'", col, n_filled, fill_val)

        # 4. Fix emails
        if "email" in df.columns:
            before_email = int((~df["email"].str.match(_EMAIL_RE, na=False)).sum())
            df["email"] = df["email"].apply(
                lambda e: e if isinstance(e, str) and _EMAIL_RE.match(e) else "invalid@placeholder.com"
            )
            logger.info("  [fix_email] replaced %d invalid emails", before_email)

        # 5. Normalise province codes
        if "province" in df.columns:
            df["province"] = df["province"].apply(
                lambda p: _PROVINCE_MAP.get(str(p).strip().lower(), str(p).strip().upper()[:2]) if pd.notna(p) else "XX"
            )

        logger.info("=== customers cleaning done (output rows: %d) ===", len(df))
        return df

    # ------------------------------------------------------------------
    def clean_policies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the policies DataFrame."""
        logger.info("=== Cleaning policies (input rows: %d) ===", len(df))
        df = df.copy()

        before = len(df)
        df = df.drop_duplicates()
        _log_step("drop_duplicates", before, len(df))

        for col in ["start_date", "end_date"]:
            if col in df.columns:
                df[col] = _parse_date_series(df[col])

        for col in df.select_dtypes(include="number").columns:
            median = df[col].median()
            n_filled = int(df[col].isna().sum())
            df[col] = df[col].fillna(median)
            if n_filled:
                logger.info("  [impute_numeric] %s: filled %d nulls with median=%.4f", col, n_filled, median)

        for col in df.select_dtypes(include="object").columns:
            if df[col].isna().any():
                mode_val = df[col].mode(dropna=True)
                fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
                n_filled = int(df[col].isna().sum())
                df[col] = df[col].fillna(fill_val)
                logger.info("  [impute_categorical] %s: filled %d nulls with mode='%s'", col, n_filled, fill_val)

        logger.info("=== policies cleaning done (output rows: %d) ===", len(df))
        return df

    # ------------------------------------------------------------------
    def clean_claims(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean the claims DataFrame."""
        logger.info("=== Cleaning claims (input rows: %d) ===", len(df))
        df = df.copy()

        before = len(df)
        df = df.drop_duplicates()
        _log_step("drop_duplicates", before, len(df))

        for col in ["claim_date", "settlement_date"]:
            if col in df.columns:
                df[col] = _parse_date_series(df[col])

        for col in df.select_dtypes(include="number").columns:
            median = df[col].median()
            n_filled = int(df[col].isna().sum())
            df[col] = df[col].fillna(median)
            if n_filled:
                logger.info("  [impute_numeric] %s: filled %d nulls with median=%.4f", col, n_filled, median)

        # IQR cap on claim_amount
        if "claim_amount" in df.columns:
            before_sum = df["claim_amount"].sum()
            df["claim_amount"] = _cap_outliers_iqr(df["claim_amount"], self.iqr_factor)
            logger.info("  [iqr_cap] claim_amount sum change: %.2f -> %.2f", before_sum, df["claim_amount"].sum())

        for col in df.select_dtypes(include="object").columns:
            if df[col].isna().any():
                mode_val = df[col].mode(dropna=True)
                fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "unknown"
                n_filled = int(df[col].isna().sum())
                df[col] = df[col].fillna(fill_val)
                logger.info("  [impute_categorical] %s: filled %d nulls with mode='%s'", col, n_filled, fill_val)

        logger.info("=== claims cleaning done (output rows: %d) ===", len(df))
        return df
