# Executive Summary - B2B Pricing Experimentation Workbench

## Business question

Should a digital marketplace offer a pricing incentive to selected partner segments to increase incremental bookings without damaging margin, quality, cancellation guardrails or other partner/customer segments?

## Decision workflow

The workbench follows a pricing-manager decision path:

1. Define the business question.
2. Identify eligible partner segments.
3. Create treatment/control assignment.
4. Measure booking uplift.
5. Check revenue and margin impact.
6. Check guardrails.
7. Estimate net incrementality after cannibalization adjustment.
8. Produce recommendation: scale, stop, retest, or narrow eligibility.
9. Generate an executive memo for human review.

## Why this matters

A pricing action can look successful if bookings increase, but still be commercially weak if:

- margin is diluted,
- uplift is not incremental,
- demand is cannibalized from other segments,
- cancellation or quality guardrails deteriorate,
- or the result is not statistically reliable.

This project demonstrates how to avoid that mistake.

## AI-enabled productivity angle

The AI layer is used after deterministic analysis. It converts validated facts into:

- executive memo,
- risks and guardrails,
- next-test proposal,
- limitations,
- stakeholder-ready decision narrative.

This improves productivity without allowing AI to invent facts or bypass human judgement.

## Data transparency

The project uses real public hotel-booking data as the base and a documented synthetic treatment layer for B2B pricing experiment fields that are unavailable in public data.

No proprietary company data is used.
