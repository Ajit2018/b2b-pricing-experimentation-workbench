
import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title="B2B Pricing Experimentation Workbench", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent
PUBLIC_DATA = PROJECT_ROOT / "data" / "public" / "hotel_bookings.csv"
PROCESSED_DATA = PROJECT_ROOT / "data" / "processed" / "hotel_pricing_experiment_panel.csv"

@st.cache_data
def build_panel(seed=42):
    if not PUBLIC_DATA.exists():
        if PROCESSED_DATA.exists():
            return pd.read_csv(PROCESSED_DATA)
        st.error(
            "No data file found. Expected either data/public/hotel_bookings.csv "
            "for local rebuild or data/processed/hotel_pricing_experiment_panel.csv "
            "for cloud deployment."
        )
        st.stop()

    raw = pd.read_csv(PUBLIC_DATA)
    rng = np.random.default_rng(seed)

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

    segment_rules = [
        df["market_segment"].isin(["Online TA", "Offline TA/TO"]),
        df["market_segment"].isin(["Corporate", "Groups"]),
        df["adr"] >= df["adr"].quantile(0.75),
        df["adr"] <= df["adr"].quantile(0.25),
    ]
    segment_values = ["Core", "Growth", "Premium", "Long Tail"]
    df["partner_segment"] = np.select(segment_rules, segment_values, default="Core")

    df["region_proxy"] = np.select(
        [
            df["country"].isin(["PRT", "ESP", "FRA", "ITA"]),
            df["country"].isin(["GBR", "IRL", "DEU", "NLD", "BEL"]),
            df["country"].isin(["USA", "CAN", "BRA", "MEX"]),
        ],
        ["South Europe", "West/North Europe", "Americas"],
        default="Other"
    )

    df["lead_time_band"] = pd.cut(
        df["lead_time"].clip(0, 365),
        bins=[-1, 7, 30, 90, 365],
        labels=["0-7d", "8-30d", "31-90d", "90d+"]
    ).astype(str)

    df["quality_score_proxy"] = np.clip(
        85 - 25 * df["is_canceled"].astype(float)
        - 2.5 * df["previous_cancellations"].fillna(0).clip(0, 4)
        + rng.normal(0, 7, len(df)),
        35, 99
    )

    df["baseline_commission_rate"] = np.select(
        [df["partner_segment"] == "Growth", df["partner_segment"] == "Core", df["partner_segment"] == "Premium", df["partner_segment"] == "Long Tail"],
        [0.155, 0.165, 0.175, 0.150],
        default=0.160
    )

    eligible = df["partner_segment"].isin(["Growth", "Core"]) & (df["quality_score_proxy"] > 67) & (df["is_canceled"] == 0)
    df["eligible_for_test"] = eligible.astype(int)
    df["treatment_group"] = 0
    idx = df.index[df["eligible_for_test"] == 1]
    df.loc[idx, "treatment_group"] = rng.binomial(1, 0.5, len(idx))

    segment_effect = np.select(
        [df["partner_segment"] == "Growth", df["partner_segment"] == "Core", df["partner_segment"] == "Premium", df["partner_segment"] == "Long Tail"],
        [0.090, 0.045, 0.015, 0.000],
        default=0.030
    )

    nights = (df["stays_in_weekend_nights"].fillna(0) + df["stays_in_week_nights"].fillna(0)).clip(1, 30)
    df["gross_booking_value_before"] = df["adr"] * nights
    df["booking_units_before"] = 1.0
    df["test_incentive_rate"] = np.where(df["treatment_group"] == 1, 0.025, 0.000)
    df["cannibalization_pressure"] = np.where((df["region_proxy"] == "West/North Europe") & (df["lead_time_band"].isin(["8-30d", "31-90d"])), 0.025, 0.010)

    response_noise = rng.normal(0, 0.06, len(df))
    response_multiplier = 1 + df["treatment_group"] * segment_effect - df["treatment_group"] * df["cannibalization_pressure"] + response_noise
    response_multiplier = np.clip(response_multiplier, 0.70, 1.30)

    df["booking_units_after"] = df["booking_units_before"] * response_multiplier
    df["gross_booking_value_after"] = df["gross_booking_value_before"] * response_multiplier
    df["platform_margin_before"] = df["gross_booking_value_before"] * df["baseline_commission_rate"]
    df["platform_margin_after"] = df["gross_booking_value_after"] * np.maximum(0.10, df["baseline_commission_rate"] - df["test_incentive_rate"])

    df["booking_delta"] = df["booking_units_after"] - df["booking_units_before"]
    df["revenue_delta"] = df["gross_booking_value_after"] - df["gross_booking_value_before"]
    df["margin_delta"] = df["platform_margin_after"] - df["platform_margin_before"]
    df["cancellation_rate_proxy"] = df["is_canceled"].astype(float)

    keep = ["partner_id", "hotel", "arrival_date_year", "arrival_date_month", "country", "market_segment", "distribution_channel", "reserved_room_type", "customer_type", "lead_time", "lead_time_band", "adr", "partner_segment", "region_proxy", "quality_score_proxy", "eligible_for_test", "treatment_group", "baseline_commission_rate", "test_incentive_rate", "booking_units_before", "booking_units_after", "gross_booking_value_before", "gross_booking_value_after", "platform_margin_before", "platform_margin_after", "booking_delta", "revenue_delta", "margin_delta", "cancellation_rate_proxy", "cannibalization_pressure"]
    out = df[keep].copy()
    PROCESSED_DATA.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(PROCESSED_DATA, index=False)
    return out

