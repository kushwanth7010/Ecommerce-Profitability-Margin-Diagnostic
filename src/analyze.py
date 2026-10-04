"""Create reproducible financial diagnostics and transparent pricing scenarios."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from contextlib import closing
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def analyze(db_path: Path = ROOT / "outputs" / "ecommerce.sqlite",
            output_dir: Path = ROOT / "outputs") -> dict:
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not found: {db_path}; run python -m src.build_db")
    output_dir.mkdir(parents=True, exist_ok=True)
    # The SQLite context manager only commits/rolls back; explicitly close.
    with closing(sqlite3.connect(db_path)) as con:
        df = pd.read_sql_query("SELECT * FROM line_profitability", con)
        orders = pd.read_sql_query("SELECT * FROM orders", con)
    if df.empty:
        raise ValueError("Database has no order lines")
    for field in ("net_revenue_inr", "cogs_inr", "allocated_shipping_inr",
                  "payment_fee_inr", "gross_profit_inr", "contribution_profit_inr"):
        if df[field].isna().any() or not df[field].map(math.isfinite).all():
            raise ValueError(f"Invalid calculated amount: {field}")

    shipping_actual = float(orders["shipping_cost_inr"].sum())
    shipping_allocated = float(df["allocated_shipping_inr"].sum())
    assert math.isclose(shipping_actual, shipping_allocated, rel_tol=0, abs_tol=0.00001), "Shipping must reconcile"

    amounts = {name: float(df[name].sum()) for name in
               ("original_sale_inr", "net_revenue_inr", "cogs_inr",
                "allocated_shipping_inr", "payment_fee_inr", "gross_profit_inr", "contribution_profit_inr")}
    revenue = amounts["net_revenue_inr"]
    if not math.isclose(amounts["contribution_profit_inr"],
                        revenue - amounts["cogs_inr"] - shipping_actual - amounts["payment_fee_inr"],
                        abs_tol=0.00001):
        raise AssertionError("Contribution profit reconciliation failed")

    def segment(columns: list[str], filename: str) -> pd.DataFrame:
        data = df.groupby(columns, as_index=False).agg(
            orders=("order_id", "nunique"),
            net_revenue_inr=("net_revenue_inr", "sum"),
            cogs_inr=("cogs_inr", "sum"),
            shipping_inr=("allocated_shipping_inr", "sum"),
            fees_inr=("payment_fee_inr", "sum"),
            contribution_profit_inr=("contribution_profit_inr", "sum"),
            purchased_units=("quantity", "sum"),
            returned_units=("returned_qty", "sum"),
        )
        data["contribution_margin_pct"] = 100 * data["contribution_profit_inr"] / data["net_revenue_inr"].replace(0, float("nan"))
        data["unit_return_rate_pct"] = 100 * data["returned_units"] / data["purchased_units"]
        data.round(3).to_csv(output_dir / filename, index=False)
        return data

    categories = segment(["category"], "by_category.csv")
    segment(["region"], "by_region.csv")
    segment(["channel"], "by_channel.csv")
    skus = segment(["product_id", "product_name", "category"], "by_sku.csv")

    monthly = df.copy()
    monthly["month"] = monthly["order_date"].str.slice(0, 7)
    monthly = monthly.groupby("month", as_index=False)[["net_revenue_inr", "contribution_profit_inr"]].sum().sort_values("month")
    monthly["mom_revenue_growth_pct"] = monthly["net_revenue_inr"].pct_change() * 100
    monthly.round(3).to_csv(output_dir / "monthly_trends.csv", index=False)

    lossmakers = skus.loc[skus["contribution_profit_inr"] < 0].sort_values("contribution_profit_inr")
    lossmakers.head(20).round(3).to_csv(output_dir / "loss_making_skus.csv", index=False)
    target_ids = set(lossmakers["product_id"])
    target = df.loc[df["product_id"].isin(target_ids)]
    target_rev = float(target["net_revenue_inr"].sum())
    target_fees = float(target["payment_fee_inr"].sum())
    target_fee_rate = target_fees / target_rev if target_rev else 0.0
    # Constant-volume, constant-return-mix illustrative scenario, NOT a forecast.
    scenarios = []
    for uplift in (0, 0.03, 0.05, 0.08, 0.10):
        revenue_gain = target_rev * uplift
        fee_gain = revenue_gain * target_fee_rate
        profit_gain = revenue_gain - fee_gain
        scenarios.append({
            "target_price_increase_pct": uplift * 100,
            "assumed_revenue_gain_inr": round(revenue_gain, 2),
            "incremental_variable_fees_inr": round(fee_gain, 2),
            "illustrative_contribution_gain_inr": round(profit_gain, 2),
            "scenario_total_revenue_inr": round(revenue + revenue_gain, 2),
            "scenario_contribution_profit_inr": round(amounts["contribution_profit_inr"] + profit_gain, 2),
            "scenario_contribution_margin_pct": round(100 * (amounts["contribution_profit_inr"] + profit_gain) / (revenue + revenue_gain), 3),
        })
    pd.DataFrame(scenarios).to_csv(output_dir / "pricing_sensitivity.csv", index=False)

    summary = {
        "dataset": "100% synthetic; prices and costs are fictional INR-denominated model inputs",
        "period_start": str(df["order_date"].min()),
        "period_end": str(df["order_date"].max()),
        "order_count": int(orders.shape[0]),
        "order_line_count": int(df.shape[0]),
        "product_count": int(df["product_id"].nunique()),
        "purchased_units": int(df["quantity"].sum()),
        "returned_units": int(df["returned_qty"].sum()),
        "unit_return_rate_pct": round(100 * df["returned_qty"].sum() / df["quantity"].sum(), 3),
        "net_revenue_inr": round(revenue, 2),
        "cogs_inr": round(amounts["cogs_inr"], 2),
        "outbound_shipping_inr": round(shipping_actual, 2),
        "variable_fees_inr": round(amounts["payment_fee_inr"], 2),
        "gross_profit_inr": round(amounts["gross_profit_inr"], 2),
        "gross_margin_pct": round(100 * amounts["gross_profit_inr"] / revenue, 3),
        "contribution_profit_inr": round(amounts["contribution_profit_inr"], 2),
        "contribution_margin_pct": round(100 * amounts["contribution_profit_inr"] / revenue, 3),
        "loss_making_sku_count": int(len(lossmakers)),
        "pricing_target_net_revenue_inr": round(target_rev, 2),
        "pricing_target_weighted_fee_rate": round(target_fee_rate, 8),
        "pricing_target_definition": "SKUs with negative total contribution over the observed synthetic period",
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(monthly["month"], monthly["net_revenue_inr"] / 1_000_000, marker="o", markersize=3)
    ax.set(title="Synthetic monthly net revenue", ylabel="INR millions", xlabel="Month")
    ax.tick_params(axis="x", labelrotation=55)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "monthly_revenue.png", dpi=150)
    plt.close(fig)

    ordered = categories.sort_values("contribution_profit_inr")
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(ordered["category"], ordered["contribution_profit_inr"] / 1_000_000)
    ax.set(title="Synthetic contribution profit by category", xlabel="INR millions")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_dir / "category_contribution.png", dpi=150)
    plt.close(fig)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "outputs" / "ecommerce.sqlite")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    print(json.dumps(analyze(args.db, args.output_dir), indent=2))
