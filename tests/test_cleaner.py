"""Tests for DataCleaner."""

import pytest
import pandas as pd
import numpy as np
from src.cleaner import DataCleaner


def test_clean_customers_removes_duplicates(sample_customers):
    cleaner = DataCleaner()
    result = cleaner.clean_customers(sample_customers)
    assert result.duplicated().sum() == 0


def test_clean_customers_no_nulls_after_imputation(sample_customers):
    cleaner = DataCleaner()
    result = cleaner.clean_customers(sample_customers)
    # After imputation risk_score and categoricals should have no nulls
    assert result["risk_score"].isna().sum() == 0


def test_clean_customers_email_fix(sample_customers):
    cleaner = DataCleaner()
    result = cleaner.clean_customers(sample_customers)
    import re
    pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    invalid = result["email"].apply(lambda e: not bool(pattern.match(str(e)))).sum()
    assert invalid == 0, f"{invalid} invalid emails remain after cleaning"


def test_clean_customers_date_standardisation(sample_customers):
    cleaner = DataCleaner()
    result = cleaner.clean_customers(sample_customers)
    # All non-null dates should match ISO format
    import re
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    valid = result["dob"].dropna().apply(lambda d: bool(iso_pattern.match(str(d))))
    assert valid.all(), "Some dob values are not ISO 8601"


def test_clean_policies_imputes_premium(sample_policies):
    cleaner = DataCleaner()
    result = cleaner.clean_policies(sample_policies)
    assert result["premium_amount"].isna().sum() == 0


def test_clean_claims_iqr_capping(sample_claims):
    cleaner = DataCleaner(iqr_factor=1.5)
    result = cleaner.clean_claims(sample_claims)
    # The 350k outlier should be capped
    assert result["claim_amount"].max() < 350000.0


def test_clean_claims_no_nulls_in_claim_amount(sample_claims):
    cleaner = DataCleaner()
    result = cleaner.clean_claims(sample_claims)
    assert result["claim_amount"].isna().sum() == 0
