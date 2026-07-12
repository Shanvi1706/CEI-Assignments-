"""
generate_data.py
-----------------
Generates 4 raw CSV files for the E-Commerce Order Analytics System:
    - customers.csv
    - products.csv
    - orders.csv
    - order_items.csv

Intentional data quality issues are injected on purpose so that the
cleaning (Part 2) and edge-case (Part 5) stages have real problems to
solve:

    customers.csv
        - 2% of emails are invalid (missing '@' or missing domain)

    products.csv
        - Some product names have extra leading/trailing spaces and
          inconsistent casing (e.g. "  wireless mouse")

    orders.csv
        - 5% of orders have a NULL / empty customer_id
        - A portion of order_date values are written in the WRONG
          format (DD-MM-YYYY instead of YYYY-MM-DD HH:MM:SS)

    order_items.csv
        - 3% of rows have a negative quantity (treated as returns)
        - A handful of rows reference an order_id that does NOT exist
          in orders.csv, on purpose, so check_referential_integrity()
          in clean_data.py has something real to catch.

Run:
    python3 generate_data.py
Output:
    ../data/raw/*.csv
"""

import csv
import os
import random
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# ---------------------------------------------------------------- #
# Config
# ---------------------------------------------------------------- #
N_CUSTOMERS = 600
N_PRODUCTS = 550
N_ORDERS = 2000
MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 4

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

CATEGORIES = {
    "Electronics": ["Mobiles", "Laptops", "Accessories", "Cameras", "Audio"],
    "Clothing": ["Men", "Women", "Kids", "Footwear", "Winterwear"],
    "Home": ["Kitchen", "Furniture", "Decor", "Lighting", "Storage"],
    "Books": ["Fiction", "Non-Fiction", "Academic", "Comics", "Children"],
}

STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
STATUS_WEIGHTS = [0.15, 0.20, 0.45, 0.10, 0.10]

CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]
CUSTOMER_TYPE_WEIGHTS = [0.65, 0.25, 0.10]

REGION_CODES = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)


def random_datetime(start: datetime, end: datetime) -> datetime:
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def messy_product_name(name: str) -> str:
    """Randomly mangle a product name with spacing / casing issues."""
    roll = random.random()
    if roll < 0.10:
        return f"  {name}  "          # extra spaces
    elif roll < 0.20:
        return name.upper()           # ALL CAPS
    elif roll < 0.30:
        return name.lower()           # all lower
    return name


def maybe_bad_email(email: str) -> str:
    """2% chance of returning a broken email."""
    if random.random() < 0.02:
        variant = random.choice(["no_at", "no_domain"])
        if variant == "no_at":
            return email.replace("@", "")
        else:
            return email.split("@")[0] + "@"
    return email


# ---------------------------------------------------------------- #
# 1. customers.csv
# ---------------------------------------------------------------- #
def generate_customers():
    rows = []
    for cid in range(1, N_CUSTOMERS + 1):
        name = fake.name()
        base_email = f"{name.lower().replace(' ', '.')}{cid}@{fake.free_email_domain()}"
        email = maybe_bad_email(base_email)
        reg_date = random_datetime(START_DATE, END_DATE - timedelta(days=30))
        ctype = random.choices(CUSTOMER_TYPES, weights=CUSTOMER_TYPE_WEIGHTS)[0]
        rows.append(
            {
                "customer_id": cid,
                "customer_name": name,
                "email": email,
                "registration_date": reg_date.strftime("%Y-%m-%d %H:%M:%S"),
                "customer_type": ctype,
            }
        )

    path = os.path.join(OUT_DIR, "customers.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] wrote {len(rows)} rows -> {path}")
    return rows


# ---------------------------------------------------------------- #
# 2. products.csv
# ---------------------------------------------------------------- #
def generate_products():
    rows = []
    pid = 1
    for category, subcats in CATEGORIES.items():
        per_cat = N_PRODUCTS // len(CATEGORIES)
        for _ in range(per_cat):
            subcat = random.choice(subcats)
            raw_name = f"{fake.word().capitalize()} {subcat[:-1] if subcat.endswith('s') else subcat}"
            name = messy_product_name(raw_name)
            cost_price = round(random.uniform(50, 25000), 2)
            rows.append(
                {
                    "product_id": pid,
                    "product_name": name,
                    "category": category,
                    "subcategory": subcat,
                    "cost_price": cost_price,
                }
            )
            pid += 1

    path = os.path.join(OUT_DIR, "products.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] wrote {len(rows)} rows -> {path}")
    return rows


# ---------------------------------------------------------------- #
# 3. orders.csv
# ---------------------------------------------------------------- #
def generate_orders(customers):
    rows = []
    customer_ids = [c["customer_id"] for c in customers]

    for oid in range(1, N_ORDERS + 1):
        # 5% missing customer_id
        if random.random() < 0.05:
            cust_id = ""  # NULL / empty
        else:
            cust_id = random.choice(customer_ids)

        order_dt = random_datetime(START_DATE, END_DATE)

        # Most dates correct format; some intentionally wrong (DD-MM-YYYY)
        if random.random() < 0.06:
            order_date_str = order_dt.strftime("%d-%m-%Y")  # wrong format, no time
        else:
            order_date_str = order_dt.strftime("%Y-%m-%d %H:%M:%S")

        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        region = random.choice(REGION_CODES)

        rows.append(
            {
                "order_id": oid,
                "customer_id": cust_id,
                "order_date": order_date_str,
                "status": status,
                "region_code": region,
            }
        )

    path = os.path.join(OUT_DIR, "orders.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] wrote {len(rows)} rows -> {path}")
    return rows


# ---------------------------------------------------------------- #
# 4. order_items.csv
# ---------------------------------------------------------------- #
def generate_order_items(orders, products):
    rows = []
    item_id = 1
    product_ids = [p["product_id"] for p in products]
    order_ids = [o["order_id"] for o in orders]

    for order in orders:
        n_items = random.randint(MIN_ITEMS_PER_ORDER, MAX_ITEMS_PER_ORDER)
        for _ in range(n_items):
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 6)

            # 3% negative quantity (returns)
            if random.random() < 0.03:
                quantity = -quantity

            unit_price = round(random.uniform(100, 30000), 2)
            discount_percent = round(random.uniform(0, 40), 2)  # within 0-100

            rows.append(
                {
                    "item_id": item_id,
                    "order_id": order["order_id"],
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_percent": discount_percent,
                }
            )
            item_id += 1

    # Intentionally inject a few order_items rows that reference a
    # NON-EXISTENT order_id, so check_referential_integrity() has
    # something real to detect (see Part 2 / Part 5 requirements).
    max_order_id = max(order_ids)
    for _ in range(6):
        rows.append(
            {
                "item_id": item_id,
                "order_id": max_order_id + random.randint(1000, 5000),  # doesn't exist
                "product_id": random.choice(product_ids),
                "quantity": random.randint(1, 3),
                "unit_price": round(random.uniform(100, 5000), 2),
                "discount_percent": round(random.uniform(0, 20), 2),
            }
        )
        item_id += 1

    random.shuffle(rows)

    path = os.path.join(OUT_DIR, "order_items.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"[ok] wrote {len(rows)} rows -> {path}")
    return rows


def main():
    print("Generating e-commerce datasets ...")
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers)
    generate_order_items(orders, products)
    print("Done. Raw CSVs are in data/raw/")


if __name__ == "__main__":
    main()
