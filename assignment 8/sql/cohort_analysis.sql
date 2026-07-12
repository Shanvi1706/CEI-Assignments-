-- cohort_analysis.sql
-- Multi-level CTE, Year-over-Year comparison, and Cohort/Retention analysis
-- (Q10, Q12, Q15)
-- Dialect: SQLite

-- ------------------------------------------------------------------
-- Q10. Multi-level CTE: monthly revenue per customer -> spend tier ->
--      count of customers per tier per month
-- ------------------------------------------------------------------
WITH monthly_customer_revenue AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS order_month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS monthly_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id <> 'UNKNOWN' AND oi.quantity > 0
    GROUP BY o.customer_id, order_month
),
tiered AS (
    SELECT
        customer_id,
        order_month,
        monthly_revenue,
        CASE
            WHEN monthly_revenue > 10000 THEN 'High'
            WHEN monthly_revenue >= 5000 THEN 'Medium'
            ELSE 'Low'
        END AS spend_tier
    FROM monthly_customer_revenue
)
SELECT
    order_month,
    spend_tier,
    COUNT(DISTINCT customer_id) AS customer_count
FROM tiered
GROUP BY order_month, spend_tier
ORDER BY order_month, spend_tier;


-- ------------------------------------------------------------------
-- Q12. Year-over-year revenue comparison per month
-- Show: year, month, revenue, prev_year_revenue, yoy_growth_percent
-- ------------------------------------------------------------------
WITH monthly_revenue AS (
    SELECT
        CAST(strftime('%Y', o.order_date) AS INTEGER) AS year,
        CAST(strftime('%m', o.order_date) AS INTEGER) AS month,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
    GROUP BY year, month
)
SELECT
    cur.year,
    cur.month,
    ROUND(cur.revenue, 2) AS revenue,
    ROUND(prev.revenue, 2) AS prev_year_revenue,
    CASE
        WHEN prev.revenue IS NULL OR prev.revenue = 0 THEN NULL
        ELSE ROUND(100.0 * (cur.revenue - prev.revenue) / prev.revenue, 2)
    END AS yoy_growth_percent
FROM monthly_revenue cur
LEFT JOIN monthly_revenue prev
    ON prev.year = cur.year - 1 AND prev.month = cur.month
ORDER BY cur.year, cur.month;


-- ------------------------------------------------------------------
-- Q15. Cohort analysis: group customers by registration month,
--      track ordering activity in month 0/1/2/3, compute retention %
-- ------------------------------------------------------------------
WITH cohorts AS (
    SELECT
        customer_id,
        strftime('%Y-%m', registration_date) AS cohort_month,
        DATE(registration_date) AS reg_date
    FROM customers
),
customer_order_months AS (
    SELECT
        o.customer_id,
        DATE(o.order_date) AS order_date
    FROM orders o
    WHERE o.customer_id <> 'UNKNOWN'
),
cohort_activity AS (
    SELECT
        c.cohort_month,
        c.customer_id,
        CAST(
            (strftime('%Y', co.order_date) - strftime('%Y', c.reg_date)) * 12
            + (strftime('%m', co.order_date) - strftime('%m', c.reg_date))
            AS INTEGER
        ) AS month_offset
    FROM cohorts c
    JOIN customer_order_months co ON co.customer_id = c.customer_id
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
),
month_activity AS (
    SELECT
        cohort_month,
        month_offset,
        COUNT(DISTINCT customer_id) AS active_customers
    FROM cohort_activity
    WHERE month_offset BETWEEN 0 AND 3
    GROUP BY cohort_month, month_offset
)
SELECT
    ma.cohort_month,
    ma.month_offset,
    ma.active_customers,
    cs.cohort_size,
    ROUND(100.0 * ma.active_customers / cs.cohort_size, 2) AS retention_rate_percent
FROM month_activity ma
JOIN cohort_sizes cs ON cs.cohort_month = ma.cohort_month
ORDER BY ma.cohort_month, ma.month_offset;
