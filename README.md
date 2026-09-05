# B2B Pricing Experimentation Workbench

## Purpose

This is an applied portfolio project by Ajit Pal Singh. It demonstrates how a pricing analytics workflow can move from an ambiguous commercial question to experiment design, SQL/Python analysis, pricing readout, incrementality/cannibalization checks and an executive recommendation.

The project uses public/synthetic data only. It does not use or infer any proprietary company data.

## Business question

Should a digital marketplace offer a pricing incentive to selected partner segments to increase incremental bookings without damaging margin, quality, cancellation guardrails or other partner/customer segments?

## What the project demonstrates

- B2B partner-pricing logic
- Controlled test design
- A/B test readout
- Booking uplift and margin impact
- Confidence intervals and p-value
- Guardrail metrics
- Elasticity-style scenario modelling
- Incrementality and cannibalization check
- SQL-style segment diagnostics
- AI-assisted executive memo workflow
- Business recommendation: scale / stop / retest / narrow eligibility

## Why this is not just a notebook

The project is built as a decision workbench. The core principle is:

Python/statistics calculate validated facts first.  
The AI layer then converts those facts into an executive memo, risks, limitations and next-test plan for human review.

## Data

The synthetic dataset is generated from a transparent simulation process and saved in:

`data/synthetic/b2b_pricing_experiment_synthetic_data.csv`

Fields include:
- partner_id
- partner_segment
- region
- channel
- price_band
- quality_score
- eligible_for_test
- treatment_group
- baseline_commission_rate
- test_incentive_rate
- bookings_before
- bookings_after
- adr
- gross_revenue_before
- gross_revenue_after
- platform_margin_before
- platform_margin_after
- cancellation_rate_before
- cancellation_rate_after
- cannibalization_pressure
- booking_delta
- revenue_delta
- margin_delta

## Limitations

This is a portfolio case study using synthetic data. It is designed to demonstrate methodology and decision thinking, not to estimate real marketplace effects.

A real production version would require:
- verified randomized assignment
- real partner and booking data
- seasonality controls
- eligibility governance
- experiment power analysis
- longer monitoring period
- true causal-inference validation
- privacy/security review
- stakeholder approval workflow

## Run locally

```powershell
cd E:\AJIT_JOB_PORTFOLIO\02_PROJECTS\01_b2b_pricing_experimentation
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python .\src\generate_synthetic_data.py
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

Open:

`http://localhost:8502`

## Portfolio positioning

This project supports roles in:
- pricing analytics
- B2B pricing strategy
- revenue growth management
- commercial decision support
- experimentation analytics
- AI-enabled analytics workflows
- consulting / transformation analytics

## Honest CV wording

Built an applied B2B pricing experimentation workbench using synthetic partner-pricing data, covering controlled test design, uplift readout, margin trade-off analysis, elasticity-style scenarios, incrementality/cannibalization checks, SQL/Python analysis and AI-assisted executive memo workflow.

