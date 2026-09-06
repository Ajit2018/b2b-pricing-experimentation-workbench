# Deployment QA

Use this checklist after changes to `main` and before sharing the portfolio with recruiters.

## Required checks

1. Open `https://ajit-b2b-pricing-workbench.streamlit.app/` from a computer/session that is not managing the Streamlit app.
2. Confirm the app opens without a Streamlit login wall.
3. Confirm the sidebar contains only the eligible segment selector (`All eligible`, `Growth`, `Core`) plus the fixed-seed note.
4. Confirm there is no public Experiment Seed slider.
5. Confirm the Scenario Incentive slider appears only inside the `Scenario / Elasticity` tab.
6. Move the incentive slider and confirm Selected incentive, Expected booking lift and Expected margin lift update immediately.
7. Confirm Decision, Why and Action are logically consistent.
8. Confirm the top Decision value is fully visible and not truncated.
9. Confirm Experiment Design states that the same booking's cancellation outcome is excluded from eligibility.
10. Confirm the cancellation comparison is presented as an outcome guardrail, not as an eligibility field.
11. Confirm Incrementality states that cannibalization is deducted exactly once.
12. Confirm the AI-ready Memo tab states that the public app generates a prompt pack and does not call an LLM.
13. Confirm the Data + SQL tab shows the corrected in-memory experiment panel and the SQL example using CTEs, conditional aggregation and window ranking.
14. Confirm README arrows and repository tree render cleanly with no encoding corruption.
15. Confirm the README contains public data source/licensing information and generic clone/run instructions rather than a local machine path.
16. Click the Live dashboard and GitHub links from the final CV PDF.
17. Keep the CV and cover letter frozen after this check unless a factual error is found.

## Final deployment record - 6 September 2026

- Public access confirmed from a separate computer: **PASS**. The app opened directly without an owner `Manage app` control or Streamlit login wall.
- Eligible-segment selector (`All eligible`, `Growth`, `Core`): **PASS**.
- Segment outputs changed consistently and `Growth + Core = All eligible` observation count: **PASS**.
- Experiment seed fixed at 42 with no public seed slider: **PASS**.
- Cancellation-leakage correction committed to `main`: **PASS**.
- Cannibalization single-deduction correction committed to `main`: **PASS**.
- Decision / Why / Action use one decision function: **PASS**.
- Recruiter-facing UI polish committed: internal `V3` label removed, public data-source wording clarified, and top Decision display changed to avoid metric truncation.
- README encoding, data-source/license disclosure and generic setup instructions: **PASS**.
- CV and cover-letter links remain unchanged because the public dashboard URL and repository URL did not change.

Final manual smoke check after the last Streamlit redeploy: refresh the app, confirm the full Decision label is visible, and move the Scenario / Elasticity incentive slider once to confirm the three scenario KPIs respond. After that, freeze the portfolio for this application.
