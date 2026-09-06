# Executive Summary - B2B Pricing Experimentation Workbench

## Business question

Should a digital marketplace offer a pricing incentive to selected partner segments to increase incremental bookings without damaging margin, cancellation guardrails or other partner/customer segments?

## Decision workflow

The workbench follows a pricing-manager decision path:

1. Define the business question.
2. Freeze pre-treatment eligibility for the Growth/Core partner-segment proxies.
3. Randomize eligible observations into treatment and control with fixed seed 42.
4. Measure booking uplift versus the control trend.
5. Check revenue and platform-margin impact.
6. Check cancellation and statistical guardrails.
7. Estimate net incrementality after a one-time cannibalization adjustment.
8. Produce a recommendation: scale, narrow target, retest, or do not scale.
9. Generate an AI-ready executive-memo prompt pack for human review.

## Why this matters

A pricing action can look successful if bookings increase, but still be commercially weak if:

- margin is diluted,
- uplift is not incremental,
- demand is cannibalized from other segments,
- cancellation guardrails deteriorate,
- or the result is not statistically reliable.

The workbench demonstrates how to structure these trade-offs rather than optimize volume alone.

## Experiment-governance corrections

The current version explicitly prevents two common analytical errors:

- The same booking's eventual cancellation outcome is not used to determine eligibility; cancellation is retained only as an outcome guardrail.
- Cannibalization is not embedded in the gross response and then deducted again. It is applied once in the incrementality bridge.

## AI-enabled productivity angle

Python and statistics calculate the facts first. The public app then creates a governed prompt pack containing validated facts, limitations and the requested decision structure.

The app itself does not call an LLM. This preserves human accountability while showing how AI can accelerate executive communication after the analytical layer is complete.

## Data transparency

The project uses real public hotel-booking observations as the base and a documented synthetic treatment layer for B2B pricing experiment fields that are unavailable in public data.

No proprietary company data is used, and the project does not claim real Booking.com or production marketplace causal effects.
