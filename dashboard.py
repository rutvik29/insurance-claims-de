import os
import json
import sqlite3
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Insurance Claims Dashboard",
    page_icon="🛡️",
)

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "warehouse" / "insurance_claims.db"
REPORT_PATH = BASE_DIR / "data" / "warehouse" / "pipeline_report.json"


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_table(query: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    con = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, con)
    con.close()
    return df


@st.cache_data
def load_all_data():
    fact = load_table("SELECT * FROM fact_claims")
    analytical = load_table("SELECT * FROM analytical")
    fraud_province = load_table("SELECT * FROM fraud_rate_by_province")
    return fact, analytical, fraud_province


@st.cache_data
def load_pipeline_report():
    if not REPORT_PATH.exists():
        return None
    with open(REPORT_PATH) as f:
        return json.load(f)


# ── Guard: DB must exist ───────────────────────────────────────────────────────
if not DB_PATH.exists():
    st.error(
        f"Database not found at `{DB_PATH}`.\n\n"
        "Run the ETL pipeline first:  `python pipeline/etl_pipeline.py`"
    )
    st.stop()

# ── Load data ──────────────────────────────────────────────────────────────────
fact_raw, analytical_raw, fraud_province_df = load_all_data()

# Parse dates
fact_raw["claim_date"] = pd.to_datetime(fact_raw["claim_date"])
analytical_raw["claim_date"] = pd.to_datetime(analytical_raw["claim_date"])

# ── Sidebar filters ────────────────────────────────────────────────────────────
st.sidebar.title("Filters")

