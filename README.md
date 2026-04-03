# Insurance Claims Data Engineering Pipeline

A production-grade ETL pipeline demonstrating end-to-end data engineering for insurance claims data. Built for a Deloitte Data Engineer interview portfolio.

## Tech Stack
- **Python 3.10+** -- pandas, SQLAlchemy, Faker, NumPy
- **SQLite** -- portable data warehouse
- **Apache Airflow** -- production scheduling (optional)
- **pytest** -- unit test suite

## Quick Start
```bash
pip install -r requirements.txt
python pipeline/etl_pipeline.py
```

## Project Structure
```
insurance-claims-de/
├── data/
│   ├── raw/          # Generated CSV files
│   ├── staging/      # Cleaned CSVs + profile report
│   └── warehouse/    # SQLite DB + pipeline report
├── src/
│   ├── generate_data.py   # Faker-based data generation
│   ├── profiler.py        # Data quality profiling
│   ├── cleaner.py         # Data cleaning transformations
│   ├── transformer.py     # Dimensional modelling
│   ├── loader.py          # SQLAlchemy-based data loading
│   └── utils.py           # Shared utilities
├── pipeline/
│   ├── etl_pipeline.py    # End-to-end orchestrator
│   └── airflow_dag.py     # Airflow DAG definition
├── sql/
│   ├── create_tables.sql  # DDL
│   ├── create_views.sql   # Analytical views
│   └── analytical_queries.sql  # Business queries
├── tests/                 # pytest test suite
├── docs/                  # Architecture + runbook
└── config/config.yaml     # Pipeline configuration
```

## Pipeline Steps
1. **Generate** -- 2000 customers, 3000 policies, 10000 claims with realistic quality issues
2. **Profile** -- Null rates, duplicates, cardinality, referential integrity
3. **Clean** -- Dedup, impute, date standardise, IQR outlier cap, email validation
4. **Transform** -- Denormalise, derive features, build dimensional model
5. **Load** -- Chunked writes to SQLite via SQLAlchemy
6. **Validate** -- Post-load DQ checks

## Running Tests
```bash
pytest tests/ -v --tb=short
```
