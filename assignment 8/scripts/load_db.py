"""
load_db.py
----------
Loads the cleaned CSVs (data/cleaned/) into a SQLite database
(ecommerce.db) using the schema defined in sql/schema.sql.

Run:
    python3 load_db.py
"""

import csv
import os
import sqlite3

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "cleaned")
SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")
DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")


def build_schema(conn):
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def load_csv(conn, table, path, columns):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = [tuple(row[c] for c in columns) for row in reader]
    placeholders = ", ".join(["?"] * len(columns))
    col_list = ", ".join(columns)
    conn.executemany(
        f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})", rows
    )
    print(f"[ok] loaded {len(rows)} rows into {table}")


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")  # off during bulk load
    build_schema(conn)

    load_csv(
        conn, "customers",
        os.path.join(CLEAN_DIR, "customers_clean.csv"),
        ["customer_id", "customer_name", "email", "registration_date", "customer_type"],
    )
    load_csv(
        conn, "products",
        os.path.join(CLEAN_DIR, "products_clean.csv"),
        ["product_id", "product_name", "category", "subcategory", "cost_price"],
    )
    load_csv(
        conn, "orders",
        os.path.join(CLEAN_DIR, "orders_clean.csv"),
        ["order_id", "customer_id", "order_date", "status", "region_code"],
    )
    load_csv(
        conn, "order_items",
        os.path.join(CLEAN_DIR, "order_items_clean.csv"),
        ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent", "is_return"],
    )

    conn.commit()

    # sanity check row counts
    for table in ("customers", "products", "orders", "order_items"):
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"[check] {table}: {n} rows")

    conn.close()
    print(f"\n[ok] database ready -> {DB_PATH}")


if __name__ == "__main__":
    main()
