import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px

st.set_page_config(page_title="B2B Pricing Experimentation Workbench", layout="wide")

@st.cache_data
def generate_partner_pricing_data(n_partners=900, seed=42):
    rng = np.random.default_rng(seed)
    segments = np.array(["Growth", "Core", "Premium", "Long Tail"])
    regions = np.array(["North Europe", "West Europe", "South Europe", "Central Europe"])
    channels = np.array(["Direct", "Affiliate", "Mobile", "Corporate"])
    partner_segment = rng.choice(segments, size=n_partners, p=[0.26, 0.42, 0.16, 0.16])
    region = rng.choice(regions, size=n_partners, p=[0.24, 0.33, 0.23, 0.20])
    channel = rng.choice(channels, size=n_partners, p=[0.45, 0.20, 0.25, 0.10])
    price_band = rng.choice(["Budget", "Midscale", "Upscale"], size=n_partners, p=[0.34, 0.48, 0.18])
    quality_score = np.clip(rng.normal(78, 10, n_partners), 35, 98)

    base_bookings = rng.gamma(shape=8, scale=18, size=n_partners)
    seg_mult = np.select([partner_segment == "Growth", partner_segment == "Core", partner_segment == "Premium", partner_segment == "Long Tail"], [1.10, 1.00, 1.22, 0.68])
    bookings_before = np.maximum(5, base_bookings * seg_mult * (0.65 + quality_score / 100)).round()
    adr = np.select([price_band == "Budget", price_band == "Midscale", price_band == "Upscale"], [rng.normal(82,14,n_partners), rng.normal(135,22,n_partners), rng.normal(230,44,n_partners)])
    adr = np.clip(adr, 45, 420)
    baseline_commission = np.select([partner_segment == "Growth", partner_segment == "Core", partner_segment == "Premium", partner_segment == "Long Tail"], [0.155, 0.165, 0.175, 0.150])

    eligible = ((partner_segment == "Growth") | (partner_segment == "Core")) & (quality_score > 67)
    treatment = np.zeros(n_partners, dtype=int)
    idx = np.where(eligible)[0]
    treatment[idx] = rng.binomial(1, 0.50, len(idx))

    true_uplift = np.select([partner_segment == "Growth", partner_segment == "Core", partner_segment == "Premium", partner_segment == "Long Tail"], [0.105, 0.045, 0.010, 0.000])
    incentive_rate = np.where(treatment == 1, 0.025, 0.000)
    cannibalization_pressure = np.where((region == "West Europe") & (price_band == "Midscale"), 0.025, 0.010)
    noise = rng.normal(0, 0.09, n_partners)
    bookings_after = np.maximum(1, bookings_before * (1 + treatment * true_uplift - treatment * cannibalization_pressure + noise)).round()

    gross_before = bookings_before * adr
    gross_after = bookings_after * adr
    margin_before = gross_before * baseline_commission
    margin_after = gross_after * np.maximum(0.10, baseline_commission - incentive_rate)
    cancel_before = np.clip(0.18 - quality_score / 900 + rng.normal(0,0.025,n_partners), 0.03, 0.36)
    cancel_after = np.clip(cancel_before + np.where(treatment == 1, rng.normal(0.005,0.015,n_partners), rng.normal(0,0.012,n_partners)), 0.02, 0.40)

    df = pd.DataFrame({
        "partner_id": np.arange(100000, 100000+n_partners),
        "partner_segment": partner_segment,
        "region": region,
        "channel": channel,
        "price_band": price_band,
        "quality_score": quality_score.round(1),
        "eligible_for_test": eligible.astype(int),
        "treatment_group": treatment,
        "baseline_commission_rate": baseline_commission,
        "test_incentive_rate": incentive_rate,
        "bookings_before": bookings_before.astype(int),
        "bookings_after": bookings_after.astype(int),
        "adr": adr.round(2),
        "gross_revenue_before": gross_before.round(2),
        "gross_revenue_after": gross_after.round(2),
        "platform_margin_before": margin_before.round(2),
        "platform_margin_after": margin_after.round(2),
        "cancellation_rate_before": cancel_before.round(4),
        "cancellation_rate_after": cancel_after.round(4),
        "cannibalization_pressure": cannibalization_pressure.round(4),
    })
    df["booking_delta"] = df["bookings_after"] - df["bookings_before"]
    df["revenue_delta"] = df["gross_revenue_after"] - df["gross_revenue_before"]
    df["margin_delta"] = df["platform_margin_after"] - df["platform_margin_before"]
    return df

