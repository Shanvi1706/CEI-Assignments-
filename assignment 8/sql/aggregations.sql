-- aggregations.sql
-- Basic & Intermediate queries: joins, aggregations, revenue metrics.
-- Dialect: SQLite. revenue = quantity * unit_price * (1 - discount_percent/100)

-- ------------------------------------------------------------------
-- Q1. Total revenue per category
-- ------------------------------------------------------------------
SELECT
    p.category,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
WHERE oi.quantity > 0            -- exclude returns from revenue
GROUP BY p.category
ORDER BY total_revenue DESC;


-- ------------------------------------------------------------------
-- Q2. Top 10 customers by total order value
-- ------------------------------------------------------------------
SELECT
    o.customer_id,
    c.customer_name,
    ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_order_value
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE o.customer_id <> 'UNKNOWN'
  AND oi.quantity > 0
GROUP BY o.customer_id, c.customer_name
ORDER BY total_order_value DESC
LIMIT 10;


-- ------------------------------------------------------------------
-- Q3. Month-wise order count for the last 12 months
--     (relative to the most recent order_date in the dataset)
-- ------------------------------------------------------------------
WITH max_date AS (
    SELECT MAX(order_date) AS d FROM orders
)
SELECT
    strftime('%Y-%m', o.order_date) AS order_month,
    COUNT(DISTINCT o.order_id) AS order_count
FROM orders o, max_date
WHERE o.order_date >= datetime(max_date.d, '-12 months')
GROUP BY order_month
ORDER BY order_month;


-- ------------------------------------------------------------------
-- Q4. Customers who placed orders but never had any item delivered
-- ------------------------------------------------------------------
SELECT DISTINCT o.customer_id, c.customer_name
FROM orders o
LEFT JOIN customers c ON c.customer_id = o.customer_id
WHERE o.customer_id <> 'UNKNOWN'
  AND o.customer_id NOT IN (
        SELECT customer_id FROM orders WHERE status = 'DELIVERED'
  );


-- ------------------------------------------------------------------
-- Q5. Products that were ordered but had more returns than purchases
--     (returns = rows with negative quantity / is_return = 1)
-- ------------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    SUM(CASE WHEN oi.is_return = 1 THEN ABS(oi.quantity) ELSE 0 END) AS total_returned,
    SUM(CASE WHEN oi.is_return = 0 THEN oi.quantity ELSE 0 END) AS total_purchased
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
HAVING total_returned > total_purchased;


-- ------------------------------------------------------------------
-- Q6. Return rate (returned items / total items) per category
-- ------------------------------------------------------------------
SELECT
    p.category,
    SUM(CASE WHEN oi.is_return = 1 THEN ABS(oi.quantity) ELSE 0 END) AS returned_items,
    SUM(ABS(oi.quantity)) AS total_items,
    ROUND(
        1.0 * SUM(CASE WHEN oi.is_return = 1 THEN ABS(oi.quantity) ELSE 0 END)
        / NULLIF(SUM(ABS(oi.quantity)), 0),
        4
    ) AS return_rate
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY return_rate DESC;