def summarize_experiment(df):
    test_df = df[df["eligible_for_test"] == 1].copy()
    control = test_df[test_df["treatment_group"] == 0]
    treatment = test_df[test_df["treatment_group"] == 1]
    def rel_change(after, before):
        return (after.sum() - before.sum()) / max(before.sum(), 1e-9)
    ctrl_booking = rel_change(control["booking_units_after"], control["booking_units_before"])
    trt_booking = rel_change(treatment["booking_units_after"], treatment["booking_units_before"])
    booking_uplift = trt_booking - ctrl_booking
    ctrl_margin = rel_change(control["platform_margin_after"], control["platform_margin_before"])
    trt_margin = rel_change(treatment["platform_margin_after"], treatment["platform_margin_before"])
    margin_uplift = trt_margin - ctrl_margin
    c_delta = ((control["booking_units_after"] - control["booking_units_before"]) / control["booking_units_before"]).dropna()
    t_delta = ((treatment["booking_units_after"] - treatment["booking_units_before"]) / treatment["booking_units_before"]).dropna()
    _, p_value = stats.ttest_ind(t_delta, c_delta, equal_var=False)
    diff = t_delta.mean() - c_delta.mean()
    se = np.sqrt(t_delta.var(ddof=1)/len(t_delta) + c_delta.var(ddof=1)/len(c_delta))
    return {
        "eligible_partners": len(test_df), "treatment_partners": len(treatment), "control_partners": len(control),
        "booking_uplift": booking_uplift, "margin_uplift": margin_uplift, "p_value": p_value,
        "ci_low": diff - 1.96 * se, "ci_high": diff + 1.96 * se,
        "treatment_margin_delta": treatment["margin_delta"].sum(), "treatment_revenue_delta": treatment["revenue_delta"].sum(),
        "cancellation_guardrail": treatment["cancellation_rate_proxy"].mean() - control["cancellation_rate_proxy"].mean(),
    }

def decision(summary):
    if summary["booking_uplift"] > 0.035 and summary["margin_uplift"] > 0 and summary["p_value"] < 0.10:
        return "Scale", "Positive demand and margin signal."
    if summary["booking_uplift"] > 0.02 and summary["margin_uplift"] <= 0:
        return "Narrow Target", "Bookings improve, but margin is diluted. Retest with tighter eligibility."
    if summary["booking_uplift"] > 0.02:
        return "Retest", "Directional uplift exists, but more evidence is needed."
    return "Do Not Scale", "Evidence is not strong enough for rollout."

