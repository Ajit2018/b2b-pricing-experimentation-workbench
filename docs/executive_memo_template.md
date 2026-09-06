# Executive Memo Template

This template is intended for human review after deterministic analysis. The public dashboard generates an AI-ready prompt pack from validated facts; it does not call an LLM itself.

## Decision

Scale / narrow target / retest / do not scale.

## Business question

Should the pricing incentive be rolled out to the selected eligible partner segment?

## Evidence

- Booking uplift vs control:
- Margin uplift vs control:
- 95% confidence interval:
- p-value:
- Cancellation guardrail difference:
- Gross direct uplift:
- Cannibalization adjustment:
- Net incrementality:

## Recommendation

State the decision and why.

## Commercial rationale

Explain booking, revenue, margin and partner/customer implications.

## Risks and guardrails

- margin dilution
- weak statistical confidence
- cancellation deterioration
- cannibalization
- eligibility bias
- seasonality / channel confounding in a real deployment
- data-quality limitations

## Next test

Define the next experiment design, target segment, sample-size/power requirement, duration, guardrail metrics and decision threshold.

## Limitations

State clearly that this case study uses public hotel-booking observations plus a synthetic pricing-treatment layer, does not use proprietary company data, and does not claim production causal estimates.
