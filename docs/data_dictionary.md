# Data Dictionary

## customers
| Column | Type | Description |
|--------|------|-------------|
| customer_id | TEXT | Surrogate key (CUST#####) |
| first_name | TEXT | Customer first name |
| last_name | TEXT | Customer last name |
| dob | TEXT | Date of birth (ISO 8601) |
| gender | TEXT | M / F / NB / U |
| address | TEXT | Street address |
| city | TEXT | City of residence |
| province | TEXT | Two-letter Canadian province code |
| postal_code | TEXT | Canadian postal code |
| email | TEXT | Email address (validated) |
| phone | TEXT | Phone number |
| signup_date | TEXT | Date customer signed up (ISO 8601) |
| risk_score | REAL | Actuarial risk score [0.0 - 1.0] |

## policies
| Column | Type | Description |
|--------|------|-------------|
| policy_id | TEXT | Surrogate key (POL######) |
| customer_id | TEXT | FK -> customers |
| policy_type | TEXT | auto / home / life / health / travel |
| start_date | TEXT | Policy start (ISO 8601) |
| end_date | TEXT | Policy end (ISO 8601) |
| premium_amount | REAL | Annual premium (CAD) |
| coverage_amount | REAL | Maximum coverage (CAD) |
| deductible | REAL | Deductible amount (CAD) |
| agent_id | TEXT | Agent identifier |
| status | TEXT | active / lapsed / cancelled / expired |

## claims
| Column | Type | Description |
|--------|------|-------------|
| claim_id | TEXT | Surrogate key (CLM#######) |
| policy_id | TEXT | FK -> policies |
| customer_id | TEXT | FK -> customers |
| claim_date | TEXT | Date claim was filed (ISO 8601) |
| claim_type | TEXT | collision / theft / fire / flood / medical / liability / property |
| claim_amount | REAL | Claimed amount (CAD) |
| status | TEXT | open / closed / pending / denied |
| adjuster_id | TEXT | Claims adjuster identifier |
| fraud_flag | INTEGER | 1 = suspected fraud, 0 = clean |
| settlement_date | TEXT | Date claim was settled (ISO 8601) |
| description | TEXT | Free-text claim description |

## Derived Columns (fact_claims)
| Column | Description |
|--------|-------------|
| claim_age_days | Days since claim was filed |
| is_high_value_claim | 1 if claim_amount > $50,000 |
| customer_tenure_years | Years since customer signup |
| policy_active_flag | 1 if policy status = "active" |