def prompt_pack(summary, focus):
    return f"""
You are a senior pricing analytics advisor. Draft an executive memo from these validated facts.

Context: public hotel-booking data enriched with a transparent synthetic pricing-treatment layer. No proprietary company data is used.
Segment focus: {focus}

Facts:
- Eligible rows/partners: {summary['eligible_partners']}
- Treatment: {summary['treatment_partners']}
- Control: {summary['control_partners']}
- Booking uplift vs control trend: {summary['booking_uplift']:.2%}
- Margin uplift vs control trend: {summary['margin_uplift']:.2%}
- 95% confidence interval: {summary['ci_low']:.2%} to {summary['ci_high']:.2%}
- p-value: {summary['p_value']:.4f}
- Treatment revenue delta: EUR {summary['treatment_revenue_delta']:,.0f}
- Treatment margin delta: EUR {summary['treatment_margin_delta']:,.0f}
- Cancellation guardrail difference: {summary['cancellation_guardrail']:.2%}

Return: recommendation, commercial rationale, risks/guardrails, next experiment, limitations.
"""

st.title("B2B Pricing Experimentation Workbench")
st.caption("V2: real public hotel-booking base data + transparent synthetic pricing-treatment layer")
st.info("Public hotel-booking data is used as the base. A documented synthetic pricing-treatment layer is added for partner incentives/control-treatment logic. Python/statistics calculate facts first; the AI layer turns validated facts into an executive memo.")
with st.sidebar:
    st.header("Scenario Controls")
    seed = st.slider("Experiment seed", 1, 99, 42)
    focus = st.selectbox("Partner segment focus", ["All eligible", "Growth", "Core", "Premium", "Long Tail"])
    incentive = st.slider("Scenario incentive level", 0.0, 6.0, 2.5, 0.5)
    st.markdown("---")
    st.subheader("Data source")
    st.write("Base: public hotel_bookings.csv")
    st.write("Layer: synthetic treatment/control and partner-pricing fields")

df = build_panel(seed=seed)
view = df if focus == "All eligible" else df[df["partner_segment"] == focus].copy()
summary = summarize_experiment(view)
label, rationale = decision(summary)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Eligible rows/partners", f"{summary['eligible_partners']:,}")
m2.metric("Booking uplift", f"{summary['booking_uplift']:.1%}")
m3.metric("Margin uplift", f"{summary['margin_uplift']:.1%}")
m4.metric("Decision", label)

st.markdown("### Decision Snapshot")
st.write(f"**Decision:** {label}")
st.write(f"**Why:** {rationale}")
st.write("**Action:** Do not scale broadly until margin quality and eligibility are improved.")

tabs = st.tabs(["Executive Decision", "Experiment Design", "Test Readout", "Scenario / Elasticity", "Incrementality", "AI Memo", "Data + SQL"])
with tabs[0]:
    st.header("Executive Decision")
    st.markdown(f"""
**Recommendation:** {label}

**Business interpretation:** {rationale}

**Observed signal**
- Booking uplift vs control trend: **{summary['booking_uplift']:.1%}**
- Margin uplift vs control trend: **{summary['margin_uplift']:.1%}**
- 95% confidence interval for booking response: **{summary['ci_low']:.1%} to {summary['ci_high']:.1%}**
- Statistical p-value: **{summary['p_value']:.3f}**
- Cancellation guardrail difference: **{summary['cancellation_guardrail']:.1%}**

**Limitations**
- Public hotel-booking base data; synthetic partner-pricing treatment layer.
- Real deployment would require true randomized assignment, seasonality controls, partner eligibility governance, and longer post-test monitoring.
""")
with tabs[1]:
    st.header("Experiment Design")
    st.write("Eligible rows are Growth/Core partner-segment proxies with acceptable quality score and non-cancelled base booking rows.")
    st.write("Treatment receives a synthetic commission discount / incentive. Control does not.")
    st.write("Success metrics: booking uplift, revenue delta, margin delta. Guardrails: margin dilution, cancellation proxy, cannibalization risk, confidence.")
with tabs[2]:
    st.header("Test Readout")
    exp = view[view["eligible_for_test"] == 1].copy()
    exp["group"] = np.where(exp["treatment_group"] == 1, "Treatment", "Control")
    exp["booking_change_pct"] = (exp["booking_units_after"] - exp["booking_units_before"]) / exp["booking_units_before"]
    exp["margin_change_pct"] = (exp["platform_margin_after"] - exp["platform_margin_before"]) / exp["platform_margin_before"]
    metric = st.selectbox("Metric", ["booking_change_pct", "margin_change_pct", "revenue_delta", "margin_delta"])
    st.plotly_chart(px.box(exp, x="group", y=metric, color="group", title=f"Control vs Treatment: {metric}"), width='stretch')
    seg = exp.groupby(["partner_segment", "group"], as_index=False).agg(rows=("partner_id", "count"), booking_delta=("booking_delta", "sum"), revenue_delta=("revenue_delta", "sum"), margin_delta=("margin_delta", "sum"), avg_adr=("adr", "mean"))
    st.dataframe(seg, width='stretch')
