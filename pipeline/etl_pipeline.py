"""
End-to-end ETL pipeline for the Insurance Claims Data Engineering project.

Usage:
    python pipeline/etl_pipeline.py
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generate_data import generate_customers, generate_policies, generate_claims, save_raw_data
from src.profiler import DataProfiler
from src.cleaner import DataCleaner
from src.transformer import DataTransformer
from src.loader import DataLoader
from src.utils import setup_logging, load_config, get_engine

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Orchestrates the full generate -> profile -> clean -> transform -> load -> validate flow."""

    def __init__(self, config_path: str = "config/config.yaml") -> None:
        self.config = load_config(config_path)
        setup_logging(self.config["logging"]["level"])
        self.raw_dir = self.config["data"]["raw_dir"]
        self.staging_dir = self.config["data"]["staging_dir"]
        self.warehouse_dir = self.config["data"]["warehouse_dir"]
        self.db_path = self.config["database"]["path"]
        self.chunk_size = self.config["pipeline"]["chunk_size"]
        self.iqr_factor = self.config["pipeline"]["outlier_iqr_factor"]
        self.summary: Dict[str, Any] = {"start_time": datetime.utcnow().isoformat(), "steps": {}}

        for d in [self.raw_dir, self.staging_dir, self.warehouse_dir]:
            Path(d).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def _record_step(self, step: str, rows_in: int, rows_out: int, elapsed: float, extra: Dict = None) -> None:
        self.summary["steps"][step] = {
            "rows_in": rows_in,
            "rows_out": rows_out,
            "elapsed_s": round(elapsed, 2),
            **(extra or {}),
        }
        logger.info("STEP [%s] done -- rows_in=%d rows_out=%d elapsed=%.2fs", step, rows_in, rows_out, elapsed)

    # ------------------------------------------------------------------
    def step_generate(self) -> tuple:
        logger.info("=" * 60)
        logger.info("STEP: generate_data")
        t0 = time.time()
        customers = generate_customers(2000)
        policies = generate_policies(customers, 3000)
        claims = generate_claims(policies, customers, 10000)
        save_raw_data(customers, policies, claims, self.raw_dir)
        elapsed = time.time() - t0
        total_in = 0
        total_out = len(customers) + len(policies) + len(claims)
        self._record_step("generate", total_in, total_out, elapsed)
        return customers, policies, claims

    # ------------------------------------------------------------------
    def step_profile(self, customers, policies, claims) -> DataProfiler:
        logger.info("=" * 60)
        logger.info("STEP: profile_data")
        t0 = time.time()
        profiler = DataProfiler()
        profiler.profile(customers, "customers_raw")
        profiler.profile(policies, "policies_raw")
        profiler.profile(claims, "claims_raw")
        profiler.check_referential_integrity(policies, customers, "customer_id", "customer_id", "policies", "customers")
        profiler.check_referential_integrity(claims, policies, "policy_id", "policy_id", "claims", "policies")
        profiler.save_report(f"{self.staging_dir}/profile_report.json")
        elapsed = time.time() - t0
        total = len(customers) + len(policies) + len(claims)
        self._record_step("profile", total, total, elapsed)
        return profiler

    # ------------------------------------------------------------------
    def step_clean(self, customers, policies, claims) -> tuple:
        logger.info("=" * 60)
        logger.info("STEP: clean_data")
        t0 = time.time()
        cleaner = DataCleaner(iqr_factor=self.iqr_factor)
        c_customers = cleaner.clean_customers(customers)
        c_policies = cleaner.clean_policies(policies)
        c_claims = cleaner.clean_claims(claims)
        # Save staging CSVs
        c_customers.to_csv(f"{self.staging_dir}/customers_clean.csv", index=False)
        c_policies.to_csv(f"{self.staging_dir}/policies_clean.csv", index=False)
        c_claims.to_csv(f"{self.staging_dir}/claims_clean.csv", index=False)
        elapsed = time.time() - t0
        rows_in = len(customers) + len(policies) + len(claims)
        rows_out = len(c_customers) + len(c_policies) + len(c_claims)
        self._record_step("clean", rows_in, rows_out, elapsed)
        return c_customers, c_policies, c_claims

    # ------------------------------------------------------------------
    def step_transform(self, customers, policies, claims) -> dict:
        logger.info("=" * 60)
        logger.info("STEP: transform_data")
        t0 = time.time()
        transformer = DataTransformer()
        analytical = transformer.join_all(customers, policies, claims)
        dim_customer = transformer.build_dim_customer(analytical)
        dim_policy = transformer.build_dim_policy(analytical)
        fact_claims = transformer.build_fact_claims(analytical)
        aggs = transformer.build_aggregations(analytical)
        tables = {
            "analytical": analytical,
            "dim_customer": dim_customer,
            "dim_policy": dim_policy,
            "fact_claims": fact_claims,
            **aggs,
        }
        elapsed = time.time() - t0
        rows_in = len(customers) + len(policies) + len(claims)
        rows_out = sum(len(v) for v in tables.values())
        self._record_step("transform", rows_in, rows_out, elapsed, {"tables_created": list(tables.keys())})
        return tables

    # ------------------------------------------------------------------
    def step_load(self, tables: dict) -> dict:
        logger.info("=" * 60)
        logger.info("STEP: load_warehouse")
        engine = get_engine(self.db_path)
        loader = DataLoader(engine, chunk_size=self.chunk_size)

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                t0 = time.time()
                load_results = loader.load_all(tables)
                elapsed = time.time() - t0
                rows_written = sum(load_results.values())
                self._record_step("load", sum(len(v) for v in tables.values()), rows_written, elapsed, {"tables": load_results})
                return load_results
            except Exception as exc:
                logger.error("Load attempt %d/%d failed: %s", attempt, max_retries, exc)
                if attempt == max_retries:
                    raise
                time.sleep(2)

    # ------------------------------------------------------------------
    def step_validate(self, tables: dict) -> Dict[str, Any]:
        logger.info("=" * 60)
        logger.info("STEP: run_dq_checks")
        t0 = time.time()
        checks: Dict[str, Any] = {}

        fact = tables.get("fact_claims", None)
        if fact is not None:
            checks["fact_claims_nulls"] = int(fact.isnull().sum().sum())
            checks["fact_claims_rows"] = len(fact)
            checks["fraud_flag_rate"] = round(fact["fraud_flag"].mean(), 4) if "fraud_flag" in fact.columns else None
            checks["high_value_claim_pct"] = round(fact["is_high_value_claim"].mean() * 100, 2) if "is_high_value_claim" in fact.columns else None

        dim_cust = tables.get("dim_customer", None)
        if dim_cust is not None:
            checks["dim_customer_rows"] = len(dim_cust)
            checks["customer_id_unique"] = bool(dim_cust["customer_id"].nunique() == len(dim_cust))

        elapsed = time.time() - t0
        self._record_step("validate", 0, 0, elapsed, {"dq_checks": checks})
        logger.info("DQ checks: %s", json.dumps(checks, indent=2))
        return checks

    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """Execute the full pipeline end-to-end."""
        logger.info("*" * 60)
        logger.info("Insurance Claims ETL Pipeline -- START")
        pipeline_start = time.time()

        try:
            customers_raw, policies_raw, claims_raw = self.step_generate()
            self.step_profile(customers_raw, policies_raw, claims_raw)
            customers_clean, policies_clean, claims_clean = self.step_clean(customers_raw, policies_raw, claims_raw)
            tables = self.step_transform(customers_clean, policies_clean, claims_clean)
            self.step_load(tables)
            self.step_validate(tables)
            self.summary["status"] = "SUCCESS"
        except Exception as exc:
            logger.exception("Pipeline failed: %s", exc)
            self.summary["status"] = "FAILED"
            self.summary["error"] = str(exc)

        self.summary["end_time"] = datetime.utcnow().isoformat()
        self.summary["total_elapsed_s"] = round(time.time() - pipeline_start, 2)

        report_path = f"{self.warehouse_dir}/pipeline_report.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w") as fh:
            json.dump(self.summary, fh, indent=2)
        logger.info("Pipeline report saved to %s", report_path)
        logger.info("*" * 60)
        logger.info("Pipeline %s in %.2fs", self.summary["status"], self.summary["total_elapsed_s"])
        return self.summary


if __name__ == "__main__":
    pipeline = ETLPipeline()
    result = pipeline.run()
    sys.exit(0 if result.get("status") == "SUCCESS" else 1)
