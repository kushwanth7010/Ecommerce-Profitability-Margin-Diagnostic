PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    list_price_inr REAL NOT NULL CHECK (list_price_inr > 0),
    unit_cost_inr REAL NOT NULL CHECK (unit_cost_inr >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL CHECK (order_date LIKE '____-__-__'),
    region TEXT NOT NULL,
    channel TEXT NOT NULL,
    shipping_cost_inr REAL NOT NULL CHECK (shipping_cost_inr >= 0),
    fee_rate REAL NOT NULL CHECK (fee_rate BETWEEN 0 AND 1)
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES orders(order_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    returned_qty INTEGER NOT NULL CHECK (returned_qty >= 0 AND returned_qty <= quantity),
    unit_price_inr REAL NOT NULL CHECK (unit_price_inr > 0),
    unit_cost_inr REAL NOT NULL CHECK (unit_cost_inr >= 0),
    discount_pct REAL NOT NULL CHECK (discount_pct BETWEEN 0 AND 1)
);

CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id);

-- Revenue excludes refunded units; restocked units recover COGS (model assumption).
-- The full original outbound shipping cost is retained even on returns.
-- Shipping is allocated by each line's original discounted revenue before returns.
-- Values in the view retain full precision; reports round only when displayed.
DROP VIEW IF EXISTS line_profitability;
CREATE VIEW line_profitability AS
WITH line_base AS (
    SELECT i.item_id, i.order_id, i.product_id, p.product_name, p.category,
           o.order_date, o.region, o.channel, o.shipping_cost_inr, o.fee_rate,
           i.quantity, i.returned_qty, i.unit_price_inr, i.unit_cost_inr, i.discount_pct,
           (i.quantity * i.unit_price_inr * (1 - i.discount_pct)) AS original_sale_inr,
           ((i.quantity - i.returned_qty) * i.unit_price_inr * (1 - i.discount_pct)) AS net_revenue_inr,
           ((i.quantity - i.returned_qty) * i.unit_cost_inr) AS cogs_inr
    FROM order_items i
    JOIN products p ON p.product_id = i.product_id
    JOIN orders o ON o.order_id = i.order_id
), allocations AS (
    SELECT *,
        shipping_cost_inr * original_sale_inr /
        SUM(original_sale_inr) OVER (PARTITION BY order_id) AS allocated_shipping_inr,
        fee_rate * net_revenue_inr AS payment_fee_inr
    FROM line_base
)
SELECT *,
       net_revenue_inr - cogs_inr AS gross_profit_inr,
       net_revenue_inr - cogs_inr - allocated_shipping_inr - payment_fee_inr
           AS contribution_profit_inr
FROM allocations;