# Date range
min_date = fact_raw["claim_date"].min().date()
max_date = fact_raw["claim_date"].max().date()
date_range = st.sidebar.date_input(
    "Claim Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Claim type
all_types = sorted(analytical_raw["claim_type"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect(
    "Claim Type", options=all_types, default=all_types
)

# Province
all_provinces = sorted(analytical_raw["province"].dropna().unique().tolist())
selected_provinces = st.sidebar.multiselect(
    "Province", options=all_provinces, default=all_provinces
)

# Fraud flag
fraud_toggle = st.sidebar.toggle("Show Fraud Only", value=False)

# ── Apply filters ──────────────────────────────────────────────────────────────
mask = (
    (analytical_raw["claim_date"].dt.date >= start_date)
    & (analytical_raw["claim_date"].dt.date <= end_date)
    & (analytical_raw["claim_type"].isin(selected_types))
    & (analytical_raw["province"].isin(selected_provinces))
)
if fraud_toggle:
    mask &= analytical_raw["fraud_flag"] == 1

filtered = analytical_raw[mask].copy()

# Also filter the plain fact table to match (for the data table at the bottom)
fact_mask = (
    (fact_raw["claim_date"].dt.date >= start_date)
    & (fact_raw["claim_date"].dt.date <= end_date)
    & (fact_raw["claim_type"].isin(selected_types))
)
if fraud_toggle:
    fact_mask &= fact_raw["fraud_flag"] == 1
fact_filtered = fact_raw[fact_mask].copy()

# ── Title ──────────────────────────────────────────────────────────────────────
st.title("🛡️ Insurance Claims Dashboard")
st.caption(f"Showing **{len(filtered):,}** claims  •  {start_date} → {end_date}")

# ── KPI Row ────────────────────────────────────────────────────────────────────
total_claims = len(filtered)
total_amount = filtered["claim_amount"].sum() if total_claims else 0
fraud_rate = (
    filtered["fraud_flag"].mean() * 100 if total_claims else 0.0
)
avg_settlement = (
    filtered["claim_age_days"].mean() if "claim_age_days" in filtered.columns and total_claims else 0.0
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Claims", f"{total_claims:,}")
k2.metric("Total Claim Amount", f"${total_amount:,.0f}")
k3.metric("Fraud Rate", f"{fraud_rate:.2f}%")
k4.metric("Avg Settlement Days", f"{avg_settlement:.1f}")

st.divider()

# ── Charts ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

# 1. Bar: Claims by claim_type
with col1:
    st.subheader("Claims by Type")
    if not filtered.empty:
        type_counts = (
            filtered.groupby("claim_type")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        fig_type = px.bar(
            type_counts,
            x="claim_type",
            y="count",
            color="claim_type",
            labels={"claim_type": "Claim Type", "count": "Number of Claims"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_type.update_layout(showlegend=False, height=350)
        st.plotly_chart(fig_type, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# 2. Line: Monthly claim volume
with col2:
    st.subheader("Monthly Claim Volume")
    if not filtered.empty:
        monthly = (
            filtered.set_index("claim_date")
            .resample("M")
            .size()
            .reset_index(name="count")
        )
        monthly["claim_date"] = monthly["claim_date"].dt.to_period("M").astype(str)
        fig_monthly = px.line(
            monthly,
            x="claim_date",
            y="count",
            markers=True,
            labels={"claim_date": "Month", "count": "Claims"},
            color_discrete_sequence=["#636EFA"],
        )
        fig_monthly.update_layout(height=350)
        st.plotly_chart(fig_monthly, use_container_width=True)
    else:
        st.info("No data for selected filters.")

col3, col4 = st.columns(2)

# 3. Bar: Fraud rate by province (from precomputed table)
with col3:
    st.subheader("Fraud Rate by Province")
    if not fraud_province_df.empty:
        fp = fraud_province_df.copy()
        if selected_provinces:
            fp = fp[fp["province"].isin(selected_provinces)]
        fp = fp.sort_values("fraud_rate", ascending=False)
        fig_fraud = px.bar(
            fp,
            x="province",
            y="fraud_rate",
            color="fraud_rate",
            labels={"province": "Province", "fraud_rate": "Fraud Rate"},
            color_continuous_scale="Reds",
            text_auto=".2f",
        )
        fig_fraud.update_layout(height=350, coloraxis_showscale=False)
        st.plotly_chart(fig_fraud, use_container_width=True)
    else:
        st.info("No fraud data available.")

# 4. Pie: Claims by status
with col4:
    st.subheader("Claims by Status")
    if not filtered.empty:
        status_counts = (
            filtered.groupby("status")
            .size()
            .reset_index(name="count")
        )
        fig_pie = px.pie(
            status_counts,
            names="status",
            values="count",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.35,
        )
        fig_pie.update_layout(height=350)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No data for selected filters.")

# 5. Histogram: Claim amount distribution (full width)
st.subheader("Claim Amount Distribution")
if not filtered.empty:
    fig_hist = px.histogram(
        filtered,
        x="claim_amount",
        nbins=50,
        labels={"claim_amount": "Claim Amount ($)", "count": "Frequency"},
        color_discrete_sequence=["#19D3F3"],
    )
    fig_hist.update_layout(height=350, bargap=0.05)
    st.plotly_chart(fig_hist, use_container_width=True)
else:
    st.info("No data for selected filters.")

st.divider()

# ── Data Table ─────────────────────────────────────────────────────────────────
st.subheader("Claims Data Table")

TABLE_COLS = [
    "claim_id", "claim_date", "claim_type", "claim_amount",
    "status", "fraud_flag", "province",
]
available_cols = [c for c in TABLE_COLS if c in filtered.columns]
table_df = filtered[available_cols].copy()
table_df["claim_date"] = table_df["claim_date"].dt.date

PAGE_SIZE = 50
total_rows = len(table_df)
total_pages = max(1, math.ceil(total_rows / PAGE_SIZE))

st.caption(f"{total_rows:,} rows  •  page size {PAGE_SIZE}")

page = st.number_input(
    "Page", min_value=1, max_value=total_pages, value=1, step=1
)
start_idx = (page - 1) * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE

st.dataframe(
    table_df.iloc[start_idx:end_idx].reset_index(drop=True),
    use_container_width=True,
    height=400,
)
st.caption(f"Page {page} of {total_pages}")

st.divider()

# ── Pipeline Report ────────────────────────────────────────────────────────────
st.subheader("Pipeline Report")

report = load_pipeline_report()
if report is None:
    st.warning(f"Pipeline report not found at `{REPORT_PATH}`.")
else:
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Pipeline Status", report.get("status", "—"))
    r2.metric("Start Time", report.get("start_time", "—")[:19].replace("T", " "))
    r3.metric("End Time", report.get("end_time", "—")[:19].replace("T", " "))
    r4.metric("Total Elapsed (s)", f"{report.get('total_elapsed_s', 0):.2f}")

    steps = report.get("steps", {})
    if steps:
        st.markdown("**Step Details**")
        step_rows = []
        for step_name, s in steps.items():
            step_rows.append(
                {
                    "Step": step_name,
                    "Rows In": s.get("rows_in", "—"),
                    "Rows Out": s.get("rows_out", "—"),
                    "Elapsed (s)": round(s.get("elapsed_s", 0), 3),
                }
            )
        steps_df = pd.DataFrame(step_rows)
        st.dataframe(steps_df, use_container_width=True, hide_index=True)

    # Data quality checks live inside validate step
    dq = steps.get("validate", {}).get("dq_checks", {})
    if dq:
        st.markdown("**Data Quality Checks**")
        qcols = st.columns(min(len(dq), 3))
        for i, (k, v) in enumerate(dq.items()):
            label = k.replace("_", " ").title()
            val = f"{v:.2%}" if isinstance(v, float) and k.endswith("rate") else str(v)
            qcols[i % 3].metric(label, val)

    # Tables loaded
    tables_loaded = steps.get("load", {}).get("tables", {})
    if tables_loaded:
        st.markdown("**Tables Loaded**")
        tdf = pd.DataFrame(
            [{"Table": t, "Rows": f"{n:,}"} for t, n in tables_loaded.items()]
        )
        st.dataframe(tdf, use_container_width=True, hide_index=True)
