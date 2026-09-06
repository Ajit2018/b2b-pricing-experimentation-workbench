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
