# Methodology

## 1. Problem framing

The workbench starts from a commercial pricing question:

Should a marketplace provide a pricing incentive to selected partner segments?

The decision is not based only on volume uplift. It also considers margin quality, cancellation guardrails, statistical confidence and possible cannibalization.

## 2. Experiment design

Eligibility is frozen before treatment. The public hotel-booking observations are mapped to partner-segment proxies, and only Growth/Core observations with an acceptable synthetic pre-treatment quality score are eligible.

The quality score uses pre-treatment information such as segment and lead time plus fixed-seed variation. The same booking's eventual cancellation outcome is not used to determine eligibility.

Eligible observations are randomized 50/50 into control and treatment groups using fixed seed 42. The treatment group receives a synthetic pricing incentive; control does not.

## 3. Metrics

Success metrics:
- booking uplift
- revenue delta
- platform margin delta
- segment-level response

Guardrail metrics:
- cancellation outcome difference
- margin dilution
- cannibalization risk
- confidence in the result

## 4. Statistical readout

The workbench compares treatment and control changes and calculates:
- treatment vs control booking uplift
- 95% confidence interval
- p-value
- segment readout
- revenue and margin impact

This is a portfolio demonstration using a synthetic treatment layer, not a claim of production causal measurement.

## 5. Scenario and elasticity-style modelling

The scenario tab lets the user vary a hypothetical incentive level and immediately see expected booking and margin trade-offs by eligible segment.

This is explicitly a scenario model, not a true causal elasticity estimate.

## 6. Incrementality and cannibalization

The synthetic booking response represents gross direct response. Cannibalization is not embedded in that response equation.

The Incrementality tab therefore applies the cannibalization adjustment exactly once:

`gross direct uplift -> cannibalization adjustment -> net incremental units`

This avoids double-counting displacement.

## 7. AI-ready workflow

The deterministic Python/statistical layer produces the facts first. The public app then generates an AI-ready prompt pack containing only those validated facts, limitations and requested decision structure.

The public app does not call an LLM and does not claim autonomous decision-making. A user may pass the prompt pack to an approved AI tool to draft:
- executive memo
- risks and guardrails
- limitations
- next-test proposal
- stakeholder-ready decision narrative

## 8. Human-in-the-loop principle

The recommendation is not auto-approved. It is a structured decision-support output for a pricing manager or leadership team.

A real production implementation would additionally require verified experiment instrumentation, power analysis, seasonality and channel controls, real partner economics, governance, privacy/security review and longer post-test monitoring.
