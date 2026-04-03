-- =============================================================
-- Insurance Claims Data Warehouse -- Analytical Views
-- =============================================================

-- View 1: Fraud summary by claim type and province
CREATE VIEW IF NOT EXISTS vw_fraud_summary AS
SELECT
    fc.claim_type,
    dc.province,
    COUNT(fc.claim_id)                                      AS total_claims,
    SUM(fc.fraud_flag)                                      AS fraud_claims,
    ROUND(CAST(SUM(fc.fraud_flag) AS REAL)
          / NULLIF(COUNT(fc.claim_id), 0) * 100, 2)        AS fraud_rate_pct,
    ROUND(AVG(fc.claim_amount), 2)                         AS avg_claim_amount,
    ROUND(SUM(fc.claim_amount), 2)                         AS total_claim_amount
FROM fact_claims fc
LEFT JOIN dim_customer dc ON fc.customer_id = dc.customer_id
GROUP BY fc.claim_type, dc.province;

-- View 2: Claims summary by province
CREATE VIEW IF NOT EXISTS vw_claims_by_province AS
SELECT
    dc.province,
    COUNT(fc.claim_id)                                      AS total_claims,
    ROUND(AVG(fc.claim_amount), 2)                         AS avg_claim_amount,
    ROUND(SUM(fc.claim_amount), 2)                         AS total_claim_amount,
    SUM(fc.is_high_value_claim)                            AS high_value_claims,
    ROUND(CAST(SUM(fc.is_high_value_claim) AS REAL)
          / NULLIF(COUNT(fc.claim_id), 0) * 100, 2)        AS high_value_pct,
    COUNT(DISTINCT fc.customer_id)                         AS unique_customers
FROM fact_claims fc
LEFT JOIN dim_customer dc ON fc.customer_id = dc.customer_id
GROUP BY dc.province;

-- View 3: Customer risk profile enriched with claims history
CREATE VIEW IF NOT EXISTS vw_customer_risk_profile AS
SELECT
    dc.customer_id,
    dc.first_name,
    dc.last_name,
    dc.province,
    dc.risk_score,
    dc.signup_date,
    COUNT(fc.claim_id)                                      AS lifetime_claims,
    ROUND(AVG(fc.claim_amount), 2)                         AS avg_claim_amount,
    ROUND(SUM(fc.claim_amount), 2)                         AS total_claim_amount,
    SUM(fc.fraud_flag)                                      AS fraud_claim_count,
    MAX(fc.claim_date)                                      AS last_claim_date,
    CASE
        WHEN dc.risk_score >= 0.75 THEN 'HIGH'
        WHEN dc.risk_score >= 0.45 THEN 'MEDIUM'
        ELSE 'LOW'
    END                                                     AS risk_band
FROM dim_customer dc
LEFT JOIN fact_claims fc ON dc.customer_id = fc.customer_id
GROUP BY
    dc.customer_id, dc.first_name, dc.last_name,
    dc.province, dc.risk_score, dc.signup_date;
