"""
clean_data.py
-------------
Loads the raw CSVs from data/raw/, cleans and validates them, writes the
cleaned CSVs to data/cleaned/, and prints/saves a data-quality report.

Functions implemented (per project spec, Part 2):
    clean_orders()               -> fix date formats, handle NULL customer_ids
    clean_products()              -> normalize product names (trim + title case)
    validate_emails()             -> list of customer_ids with invalid emails
    check_referential_integrity() -> order_items rows referencing non-existent orders

Run:
    python3 clean_data.py
Output:
    ../data/cleaned/*.csv
    ../output/sample_reports/data_quality_report.txt
"""

import os
import re
from datetime import datetime

import pandas as pd

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
CLEAN_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cleaned")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "sample_reports")
os.makedirs(CLEAN_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ------------------------------------------------------------------ #
# Loaders
# ------------------------------------------------------------------ #
def load_raw():
    customers = pd.read_csv(os.path.join(RAW_DIR, "customers.csv"), dtype=str)
    products = pd.read_csv(os.path.join(RAW_DIR, "products.csv"), dtype=str)
    orders = pd.read_csv(os.path.join(RAW_DIR, "orders.csv"), dtype=str)
    order_items = pd.read_csv(os.path.join(RAW_DIR, "order_items.csv"), dtype=str)
    return customers, products, orders, order_items


# ------------------------------------------------------------------ #
# 1. clean_orders()
# ------------------------------------------------------------------ #
def parse_order_date(value: str):
    """Try the correct format first, then fall back to DD-MM-YYYY."""
    if pd.isna(value) or str(value).strip() == "":
        return None, "missing_date"

    value = str(value).strip()

    # Correct format: YYYY-MM-DD HH:MM:SS
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S"), None
    except ValueError:
        pass

    # Wrong format seen in raw data: DD-MM-YYYY (no time component)
    try:
        return datetime.strptime(value, "%d-%m-%Y"), "fixed_date_format"
    except ValueError:
        pass

    return None, "unparseable_date"


def clean_orders(orders: pd.DataFrame):
    """
    Fix date formats, handle NULL customer_ids.
    Returns (cleaned_df, issues_dict)
    """
    df = orders.copy()
    issues = {"missing_customer_id": 0, "fixed_date_format": 0, "unparseable_date": 0}

    parsed_dates = []
    for val in df["order_date"]:
        dt, flag = parse_order_date(val)
        if flag == "fixed_date_format":
            issues["fixed_date_format"] += 1
        elif flag in ("missing_date", "unparseable_date"):
            issues["unparseable_date"] += 1
        parsed_dates.append(dt)

    df["order_date"] = parsed_dates
    # Drop rows where the date genuinely could not be parsed (kept out of
    # analytics rather than silently guessed).
    before = len(df)
    df = df[df["order_date"].notna()].copy()
    dropped_for_date = before - len(df)

    df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # Handle NULL / empty customer_id -> standardize to explicit "UNKNOWN"
    mask_missing = df["customer_id"].isna() | (df["customer_id"].str.strip() == "")
    issues["missing_customer_id"] = int(mask_missing.sum())
    df.loc[mask_missing, "customer_id"] = "UNKNOWN"

    issues["rows_dropped_unparseable_date"] = dropped_for_date
    return df, issues


# ------------------------------------------------------------------ #
# 2. clean_products()
# ------------------------------------------------------------------ #
def clean_products(products: pd.DataFrame):
    """
    Normalize product names: trim whitespace, apply Title Case.
    Returns (cleaned_df, issues_dict)
    """
    df = products.copy()
    original = df["product_name"].copy()

    df["product_name"] = df["product_name"].str.strip().str.title()
    df["cost_price"] = pd.to_numeric(df["cost_price"], errors="coerce")

    changed = int((original.str.strip().str.title() != original).sum())
    bad_price = int(df["cost_price"].isna().sum())

    issues = {"names_normalized": changed, "invalid_cost_price": bad_price}
    return df, issues


# ------------------------------------------------------------------ #
# 3. validate_emails()
# ------------------------------------------------------------------ #
def validate_emails(customers: pd.DataFrame):
    """
    Returns list of customer_ids whose email is invalid
    (missing '@' or missing a proper domain).
    """
    bad_ids = []
    for _, row in customers.iterrows():
        email = str(row["email"]) if pd.notna(row["email"]) else ""
        if not EMAIL_REGEX.match(email.strip()):
            bad_ids.append(row["customer_id"])
    return bad_ids


# ------------------------------------------------------------------ #
# 4. check_referential_integrity()
# ------------------------------------------------------------------ #
def check_referential_integrity(order_items: pd.DataFrame, orders: pd.DataFrame):
    """
    Returns the subset of order_items rows whose order_id does not
    exist in orders.
    """
    valid_order_ids = set(orders["order_id"].astype(str))
    mask = ~order_items["order_id"].astype(str).isin(valid_order_ids)
    return order_items[mask].copy()


# ------------------------------------------------------------------ #
# Extra cleaning helpers used for order_items (negative qty / discount)
# ------------------------------------------------------------------ #
def clean_order_items(order_items: pd.DataFrame, valid_order_ids: set):
    df = order_items.copy()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["discount_percent"] = pd.to_numeric(df["discount_percent"], errors="coerce")

    issues = {}

    # Referential integrity: drop items pointing at non-existent orders
    before = len(df)
    df = df[df["order_id"].astype(str).isin(valid_order_ids)].copy()
    issues["orphan_items_removed"] = before - len(df)

    # Negative quantity = returns; keep them but tag explicitly instead
    # of silently treating as purchases.
    df["is_return"] = df["quantity"] < 0
    issues["returns_flagged"] = int(df["is_return"].sum())

    # Clip discount_percent into the valid 0-100 range instead of
    # dropping the row outright.
    out_of_range = int(((df["discount_percent"] < 0) | (df["discount_percent"] > 100)).sum())
    df["discount_percent"] = df["discount_percent"].clip(lower=0, upper=100)
    issues["discount_out_of_range_clipped"] = out_of_range

    # Zero-quantity edge case: flagged, not silently dropped
    issues["zero_quantity_rows"] = int((df["quantity"] == 0).sum())

    return df, issues


def main():
    customers, products, orders, order_items = load_raw()

    report_lines = []
    report_lines.append("DATA QUALITY REPORT")
    report_lines.append("=" * 50)
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # --- customers / emails ---
    bad_emails = validate_emails(customers)
    report_lines.append(f"[customers] total rows: {len(customers)}")
    report_lines.append(f"[customers] invalid emails found: {len(bad_emails)}")
    if bad_emails:
        preview = ", ".join(map(str, bad_emails[:10]))
        report_lines.append(f"[customers] sample invalid-email customer_ids: {preview}")

    # --- products ---
    clean_products_df, prod_issues = clean_products(products)
    report_lines.append(f"\n[products] total rows: {len(products)}")
    report_lines.append(f"[products] names normalized (trim/title-case): {prod_issues['names_normalized']}")
    report_lines.append(f"[products] invalid cost_price values: {prod_issues['invalid_cost_price']}")

    # --- orders ---
    clean_orders_df, order_issues = clean_orders(orders)
    report_lines.append(f"\n[orders] total rows: {len(orders)}")
    report_lines.append(f"[orders] missing customer_id -> set to 'UNKNOWN': {order_issues['missing_customer_id']}")
    report_lines.append(f"[orders] date format fixed (DD-MM-YYYY -> YYYY-MM-DD HH:MM:SS): {order_issues['fixed_date_format']}")
    report_lines.append(f"[orders] rows dropped (unparseable date): {order_issues['rows_dropped_unparseable_date']}")

    # --- referential integrity (raw, before cleaning order_items) ---
    orphan_items = check_referential_integrity(order_items, clean_orders_df)
    report_lines.append(f"\n[order_items] total rows: {len(order_items)}")
    report_lines.append(f"[order_items] rows referencing non-existent order_id: {len(orphan_items)}")
    if len(orphan_items):
        preview_ids = ", ".join(orphan_items["order_id"].astype(str).unique()[:10])
        report_lines.append(f"[order_items] sample orphan order_ids: {preview_ids}")

    valid_order_ids = set(clean_orders_df["order_id"].astype(str))
    clean_items_df, item_issues = clean_order_items(order_items, valid_order_ids)
    report_lines.append(f"[order_items] orphan rows removed: {item_issues['orphan_items_removed']}")
    report_lines.append(f"[order_items] rows flagged as returns (negative qty): {item_issues['returns_flagged']}")
    report_lines.append(f"[order_items] discount_percent out of 0-100 range (clipped): {item_issues['discount_out_of_range_clipped']}")
    report_lines.append(f"[order_items] zero-quantity rows found: {item_issues['zero_quantity_rows']}")

    # --- write cleaned CSVs ---
    customers.to_csv(os.path.join(CLEAN_DIR, "customers_clean.csv"), index=False)
    clean_products_df.to_csv(os.path.join(CLEAN_DIR, "products_clean.csv"), index=False)
    clean_orders_df.to_csv(os.path.join(CLEAN_DIR, "orders_clean.csv"), index=False)
    clean_items_df.to_csv(os.path.join(CLEAN_DIR, "order_items_clean.csv"), index=False)

    report_lines.append("\nCleaned files written to data/cleaned/:")
    report_lines.append("  - customers_clean.csv")
    report_lines.append("  - products_clean.csv")
    report_lines.append("  - orders_clean.csv")
    report_lines.append("  - order_items_clean.csv")

    report_text = "\n".join(report_lines)
    print(report_text)

    report_path = os.path.join(REPORT_DIR, "data_quality_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")
    print(f"\n[ok] report saved -> {report_path}")


if __name__ == "__main__":
    main()
