"""Shared pytest fixtures for the insurance claims test suite."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def sample_customers() -> pd.DataFrame:
    """Minimal customers DataFrame with known quality issues."""
    data = {
        "customer_id": ["CUST00001", "CUST00002", "CUST00003", "CUST00001"],  # dup
        "first_name": ["Alice", "Bob", "Carol", None],
        "last_name": ["Smith", "Jones", "White", "Smith"],
        "dob": ["1980-05-14", "15/03/1992", "07-22-1975", "1980-05-14"],
        "gender": ["F", "M", None, "F"],
        "address": ["123 Main St", "456 Oak Ave", None, "123 Main St"],
        "city": ["Toronto", "Vancouver", "Calgary", "Toronto"],
        "province": ["ON", "BC", "AB", "ON"],
        "postal_code": ["M5V 1A1", "V6B 2W9", "T2P 5G4", "M5V 1A1"],
        "email": ["alice@example.com", "notanemail", "carol@test.ca", "alice@example.com"],
        "phone": ["416-555-0101", "604-555-0202", "403-555-0303", "416-555-0101"],
        "signup_date": ["2020-01-15", "2019-06-30", "2021-11-01", "2020-01-15"],
        "risk_score": [0.32, np.nan, 0.75, 0.32],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_policies(sample_customers) -> pd.DataFrame:
    """Minimal policies DataFrame."""
    data = {
        "policy_id": ["POL000001", "POL000002", "POL000003"],
        "customer_id": ["CUST00001", "CUST00002", "CUST00003"],
        "policy_type": ["auto", "home", None],
        "start_date": ["2021-01-01", "01/06/2020", "2022-03-15"],
        "end_date": ["2024-01-01", "2023-06-01", "2025-03-15"],
        "premium_amount": [1200.00, np.nan, 800.00],
        "coverage_amount": [500000.0, 300000.0, 200000.0],
        "deductible": [500.0, 1000.0, 750.0],
        "agent_id": ["AGT001", "AGT002", "AGT001"],
        "status": ["active", "lapsed", "active"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_claims(sample_policies) -> pd.DataFrame:
    """Minimal claims DataFrame with outlier."""
    data = {
        "claim_id": ["CLM0000001", "CLM0000002", "CLM0000003", "CLM0000004"],
        "policy_id": ["POL000001", "POL000001", "POL000002", "POL000003"],
        "customer_id": ["CUST00001", "CUST00001", "CUST00002", "CUST00003"],
        "claim_date": ["2022-05-10", "10/08/2023", "2021-12-01", "2023-07-15"],
        "claim_type": ["collision", "theft", "flood", "fire"],
        "claim_amount": [5000.0, 350000.0, 12000.0, 8000.0],  # 350k outlier
        "status": ["closed", "open", "closed", "pending"],
        "adjuster_id": ["ADJ001", "ADJ002", "ADJ001", "ADJ003"],
        "fraud_flag": [0, 1, 0, 0],
        "settlement_date": ["2022-06-01", None, "2022-01-15", None],
        "description": ["Rear collision", "Vehicle stolen", "Basement flood", "Kitchen fire"],
    }
    return pd.DataFrame(data)
