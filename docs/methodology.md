# Methodology

## 1. Problem framing

The workbench starts from a commercial pricing question:

Should a marketplace provide a pricing incentive to selected partner segments?

The decision is not based only on volume uplift. It also considers margin quality, cancellation guardrails and possible cannibalization.

## 2. Experiment design

Eligible partners are selected based on partner segment and quality score. Eligible partners are split into control and treatment groups. The treatment group receives a pricing incentive.

## 3. Metrics

Success metrics:
- booking uplift
- revenue delta
- platform margin delta
- segment-level response

Guardrail metrics:
- cancellation rate
- margin dilution
- cannibalization risk
- confidence in result

## 4. Statistical readout

The workbench compares control and treatment changes before/after the intervention. It calculates:
- treatment vs control uplift
- confidence interval
- p-value
- segment readout
- margin impact

## 5. Scenario and elasticity-style modelling

A scenario slider estimates how different incentive levels may affect bookings and margin by segment. This is not a true causal elasticity estimate; it is a pricing scenario model.

## 6. Incrementality and cannibalization

The workbench separates gross uplift from estimated net incremental uplift after cannibalization adjustment. This prevents an apparently successful pricing action from being accepted without checking whether demand shifted from other segments.

## 7. AI-assisted workflow

The AI layer does not produce facts. The deterministic Python/statistical layer produces facts. The AI layer transforms those validated facts into:
- executive memo
- risks and guardrails
- limitations
- next-test proposal
- stakeholder-ready decision narrative

## 8. Human-in-the-loop principle

The recommendation is not auto-approved. It is a structured decision-support output for a pricing manager or leadership team.
