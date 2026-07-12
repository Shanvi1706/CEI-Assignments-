"""
test_edge_cases.py
-------------------
Edge case handling tests for the E-Commerce Order Analytics System
(Part 5 / Step 9 of the project spec).

These are plain Python test functions (no pytest dependency required,
but they run cleanly under pytest too since they're named test_*).

Run directly:
    python3 test_edge_cases.py

Or with pytest (if installed):
    pytest test_edge_cases.py -v
"""

import os
import sys
from datetime import datetime, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from clean_data import check_referential_integrity, clean_order_items  # noqa: E402


# ------------------------------------------------------------------ #
# 1. order_items references an order_id that doesn't exist in orders
# ------------------------------------------------------------------ #
def test_order_items_with_missing_order_id():
    orders = pd.DataFrame({"order_id": ["1", "2", "3"]})
    order_items = pd.DataFrame({
        "item_id": ["1", "2", "3"],
        "order_id": ["1", "2", "999"],   # 999 does not exist
        "product_id": ["10", "11", "12"],
        "quantity": ["2", "1", "3"],
        "unit_price": ["100", "200", "300"],
        "discount_percent": ["0", "5", "10"],
    })

    orphans = check_referential_integrity(order_items, orders)
    assert len(orphans) == 1, f"expected 1 orphan row, got {len(orphans)}"
    assert orphans.iloc[0]["order_id"] == "999"

    cleaned, issues = clean_order_items(order_items, valid_order_ids={"1", "2", "3"})
    assert issues["orphan_items_removed"] == 1
    assert "999" not in cleaned["order_id"].astype(str).values
    print("[pass] test_order_items_with_missing_order_id")


# ------------------------------------------------------------------ #
# 2. discount_percent > 100
# ------------------------------------------------------------------ #
def test_discount_percent_over_100():
    order_items = pd.DataFrame({
        "item_id": ["1"],
        "order_id": ["1"],
        "product_id": ["10"],
        "quantity": ["2"],
        "unit_price": ["100"],
        "discount_percent": ["150"],   # invalid, should be clipped to 100
    })
    cleaned, issues = clean_order_items(order_items, valid_order_ids={"1"})
    assert issues["discount_out_of_range_clipped"] == 1
    assert cleaned.iloc[0]["discount_percent"] == 100.0
    print("[pass] test_discount_percent_over_100")


# ------------------------------------------------------------------ #
# 3. quantity is 0
# ------------------------------------------------------------------ #
def test_zero_quantity():
    order_items = pd.DataFrame({
        "item_id": ["1"],
        "order_id": ["1"],
        "product_id": ["10"],
        "quantity": ["0"],
        "unit_price": ["100"],
        "discount_percent": ["10"],
    })
    cleaned, issues = clean_order_items(order_items, valid_order_ids={"1"})
    # zero-quantity rows are flagged in the report, not silently dropped
    assert issues["zero_quantity_rows"] == 1
    assert len(cleaned) == 1
    # zero quantity contributes 0 revenue, and is neither a purchase nor a return
    assert cleaned.iloc[0]["is_return"] == False  # noqa: E712
    print("[pass] test_zero_quantity")


# ------------------------------------------------------------------ #
# 4. order_date is in the future
# ------------------------------------------------------------------ #
def test_future_order_date():
    from clean_data import clean_orders

    future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    orders = pd.DataFrame({
        "order_id": ["1"],
        "customer_id": ["5"],
        "order_date": [future_date],
        "status": ["PLACED"],
        "region_code": ["NORTH"],
    })
    cleaned, issues = clean_orders(orders)
    # The current cleaning pipeline parses the date successfully (it IS
    # valid YYYY-MM-DD HH:MM:SS) but a future date is a business-logic
    # anomaly rather than a formatting error, so it is not silently
    # dropped -- it should still be present so it can be flagged/reported
    # downstream by a business-rule check.
    assert len(cleaned) == 1
    parsed = datetime.strptime(cleaned.iloc[0]["order_date"], "%Y-%m-%d %H:%M:%S")
    assert parsed > datetime.now(), "future date should be preserved, not silently corrected"
    print("[pass] test_future_order_date (flagged as future, not dropped)")


def run_all():
    test_order_items_with_missing_order_id()
    test_discount_percent_over_100()
    test_zero_quantity()
    test_future_order_date()
    print("\nAll edge case tests passed.")


if __name__ == "__main__":
    run_all()