def summarize_experiment(df):
    test_df = df[df["eligible_for_test"] == 1].copy()
    control = test_df[test_df["treatment_group"] == 0]
    treatment = test_df[test_df["treatment_group"] == 1]
    def rel_change(a, b): return (a.sum() - b.sum()) / max(b.sum(), 1)
    ctrl_b = rel_change(control["bookings_after"], control["bookings_before"])
    trt_b = rel_change(treatment["bookings_after"], treatment["bookings_before"])
    ctrl_m = rel_change(control["platform_margin_after"], control["platform_margin_before"])
    trt_m = rel_change(treatment["platform_margin_after"], treatment["platform_margin_before"])
    c_delta = ((control["bookings_after"] - control["bookings_before"]) / control["bookings_before"].replace(0, np.nan)).dropna()
    t_delta = ((treatment["bookings_after"] - treatment["bookings_before"]) / treatment["bookings_before"].replace(0, np.nan)).dropna()
    t_stat, p_value = stats.ttest_ind(t_delta, c_delta, equal_var=False)
    diff = t_delta.mean() - c_delta.mean()
    se = np.sqrt(t_delta.var(ddof=1)/len(t_delta) + c_delta.var(ddof=1)/len(c_delta))
    return {
        "eligible_partners": len(test_df), "treatment_partners": len(treatment), "control_partners": len(control),
        "booking_uplift": trt_b - ctrl_b, "margin_uplift": trt_m - ctrl_m, "p_value": p_value,
        "ci_low": diff - 1.96*se, "ci_high": diff + 1.96*se,
        "treatment_margin_delta": treatment["margin_delta"].sum(), "treatment_revenue_delta": treatment["revenue_delta"].sum(),
        "cancellation_guardrail": treatment["cancellation_rate_after"].mean() - control["cancellation_rate_after"].mean(),
    }

def make_recommendation(s, segment):
    if s["booking_uplift"] > 0.035 and s["margin_uplift"] > 0 and s["p_value"] < 0.10 and s["cancellation_guardrail"] < 0.025:
        action = "Scale with controls"
        rationale = "The treatment shows positive booking uplift and positive margin movement without a material cancellation guardrail breach."
    elif s["booking_uplift"] > 0.02 and s["margin_uplift"] <= 0:
        action = "Retest with narrower eligibility"
        rationale = "The treatment creates demand but margin quality is weak. Narrow eligibility to preserve upside while reducing subsidy leakage."
    elif s["booking_uplift"] > 0.02 and s["p_value"] >= 0.10:
        action = "Extend test"
        rationale = "Directional uplift exists, but statistical confidence is not strong enough for broad rollout."
    else:
        action = "Do not scale yet"
        rationale = "The current evidence is not strong enough to support rollout."
    memo = f"""
### Executive recommendation

**Recommendation:** {action}

**Business interpretation:** {rationale}

**Target segment reviewed:** {segment}

**Observed experiment signal**
- Booking uplift vs control trend: **{s['booking_uplift']:.1%}**
- Margin uplift vs control trend: **{s['margin_uplift']:.1%}**
- 95% confidence interval for booking response: **{s['ci_low']:.1%} to {s['ci_high']:.1%}**
- Statistical p-value: **{s['p_value']:.3f}**
- Cancellation guardrail difference: **{s['cancellation_guardrail']:.1%}**

**Decision logic**
- Scale only when incremental bookings are positive, margin impact is not diluted, and guardrail metrics remain acceptable.
- If uplift is positive but margin weak, redesign the incentive rather than scaling broadly.
- If confidence is weak, extend or redesign the test before rollout.

**Limitations**
- Public/synthetic portfolio case study. No proprietary company data used.
- Real deployment would require randomization validation, seasonality controls, partner eligibility governance and longer post-test monitoring.
"""
    return action, memo

def ai_prompt_pack(s, segment, business_question):
    return f"""You are a senior pricing analytics advisor. Create an executive pricing memo from the validated analysis below.

Business question: {business_question}
Segment: {segment}
Eligible partners: {s['eligible_partners']}
Treatment partners: {s['treatment_partners']}
Control partners: {s['control_partners']}
Booking uplift vs control: {s['booking_uplift']:.2%}
Margin uplift vs control: {s['margin_uplift']:.2%}
95% confidence interval: {s['ci_low']:.2%} to {s['ci_high']:.2%}
p-value: {s['p_value']:.4f}
Treatment revenue delta: EUR {s['treatment_revenue_delta']:,.0f}
Treatment margin delta: EUR {s['treatment_margin_delta']:,.0f}
Cancellation guardrail difference: {s['cancellation_guardrail']:.2%}

Produce:
1. Recommendation: scale / stop / retest / narrow eligibility
2. Commercial rationale
3. Risks and guardrails
4. Next experiment design
5. Limitations and data needed for production use
"""

