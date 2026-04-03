"""Tests for DataProfiler."""

import pytest
import pandas as pd
import numpy as np
from src.profiler import DataProfiler


def test_profile_returns_dict(sample_customers):
    profiler = DataProfiler()
    report = profiler.profile(sample_customers, "customers")
    assert isinstance(report, dict)
    assert report["dataset"] == "customers"


def test_profile_row_count(sample_customers):
    profiler = DataProfiler()
    report = profiler.profile(sample_customers, "customers")
    assert report["row_count"] == len(sample_customers)


def test_profile_duplicate_count(sample_customers):
    profiler = DataProfiler()
    report = profiler.profile(sample_customers, "customers")
    assert report["duplicate_count"] == 1  # one duplicate row


def test_profile_null_detection(sample_customers):
    profiler = DataProfiler()
    report = profiler.profile(sample_customers, "customers")
    assert report["columns"]["first_name"]["null_count"] == 1
    assert report["columns"]["risk_score"]["null_count"] == 1


def test_profile_numeric_stats(sample_customers):
    profiler = DataProfiler()
    report = profiler.profile(sample_customers, "customers")
    rs = report["columns"]["risk_score"]
    assert "min" in rs
    assert "max" in rs
    assert "mean" in rs


def test_profile_categorical_top_values(sample_customers):
    profiler = DataProfiler()
    report = profiler.profile(sample_customers, "customers")
    assert "top_values" in report["columns"]["province"]


def test_referential_integrity(sample_customers, sample_policies):
    profiler = DataProfiler()
    result = profiler.check_referential_integrity(
        sample_policies, sample_customers, "customer_id", "customer_id", "policies", "customers"
    )
    assert result["orphan_count"] == 0


def test_save_report(tmp_path, sample_customers):
    profiler = DataProfiler()
    profiler.profile(sample_customers, "customers")
    out = str(tmp_path / "report.json")
    profiler.save_report(out)
    import json, pathlib
    data = json.loads(pathlib.Path(out).read_text())
    assert "customers" in data
