"""Legacy standalone synthetic-data generator.

This file is retained only as an earlier development artifact / standalone demo.

IMPORTANT:
- It is NOT used by the deployed Streamlit application.
- It is NOT the provenance of the current public-data-based workbench.
- The authoritative deployed application is repository-root ``app.py``.
- The current app starts from public Hotel Booking Demand observations (or the
  checked-in processed base panel) and rebuilds a transparent synthetic
  pricing-treatment layer deterministically.

See README.md and docs/methodology.md for the current methodology.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_partner_pricing_data(n_partners=900, seed=42):
    rng = np.random.default_rng(seed)

    segments = np.array(["Growth", "Core", "Premium", "Long Tail"])
    regions = np.array(["North Europe", "West Europe", "South Europe", "Central Europe"])
    channels = np.array(["Direct", "Affiliate", "Mobile", "Corporate"])

    partner_id = np.arange(100000, 100000 + n_partners)
    partner_segment = rng.choice(segments, size=n_partners, p=[0.26, 0.42, 0.16, 0.16])
    region = rng.choice(regions, size=n_partners, p=[0.24, 0.33, 0.23, 0.20])
    channel = rng.choice(channels, size=n_partners, p=[0.45, 0.20, 0.25, 0.10])

    quality_score = np.clip(rng.normal(78, 10, n_partners), 35, 98)
    price_band = rng.choice(["Budget", "Midscale", "Upscale"], size=n_partners, p=[0.34, 0.48, 0.18])

    base_bookings = rng.gamma(shape=8, scale=18, size=n_partners)
    segment_multiplier = np.select(
        [partner_segment == "Growth", partner_segment == "Core", partner_segment == "Premium", partner_segment == "Long Tail"],
        [1.10, 1.00, 1.22, 0.68],
        default=1.0,
    )
    quality_multiplier = 0.65 + quality_score / 100
    bookings_baseline = np.maximum(5, base_bookings * segment_multiplier * quality_multiplier).round()

    adr = np.select(
        [price_band == "Budget", price_band == "Midscale", price_band == "Upscale"],
        [rng.normal(82, 14, n_partners), rng.normal(135, 22, n_partners), rng.normal(230, 44, n_partners)],
    )
    adr = np.clip(adr, 45, 420)

    baseline_commission = np.select(
        [partner_segment == "Growth", partner_segment == "Core", partner_segment == "Premium", partner_segment == "Long Tail"],
        [0.155, 0.165, 0.175, 0.150],
        default=0.16,
    )

    eligible = ((partner_segment == "Growth") | (partner_segment == "Core")) & (quality_score > 67)
    treatment = np.zeros(n_partners, dtype=int)
    eligible_idx = np.where(eligible)[0]
    treatment[eligible_idx] = rng.binomial(1, 0.50, len(eligible_idx))

    true_uplift = np.select(
        [partner_segment == "Growth", partner_segment == "Core", partner_segment == "Premium", partner_segment == "Long Tail"],
        [0.105, 0.045, 0.010, 0.000],
        default=0.0,
    )

    incentive_rate = np.where(treatment == 1, 0.025, 0.000)
    cannibalization_pressure = np.where(
        (region == "West Europe") & (price_band == "Midscale"), 0.025, 0.010
    )
    noise = rng.normal(0, 0.09, n_partners)

    # Gross/direct response only. Cannibalization is intentionally NOT embedded
    # here so downstream incrementality logic can deduct it exactly once.
    bookings_after = bookings_baseline * (1 + treatment * true_uplift + noise)
    bookings_after = np.maximum(1, bookings_after).round()

    gross_revenue_before = bookings_baseline * adr
    gross_revenue_after = bookings_after * adr

    net_take_rate_before = baseline_commission
    net_take_rate_after = np.maximum(0.10, baseline_commission - incentive_rate)

    platform_margin_before = gross_revenue_before * net_take_rate_before
    platform_margin_after = gross_revenue_after * net_take_rate_after

    cancellation_rate_before = np.clip(
        0.18 - quality_score / 900 + rng.normal(0, 0.025, n_partners), 0.03, 0.36
    )
    cancellation_rate_after = np.clip(
        cancellation_rate_before
        + np.where(
            treatment == 1,
            rng.normal(0.005, 0.015, n_partners),
            rng.normal(0.0, 0.012, n_partners),
        ),
        0.02,
        0.40,
    )

    df = pd.DataFrame(
        {
            "partner_id": partner_id,
            "partner_segment": partner_segment,
            "region": region,
            "channel": channel,
            "price_band": price_band,
            "quality_score": quality_score.round(1),
            "eligible_for_test": eligible.astype(int),
            "treatment_group": treatment,
            "baseline_commission_rate": baseline_commission,
            "test_incentive_rate": incentive_rate,
            "bookings_before": bookings_baseline.astype(int),
            "bookings_after": bookings_after.astype(int),
            "adr": adr.round(2),
            "gross_revenue_before": gross_revenue_before.round(2),
            "gross_revenue_after": gross_revenue_after.round(2),
            "platform_margin_before": platform_margin_before.round(2),
            "platform_margin_after": platform_margin_after.round(2),
            "cancellation_rate_before": cancellation_rate_before.round(4),
            "cancellation_rate_after": cancellation_rate_after.round(4),
            "cannibalization_pressure": cannibalization_pressure.round(4),
        }
    )

    df["booking_delta"] = df["bookings_after"] - df["bookings_before"]
    df["revenue_delta"] = df["gross_revenue_after"] - df["gross_revenue_before"]
    df["margin_delta"] = df["platform_margin_after"] - df["platform_margin_before"]
    return df


if __name__ == "__main__":
    out = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "synthetic"
        / "b2b_pricing_experiment_synthetic_data.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    df = generate_partner_pricing_data()
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
