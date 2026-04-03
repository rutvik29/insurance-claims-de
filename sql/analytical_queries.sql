-- =============================================================
-- Insurance Claims -- Business Analytical Queries
-- =============================================================

-- Query 1: Top 10 customers by total claim amount (fraud and non-fraud)
-- Business use: Identify high-cost customers for underwriting review
SELECT
    dc.customer_id,
    dc.first_name || ' ' || dc.last_name   AS customer_name,
    dc.province,
    dc.risk_score,
    COUNT(fc.claim_id)                      AS total_claims,
    ROUND(SUM(fc.claim_amount), 2)          AS total_claimed,
    SUM(fc.fraud_flag)                      AS fraud_incidents
FROM dim_customer dc
JOIN fact_claims fc ON dc.customer_id = fc.customer_id
GROUP BY dc.customer_id, dc.first_name, dc.last_name, dc.province, dc.risk_score
ORDER BY total_claimed DESC
LIMIT 10;


-- Query 2: Monthly claim volume and average amount trend
-- Business use: Detect seasonal spikes or emerging claim patterns
SELECT
    STRFTIME('%Y-%m', fc.claim_date)        AS claim_month,
    fc.claim_type,
    COUNT(fc.claim_id)                      AS claim_count,
    ROUND(AVG(fc.claim_amount), 2)          AS avg_amount,
    ROUND(SUM(fc.claim_amount), 2)          AS total_amount
FROM fact_claims fc
WHERE fc.claim_date IS NOT NULL
GROUP BY claim_month, fc.claim_type
ORDER BY claim_month, fc.claim_type;


-- Query 3: Fraud rate vs risk score cohort
-- Business use: Validate that high-risk customers exhibit higher fraud rates
SELECT
    CASE
        WHEN dc.risk_score >= 0.75 THEN 'HIGH'
        WHEN dc.risk_score >= 0.45 THEN 'MEDIUM'
        ELSE 'LOW'
    END                                     AS risk_band,
    COUNT(fc.claim_id)                      AS total_claims,
    SUM(fc.fraud_flag)                      AS fraud_claims,
    ROUND(
        CAST(SUM(fc.fraud_flag) AS REAL)
        / NULLIF(COUNT(fc.claim_id), 0) * 100, 2
    )                                       AS fraud_rate_pct,
    ROUND(AVG(fc.claim_amount), 2)          AS avg_claim_amount
FROM fact_claims fc
JOIN dim_customer dc ON fc.customer_id = dc.customer_id
GROUP BY risk_band
ORDER BY fraud_rate_pct DESC;


-- Query 4: Policy type profitability proxy
-- Business use: Compare premium revenue vs claims exposure by policy type
SELECT
    dp.policy_type,
    COUNT(DISTINCT dp.policy_id)            AS policy_count,
    ROUND(SUM(dp.premium_amount), 2)        AS total_premiums,
    ROUND(SUM(fc.claim_amount), 2)          AS total_claims_amount,
    ROUND(
        SUM(fc.claim_amount)
        / NULLIF(SUM(dp.premium_amount), 0), 4
    )                                       AS loss_ratio,
    COUNT(fc.claim_id)                      AS claim_count
FROM dim_policy dp
LEFT JOIN fact_claims fc ON dp.policy_id = fc.policy_id
GROUP BY dp.policy_type
ORDER BY loss_ratio DESC;


-- Query 5: Province leaderboard -- claims per active policy
-- Business use: Geographic risk concentration for reinsurance decisions
SELECT
    dc.province,
    COUNT(DISTINCT dp.policy_id)            AS active_policies,
    COUNT(fc.claim_id)                      AS total_claims,
    ROUND(
        CAST(COUNT(fc.claim_id) AS REAL)
        / NULLIF(COUNT(DISTINCT dp.policy_id), 0), 4
    )                                       AS claims_per_policy,
    ROUND(AVG(fc.claim_amount), 2)          AS avg_claim_amount,
    ROUND(SUM(fc.fraud_flag) * 1.0
          / NULLIF(COUNT(fc.claim_id), 0) * 100, 2)  AS fraud_rate_pct
FROM dim_customer dc
JOIN dim_policy dp   ON dc.customer_id = dp.customer_id
LEFT JOIN fact_claims fc ON dp.policy_id = fc.policy_id
GROUP BY dc.province
ORDER BY claims_per_policy DESC;
