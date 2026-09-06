# B2B Pricing Experimentation Workbench

Applied pricing analytics portfolio project by Ajit Pal Singh.

This project demonstrates pricing experimentation, commercial decision support, SQL/Python analytics, scenario modelling, incrementality/cannibalization analysis and an AI-ready executive memo workflow.

## Live dashboard

- Live Streamlit dashboard: https://ajit-b2b-pricing-workbench.streamlit.app/
- GitHub repository: https://github.com/Ajit2018/b2b-pricing-experimentation-workbench

The live dashboard is the fastest way to review the project. It shows the decision snapshot, experiment design, test readout, scenario/elasticity-style view, incrementality bridge, SQL example and AI-ready memo workflow.

## 1. Executive summary

This project answers a practical pricing question:

> Should a digital marketplace offer a pricing incentive to selected partner segments to increase incremental bookings without damaging margin, cancellation guardrails or other partner/customer segments?

The workbench uses real public hotel-booking observations as a base and adds a transparent synthetic pricing-treatment layer because the public data does not contain real partner-level pricing experiments.

Workflow:

`business question -> experiment design -> SQL/Python analysis -> uplift readout -> margin trade-off -> incrementality/cannibalization check -> executive recommendation`

## 2. What this project demonstrates

- pricing analytics and commercial decision support
- controlled A/B-style test design
- randomized treatment/control assignment on a frozen eligible population
- uplift, confidence interval and p-value interpretation
- revenue and platform-margin trade-offs
- elasticity-style scenario modelling
- incrementality and cannibalization checks
- SQL analysis using CTEs, conditional aggregation and window ranking
- AI-ready executive memo prompt generation from validated facts
- explicit assumptions, limitations and human-in-the-loop governance

## 3. What this project does not claim

This is a public portfolio case study. It does not claim to estimate real Booking.com or other marketplace effects.

It does not use:

- Booking.com data
- confidential employer data
- proprietary partner data
- real production experiment assignments
- private customer data

The treatment layer is synthetic because real B2B incentive, partner economics and randomized assignment data are proprietary.

## 4. Public data source and license

The base data comes from the **Hotel Booking Demand** datasets described by Nuno Antonio, Ana Almeida and Luis Nunes in *Data in Brief* (2019):

- Article / DOI: https://doi.org/10.1016/j.dib.2018.11.126
- Open-access article: https://pmc.ncbi.nlm.nih.gov/articles/PMC6297060/
- Common cleaned `hotel_bookings.csv` distribution: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand
- License: **CC BY 4.0**

The raw public source file is intentionally excluded from this repository. A processed base panel is included so the cloud dashboard can run without redistributing the full raw source.

## 5. Experiment governance and methodology

### Pre-treatment eligibility

Eligibility is determined before treatment using only pre-treatment proxies:

- partner-segment proxy
- lead time
- a synthetic pre-treatment quality score generated from segment, lead time, optional repeat-guest history and fixed-seed noise

The same booking's eventual cancellation outcome is **not** used to determine eligibility.

### Randomization

Eligible Growth/Core observations are randomized 50/50 into treatment and control using a fixed experiment seed of **42**. The seed is intentionally fixed rather than exposed as a public UI control so the cloud demo is reproducible.

### Cancellation guardrail

Cancellation is retained as an outcome guardrail. Because treatment assignment is independent of the cancellation outcome, the treatment/control cancellation comparison is no longer mechanically forced to zero by eligibility selection.

### Cannibalization

The synthetic booking response represents **gross direct response**. Cannibalization pressure is not subtracted inside that response equation. It is deducted exactly once in the Incrementality tab:

`gross direct uplift -> cannibalization adjustment -> net incremental units`

This avoids double-counting displacement.

## 6. Current dashboard modules

1. **Decision Snapshot** - recommendation, rationale and a decision-consistent action.
2. **Executive Decision** - leadership-facing interpretation of uplift, margin, confidence interval, p-value, guardrails and limitations.
3. **Experiment Design** - frozen eligibility, treatment/control setup, metrics and guardrails.
4. **Test Readout** - control vs treatment distribution and segment-level results.
5. **Scenario / Elasticity** - incentive slider located inside the scenario tab with immediate expected-booking and expected-margin outputs. This is explicitly not a causal elasticity estimate.
6. **Incrementality** - gross direct uplift, one-time cannibalization adjustment and net incremental effect.
7. **AI-ready Memo** - a governed prompt pack built from validated facts; the public app does not call an LLM.
8. **Data + SQL** - corrected in-memory panel, downloadable data and a stronger SQL example using CTEs and a window ranking.

## 7. Decision logic

The recommendation can be:

- **Scale**
- **Narrow Target**
- **Retest**
- **Do Not Scale**

The action text is generated from the same decision logic, so the dashboard cannot display a recommendation that contradicts its action.

A material deterioration in the cancellation guardrail can block scaling even if demand increases.

## 8. Cloud behavior

The Streamlit deployment can run from the included processed base panel. On each cached load, the app rebuilds the synthetic experiment layer deterministically with seed 42 and overwrites any older synthetic eligibility, assignment or outcome fields in memory.

This means the corrected methodology is applied even when the raw public source is not present on Streamlit Cloud.

## 9. Run locally

```bash
git clone https://github.com/Ajit2018/b2b-pricing-experimentation-workbench.git
cd b2b-pricing-experimentation-workbench
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

## 10. Repository structure

```text
b2b-pricing-experimentation-workbench/
|-- README.md
|-- requirements.txt
|-- app.py
|-- data/
|   |-- processed/
|   |   `-- hotel_pricing_experiment_panel.csv
|   `-- synthetic/
|       `-- b2b_pricing_experiment_synthetic_data.csv
|-- docs/
|   |-- methodology.md
|   |-- executive_memo_template.md
|   |-- executive_summary.md
|   `-- sharing_notes_for_recruiters.md
|-- images/
|   `-- README.md
|-- sql/
|   `-- experiment_readout.sql
`-- src/
    |-- generate_synthetic_data.py
    `-- streamlit_page.py
```

## 11. CV wording

**B2B Pricing Experimentation Workbench**  
Built an applied pricing experimentation workbench using public hotel-booking data enriched with a transparent synthetic pricing-treatment layer. Demonstrates controlled test design, uplift readout, margin trade-off analysis, elasticity-style scenarios, incrementality/cannibalization checks, SQL/Python analytics and an AI-ready executive memo workflow.

## 12. Production-readiness limitations

A real production version would require:

- verified randomized assignment and experiment instrumentation
- power and sample-size analysis
- real partner economics
- seasonality, market and channel controls
- partner eligibility governance
- privacy and security review
- monitoring for unintended consequences
- stakeholder approval workflow
- longer-term post-test measurement

These limitations are explicit because the purpose is to demonstrate applied pricing methodology and decision thinking, not to claim access to proprietary marketplace data.
