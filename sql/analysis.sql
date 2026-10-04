-- Run after python -m src.build_db: sqlite3 outputs/ecommerce.sqlite < sql/analysis.sql
-- Contribution profit = net revenue - retained COGS - outbound shipping - variable fees.
-- These are operational contribution metrics, NOT net accounting profit.

-- 1. Revenue, gross margin and contribution margin.
SELECT ROUND(SUM(net_revenue_inr), 2) AS net_revenue_inr,
       ROUND(SUM(gross_profit_inr), 2) AS gross_profit_inr,
       ROUND(100.0 * SUM(gross_profit_inr) / NULLIF(SUM(net_revenue_inr), 0), 2) AS gross_margin_pct,
       ROUND(SUM(contribution_profit_inr), 2) AS contribution_profit_inr,
       ROUND(100.0 * SUM(contribution_profit_inr) / NULLIF(SUM(net_revenue_inr), 0), 2) AS contribution_margin_pct
FROM line_profitability;

-- 2. Monthly growth: window-function example.
WITH monthly AS (
    SELECT SUBSTR(order_date, 1, 7) AS month, SUM(net_revenue_inr) AS revenue_inr
    FROM line_profitability GROUP BY 1
)
SELECT month, ROUND(revenue_inr, 2) AS revenue_inr,
       ROUND(100.0 * (revenue_inr - LAG(revenue_inr) OVER (ORDER BY month)) /
             NULLIF(LAG(revenue_inr) OVER (ORDER BY month), 0), 2) AS mom_growth_pct
FROM monthly ORDER BY month;

-- 3. Segment contribution after costs.
SELECT category, ROUND(SUM(net_revenue_inr), 2) AS revenue_inr,
       ROUND(SUM(contribution_profit_inr), 2) AS contribution_profit_inr,
       ROUND(100.0 * SUM(contribution_profit_inr) / NULLIF(SUM(net_revenue_inr), 0), 2) AS contribution_margin_pct
FROM line_profitability GROUP BY category ORDER BY contribution_profit_inr DESC;

-- 4. Rank SKUs by negative contribution using a window function.
WITH sku AS (
    SELECT product_id, product_name, ROUND(SUM(contribution_profit_inr), 2) AS contribution_inr
    FROM line_profitability GROUP BY product_id, product_name
)
SELECT DENSE_RANK() OVER (ORDER BY contribution_inr ASC) AS loss_rank,
       product_id, product_name, contribution_inr
FROM sku WHERE contribution_inr < 0 ORDER BY contribution_inr LIMIT 20;

-- 5. Region and channel mix.
SELECT region, channel, COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(net_revenue_inr), 2) AS revenue_inr,
       ROUND(SUM(contribution_profit_inr), 2) AS contribution_inr
FROM line_profitability GROUP BY region, channel ORDER BY contribution_inr DESC;

-- 6. Line-level return units and profitability.
SELECT category, SUM(quantity) AS purchased_units, SUM(returned_qty) AS returned_units,
       ROUND(100.0 * SUM(returned_qty) / SUM(quantity), 2) AS returned_units_pct,
       ROUND(SUM(contribution_profit_inr), 2) AS contribution_inr
FROM line_profitability GROUP BY category ORDER BY returned_units_pct DESC;
