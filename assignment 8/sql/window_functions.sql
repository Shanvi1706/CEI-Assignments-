-- window_functions.sql
-- Advanced queries built around window functions (Q7, Q8, Q9, Q11, Q13, Q14, Q16)
-- Dialect: SQLite (3.25+)

-- ------------------------------------------------------------------
-- Q7. Running total of revenue per region, ordered by date
-- Show: region_code, order_date, daily_revenue, running_total
-- ------------------------------------------------------------------
WITH daily_region_revenue AS (
    SELECT
        o.region_code,
        DATE(o.order_date) AS order_day,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS daily_revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE oi.quantity > 0
    GROUP BY o.region_code, DATE(o.order_date)
)
SELECT
    region_code,
    order_day AS order_date,
    ROUND(daily_revenue, 2) AS daily_revenue,
    ROUND(SUM(daily_revenue) OVER (
        PARTITION BY region_code
        ORDER BY order_day
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total
FROM daily_region_revenue
ORDER BY region_code, order_day;


-- ------------------------------------------------------------------
-- Q8. Rank products by total revenue within each category (DENSE_RANK)
-- Show: category, product_name, total_revenue, rank_in_category
-- ------------------------------------------------------------------
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_name,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    WHERE oi.quantity > 0
    GROUP BY p.category, p.product_name
)
SELECT
    category,
    product_name,
    ROUND(total_revenue, 2) AS total_revenue,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category;


-- ------------------------------------------------------------------
-- Q9. LAG analysis: days between consecutive orders per customer
-- Show: customer_id, order_date, previous_order_date, days_gap
-- Customers with average gap > 30 days flagged as "At Risk"
-- ------------------------------------------------------------------
WITH customer_orders AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_order_date
    FROM orders
    WHERE customer_id <> 'UNKNOWN'
),
gaps AS (
    SELECT
        customer_id,
        order_date,
        previous_order_date,
        CASE
            WHEN previous_order_date IS NULL THEN NULL
            ELSE CAST(julianday(order_date) - julianday(previous_order_date) AS INTEGER)
        END AS days_gap
    FROM customer_orders
),
avg_gap AS (
    SELECT customer_id, AVG(days_gap) AS avg_days_gap
    FROM gaps
    WHERE days_gap IS NOT NULL
    GROUP BY customer_id
)
SELECT
    g.customer_id,
    g.order_date,
    g.previous_order_date,
    g.days_gap,
    CASE WHEN a.avg_days_gap > 30 THEN 'At Risk' ELSE 'Active' END AS customer_status
FROM gaps g
LEFT JOIN avg_gap a ON a.customer_id = g.customer_id
ORDER BY g.customer_id, g.order_date;


-- ------------------------------------------------------------------
-- Q11. NTILE: divide customers into 4 quartiles by lifetime value
-- Show: customer_id, total_value, quartile, quartile_label
-- ------------------------------------------------------------------
WITH customer_value AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS total_value
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id <> 'UNKNOWN' AND oi.quantity > 0
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(total_value, 2) AS total_value,
    NTILE(4) OVER (ORDER BY total_value DESC) AS quartile,
    CASE NTILE(4) OVER (ORDER BY total_value DESC)
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        WHEN 4 THEN 'Bronze'
    END AS quartile_label
FROM customer_value
ORDER BY total_value DESC;


-- ------------------------------------------------------------------
-- Q13. First/Last purchased category per customer (category shift)
-- ------------------------------------------------------------------
WITH customer_category_orders AS (
    SELECT
        o.customer_id,
        p.category,
        o.order_date,
        FIRST_VALUE(p.category) OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS first_category,
        LAST_VALUE(p.category) OVER (
            PARTITION BY o.customer_id ORDER BY o.order_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS last_category
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.customer_id <> 'UNKNOWN'
)
SELECT DISTINCT
    customer_id,
    first_category,
    last_category,
    CASE WHEN first_category <> last_category THEN 'Yes' ELSE 'No' END AS category_shift
FROM customer_category_orders
ORDER BY customer_id;


-- ------------------------------------------------------------------
-- Q14. Cumulative distribution: % of revenue from top N% of customers
-- Show: customer_id, revenue, cumulative_revenue, cumulative_percent
-- ------------------------------------------------------------------
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)) AS revenue
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    WHERE o.customer_id <> 'UNKNOWN' AND oi.quantity > 0
    GROUP BY o.customer_id
),
totals AS (
    SELECT SUM(revenue) AS grand_total FROM customer_revenue
)
SELECT
    customer_id,
    ROUND(revenue, 2) AS revenue,
    ROUND(SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS cumulative_revenue,
    ROUND(
        100.0 * SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
        / (SELECT grand_total FROM totals),
        2
    ) AS cumulative_percent
FROM customer_revenue
ORDER BY revenue DESC;


-- ------------------------------------------------------------------
-- Q16. Self-join: products frequently bought together
-- Show: product_a, product_b, times_bought_together
-- ------------------------------------------------------------------
SELECT
    pa.product_name AS product_a,
    pb.product_name AS product_b,
    COUNT(*) AS times_bought_together
FROM order_items oi1
JOIN order_items oi2
    ON oi1.order_id = oi2.order_id
    AND oi1.product_id < oi2.product_id      -- avoids A-B/B-A duplicates & self-pairs
JOIN products pa ON pa.product_id = oi1.product_id
JOIN products pb ON pb.product_id = oi2.product_id
WHERE oi1.quantity > 0 AND oi2.quantity > 0
GROUP BY pa.product_name, pb.product_name
HAVING times_bought_together > 1
ORDER BY times_bought_together DESC
LIMIT 50;
