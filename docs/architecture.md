# Insurance Claims Data Engineering -- Architecture

## Overview
A fully automated ETL pipeline that ingests synthetic insurance data, profiles quality, cleans and transforms it, and loads it into a SQLite data warehouse. Designed to demonstrate production-grade data engineering patterns for a Deloitte interview portfolio.

## Architecture Diagram
```
[generate_data.py]
      |  2000 customers, 3000 policies, 10000 claims (raw CSVs with intentional quality issues)
      v
[profiler.py] -> staging/profile_report.json
      |
      v
[cleaner.py]  -> staging/customers_clean.csv, policies_clean.csv, claims_clean.csv
      |
      v
[transformer.py] -> dim_customer, dim_policy, fact_claims, aggregation tables
      |
      v
[loader.py]   -> SQLite (data/warehouse/insurance_claims.db)
      |
      v
[DQ Checks]   -> warehouse/pipeline_report.json
```

## Components

| Component | Purpose |
|-----------|---------|
| `src/generate_data.py` | Synthetic data generation with realistic quality issues |
| `src/profiler.py` | Automated data quality profiling |
| `src/cleaner.py` | Null imputation, deduplication, outlier capping, date standardisation |
| `src/transformer.py` | Denormalisation, derived columns, dimensional modelling |
| `src/loader.py` | Chunked SQLite loading via SQLAlchemy |
| `pipeline/etl_pipeline.py` | End-to-end orchestrator with retry logic |
| `pipeline/airflow_dag.py` | Airflow DAG for production scheduling |
| `sql/` | DDL, views, and analytical queries |

## Data Flow
1. **Raw Layer** (`data/raw/`) -- CSV files with deliberate quality issues
2. **Staging Layer** (`data/staging/`) -- Cleaned CSVs + profile JSON
3. **Warehouse Layer** (`data/warehouse/`) -- SQLite DB + pipeline report

## Design Decisions
- **SQLite** chosen for portability; swap `get_engine()` in `utils.py` for PostgreSQL/Snowflake
- **IQR outlier capping** (factor=1.5) for claim_amount to prevent skewed aggregations
- **Chunked writes** (1000 rows/batch) to bound memory usage on large datasets
- **Retry logic** (3 attempts) on the load step to handle transient IO errors
