# Pipeline Runbook

## Prerequisites
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the Pipeline
```bash
python pipeline/etl_pipeline.py
```

## Expected Outputs
| Path | Description |
|------|-------------|
| `data/raw/*.csv` | Raw synthetic data |
| `data/staging/profile_report.json` | Data quality profile |
| `data/staging/*_clean.csv` | Cleaned datasets |
| `data/warehouse/insurance_claims.db` | SQLite warehouse |
| `data/warehouse/pipeline_report.json` | Run summary |

## Run Tests
```bash
pytest tests/ -v
```

## Common Issues
| Symptom | Resolution |
|---------|------------|
| `ModuleNotFoundError` | Ensure you ran `pip install -r requirements.txt` |
| `FileNotFoundError: config.yaml` | Run from project root directory |
| SQLite locked | Delete the `.db` file and re-run |

## Airflow Deployment
1. Copy `pipeline/airflow_dag.py` to your Airflow `dags/` folder
2. Set `AIRFLOW_HOME` environment variable
3. Trigger via `airflow dags trigger insurance_claims_etl`
