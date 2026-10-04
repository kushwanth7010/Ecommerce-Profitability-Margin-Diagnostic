"""Deterministically generate SYNTHETIC Indian e-commerce order data.

All names, transactions, and monetary amounts are fictional demonstration data.
Run: python -m src.generate_data --orders 12000 --seed 2026
"""
from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CATEGORIES = ("Electronics", "Home & Kitchen", "Fashion", "Beauty", "Sports", "Grocery")
REGIONS = ("North", "South", "East", "West", "Central")
CHANNELS = ("Website", "Marketplace", "Mobile App")


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def generate(n_orders: int = 12000, seed: int = 2026, output_dir: Path = DATA) -> dict[str, int]:
    if n_orders < 1:
        raise ValueError("n_orders must be positive")
    rng = random.Random(seed)
    products: list[list[object]] = []
    for idx in range(1, 121):
        category = CATEGORIES[(idx - 1) % len(CATEGORIES)]
        # Relatively costly low-ticket items ensure realistic negative-contribution cases.
        price = rng.randrange(180, 3700, 10)
        unit_cost = round(price * rng.uniform(0.53, 0.89), 2)
        products.append([f"P{idx:03d}", f"{category} Item {idx:03d}", category, price, unit_cost])

    orders: list[list[object]] = []
    items: list[list[object]] = []
    start = date(2024, 1, 1)
    for order_idx in range(1, n_orders + 1):
        order_id = f"O{order_idx:06d}"
        placed = start + timedelta(days=rng.randrange(731))
        region = rng.choice(REGIONS)
        channel = rng.choices(CHANNELS, weights=[38, 37, 25])[0]
        # Fees represent hypothetical payment/channel variable selling fees.
        fee_rate = {"Website": 0.021, "Marketplace": 0.045, "Mobile App": 0.026}[channel]
        shipping = round(rng.uniform(49, 180), 2)
        orders.append([order_id, placed.isoformat(), region, channel, shipping, fee_rate])
        selected = rng.sample(products, k=rng.choices([1, 2, 3], weights=[55, 35, 10])[0])
        for line_no, product in enumerate(selected, 1):
            quantity = rng.choices([1, 2, 3], weights=[78, 19, 3])[0]
            unit_price = round(float(product[3]) * rng.uniform(0.92, 1.06), 2)
            discount = rng.choices([0.0, 0.05, 0.1, 0.2, 0.3], weights=[42, 22, 20, 12, 4])[0]
            returned = (rng.randint(1, quantity)
                        if rng.random() < (0.085 if channel == "Marketplace" else 0.048)
                        else 0)
            items.append([f"I{order_idx:06d}_{line_no}", order_id, product[0], quantity,
                          returned, unit_price, product[4], discount])

    write_csv(output_dir / "products.csv",
              ["product_id", "product_name", "category", "list_price_inr", "unit_cost_inr"], products)
    write_csv(output_dir / "orders.csv",
              ["order_id", "order_date", "region", "channel", "shipping_cost_inr", "fee_rate"], orders)
    write_csv(output_dir / "order_items.csv",
              ["item_id", "order_id", "product_id", "quantity", "returned_qty", "unit_price_inr", "unit_cost_inr", "discount_pct"], items)
    return {"products": len(products), "orders": len(orders), "order_items": len(items)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    print(generate(args.orders, args.seed))
