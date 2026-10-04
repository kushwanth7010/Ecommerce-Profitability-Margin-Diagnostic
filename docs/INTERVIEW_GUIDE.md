# Technical interview guide

## 30-second overview

I built a reproducible synthetic e-commerce profitability case study using Python, Pandas, SQLite and Excel. It models 12,000 fictional orders and reconciles discounts, returns, retained COGS, shipping and variable selling fees. I used SQL window functions and Python segmentation to identify ten negative-contribution SKUs, then modeled price-change scenarios with explicit constant-demand assumptions.

## What makes this a data analytics project?

It integrates input validation, relational modeling, SQL transformations, exploratory segmentation, financial reconciliation, visualization and scenario analysis. The output is intended to support a business decision, not merely produce a dashboard.

## Why use contribution profit instead of net profit?

Gross profit subtracts merchandise cost from retained sales. Contribution profit further subtracts modeled variable selling fees and outbound shipping. Marketing, rent, wages and other fixed or excluded costs are not modeled, so calling it accounting net profit would be misleading.

## How are refunds treated?

A returned unit generates no retained revenue and is assumed to be fully restocked, recovering its COGS. The original outbound shipping expense remains. Payment/channel fees are modeled only on retained revenue.

## Why allocate shipping by original line revenue?

This allocates each order's entire original outbound shipping across its lines, regardless of subsequent returns. The tests check that allocated shipping sums to the original cost of each order.

## Which SQL features are used?

CTEs construct the line-profitability view; window functions calculate proportional shipping allocation, `LAG` computes month-over-month revenue changes and `DENSE_RANK` ranks negative-contribution SKUs.

## How are price increases modeled?

Only SKUs with negative total contribution are targeted. A price uplift multiplies their retained revenue at a fixed volume/return mix; fees grow proportionally. No demand elasticity or competitive response is estimated. The 5% example is an illustrative gain over the entire synthetic two-year period, not annual realized savings.

## How do I verify the results?

Rebuild with the documented seed; run the seven automated tests; use `PRAGMA integrity_check` and `PRAGMA foreign_key_check`; compare the sum of segment-level contribution with the total in `outputs/summary.json`. CI performs the pipeline and test suite on GitHub.

## Can I present this as internship company data?

No. This is an independent educational portfolio project with generated transactions. It does not contain real customer records, employer data or proven financial improvement.
