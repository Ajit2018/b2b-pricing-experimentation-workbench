# B2B Pricing Experimentation Workbench

## Purpose

This is an applied portfolio project by Ajit Pal Singh. It demonstrates how a pricing analytics workflow can move from an ambiguous commercial question to experiment design, SQL/Python analysis, pricing readout, incrementality/cannibalization checks and an executive recommendation.

## Data approach

V2 uses a hybrid data design:

1. **Real public hotel-booking data** as the base: `data/public/hotel_bookings.csv`
2. **Transparent synthetic pricing-treatment layer** for partner IDs, partner segments, treatment/control assignment, commission incentives, margin proxy and cannibalization pressure.

No proprietary employer or target-company data is used.

## Business question

Should a digital marketplace offer a pricing incentive to selected partner segments to increase incremental bookings without damaging margin, quality, cancellation guardrails or other partner/customer segments?

## What the project demonstrates

- Public-data analytics foundation
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

## Core principle

Python/statistics calculate validated facts first.  
The AI layer then converts those facts into an executive memo, risks, limitations and next-test plan for human review.

## Run locally

```powershell
cd E:\AJIT_JOB_PORTFOLIO_PROJECTS_b2b_pricing_experimentation
.\.venv\Scriptsctivate
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

Open: `http://localhost:8502`

## Honest CV wording

Built an applied B2B pricing experimentation workbench using public hotel-booking data enriched with a transparent synthetic pricing-treatment layer, covering controlled test design, uplift readout, margin trade-off analysis, elasticity-style scenarios, incrementality/cannibalization checks, SQL/Python analysis and AI-assisted executive memo workflow.

## Limitations

This is a portfolio case study. It does not estimate real marketplace effects. A production version would require true randomized assignment, real partner economics, seasonality controls, experiment power analysis, privacy/security review and stakeholder governance.
