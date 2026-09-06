# Deployment QA

Use this checklist after changes to `main` and before sharing the portfolio with recruiters.

1. Open `https://ajit-b2b-pricing-workbench.streamlit.app/` in a logged-out Incognito window.
2. Confirm the app opens without a Streamlit login wall.
3. Confirm the sidebar contains only the eligible segment selector (`All eligible`, `Growth`, `Core`) plus the fixed-seed note.
4. Confirm there is no public Experiment Seed slider.
5. Confirm the Scenario Incentive slider appears only inside the `Scenario / Elasticity` tab.
6. Move the incentive slider and confirm Selected incentive, Expected booking lift and Expected margin lift update immediately.
7. Confirm Decision, Why and Action are logically consistent.
8. Confirm Experiment Design states that the same booking's cancellation outcome is excluded from eligibility.
9. Confirm the cancellation comparison is presented as an outcome guardrail, not as an eligibility field.
10. Confirm Incrementality states that cannibalization is deducted exactly once.
11. Confirm the AI-ready Memo tab states that the public app generates a prompt pack and does not call an LLM.
12. Confirm the Data + SQL tab shows the corrected in-memory experiment panel and the SQL example using CTEs, conditional aggregation and window ranking.
13. Confirm README arrows and repository tree render cleanly with no encoding corruption.
14. Confirm the README contains public data source/licensing information and generic clone/run instructions rather than a local machine path.
15. Click the Live dashboard and GitHub links from the final CV PDF.
16. Keep the CV and cover letter frozen after this check unless a factual error is found.
