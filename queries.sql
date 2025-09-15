
-- Monthly revenue
SELECT strftime('%Y-%m', o.invoice_date) AS month,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       COUNT(DISTINCT o.order_id) AS orders,
       COUNT(DISTINCT o.customer_id) AS customers
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY month
ORDER BY month;

-- Top products by revenue
SELECT p.product_id, p.description,
       SUM(oi.quantity * oi.unit_price) AS revenue,
       SUM(oi.quantity) AS total_qty
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id, p.description
ORDER BY revenue DESC
LIMIT 10;

-- Cohort / retention (month offsets)
WITH first_order AS (
  SELECT customer_id, MIN(strftime('%Y-%m', invoice_date)) AS cohort_month
  FROM orders
  GROUP BY customer_id
),
customer_orders AS (
  SELECT customer_id, strftime('%Y-%m', invoice_date) AS order_month
  FROM orders
)
SELECT f.cohort_month, c.order_month,
       COUNT(DISTINCT c.customer_id) AS active_customers
FROM first_order f
JOIN customer_orders c USING(customer_id)
GROUP BY f.cohort_month, c.order_month
ORDER BY f.cohort_month, c.order_month;

-- RFM
WITH latest AS (SELECT MAX(invoice_date) AS max_date FROM orders),
cust AS (
  SELECT o.customer_id,
         CAST((julianday((SELECT max_date FROM latest)) - julianday(MAX(o.invoice_date))) AS INTEGER) AS recency,
         COUNT(DISTINCT o.order_id) AS frequency,
         SUM(oi.quantity * oi.unit_price) AS monetary
  FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  GROUP BY o.customer_id
)
SELECT customer_id, recency, frequency, monetary
FROM cust
ORDER BY monetary DESC
LIMIT 50;