st.title("B2B Pricing Experimentation Workbench")
st.caption("Portfolio case study: controlled pricing test readout, incrementality, cannibalization and AI-assisted executive memo workflow.")
st.info("Public/synthetic-data case study. No proprietary company data is used. Python/statistics calculate facts first; the AI layer turns validated facts into an executive memo and next-test plan.")

with st.sidebar:
    st.header("Scenario Controls")
    seed = st.slider("Synthetic data seed", 1, 99, 42)
    selected_segment = st.selectbox("Partner segment focus", ["All eligible", "Growth", "Core", "Premium", "Long Tail"])
    incentive_slider = st.slider("Scenario incentive level", 0.0, 6.0, 2.5, 0.5)
    st.markdown("---")
    st.write("Wow element: AI-assisted pricing workflow")
    st.caption("Business question -> SQL/Python analysis -> experiment readout -> executive memo")

df = generate_partner_pricing_data(seed=seed)
view_df = df if selected_segment == "All eligible" else df[df["partner_segment"] == selected_segment].copy()
business_question = "Should a digital marketplace offer a pricing incentive to selected partner segments to increase incremental bookings without damaging margin, quality or other partner/customer segments?"
summary = summarize_experiment(view_df)
action, memo = make_recommendation(summary, selected_segment)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Eligible partners", f"{summary['eligible_partners']:,}")
c2.metric("Booking uplift", f"{summary['booking_uplift']:.1%}")
c3.metric("Margin uplift", f"{summary['margin_uplift']:.1%}")
c4.metric("Recommendation", action)

tabs = st.tabs(["Executive Summary", "Experiment Design", "Results", "Scenario and Elasticity", "Incrementality", "AI Memo", "Data and SQL"])

with tabs[0]:
    st.header("Executive Summary")
    st.markdown(memo)
    st.subheader("Why this is a decision workbench, not just a notebook")
    st.write("The page converts an ambiguous pricing question into a test design, statistical readout, commercial trade-off, risk check and leadership-ready recommendation.")

with tabs[1]:
    st.header("Experiment Design")
    a, b = st.columns(2)
    with a:
        st.subheader("Hypothesis")
        st.write("A targeted incentive for high-quality Growth/Core partners increases incremental bookings without unacceptable margin dilution.")
        st.subheader("Treatment logic")
        st.write("Eligible partners: Growth/Core and quality score above threshold. Random split into control and treatment. Treatment receives commission discount or equivalent incentive.")
    with b:
        st.subheader("Success metrics")
        st.write("Incremental bookings, revenue delta, margin delta, segment-level response.")
        st.subheader("Guardrails")
        st.write("Cancellation rate, margin dilution, cannibalization risk, statistical confidence.")

with tabs[2]:
    st.header("Experiment Results")
    exp_df = view_df[view_df["eligible_for_test"] == 1].copy()
    exp_df["group"] = np.where(exp_df["treatment_group"] == 1, "Treatment", "Control")
    exp_df["booking_change_pct"] = (exp_df["bookings_after"] - exp_df["bookings_before"]) / exp_df["bookings_before"]
    exp_df["margin_change_pct"] = (exp_df["platform_margin_after"] - exp_df["platform_margin_before"]) / exp_df["platform_margin_before"]
    metric = st.selectbox("Metric", ["booking_change_pct", "margin_change_pct", "revenue_delta", "margin_delta"])
    st.plotly_chart(px.box(exp_df, x="group", y=metric, color="group", points="outliers", title=f"Control vs Treatment: {metric}"), use_container_width=True)
    segment_summary = exp_df.groupby(["partner_segment", "group"], as_index=False).agg(partners=("partner_id","count"), bookings_before=("bookings_before","sum"), bookings_after=("bookings_after","sum"), revenue_delta=("revenue_delta","sum"), margin_delta=("margin_delta","sum"), avg_cancel_after=("cancellation_rate_after","mean"))
    segment_summary["booking_change_pct"] = (segment_summary["bookings_after"] - segment_summary["bookings_before"]) / segment_summary["bookings_before"]
    st.dataframe(segment_summary, use_container_width=True)

