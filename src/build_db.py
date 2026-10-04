"""Validate synthetic CSVs and import them into a fresh SQLite database."""
from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "products": ("product_id", "product_name", "category", "list_price_inr", "unit_cost_inr"),
    "orders": ("order_id", "order_date", "region", "channel", "shipping_cost_inr", "fee_rate"),
    "order_items": ("item_id", "order_id", "product_id", "quantity", "returned_qty", "unit_price_inr", "unit_cost_inr", "discount_pct"),
}


def build(data_dir: Path = ROOT / "data", db_path: Path = ROOT / "outputs" / "ecommerce.sqlite") -> Path:
    loaded_rows: dict[str, list[dict[str, str]]] = {}
    for table, columns in FIELDS.items():
        path = data_dir / f"{table}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Missing required input: {path}")
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != columns:
                raise ValueError(f"Unexpected columns in {path.name}")
            rows = list(reader)
        if not rows:
            raise ValueError(f"Empty input: {path.name}")
        if table == "orders":
            for row in rows:
                if date.fromisoformat(row["order_date"]).isoformat() != row["order_date"]:
                    raise ValueError("Order date must be a real ISO date")
        if table == "order_items":
            for row in rows:
                if int(row["returned_qty"]) > int(row["quantity"]):
                    raise ValueError("Return quantity exceeds sold quantity")
        # Keep imported rows isolated to this build.
        loaded_rows[table] = rows

    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))
        with connection:
            for table, columns in FIELDS.items():
                placeholders = ",".join("?" for _ in columns)
                connection.executemany(
                    f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                    ([row[col] for col in columns] for row in loaded_rows[table]),
                )
            missing = connection.execute("PRAGMA foreign_key_check").fetchall()
            if missing:
                raise ValueError(f"Foreign-key violations: {missing[:5]}")
    except Exception:
        connection.close()
        db_path.unlink(missing_ok=True)
        raise
    connection.close()
    return db_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--db", type=Path, default=ROOT / "outputs" / "ecommerce.sqlite")
    options = parser.parse_args()
    print(f"Built: {build(options.data_dir, options.db)}")
