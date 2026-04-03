"""Tests for DataTransformer."""

import pytest
import pandas as pd
import numpy as np
from src.cleaner import DataCleaner
from src.transformer import DataTransformer


@pytest.fixture
def cleaned_data(sample_customers, sample_policies, sample_claims):
    cleaner = DataCleaner()
    c = cleaner.clean_customers(sample_customers)
    p = cleaner.clean_policies(sample_policies)
    cl = cleaner.clean_claims(sample_claims)
    return c, p, cl


def test_join_all_returns_dataframe(cleaned_data):
    customers, policies, claims = cleaned_data
    transformer = DataTransformer()
    result = transformer.join_all(customers, policies, claims)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == len(claims.drop_duplicates())


def test_join_all_derived_columns(cleaned_data):
    customers, policies, claims = cleaned_data
    transformer = DataTransformer()
    result = transformer.join_all(customers, policies, claims)
    for col in ["claim_age_days", "is_high_value_claim", "customer_tenure_years", "policy_active_flag"]:
        assert col in result.columns, f"Missing derived column: {col}"


def test_is_high_value_claim_flag(cleaned_data):
    customers, policies, claims = cleaned_data
    transformer = DataTransformer()
    result = transformer.join_all(customers, policies, claims)
    # All claims > 50000 should have flag = 1
    mask = result["claim_amount"] > 50000
    assert (result.loc[mask, "is_high_value_claim"] == 1).all()


def test_build_dim_customer(cleaned_data):
    customers, policies, claims = cleaned_data
    transformer = DataTransformer()
    analytical = transformer.join_all(customers, policies, claims)
    dim = transformer.build_dim_customer(analytical)
    assert "customer_id" in dim.columns
    assert dim["customer_id"].nunique() == len(dim)  # PK uniqueness


def test_build_fact_claims(cleaned_data):
    customers, policies, claims = cleaned_data
    transformer = DataTransformer()
    analytical = transformer.join_all(customers, policies, claims)
    fact = transformer.build_fact_claims(analytical)
    assert "claim_id" in fact.columns
    assert fact["claim_id"].nunique() == len(fact)


def test_build_aggregations(cleaned_data):
    customers, policies, claims = cleaned_data
    transformer = DataTransformer()
    analytical = transformer.join_all(customers, policies, claims)
    aggs = transformer.build_aggregations(analytical)
    assert "claims_per_customer" in aggs
    assert "avg_claim_by_type" in aggs
    assert "fraud_rate_by_province" in aggs
