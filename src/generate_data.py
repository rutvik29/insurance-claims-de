"""Generate synthetic insurance data using Faker with intentional data quality issues."""

import logging
import random
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from faker import Faker

logger = logging.getLogger(__name__)

fake = Faker("en_CA")
random.seed(42)
np.random.seed(42)
Faker.seed(42)

PROVINCES = ["AB", "BC", "MB", "NB", "NL", "NS", "ON", "PE", "QC", "SK"]
POLICY_TYPES = ["auto", "home", "life", "health", "travel"]
CLAIM_TYPES = ["collision", "theft", "fire", "flood", "medical", "liability", "property"]
CLAIM_STATUSES = ["open", "closed", "pending", "denied"]
POLICY_STATUSES = ["active", "lapsed", "cancelled", "expired"]
GENDERS = ["M", "F", "NB", "U"]

# Date format variants to introduce inconsistencies
DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"]


def _random_date_str(start_year: int = 2018, end_year: int = 2024) -> str:
    """Generate a random date string with a random format."""
    d = fake.date_between(start_date=f"-{2024 - start_year + 1}y", end_date="today")
    fmt = random.choice(DATE_FORMATS)
    return d.strftime(fmt)


def _introduce_nulls(df: pd.DataFrame, null_rate: float = 0.08) -> pd.DataFrame:
    """Randomly set ~null_rate fraction of cells to NaN, skipping PK columns."""
    df = df.copy()
    pk_cols = [c for c in df.columns if c.endswith("_id")]
    nullable_cols = [c for c in df.columns if c not in pk_cols]
    total_cells = len(df) * len(nullable_cols)
    n_nulls = int(total_cells * null_rate)
    rows = np.random.randint(0, len(df), n_nulls)
    cols = np.random.randint(0, len(nullable_cols), n_nulls)
    for r, c in zip(rows, cols):
        df.iloc[r, df.columns.get_loc(nullable_cols[c])] = np.nan
    return df


def _introduce_duplicates(df: pd.DataFrame, dup_rate: float = 0.03) -> pd.DataFrame:
    """Append ~dup_rate fraction of rows as duplicates (same data, duplicate rows)."""
    n_dups = int(len(df) * dup_rate)
    dup_rows = df.sample(n=n_dups, replace=True, random_state=42)
    return pd.concat([df, dup_rows], ignore_index=True)


def generate_customers(n: int = 2000) -> pd.DataFrame:
    """Generate synthetic customer data."""
    logger.info("Generating %d customer records ...", n)
    records = []
    for i in range(1, n + 1):
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
        email = fake.email()
        # Corrupt ~5% of emails
        if random.random() < 0.05:
            email = email.replace("@", "").replace(".", "")
        records.append(
            {
                "customer_id": f"CUST{i:05d}",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "dob": dob.strftime(random.choice(DATE_FORMATS)),
                "gender": random.choice(GENDERS),
                "address": fake.street_address(),
                "city": fake.city(),
                "province": random.choice(PROVINCES),
                "postal_code": fake.postcode(),
                "email": email,
                "phone": fake.phone_number(),
                "signup_date": _random_date_str(2015, 2023),
                "risk_score": round(random.uniform(0.0, 1.0), 4),
            }
        )
    df = pd.DataFrame(records)
    df = _introduce_nulls(df, null_rate=0.08)
    df = _introduce_duplicates(df, dup_rate=0.03)
    logger.info("customers shape after quality issues: %s", df.shape)
    return df


def generate_policies(customers_df: pd.DataFrame, n: int = 3000) -> pd.DataFrame:
    """Generate synthetic policy data referencing existing customer IDs."""
    logger.info("Generating %d policy records ...", n)
    cust_ids = customers_df["customer_id"].dropna().unique().tolist()
    records = []
    for i in range(1, n + 1):
        start = fake.date_between(start_date="-6y", end_date="-1y")
        end = fake.date_between(start_date=start, end_date="+3y")
        records.append(
            {
                "policy_id": f"POL{i:06d}",
                "customer_id": random.choice(cust_ids),
                "policy_type": random.choice(POLICY_TYPES),
                "start_date": start.strftime(random.choice(DATE_FORMATS)),
                "end_date": end.strftime(random.choice(DATE_FORMATS)),
                "premium_amount": round(random.uniform(500, 5000), 2),
                "coverage_amount": round(random.uniform(50000, 1000000), 2),
                "deductible": round(random.uniform(250, 5000), 2),
                "agent_id": f"AGT{random.randint(1, 50):03d}",
                "status": random.choice(POLICY_STATUSES),
            }
        )
    df = pd.DataFrame(records)
    df = _introduce_nulls(df, null_rate=0.08)
    df = _introduce_duplicates(df, dup_rate=0.03)
    logger.info("policies shape after quality issues: %s", df.shape)
    return df


def generate_claims(policies_df: pd.DataFrame, customers_df: pd.DataFrame, n: int = 10000) -> pd.DataFrame:
    """Generate synthetic claims data."""
    logger.info("Generating %d claim records ...", n)
    pol_ids = policies_df["policy_id"].dropna().unique().tolist()
    cust_ids = customers_df["customer_id"].dropna().unique().tolist()
    records = []
    for i in range(1, n + 1):
        claim_date = fake.date_between(start_date="-4y", end_date="today")
        settlement_date = fake.date_between(start_date=claim_date, end_date="+1y") if random.random() > 0.3 else None
        # Introduce outliers ~2% of the time
        if random.random() < 0.02:
            claim_amount = round(random.uniform(200000, 500000), 2)
        else:
            claim_amount = round(random.uniform(1000, 80000), 2)
        records.append(
            {
                "claim_id": f"CLM{i:07d}",
                "policy_id": random.choice(pol_ids),
                "customer_id": random.choice(cust_ids),
                "claim_date": claim_date.strftime(random.choice(DATE_FORMATS)),
                "claim_type": random.choice(CLAIM_TYPES),
                "claim_amount": claim_amount,
                "status": random.choice(CLAIM_STATUSES),
                "adjuster_id": f"ADJ{random.randint(1, 30):03d}",
                "fraud_flag": int(random.random() < 0.07),
                "settlement_date": settlement_date.strftime(random.choice(DATE_FORMATS)) if settlement_date else None,
                "description": fake.sentence(nb_words=12),
            }
        )
    df = pd.DataFrame(records)
    df = _introduce_nulls(df, null_rate=0.08)
    df = _introduce_duplicates(df, dup_rate=0.03)
    logger.info("claims shape after quality issues: %s", df.shape)
    return df


def save_raw_data(customers: pd.DataFrame, policies: pd.DataFrame, claims: pd.DataFrame, raw_dir: str = "data/raw") -> None:
    """Persist raw DataFrames to CSV."""
    Path(raw_dir).mkdir(parents=True, exist_ok=True)
    customers.to_csv(f"{raw_dir}/customers.csv", index=False)
    policies.to_csv(f"{raw_dir}/policies.csv", index=False)
    claims.to_csv(f"{raw_dir}/claims.csv", index=False)
    logger.info("Raw data saved to %s", raw_dir)