with tabs[3]:
    st.header("Scenario and Elasticity-Style Modelling")
    st.write("Scenario model only; not a claim of true causal elasticity from real marketplace data.")
    eligible = view_df[view_df["eligible_for_test"] == 1].copy()
    incentive = incentive_slider / 100
    response = np.select([eligible["partner_segment"] == "Growth", eligible["partner_segment"] == "Core", eligible["partner_segment"] == "Premium", eligible["partner_segment"] == "Long Tail"], [1.9, 1.1, 0.4, 0.2])
    expected_lift = np.clip(incentive * response, 0, 0.18)
    expected_bookings = eligible["bookings_before"] * (1 + expected_lift)
    expected_revenue = expected_bookings * eligible["adr"]
    expected_margin = expected_revenue * np.maximum(0.10, eligible["baseline_commission_rate"] - incentive)
    scenario = pd.DataFrame({"partner_segment": eligible["partner_segment"], "baseline_bookings": eligible["bookings_before"], "expected_bookings": expected_bookings, "baseline_margin": eligible["platform_margin_before"], "expected_margin": expected_margin})
    out = scenario.groupby("partner_segment", as_index=False).sum()
    out["expected_booking_lift"] = (out["expected_bookings"] - out["baseline_bookings"]) / out["baseline_bookings"]
    out["expected_margin_lift"] = (out["expected_margin"] - out["baseline_margin"]) / out["baseline_margin"]
    st.dataframe(out, use_container_width=True)
    st.plotly_chart(px.bar(out, x="partner_segment", y=["expected_booking_lift", "expected_margin_lift"], barmode="group", title="Scenario impact by segment"), use_container_width=True)

with tabs[4]:
    st.header("Incrementality and Cannibalization Check")
    eligible = view_df[view_df["eligible_for_test"] == 1].copy()
    tr = eligible[eligible["treatment_group"] == 1]
    gross_inc = tr["booking_delta"].sum()
    cannib = np.maximum(0, tr["bookings_after"] * tr["cannibalization_pressure"]).sum()
    net_inc = gross_inc - cannib
    ratio = cannib / max(gross_inc, 1)
    a, b, c = st.columns(3)
    a.metric("Gross incremental bookings", f"{gross_inc:,.0f}")
    b.metric("Estimated cannibalized bookings", f"{cannib:,.0f}")
    c.metric("Net incremental bookings", f"{net_inc:,.0f}", f"Cannibalization {ratio:.1%}")
    bridge = pd.DataFrame({"step": ["Gross uplift", "Cannibalization adjustment", "Net incremental"], "bookings": [gross_inc, -cannib, net_inc]})
    st.plotly_chart(px.bar(bridge, x="step", y="bookings", title="Gross to net incrementality bridge"), use_container_width=True)

with tabs[5]:
    st.header("AI-Assisted Executive Memo Workflow")
    st.write("The AI layer does not replace calculations. It converts validated facts into a structured memo, risks, limitations and next-test plan for human review.")
    st.subheader("Generated memo")
    st.markdown(memo)
    st.subheader("AI-ready prompt pack")
    st.code(ai_prompt_pack(summary, selected_segment, business_question), language="text")
    st.subheader("Efficiency story")
    st.write("Manual: define metrics, extract data, compute readout, write memo, revise for stakeholders. AI-assisted: deterministic analytics engine creates validated facts; AI drafts memo, risk section and next-test plan for human review.")

with tabs[6]:
    st.header("Data and SQL Logic")
    st.dataframe(view_df.head(100), use_container_width=True)
    sql = """
WITH eligible_partners AS (
    SELECT partner_id, partner_segment, region, treatment_group,
           bookings_before, bookings_after, gross_revenue_before, gross_revenue_after,
           platform_margin_before, platform_margin_after
    FROM partner_pricing_experiment
    WHERE eligible_for_test = 1
),
partner_deltas AS (
    SELECT *,
           bookings_after - bookings_before AS booking_delta,
           gross_revenue_after - gross_revenue_before AS revenue_delta,
           platform_margin_after - platform_margin_before AS margin_delta,
           1.0 * (bookings_after - bookings_before) / NULLIF(bookings_before, 0) AS booking_change_pct
    FROM eligible_partners
),
segment_readout AS (
    SELECT partner_segment, treatment_group, COUNT(*) AS partners,
           SUM(booking_delta) AS total_booking_delta,
           SUM(revenue_delta) AS total_revenue_delta,
           SUM(margin_delta) AS total_margin_delta,
           AVG(booking_change_pct) AS avg_booking_change_pct
    FROM partner_deltas
    GROUP BY partner_segment, treatment_group
)
SELECT * FROM segment_readout ORDER BY partner_segment, treatment_group;
"""
    st.code(sql, language="sql")
    st.download_button("Download synthetic experiment data", data=view_df.to_csv(index=False).encode("utf-8"), file_name="b2b_pricing_experiment_synthetic_data.csv", mime="text/csv")