with tabs[3]:
    st.header("Scenario / Elasticity-Style Modelling")
    st.write("This is a scenario model, not a true causal elasticity estimate.")
    eligible = view[view["eligible_for_test"] == 1].copy()
    inc = incentive / 100.0
    response = np.select([eligible["partner_segment"] == "Growth", eligible["partner_segment"] == "Core", eligible["partner_segment"] == "Premium", eligible["partner_segment"] == "Long Tail"], [1.9, 1.1, 0.4, 0.2], default=0.8)
    expected_lift = np.clip(inc * response, 0, 0.18)
    expected_value = eligible["gross_booking_value_before"] * (1 + expected_lift)
    expected_margin = expected_value * np.maximum(0.10, eligible["baseline_commission_rate"] - inc)
    scen = eligible.assign(expected_booking_lift=expected_lift, expected_margin=expected_margin).groupby("partner_segment", as_index=False).agg(expected_booking_lift=("expected_booking_lift", "mean"), baseline_margin=("platform_margin_before", "sum"), expected_margin=("expected_margin", "sum"))
    scen["expected_margin_lift"] = (scen["expected_margin"] - scen["baseline_margin"]) / scen["baseline_margin"]
    st.dataframe(scen, width='stretch')
    st.plotly_chart(px.bar(scen, x="partner_segment", y=["expected_booking_lift", "expected_margin_lift"], barmode="group"), width='stretch')
with tabs[4]:
    st.header("Incrementality and Cannibalization")
    trt = view[(view["eligible_for_test"] == 1) & (view["treatment_group"] == 1)].copy()
    gross = trt["booking_delta"].sum()
    cann = np.maximum(0, trt["booking_units_after"] * trt["cannibalization_pressure"]).sum()
    net = gross - cann
    c1, c2, c3 = st.columns(3)
    c1.metric("Gross uplift units", f"{gross:,.0f}")
    c2.metric("Cannibalization adjustment", f"{cann:,.0f}")
    c3.metric("Net incremental units", f"{net:,.0f}")
    st.plotly_chart(px.bar(pd.DataFrame({"Step": ["Gross", "Cannibalization", "Net"], "Units": [gross, -cann, net]}), x="Step", y="Units"), width='stretch')
with tabs[5]:
    st.header("AI-Assisted Memo")
    st.write("AI is used after deterministic calculations, not before. The workflow turns validated facts into an executive recommendation for human review.")
    st.code(prompt_pack(summary, focus), language="text")
with tabs[6]:
    st.header("Data + SQL")
    st.write(f"Public source file detected: `{PUBLIC_DATA}`")
    st.write(f"Processed panel saved to: `{PROCESSED_DATA}`")
    st.dataframe(view.head(100), width='stretch')
    sql = """
WITH eligible AS (
  SELECT * FROM hotel_pricing_experiment_panel WHERE eligible_for_test = 1
),
deltas AS (
  SELECT partner_segment, treatment_group,
         booking_units_after - booking_units_before AS booking_delta,
         gross_booking_value_after - gross_booking_value_before AS revenue_delta,
         platform_margin_after - platform_margin_before AS margin_delta
  FROM eligible
)
SELECT partner_segment, treatment_group, COUNT(*) AS rows,
       SUM(booking_delta) AS booking_delta,
       SUM(revenue_delta) AS revenue_delta,
       SUM(margin_delta) AS margin_delta
FROM deltas
GROUP BY partner_segment, treatment_group
ORDER BY partner_segment, treatment_group;
"""
    st.code(sql, language="sql")
    st.download_button("Download processed pricing experiment panel", data=view.to_csv(index=False).encode("utf-8"), file_name="hotel_pricing_experiment_panel.csv", mime="text/csv")


