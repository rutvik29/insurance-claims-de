# Insurance Claims Data Engineering Pipeline

A production-grade, end-to-end data engineering pipeline for insurance claims data. Built as a personal portfolio project to demonstrate real-world ETL, data quality, and analytics engineering skills.

## Overview

This project simulates a complete insurance claims data platform — from raw data ingestion through to a clean analytical warehouse and interactive dashboard. It demonstrates core data engineering competencies: ETL pipeline design, data profiling, data cleansing, dimensional modelling, orchestration, and observability.

## Tech Stack

| Layer | Tools |
|---|---|
| Data Generation | Python, Faker |
| ETL & Transformation | Pandas, NumPy, PySpark-compatible patterns |
| Orchestration | Apache Airflow (DAG provided) |
| Data Warehouse | SQLite via SQLAlchemy |
| Dashboard | Streamlit, Plotly Express |
| Testing | pytest |
| Config | YAML, python-dotenv |

## Architecture

```
Raw CSVs (data/raw/)
    ↓  [Data Profiling]
Staging Layer (data/staging/)
    ↓  [Cleaning + Transformation]
Warehouse Layer (data/warehouse/insurance_claims.db)
    ↓  [Streamlit Dashboard]
Interactive Analytics (localhost:8501)
```

## Pipeline Steps

1. **Generate** — Synthetic customers, policies, and claims data (2,000 / 3,000 / 10,000 rows) with realistic quality issues: ~8% nulls, ~3% duplicates, inconsistent date formats, outliers, invalid emails
2. **Profile** — Statistical profiling: null rates, cardinality, referential integrity, numeric distributions
3. **Clean** — Deduplication, null imputation (median/mode), IQR outlier capping, date standardisation, email validation, province normalisation
4. **Transform** — Denormalised analytical table + dimensional model (fact_claims, dim_customer, dim_policy) + business aggregations
5. **Load** — Chunked writes to SQLite via SQLAlchemy with upsert logic
6. **Validate** — Post-load data quality checks with summary report

## Project Structure

```
insurance-claims-de/
├── data/
│   ├── raw/              # Generated source CSVs
│   ├── staging/          # Profiled + cleaned CSVs
│   └── warehouse/        # SQLite DB + pipeline report
├── src/
│   ├── generate_data.py  # Synthetic data generation
│   ├── profiler.py       # DataProfiler class
│   ├── cleaner.py        # DataCleaner class
│   ├── transformer.py    # DataTransformer class
│   ├── loader.py         # DataLoader (SQLAlchemy)
│   └── utils.py          # Shared utilities
├── pipeline/
│   ├── etl_pipeline.py   # End-to-end orchestrator
│   └── airflow_dag.py    # Airflow DAG (@daily)
├── sql/
│   ├── create_tables.sql # DDL with indexes
│   ├── create_views.sql  # Analytical views
│   └── analytical_queries.sql
├── tests/                # pytest suite
├── docs/                 # Architecture, data dictionary, runbook
├── dashboard.py          # Streamlit dashboard
└── config/config.yaml
```

## Quick Start

```bash
# Clone the repo
git clone https://github.com/rutvik29/insurance-claims-de.git
cd insurance-claims-de

# Install dependencies
pip install -r requirements.txt

# Run the full ETL pipeline
python pipeline/etl_pipeline.py

# Launch the dashboard
streamlit run dashboard.py
```

## Dashboard

The Streamlit dashboard connects directly to the SQLite warehouse and provides:
- KPI cards: total claims, total amount, fraud rate, avg settlement days
- Interactive filters: date range, claim type, province, fraud toggle
- Charts: claims by type, monthly volume trend, fraud by province, status breakdown, amount distribution
- Paginated data table
- Pipeline execution report

## Running Tests

```bash
pytest tests/ -v --tb=short
```

## Key Design Decisions

- **Medallion architecture** — raw → staging → warehouse mirrors production lakehouse patterns
- **Modular, class-based code** — each pipeline step is a reusable class with a clean interface
- **Observability built in** — every step logs row counts in/out, elapsed time, and transformation counts
- **Airflow-ready** — the pipeline is fully encapsulated so each step can be wrapped in a PythonOperator with minimal changes
- **SQLite for portability** — the warehouse layer uses SQLAlchemy ORM so swapping to PostgreSQL or BigQuery requires only a connection string change

## Author

Rutvik Trivedi — [LinkedIn](https://linkedin.com/in/rutviktrivedi29) | [GitHub](https://github.com/rutvik29)
