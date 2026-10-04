# Data dictionary and accounting methodology

All fields are synthetic demonstration data. Amounts are illustrative INR, not actual financial reporting.

## products.csv

| Field | Meaning |
|---|---|
| product_id | Unique fictional product key (e.g., P001). |
| product_name | Synthetic product description. |
| category | Electronics, Home & Kitchen, Fashion, Beauty, Sports or Grocery. |
| list_price_inr | Fictional original product price. |
| unit_cost_inr | Fictional per-unit merchandise cost. |

## orders.csv

| Field | Meaning |
|---|---|
| order_id | Unique order identifier. |
| order_date | Simulated ISO calendar date. |
| region | Simulated geographic sales region. |
| channel | Website, Marketplace or Mobile App. |
| shipping_cost_inr | Original outbound shipment cost per order. |
| fee_rate | Simulated proportional selling/payment fee for the channel. |

## order_items.csv

| Field | Meaning |
|---|---|
| item_id | Unique order-line identifier. |
| order_id | Foreign key referencing orders. |
| product_id | Foreign key referencing products. |
| quantity | Purchased unit quantity; strictly positive. |
| returned_qty | Returned unit quantity; between 0 and quantity. |
| unit_price_inr | Actual fictional pre-discount unit selling price. |
| unit_cost_inr | Cost applied to the purchased SKU at order time. |
| discount_pct | Fractional line discount between 0 and 1. |

## Derived line_profitability view

- `original_sale_inr = quantity * unit_price_inr * (1 - discount_pct)`.
- `net_revenue_inr = (quantity - returned_qty) * unit_price_inr * (1 - discount_pct)`.
- `cogs_inr = (quantity - returned_qty) * unit_cost_inr` (returned items assumed fully restocked).
- `allocated_shipping_inr = order.shipping_cost_inr * line.original_sale_inr / order.original_discounted_sale_inr`.
- `payment_fee_inr = fee_rate * net_revenue_inr`.
- `gross_profit_inr = net_revenue_inr - cogs_inr`.
- `contribution_profit_inr = gross_profit_inr - allocated_shipping_inr - payment_fee_inr`.

Shipping allocation uses **original** discounted order value so the full outbound cost remains even for returned products. Fees are assessed on retained net revenue. Source calculations retain floating-point precision and reports round only at presentation.

Gross margin and contribution margin divide the corresponding profit by net revenue. Returned unit rate divides returned units by purchased units. Contribution is operational profit after the variable costs modeled here, **not** accounting net profit.

## Pricing scenario assumptions

The target is the set of SKUs with negative aggregate contribution in the generated period. The 0%, 3%, 5%, 8% and 10% price changes apply only to their retained revenue. Unit demand, discount mix, returns, COGS and outbound shipping are constant; additional variable fees equal additional retained revenue multiplied by the target's weighted fee rate. This is a sensitivity calculation, not a causal demand model.

Excluded: marketing, employee costs, rent, taxes, depreciation, returns freight, damaged-item write-offs, demand elasticity, competitor behavior and real-world market pricing.
