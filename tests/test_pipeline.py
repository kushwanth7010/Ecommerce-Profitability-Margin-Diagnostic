"""Reproducibility, financial reconciliation and data-integrity tests."""
from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from src.generate_data import generate
from src.build_db import build
from src.analyze import analyze


@pytest.fixture(scope="module")
def fixture_project(tmp_path_factory):
    root = tmp_path_factory.mktemp("ecommerce")
    data_dir, outputs = root / "data", root / "outputs"
    counts = generate(n_orders=280, seed=11, output_dir=data_dir)
    db = build(data_dir=data_dir, db_path=outputs / "test.sqlite")
    summary = analyze(db_path=db, output_dir=outputs)
    return counts, data_dir, db, outputs, summary


def test_counts_and_nonempty_outputs(fixture_project):
    counts, _, _, outputs, summary = fixture_project
    assert counts["orders"] == summary["order_count"] == 280
    assert counts["products"] == 120
    assert summary["order_line_count"] >= counts["orders"]
    assert (outputs / "monthly_revenue.png").is_file()
    assert (outputs / "pricing_sensitivity.csv").is_file()


def test_generation_is_reproducible(tmp_path, fixture_project):
    _, data_dir, _, _, _ = fixture_project
    other = tmp_path / "data"
    generate(n_orders=280, seed=11, output_dir=other)
    for filename in ("products.csv", "orders.csv", "order_items.csv"):
        assert (other / filename).read_bytes() == (data_dir / filename).read_bytes()


def test_order_shipping_allocation_reconciles(fixture_project):
    _, _, db, _, summary = fixture_project
    with closing(sqlite3.connect(db)) as conn:
        bad = conn.execute("""
            SELECT o.order_id FROM orders o JOIN line_profitability l ON o.order_id = l.order_id
            GROUP BY o.order_id HAVING ABS(MAX(o.shipping_cost_inr) - SUM(l.allocated_shipping_inr)) > 0.000001
        """).fetchall()
    assert not bad
    assert summary["outbound_shipping_inr"] > 0


def test_financials_and_returns_reconcile(fixture_project):
    _, _, db, _, summary = fixture_project
    assert math.isclose(summary["net_revenue_inr"] - summary["cogs_inr"] -
                        summary["outbound_shipping_inr"] - summary["variable_fees_inr"],
                        summary["contribution_profit_inr"], abs_tol=0.03)
    with closing(sqlite3.connect(db)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM order_items WHERE returned_qty > quantity OR returned_qty < 0").fetchone()[0]
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert count == 0
    assert not fk_violations


def test_scenario_math_and_baseline(fixture_project):
    _, _, _, outputs, summary = fixture_project
    scenarios = pd.read_csv(outputs / "pricing_sensitivity.csv")
    assert scenarios["target_price_increase_pct"].tolist() == [0, 3, 5, 8, 10]
    assert math.isclose(scenarios.iloc[0]["scenario_contribution_profit_inr"],
                        summary["contribution_profit_inr"], abs_tol=0.01)
    assert (scenarios["illustrative_contribution_gain_inr"] >= 0).all()
    assert scenarios["illustrative_contribution_gain_inr"].is_monotonic_increasing


def test_constraints_reject_invalid_refund(fixture_project):
    _, _, db, _, _ = fixture_project
    with closing(sqlite3.connect(db)) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE order_items SET returned_qty = quantity + 1 WHERE item_id = (SELECT MIN(item_id) FROM order_items)")


def test_output_summary_is_serializable(fixture_project):
    _, _, _, outputs, summary = fixture_project
    assert json.loads((outputs / "summary.json").read_text()) == summary
