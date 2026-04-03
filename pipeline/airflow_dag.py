"""
Airflow DAG definition for the Insurance Claims ETL pipeline.

Schedule: daily
DAG ID:   insurance_claims_etl
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path so Airflow workers can import src/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except ImportError:
    # Airflow is optional; provide stubs so the module is importable without it
    DAG = None  # type: ignore
    PythonOperator = None  # type: ignore


# ---------------------------------------------------------------------------
# Task callables
# ---------------------------------------------------------------------------

def _generate_data(**kwargs) -> None:
    from src.utils import load_config
    from src.generate_data import generate_customers, generate_policies, generate_claims, save_raw_data
    cfg = load_config()
    customers = generate_customers(2000)
    policies = generate_policies(customers, 3000)
    claims = generate_claims(policies, customers, 10000)
    save_raw_data(customers, policies, claims, cfg["data"]["raw_dir"])


def _profile_data(**kwargs) -> None:
    import pandas as pd
    from src.utils import load_config
    from src.profiler import DataProfiler
    cfg = load_config()
    raw = cfg["data"]["raw_dir"]
    staging = cfg["data"]["staging_dir"]
    customers = pd.read_csv(f"{raw}/customers.csv")
    policies = pd.read_csv(f"{raw}/policies.csv")
    claims = pd.read_csv(f"{raw}/claims.csv")
    profiler = DataProfiler()
    profiler.profile(customers, "customers_raw")
    profiler.profile(policies, "policies_raw")
    profiler.profile(claims, "claims_raw")
    profiler.save_report(f"{staging}/profile_report.json")


def _clean_data(**kwargs) -> None:
    import pandas as pd
    from src.utils import load_config
    from src.cleaner import DataCleaner
    cfg = load_config()
    raw = cfg["data"]["raw_dir"]
    staging = cfg["data"]["staging_dir"]
    customers = pd.read_csv(f"{raw}/customers.csv")
    policies = pd.read_csv(f"{raw}/policies.csv")
    claims = pd.read_csv(f"{raw}/claims.csv")
    cleaner = DataCleaner(iqr_factor=cfg["pipeline"]["outlier_iqr_factor"])
    c_customers = cleaner.clean_customers(customers)
    c_policies = cleaner.clean_policies(policies)
    c_claims = cleaner.clean_claims(claims)
    c_customers.to_csv(f"{staging}/customers_clean.csv", index=False)
    c_policies.to_csv(f"{staging}/policies_clean.csv", index=False)
    c_claims.to_csv(f"{staging}/claims_clean.csv", index=False)


def _transform_data(**kwargs) -> None:
    import pandas as pd
    from src.utils import load_config
    from src.transformer import DataTransformer
    cfg = load_config()
    staging = cfg["data"]["staging_dir"]
    customers = pd.read_csv(f"{staging}/customers_clean.csv")
    policies = pd.read_csv(f"{staging}/policies_clean.csv")
    claims = pd.read_csv(f"{staging}/claims_clean.csv")
    transformer = DataTransformer()
    analytical = transformer.join_all(customers, policies, claims)
    analytical.to_csv(f"{staging}/analytical.csv", index=False)


def _load_warehouse(**kwargs) -> None:
    import pandas as pd
    from src.utils import load_config, get_engine
    from src.loader import DataLoader
    from src.transformer import DataTransformer
    cfg = load_config()
    staging = cfg["data"]["staging_dir"]
    customers = pd.read_csv(f"{staging}/customers_clean.csv")
    policies = pd.read_csv(f"{staging}/policies_clean.csv")
    claims = pd.read_csv(f"{staging}/claims_clean.csv")
    transformer = DataTransformer()
    analytical = transformer.join_all(customers, policies, claims)
    tables = {
        "dim_customer": transformer.build_dim_customer(analytical),
        "dim_policy": transformer.build_dim_policy(analytical),
        "fact_claims": transformer.build_fact_claims(analytical),
    }
    engine = get_engine(cfg["database"]["path"])
    loader = DataLoader(engine, chunk_size=cfg["pipeline"]["chunk_size"])
    loader.load_all(tables)


def _run_dq_checks(**kwargs) -> None:
    import pandas as pd
    from src.utils import load_config
    cfg = load_config()
    staging = cfg["data"]["staging_dir"]
    fact = pd.read_csv(f"{staging}/claims_clean.csv")
    assert fact["claim_id"].nunique() > 0, "fact_claims is empty"
    assert fact["claim_amount"].isna().sum() == 0, "claim_amount has nulls post-clean"


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

if DAG is not None:
    default_args = {
        "owner": "data_engineering",
        "depends_on_past": False,
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
        "email_on_failure": False,
    }

    with DAG(
        dag_id="insurance_claims_etl",
        default_args=default_args,
        description="Daily ETL pipeline for insurance claims data",
        schedule_interval="@daily",
        start_date=datetime(2024, 1, 1),
        catchup=False,
        tags=["insurance", "etl", "data-engineering"],
    ) as dag:

        t_generate = PythonOperator(task_id="generate_data", python_callable=_generate_data)
        t_profile = PythonOperator(task_id="profile_data", python_callable=_profile_data)
        t_clean = PythonOperator(task_id="clean_data", python_callable=_clean_data)
        t_transform = PythonOperator(task_id="transform_data", python_callable=_transform_data)
        t_load = PythonOperator(task_id="load_warehouse", python_callable=_load_warehouse)
        t_dq = PythonOperator(task_id="run_dq_checks", python_callable=_run_dq_checks)

        t_generate >> t_profile >> t_clean >> t_transform >> t_load >> t_dq
