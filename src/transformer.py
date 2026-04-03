"""Data transformation and dimensional modelling for the insurance claims pipeline."""

import logging
from typing import Dict

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataTransformer:
    """Build analytical and dimensional tables from cleaned source DataFrames."""

    # ------------------------------------------------------------------
    def join_all(
        self,
        customers: pd.DataFrame,
        policies: pd.DataFrame,
        claims: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Produce a denormalised analytical table by joining all three sources.

        Args:
            customers: Cleaned customers DataFrame.
            policies:  Cleaned policies DataFrame.
            claims:    Cleaned claims DataFrame.

        Returns:
            Denormalised DataFrame with derived columns.
        """
        logger.info("Joining claims -> policies -> customers ...")
        df = (
            claims
            .merge(policies, on="policy_id", how="left", suffixes=("", "_pol"))
            .merge(customers, on="customer_id", how="left", suffixes=("", "_cust"))
        )
        # Drop duplicate customer_id from policies side if present
        df = df.loc[:, ~df.columns.duplicated()]
        logger.info("Joined shape: %s", df.shape)

        # Derived columns ------------------------------------------------
        today = pd.Timestamp("today").normalize()

        # claim_age_days
        df["claim_age_days"] = (
            pd.to_datetime(df["claim_date"], errors="coerce")
            .rsub(today)
            .dt.days
        )

        # is_high_value_claim
        df["is_high_value_claim"] = (df["claim_amount"] > 50000).astype(int)

        # customer_tenure_years
        df["customer_tenure_years"] = (
            (today - pd.to_datetime(df["signup_date"], errors="coerce")).dt.days / 365.25
        ).round(2)

        # policy_active_flag
        df["policy_active_flag"] = (df["status"] == "active").astype(int)

        logger.info("Derived columns added; final shape: %s", df.shape)
        return df

    # ------------------------------------------------------------------
    def build_dim_customer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract dimension table for customers."""
        cols = [
            "customer_id", "first_name", "last_name", "dob", "gender",
            "address", "city", "province", "postal_code", "email",
            "phone", "signup_date", "risk_score",
        ]
        existing = [c for c in cols if c in df.columns]
        dim = df[existing].drop_duplicates(subset=["customer_id"])
        logger.info("dim_customer: %d rows", len(dim))
        return dim

    # ------------------------------------------------------------------
    def build_dim_policy(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract dimension table for policies."""
        cols = [
            "policy_id", "customer_id", "policy_type", "start_date",
            "end_date", "premium_amount", "coverage_amount",
            "deductible", "agent_id", "status",
        ]
        existing = [c for c in cols if c in df.columns]
        dim = df[existing].drop_duplicates(subset=["policy_id"])
        logger.info("dim_policy: %d rows", len(dim))
        return dim

    # ------------------------------------------------------------------
    def build_fact_claims(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract fact table for claims with derived measures."""
        cols = [
            "claim_id", "policy_id", "customer_id", "claim_date",
            "claim_type", "claim_amount", "status", "adjuster_id",
            "fraud_flag", "settlement_date", "description",
            "claim_age_days", "is_high_value_claim",
        ]
        existing = [c for c in cols if c in df.columns]
        fact = df[existing].drop_duplicates(subset=["claim_id"])
        logger.info("fact_claims: %d rows", len(fact))
        return fact

    # ------------------------------------------------------------------
    def build_aggregations(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Build summary aggregation tables.

        Returns:
            Dictionary with keys: claims_per_customer, avg_claim_by_type,
            fraud_rate_by_province.
        """
        # Claims per customer
        claims_per_customer = (
            df.groupby("customer_id")
            .agg(
                claim_count=("claim_id", "count"),
                total_claim_amount=("claim_amount", "sum"),
                avg_claim_amount=("claim_amount", "mean"),
            )
            .reset_index()
        )

        # Avg claim by type
        avg_claim_by_type = (
            df.groupby("claim_type")
            .agg(
                claim_count=("claim_id", "count"),
                avg_claim_amount=("claim_amount", "mean"),
                median_claim_amount=("claim_amount", "median"),
            )
            .reset_index()
        )

        # Fraud rate by province
        fraud_rate_by_province = (
            df.groupby("province")
            .agg(
                total_claims=("claim_id", "count"),
                fraud_claims=("fraud_flag", "sum"),
            )
            .assign(fraud_rate=lambda x: (x["fraud_claims"] / x["total_claims"]).round(4))
            .reset_index()
        )

        logger.info(
            "Aggregations built: claims_per_customer=%d, avg_claim_by_type=%d, fraud_rate_by_province=%d",
            len(claims_per_customer),
            len(avg_claim_by_type),
            len(fraud_rate_by_province),
        )
        return {
            "claims_per_customer": claims_per_customer,
            "avg_claim_by_type": avg_claim_by_type,
            "fraud_rate_by_province": fraud_rate_by_province,
        }
