-- =============================================================
-- Insurance Claims Data Warehouse -- DDL
-- =============================================================

-- Dimension: customers
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id       TEXT PRIMARY KEY,
    first_name        TEXT,
    last_name         TEXT,
    dob               TEXT,
    gender            TEXT,
    address           TEXT,
    city              TEXT,
    province          TEXT,
    postal_code       TEXT,
    email             TEXT,
    phone             TEXT,
    signup_date       TEXT,
    risk_score        REAL
);

CREATE INDEX IF NOT EXISTS idx_dim_customer_province ON dim_customer (province);
CREATE INDEX IF NOT EXISTS idx_dim_customer_signup_date ON dim_customer (signup_date);

-- Dimension: policies
CREATE TABLE IF NOT EXISTS dim_policy (
    policy_id         TEXT PRIMARY KEY,
    customer_id       TEXT NOT NULL,
    policy_type       TEXT,
    start_date        TEXT,
    end_date          TEXT,
    premium_amount    REAL,
    coverage_amount   REAL,
    deductible        REAL,
    agent_id          TEXT,
    status            TEXT,
    FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id)
);

CREATE INDEX IF NOT EXISTS idx_dim_policy_customer_id ON dim_policy (customer_id);
CREATE INDEX IF NOT EXISTS idx_dim_policy_status      ON dim_policy (status);
CREATE INDEX IF NOT EXISTS idx_dim_policy_type        ON dim_policy (policy_type);

-- Fact: claims
CREATE TABLE IF NOT EXISTS fact_claims (
    claim_id          TEXT PRIMARY KEY,
    policy_id         TEXT NOT NULL,
    customer_id       TEXT NOT NULL,
    claim_date        TEXT,
    claim_type        TEXT,
    claim_amount      REAL,
    status            TEXT,
    adjuster_id       TEXT,
    fraud_flag        INTEGER DEFAULT 0,
    settlement_date   TEXT,
    description       TEXT,
    claim_age_days    INTEGER,
    is_high_value_claim INTEGER DEFAULT 0,
    FOREIGN KEY (policy_id)   REFERENCES dim_policy   (policy_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_claims_policy_id    ON fact_claims (policy_id);
CREATE INDEX IF NOT EXISTS idx_fact_claims_customer_id  ON fact_claims (customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_claims_claim_date   ON fact_claims (claim_date);
CREATE INDEX IF NOT EXISTS idx_fact_claims_fraud_flag   ON fact_claims (fraud_flag);
CREATE INDEX IF NOT EXISTS idx_fact_claims_claim_type   ON fact_claims (claim_type);

-- Raw / staging tables (mirrored for lineage)
CREATE TABLE IF NOT EXISTS customers (
    customer_id  TEXT,
    first_name   TEXT,
    last_name    TEXT,
    dob          TEXT,
    gender       TEXT,
    address      TEXT,
    city         TEXT,
    province     TEXT,
    postal_code  TEXT,
    email        TEXT,
    phone        TEXT,
    signup_date  TEXT,
    risk_score   REAL
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id        TEXT,
    customer_id      TEXT,
    policy_type      TEXT,
    start_date       TEXT,
    end_date         TEXT,
    premium_amount   REAL,
    coverage_amount  REAL,
    deductible       REAL,
    agent_id         TEXT,
    status           TEXT
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id        TEXT,
    policy_id       TEXT,
    customer_id     TEXT,
    claim_date      TEXT,
    claim_type      TEXT,
    claim_amount    REAL,
    status          TEXT,
    adjuster_id     TEXT,
    fraud_flag      INTEGER,
    settlement_date TEXT,
    description     TEXT
);
