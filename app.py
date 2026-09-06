from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from scipy import stats


st.set_page_config(page_title="B2B Pricing Experimentation Workbench", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent
PUBLIC_DATA = PROJECT_ROOT / "data" / "public" / "hotel_bookings.csv"
PROCESSED_DATA = PROJECT_ROOT / "data" / "processed" / "hotel_pricing_experiment_panel.csv"
EXPERIMENT_SEED = 42


def _segment_proxy(df: pd.DataFrame) -> pd.Series:
    rules = [
        df["market_segment"].isin(["Online TA", "Offline TA/TO"]),
        df["market_segment"].isin(["Corporate", "Groups"]),
        df["adr"] >= df["adr"].quantile(0.75),
        df["adr"] <= df["adr"].quantile(0.25),
    ]
    values = ["Core", "Growth", "Premium", "Long Tail"]
    return pd.Series(np.select(rules, values, default="Core"), index=df.index)


def _region_proxy(country: pd.Series) -> pd.Series:
    return pd.Series(
        np.select(
            [
                country.isin(["PRT", "ESP", "FRA", "ITA"]),
                country.isin(["GBR", "IRL", "DEU", "NLD", "BEL"]),
                country.isin(["USA", "CAN", "BRA", "MEX"]),
            ],
            ["South Europe", "West/North Europe", "Americas"],
            default="Other",
        ),
        index=country.index,
    )


def _prepare_public_base(raw: pd.DataFrame, seed: int = EXPERIMENT_SEED) -> pd.DataFrame:
    required = {
        "hotel",
        "country",
        "market_segment",
        "lead_time",
        "adr",
        "stays_in_weekend_nights",
        "stays_in_week_nights",
        "is_canceled",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Public source is missing required columns: {missing}")

    df = raw.copy()
    df = df[df["adr"].notna()]
    df = df[(df["adr"] > 0) & (df["adr"] < 1000)]
    df = df.sample(min(len(df), 25000), random_state=seed).reset_index(drop=True)

    df["partner_id"] = (
        df["hotel"].astype(str).str[:1]
        + "_"
        + df["country"].fillna("UNK").astype(str)
        + "_"
        + df["market_segment"].fillna("UNK").astype(str)
        + "_"
        + (df.index % 700).astype(str)
    )
    df["partner_segment"] = _segment_proxy(df)
    df["region_proxy"] = _region_proxy(df["country"].fillna("UNK"))
    df["lead_time_band"] = pd.cut(
        df["lead_time"].fillna(0).clip(0, 365),
        bins=[-1, 7, 30, 90, 365],
        labels=["0-7d", "8-30d", "31-90d", "90d+"],
    ).astype(str)
    df["cancellation_rate_proxy"] = df["is_canceled"].astype(float)
    return df


def _ensure_base_columns(base: pd.DataFrame) -> pd.DataFrame:
    """Normalize either the public source sample or the checked-in cloud base panel.

    Any synthetic fields from an earlier version are overwritten by
    rebuild_experiment_layer(). Cancellation is retained only as an outcome
    guardrail and is never used to determine eligibility.
    """
    df = base.copy().reset_index(drop=True)

    if "adr" not in df.columns or "lead_time" not in df.columns:
        raise ValueError("Base data must include adr and lead_time.")

    if "partner_segment" not in df.columns:
        if "market_segment" not in df.columns:
            raise ValueError("Base data must include market_segment or partner_segment.")
        df["partner_segment"] = _segment_proxy(df)

    if "country" not in df.columns:
        df["country"] = "UNK"
    if "region_proxy" not in df.columns:
        df["region_proxy"] = _region_proxy(df["country"].fillna("UNK"))

    if "lead_time_band" not in df.columns:
        df["lead_time_band"] = pd.cut(
            df["lead_time"].fillna(0).clip(0, 365),
            bins=[-1, 7, 30, 90, 365],
            labels=["0-7d", "8-30d", "31-90d", "90d+"],
        ).astype(str)

    if "partner_id" not in df.columns:
        hotel = (
            df["hotel"].astype(str).str[:1]
            if "hotel" in df.columns
            else pd.Series("H", index=df.index)
        )
        market = (
            df["market_segment"].fillna("UNK").astype(str)
            if "market_segment" in df.columns
            else pd.Series("UNK", index=df.index)
        )
        df["partner_id"] = (
            hotel
            + "_"
            + df["country"].fillna("UNK").astype(str)
            + "_"
            + market
            + "_"
            + (df.index % 700).astype(str)
        )

    if "cancellation_rate_proxy" not in df.columns:
        if "is_canceled" in df.columns:
            df["cancellation_rate_proxy"] = df["is_canceled"].astype(float)
        else:
            df["cancellation_rate_proxy"] = np.nan

    return df


def rebuild_experiment_layer(base: pd.DataFrame, seed: int = EXPERIMENT_SEED) -> pd.DataFrame:
    """Build a reproducible synthetic pricing experiment from pre-treatment features.

    Governance rules:
    1. Same-booking cancellation is excluded from eligibility.
    2. Treatment is randomized only after eligibility is frozen.
    3. Gross/direct response does not subtract cannibalization.
    4. Cannibalization is deducted once in the incrementality bridge.
    """
    df = _ensure_base_columns(base)
    rng = np.random.default_rng(seed)

    segment_quality = df["partner_segment"].map(
        {"Growth": 3.0, "Core": 1.5, "Premium": 4.0, "Long Tail": -2.0}
    ).fillna(0.0)
    lead_time_penalty = 0.035 * df["lead_time"].fillna(0).clip(0, 180)
    repeat_bonus = (
        3.0 * df["is_repeated_guest"].fillna(0).astype(float)
        if "is_repeated_guest" in df.columns
        else 0.0
    )

    df["quality_score_proxy"] = np.clip(
        79.0 + segment_quality - lead_time_penalty + repeat_bonus + rng.normal(0, 5, len(df)),
        35,
        99,
    )

    df["baseline_commission_rate"] = np.select(
        [
            df["partner_segment"] == "Growth",
            df["partner_segment"] == "Core",
            df["partner_segment"] == "Premium",
            df["partner_segment"] == "Long Tail",
        ],
        [0.155, 0.165, 0.175, 0.150],
        default=0.160,
    )

    eligible = df["partner_segment"].isin(["Growth", "Core"]) & (df["quality_score_proxy"] > 67)
    df["eligible_for_test"] = eligible.astype(int)

    df["treatment_group"] = 0
    eligible_idx = df.index[df["eligible_for_test"] == 1]
    df.loc[eligible_idx, "treatment_group"] = rng.binomial(1, 0.5, len(eligible_idx))

    segment_effect = np.select(
        [
            df["partner_segment"] == "Growth",
            df["partner_segment"] == "Core",
            df["partner_segment"] == "Premium",
            df["partner_segment"] == "Long Tail",
        ],
        [0.090, 0.045, 0.015, 0.000],
        default=0.030,
    )

    if {"stays_in_weekend_nights", "stays_in_week_nights"}.issubset(df.columns):
        nights = (
            df["stays_in_weekend_nights"].fillna(0)
            + df["stays_in_week_nights"].fillna(0)
        ).clip(1, 30)
    elif "gross_booking_value_before" in df.columns:
        nights = (
            df["gross_booking_value_before"] / df["adr"].replace(0, np.nan)
        ).fillna(1).clip(1, 30)
    else:
        nights = pd.Series(1.0, index=df.index)

    df["gross_booking_value_before"] = df["adr"] * nights
    df["booking_units_before"] = 1.0
    df["test_incentive_rate"] = np.where(df["treatment_group"] == 1, 0.025, 0.000)
    df["cannibalization_pressure"] = np.where(
        (df["region_proxy"] == "West/North Europe")
        & df["lead_time_band"].isin(["8-30d", "31-90d"]),
        0.025,
        0.010,
    )

    response_noise = rng.normal(0, 0.06, len(df))
    response_multiplier = 1 + df["treatment_group"] * segment_effect + response_noise
    response_multiplier = np.clip(response_multiplier, 0.70, 1.30)

    df["booking_units_after"] = df["booking_units_before"] * response_multiplier
    df["gross_booking_value_after"] = df["gross_booking_value_before"] * response_multiplier
    df["platform_margin_before"] = df["gross_booking_value_before"] * df["baseline_commission_rate"]
    df["platform_margin_after"] = df["gross_booking_value_after"] * np.maximum(
        0.10, df["baseline_commission_rate"] - df["test_incentive_rate"]
    )

    df["booking_delta"] = df["booking_units_after"] - df["booking_units_before"]
    df["revenue_delta"] = df["gross_booking_value_after"] - df["gross_booking_value_before"]
    df["margin_delta"] = df["platform_margin_after"] - df["platform_margin_before"]

    keep = [
        "partner_id",
        "hotel",
        "arrival_date_year",
        "arrival_date_month",
        "country",
        "market_segment",
        "distribution_channel",
        "reserved_room_type",
        "customer_type",
        "lead_time",
        "lead_time_band",
        "adr",
        "partner_segment",
        "region_proxy",
        "quality_score_proxy",
        "eligible_for_test",
        "treatment_group",
        "baseline_commission_rate",
        "test_incentive_rate",
        "booking_units_before",
        "booking_units_after",
        "gross_booking_value_before",
        "gross_booking_value_after",
        "platform_margin_before",
        "platform_margin_after",
        "booking_delta",
        "revenue_delta",
        "margin_delta",
        "cancellation_rate_proxy",
        "cannibalization_pressure",
    ]
    return df[[c for c in keep if c in df.columns]].copy()


@st.cache_data
def build_panel(seed: int = EXPERIMENT_SEED):
    if PUBLIC_DATA.exists():
        raw = pd.read_csv(PUBLIC_DATA)
        base = _prepare_public_base(raw, seed=seed)
        source = "public source file"
    elif PROCESSED_DATA.exists():
        base = pd.read_csv(PROCESSED_DATA)
        source = "processed deployment panel"
    else:
        raise FileNotFoundError(
            "No data file found. Expected data/public/hotel_bookings.csv or "
            "data/processed/hotel_pricing_experiment_panel.csv."
        )

    return rebuild_experiment_layer(base, seed=seed), source


def summarize_experiment(df: pd.DataFrame) -> dict:
    test_df = df[df["eligible_for_test"] == 1].copy()
    control = test_df[test_df["treatment_group"] == 0]
    treatment = test_df[test_df["treatment_group"] == 1]

    if len(control) < 2 or len(treatment) < 2:
        raise ValueError("Not enough eligible treatment/control observations for this view.")

    def rel_change(after, before):
        return (after.sum() - before.sum()) / max(before.sum(), 1e-9)

    ctrl_booking = rel_change(control["booking_units_after"], control["booking_units_before"])
    trt_booking = rel_change(treatment["booking_units_after"], treatment["booking_units_before"])
    booking_uplift = trt_booking - ctrl_booking

    ctrl_margin = rel_change(control["platform_margin_after"], control["platform_margin_before"])
    trt_margin = rel_change(treatment["platform_margin_after"], treatment["platform_margin_before"])
    margin_uplift = trt_margin - ctrl_margin

    c_delta = (
        (control["booking_units_after"] - control["booking_units_before"])
        / control["booking_units_before"]
    ).dropna()
    t_delta = (
        (treatment["booking_units_after"] - treatment["booking_units_before"])
        / treatment["booking_units_before"]
    ).dropna()

    _, p_value = stats.ttest_ind(t_delta, c_delta, equal_var=False)
    diff = t_delta.mean() - c_delta.mean()
    se = np.sqrt(t_delta.var(ddof=1) / len(t_delta) + c_delta.var(ddof=1) / len(c_delta))

    cancellation_guardrail = np.nan
    if (
        treatment["cancellation_rate_proxy"].notna().any()
        and control["cancellation_rate_proxy"].notna().any()
    ):
        cancellation_guardrail = (
            treatment["cancellation_rate_proxy"].mean()
            - control["cancellation_rate_proxy"].mean()
        )

    return {
        "eligible_observations": len(test_df),
        "eligible_partner_proxies": test_df["partner_id"].nunique(),
        "treatment_observations": len(treatment),
        "control_observations": len(control),
        "booking_uplift": booking_uplift,
        "margin_uplift": margin_uplift,
        "p_value": p_value,
        "ci_low": diff - 1.96 * se,
        "ci_high": diff + 1.96 * se,
        "treatment_margin_delta": treatment["margin_delta"].sum(),
        "treatment_revenue_delta": treatment["revenue_delta"].sum(),
        "cancellation_guardrail": cancellation_guardrail,
    }


def decision(summary: dict):
    cancellation = summary["cancellation_guardrail"]
    if pd.notna(cancellation) and cancellation > 0.02:
        return (
            "Do Not Scale",
            "The cancellation guardrail deteriorates by more than 2 percentage points.",
            "Stop rollout and redesign eligibility or incentive mechanics before another controlled test.",
        )
    if (
        summary["booking_uplift"] > 0.035
        and summary["margin_uplift"] > 0
        and summary["p_value"] < 0.10
    ):
        return (
            "Scale",
            "Positive demand and margin signal with sufficient directional evidence.",
            "Scale only within the tested eligible segments, with margin and cancellation guardrails monitored.",
        )
    if summary["booking_uplift"] > 0.02 and summary["margin_uplift"] <= 0:
        return (
            "Narrow Target",
            "Bookings improve, but margin is diluted.",
            "Reduce incentive exposure and retest the strongest eligible segment before broader rollout.",
        )
    if summary["booking_uplift"] > 0.02:
        return (
            "Retest",
            "Directional booking uplift exists, but the commercial evidence is not yet strong enough.",
            "Run a larger or longer controlled test and keep rollout exposure limited until the result is clearer.",
        )
    return (
        "Do Not Scale",
        "Evidence is not strong enough for rollout.",
        "Revisit incentive economics and eligibility, then redesign the next test before scaling.",
    )


def prompt_pack(summary: dict, focus: str) -> str:
    guardrail = (
        f"{summary['cancellation_guardrail']:.2%}"
        if pd.notna(summary["cancellation_guardrail"])
        else "not available"
    )
    return f"""
You are a senior pricing analytics advisor. Draft an executive memo from these validated facts.

Context: public hotel-booking data enriched with a transparent synthetic pricing-treatment layer. No proprietary company data is used.
Segment focus: {focus}

Facts:
- Eligible observations: {summary['eligible_observations']}
- Unique partner proxies: {summary['eligible_partner_proxies']}
- Treatment observations: {summary['treatment_observations']}
- Control observations: {summary['control_observations']}
- Booking uplift vs control trend: {summary['booking_uplift']:.2%}
- Margin uplift vs control trend: {summary['margin_uplift']:.2%}
- 95% confidence interval: {summary['ci_low']:.2%} to {summary['ci_high']:.2%}
- p-value: {summary['p_value']:.4f}
- Treatment revenue delta: EUR {summary['treatment_revenue_delta']:,.0f}
- Treatment margin delta: EUR {summary['treatment_margin_delta']:,.0f}
- Cancellation guardrail difference: {guardrail}

Return: recommendation, commercial rationale, risks/guardrails, next experiment, and limitations.
Do not claim real Booking.com effects or production causal estimates.
""".strip()


def advanced_sql_example() -> str:
    return """
WITH eligible AS (
    SELECT
        partner_id,
        partner_segment,
        treatment_group,
        booking_units_after - booking_units_before AS booking_delta,
        gross_booking_value_after - gross_booking_value_before AS revenue_delta,
        platform_margin_after - platform_margin_before AS margin_delta
    FROM hotel_pricing_experiment_panel
    WHERE eligible_for_test = 1
),
group_metrics AS (
    SELECT
        partner_segment,
        treatment_group,
        COUNT(*) AS observations,
        COUNT(DISTINCT partner_id) AS partner_proxies,
        AVG(booking_delta) AS avg_booking_delta,
        SUM(revenue_delta) AS revenue_delta,
        SUM(margin_delta) AS margin_delta
    FROM eligible
    GROUP BY partner_segment, treatment_group
),
segment_readout AS (
    SELECT
        partner_segment,
        MAX(CASE WHEN treatment_group = 1 THEN avg_booking_delta END)
          - MAX(CASE WHEN treatment_group = 0 THEN avg_booking_delta END) AS booking_uplift_vs_control,
        MAX(CASE WHEN treatment_group = 1 THEN margin_delta END) AS treatment_margin_delta,
        SUM(observations) AS total_observations
    FROM group_metrics
    GROUP BY partner_segment
)
SELECT
    partner_segment,
    booking_uplift_vs_control,
    treatment_margin_delta,
    total_observations,
    DENSE_RANK() OVER (ORDER BY booking_uplift_vs_control DESC) AS uplift_rank
FROM segment_readout
ORDER BY uplift_rank, partner_segment;
""".strip()


def main():
    st.title("B2B Pricing Experimentation Workbench")
    st.caption("Public hotel-booking base + governed synthetic pricing experiment")
    st.info(
        "Public hotel-booking data provides the base observations. A documented synthetic treatment layer "
        "adds partner incentives, randomized treatment/control assignment and marketplace economics. "
        "Eligibility uses pre-treatment proxies only; cancellation is an outcome guardrail."
    )

    try:
        df, source = build_panel()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()

    with st.sidebar:
        st.header("Experiment View")
        focus = st.selectbox("Eligible partner-segment focus", ["All eligible", "Growth", "Core"])
        st.caption(f"Experiment seed is fixed at {EXPERIMENT_SEED} for reproducibility.")
        st.markdown("---")
        st.subheader("Data source")
        st.write("Base: public Hotel Booking Demand data")
        st.caption(f"Deployment source: {source}")
        st.write("Synthetic layer: treatment/control assignment, incentives and marketplace economics")

    view = df if focus == "All eligible" else df[df["partner_segment"] == focus].copy()
    try:
        summary = summarize_experiment(view)
    except ValueError as exc:
        st.warning(str(exc))
        st.stop()

    label, rationale, action = decision(summary)

    m1, m2, m3, m4 = st.columns([1, 1, 1, 1.25])
    m1.metric("Eligible observations", f"{summary['eligible_observations']:,}")
    m2.metric("Booking uplift", f"{summary['booking_uplift']:.1%}")
    m3.metric("Margin uplift", f"{summary['margin_uplift']:.1%}")
    m4.markdown("**Decision**")
    m4.markdown(f"## {label}")

    st.markdown("### Decision Snapshot")
    st.write(f"**Decision:** {label}")
    st.write(f"**Why:** {rationale}")
    st.write(f"**Action:** {action}")

    tabs = st.tabs(
        [
            "Executive Decision",
            "Experiment Design",
            "Test Readout",
            "Scenario / Elasticity",
            "Incrementality",
            "AI-ready Memo",
            "Data + SQL",
        ]
    )

    with tabs[0]:
        st.header("Executive Decision")
        guardrail_text = (
            f"{summary['cancellation_guardrail']:.1%}"
            if pd.notna(summary["cancellation_guardrail"])
            else "not available"
        )
        st.markdown(
            f"""
**Recommendation:** {label}

**Business interpretation:** {rationale}

**Observed signal**
- Booking uplift vs control trend: **{summary['booking_uplift']:.1%}**
- Margin uplift vs control trend: **{summary['margin_uplift']:.1%}**
- 95% confidence interval for booking response: **{summary['ci_low']:.1%} to {summary['ci_high']:.1%}**
- Statistical p-value: **{summary['p_value']:.3f}**
- Cancellation guardrail difference: **{guardrail_text}**

**Limitations**
- Public hotel-booking base data; synthetic partner-pricing treatment layer.
- This is a portfolio demonstration, not a production causal estimate.
- Real deployment would require power analysis, verified randomized assignment, seasonality and channel controls, partner economics, governance and longer post-test monitoring.
"""
        )

    with tabs[1]:
        st.header("Experiment Design")
        st.write(
            "Eligibility is frozen before treatment using Growth/Core partner-segment proxies and a synthetic "
            "pre-treatment quality score built from segment, lead time and fixed-seed variation."
        )
        st.write(
            "The same booking's eventual cancellation outcome is explicitly excluded from eligibility and is used only as an outcome guardrail."
        )
        st.write("Eligible observations are randomized 50/50 into treatment and control with fixed seed 42.")
        st.write("Treatment receives a synthetic commission discount / incentive. Control does not.")
        st.write(
            "Success metrics: booking uplift, revenue delta and margin delta. Guardrails: margin dilution, cancellation, cannibalization and statistical confidence."
        )

    with tabs[2]:
        st.header("Test Readout")
        exp = view[view["eligible_for_test"] == 1].copy()
        exp["group"] = np.where(exp["treatment_group"] == 1, "Treatment", "Control")
        exp["booking_change_pct"] = (
            exp["booking_units_after"] - exp["booking_units_before"]
        ) / exp["booking_units_before"]
        exp["margin_change_pct"] = (
            exp["platform_margin_after"] - exp["platform_margin_before"]
        ) / exp["platform_margin_before"]

        metric = st.selectbox(
            "Metric",
            ["booking_change_pct", "margin_change_pct", "revenue_delta", "margin_delta"],
        )
        st.plotly_chart(
            px.box(exp, x="group", y=metric, color="group", title=f"Control vs Treatment: {metric}"),
            width="stretch",
        )
        seg = exp.groupby(["partner_segment", "group"], as_index=False).agg(
            observations=("partner_id", "count"),
            partner_proxies=("partner_id", "nunique"),
            booking_delta=("booking_delta", "sum"),
            revenue_delta=("revenue_delta", "sum"),
            margin_delta=("margin_delta", "sum"),
            avg_adr=("adr", "mean"),
        )
        st.dataframe(seg, width="stretch")

    with tabs[3]:
        st.header("Scenario / Elasticity-Style Modelling")
        st.write("This is a scenario model, not a true causal elasticity estimate.")
        incentive = st.slider("Scenario incentive level", 0.0, 6.0, 2.5, 0.5)

        eligible = view[view["eligible_for_test"] == 1].copy()
        inc = incentive / 100.0
        response = np.select(
            [eligible["partner_segment"] == "Growth", eligible["partner_segment"] == "Core"],
            [1.9, 1.1],
            default=0.8,
        )
        expected_lift = np.clip(inc * response, 0, 0.18)
        expected_value = eligible["gross_booking_value_before"] * (1 + expected_lift)
        expected_margin = expected_value * np.maximum(
            0.10, eligible["baseline_commission_rate"] - inc
        )

        scen = eligible.assign(
            expected_booking_lift=expected_lift,
            expected_margin=expected_margin,
        ).groupby("partner_segment", as_index=False).agg(
            expected_booking_lift=("expected_booking_lift", "mean"),
            baseline_margin=("platform_margin_before", "sum"),
            expected_margin=("expected_margin", "sum"),
        )
        scen["expected_margin_lift"] = (
            scen["expected_margin"] - scen["baseline_margin"]
        ) / scen["baseline_margin"]

        overall_booking_lift = float(expected_lift.mean()) if len(expected_lift) else np.nan
        overall_margin_lift = (
            (expected_margin.sum() - eligible["platform_margin_before"].sum())
            / max(eligible["platform_margin_before"].sum(), 1e-9)
        )
        s1, s2, s3 = st.columns(3)
        s1.metric("Selected incentive", f"{incentive:.1f}%")
        s2.metric("Expected booking lift", f"{overall_booking_lift:.1%}")
        s3.metric("Expected margin lift", f"{overall_margin_lift:.1%}")
        st.dataframe(scen, width="stretch")
        st.plotly_chart(
            px.bar(
                scen,
                x="partner_segment",
                y=["expected_booking_lift", "expected_margin_lift"],
                barmode="group",
            ),
            width="stretch",
        )

    with tabs[4]:
        st.header("Incrementality and Cannibalization")
        trt = view[
            (view["eligible_for_test"] == 1) & (view["treatment_group"] == 1)
        ].copy()
        gross = trt["booking_delta"].sum()
        cannibalization = np.maximum(
            0, trt["booking_units_after"] * trt["cannibalization_pressure"]
        ).sum()
        net = gross - cannibalization

        c1, c2, c3 = st.columns(3)
        c1.metric("Gross direct uplift units", f"{gross:,.0f}")
        c2.metric("Cannibalization adjustment", f"{cannibalization:,.0f}")
        c3.metric("Net incremental units", f"{net:,.0f}")
        st.caption(
            "Cannibalization is deducted exactly once in this bridge; it is not embedded in the gross direct-response simulation."
        )
        st.plotly_chart(
            px.bar(
                pd.DataFrame(
                    {
                        "Step": ["Gross direct uplift", "Cannibalization", "Net incremental"],
                        "Units": [gross, -cannibalization, net],
                    }
                ),
                x="Step",
                y="Units",
            ),
            width="stretch",
        )

    with tabs[5]:
        st.header("AI-ready Executive Memo")
        st.write(
            "This tab generates a governed prompt pack after deterministic calculations. It does not call an LLM or claim autonomous decision-making."
        )
        st.code(prompt_pack(summary, focus), language="text")

    with tabs[6]:
        st.header("Data + SQL")
        st.write("Base source: **public Hotel Booking Demand data**")
        st.caption(f"Deployment source: {source}")
        st.write(
            "The downloadable panel below contains the corrected in-memory experiment layer used by this dashboard."
        )
        st.dataframe(view.head(100), width="stretch")
        st.subheader("SQL example: experiment readout with CTEs and window ranking")
        st.code(advanced_sql_example(), language="sql")
        st.download_button(
            "Download processed pricing experiment panel",
            data=view.to_csv(index=False).encode("utf-8"),
            file_name="hotel_pricing_experiment_panel.csv",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
