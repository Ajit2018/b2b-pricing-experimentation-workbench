# B2B Pricing Experimentation Workbench

**Applied pricing analytics portfolio project by Ajit Pal Singh**  
GitHub-ready project demonstrating pricing experimentation, commercial decision support, SQL/Python analytics and AI-assisted executive memo workflow.

---

## 1. Executive summary

This project answers a practical pricing question:

> Should a digital marketplace offer a pricing incentive to selected partner segments to increase incremental bookings without damaging margin, quality, cancellation guardrails or other partner/customer segments?

The workbench uses **real public hotel-booking data** as the base and adds a **transparent synthetic pricing-treatment layer** where public data does not contain partner-level pricing experiments.

The project is designed to show how a pricing analytics workflow can move from:

**business question â†’ experiment design â†’ SQL/Python analysis â†’ uplift readout â†’ margin trade-off â†’ incrementality/cannibalization check â†’ executive recommendation**

---

## 2. What this project is

This is a public portfolio case study that demonstrates:

- pricing analytics and commercial decision support
- controlled test design
- A/B-style experiment readout
- uplift, confidence interval and p-value interpretation
- revenue and margin trade-off analysis
- elasticity-style scenario modelling
- incrementality and cannibalization checks
- SQL-style segment diagnostics
- AI-assisted executive memo generation
- clear assumptions, limitations and human-in-the-loop decision governance

---

## 3. What this project is not

This project does **not** claim to estimate real marketplace effects.

It does not use:
- Booking.com data
- confidential employer data
- proprietary partner data
- real production experiment assignments
- private customer data

The synthetic treatment layer exists because public datasets do not contain the confidential B2B incentive, partner economics and randomized assignment data that a real company would use.

---

## 4. Data approach

V2 uses a hybrid design:

1. **Real public hotel-booking data** as the base: `hotel_bookings.csv`
2. **Transparent synthetic pricing-treatment layer** for:
   - partner ID proxy
   - partner segment proxy
   - treatment/control assignment
   - commission/incentive logic
   - margin proxy
   - cannibalization pressure
   - pricing experiment outcomes

The raw public source file is intentionally excluded from GitHub via `.gitignore`. The processed experiment panel is included for reproducibility and review.

---

## 5. Business logic

The workbench simulates a marketplace-pricing decision:

> A selected group of partners receives a pricing incentive. Should the pricing team scale, stop, retest, or narrow eligibility?

The decision is not based on volume alone. It checks:

- booking uplift
- revenue impact
- platform margin impact
- cancellation guardrail
- gross vs net incrementality
- cannibalization pressure
- confidence of the result
- segment-level commercial trade-offs

---

## 6. Current modules

The Streamlit app includes:

1. **Decision Snapshot**  
   One-screen decision summary with recommended action and rationale.

2. **Executive Decision**  
   Leadership-facing interpretation of uplift, margin, confidence interval, p-value and limitations.

3. **Experiment Design**  
   Eligibility logic, treatment/control setup, success metrics and guardrails.

4. **Test Readout**  
   Control vs treatment comparison and segment-level performance.

5. **Scenario / Elasticity**  
   Incentive-level slider showing expected booking and margin trade-offs.

6. **Incrementality**  
   Gross uplift, cannibalization adjustment and net incremental impact.

7. **AI Memo**  
   AI-ready prompt pack generated from validated facts.

8. **Data + SQL**  
   Processed data preview, SQL example and downloadable experiment panel.

---

## 7. AI workflow principle

The AI layer does **not** replace statistical analysis or make unsupported claims.

The project follows this principle:

> Python/statistics calculate validated facts first.  
> AI converts those facts into an executive memo, risks, limitations and next-test plan for human review.

This demonstrates how AI can improve productivity in pricing analytics without removing human accountability.

---

## 8. How to run locally

```powershell
cd E:\AJIT_JOB_PORTFOLIO\02_PROJECTS\01_b2b_pricing_experimentation

# If the virtual environment already exists:
.\.venv\Scripts\streamlit.exe run app.py --server.address 0.0.0.0 --server.port 8502

# Alternative if streamlit is on PATH:
streamlit run app.py --server.address 0.0.0.0 --server.port 8502
```

Open:

`http://localhost:8502`

---

## 9. Repository structure

```text
b2b-pricing-experimentation-workbench
â”œâ”€ README.md
â”œâ”€ requirements.txt
â”œâ”€ app.py
â”œâ”€ data
â”‚  â”œâ”€ processed
â”‚  â”‚  â””â”€ hotel_pricing_experiment_panel.csv
â”‚  â””â”€ synthetic
â”‚     â””â”€ b2b_pricing_experiment_synthetic_data.csv
â”œâ”€ docs
â”‚  â”œâ”€ methodology.md
â”‚  â”œâ”€ executive_memo_template.md
â”‚  â”œâ”€ executive_summary.md
â”‚  â””â”€ sharing_notes_for_recruiters.md
â”œâ”€ images
â”‚  â””â”€ README.md
â”œâ”€ sql
â”‚  â””â”€ experiment_readout.sql
â””â”€ src
   â”œâ”€ generate_synthetic_data.py
   â””â”€ streamlit_page.py
```

---

## 10. Honest CV wording

**B2B Pricing Experimentation Workbench**  
Built an applied pricing experimentation workbench using public hotel-booking data enriched with a transparent synthetic pricing-treatment layer. Demonstrates controlled test design, uplift readout, margin trade-off analysis, elasticity-style scenarios, incrementality/cannibalization checks, SQL/Python analytics and AI-assisted executive memo workflow.

---

## 11. Honest cover-letter wording

My professional background is strongest in pricing analytics, value leakage detection, price harmonisation, scenario modelling, Power BI/Python/SQL-enabled decision tools and cross-functional stakeholder decision support. Where the role requires more direct marketplace experimentation evidence, I built a focused B2B pricing experimentation workbench using public hotel-booking data and a transparent synthetic pricing-treatment layer. It demonstrates how I approach controlled test readouts, incrementality, cannibalization, margin trade-offs and AI-assisted executive recommendation generation, with clear assumptions and limitations.

---

## 12. Production-readiness limitations

A real production version would require:

- true randomized assignment validation
- experiment power analysis
- real partner economics
- seasonality controls
- market and channel controls
- partner eligibility governance
- privacy/security review
- monitoring for unintended consequences
- stakeholder approval workflow
- long-term post-test measurement

These limitations are explicitly stated because the purpose of the project is to demonstrate applied methodology and decision thinking, not to claim access to proprietary marketplace data.

---

## 13. Portfolio positioning

This project supports applications in:

- pricing analytics
- pricing strategy
- commercial decision support
- revenue growth management
- marketplace analytics
- experimentation analytics
- AI-enabled analytics workflows
- analytics consulting and transformation
