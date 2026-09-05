WITH eligible_partners AS (
    SELECT
        partner_id,
        partner_segment,
        region,
        treatment_group,
        bookings_before,
        bookings_after,
        gross_revenue_before,
        gross_revenue_after,
        platform_margin_before,
        platform_margin_after
    FROM partner_pricing_experiment
    WHERE eligible_for_test = 1
),
partner_deltas AS (
    SELECT
        *,
        bookings_after - bookings_before AS booking_delta,
        gross_revenue_after - gross_revenue_before AS revenue_delta,
        platform_margin_after - platform_margin_before AS margin_delta,
        1.0 * (bookings_after - bookings_before) / NULLIF(bookings_before, 0) AS booking_change_pct
    FROM eligible_partners
),
segment_readout AS (
    SELECT
        partner_segment,
        treatment_group,
        COUNT(*) AS partners,
        SUM(booking_delta) AS total_booking_delta,
        SUM(revenue_delta) AS total_revenue_delta,
        SUM(margin_delta) AS total_margin_delta,
        AVG(booking_change_pct) AS avg_booking_change_pct
    FROM partner_deltas
    GROUP BY partner_segment, treatment_group
)
SELECT *
FROM segment_readout
ORDER BY partner_segment, treatment_group;
