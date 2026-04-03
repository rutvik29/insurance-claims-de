"""Utility functions for the insurance claims data engineering pipeline."""

import logging
import os
from pathlib import Path
from typing import Any, Dict

import yaml
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure root logging with a standard formatter."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load YAML configuration file."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with path.open("r") as fh:
        return yaml.safe_load(fh)


def get_engine(db_path: str) -> Engine:
    """Create and return a SQLAlchemy SQLite engine, ensuring parent dirs exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite:///{db_path}"
    engine = create_engine(url, echo=False)
    return engine
