"""
report_cli.py
-------------
Command-line reporting tool for the E-Commerce Order Analytics System.

Usage examples:
    python3 report_cli.py --report summary --type daily --start 2024-01-01 --end 2024-01-31
    python3 report_cli.py --report summary --type weekly --start 2024-01-01 --end 2024-01-31
    python3 report_cli.py --report summary --type monthly --start 2024-01-01 --end 2024-06-30
    python3 report_cli.py --report top_customers
    python3 report_cli.py --report retention

    # Interactive mode (no args) also asks for report type + date range:
    python3 report_cli.py

Notes:
    - Uses only the standard library (sqlite3, argparse, datetime) as required
      by the project spec ("No external libraries except sqlite3").
    - Connects to ecommerce.db, built by load_db.py from the cleaned CSVs.
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timedelta

BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.path.join(BASE_DIR, "ecommerce.db")


# ------------------------------------------------------------------ #
# Small text-table printer (no external 'tabulate' dependency)
# ------------------------------------------------------------------ #
def print_table(headers, rows):
    if not rows:
        print("  (no data)")
        return
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    def fmt_row(vals):
        return "  ".join(str(v).ljust(widths[i]) for i, v in enumerate(vals))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt_row(row))


# ------------------------------------------------------------------ #
# Input validation helpers (Part 5: edge case handling)
# ------------------------------------------------------------------ #
def validate_date(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError(
            f"Invalid date '{value}'. Expected format: YYYY-MM-DD"
        )


def get_connection():
    if not os.path.exists(DB_PATH):
        print(
            f"[error] Database not found at {DB_PATH}.\n"
            "        Run 'python3 load_db.py' first to build it from the cleaned CSVs."
        )
        sys.exit(1)
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1")  # verify the connection actually works
        return conn
    except sqlite3.Error as e:
        print(f"[error] Could not connect to database: {e}")
        sys.exit(1)


# ------------------------------------------------------------------ #
# Report: summary (daily / weekly / monthly) with previous-period comparison
# ------------------------------------------------------------------ #
def summary_report(conn, report_type, start_date, end_date):
    if start_date > end_date:
        print("[error] start date must be before end date.")
        return

    period_len = (end_date - start_date) + timedelta(days=1)
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - period_len + timedelta(days=1)

    def period_metrics(p_start, p_end):
        start_s = p_start.strftime("%Y-%m-%d 00:00:00")
        end_s = p_end.strftime("%Y-%m-%d 23:59:59")
        row = conn.execute(
            """
            SELECT
                COUNT(DISTINCT o.order_id) AS total_orders,
                COALESCE(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 0) AS revenue,
                COUNT(DISTINCT o.customer_id) AS unique_customers
            FROM orders o
            LEFT JOIN order_items oi ON oi.order_id = o.order_id AND oi.quantity > 0
            WHERE o.order_date BETWEEN ? AND ?
            """,
            (start_s, end_s),
        ).fetchone()
        return {"orders": row[0], "revenue": row[1] or 0.0, "customers": row[2]}

    current = period_metrics(start_date, end_date)
    previous = period_metrics(prev_start, prev_end)

    top_products = conn.execute(
        """
        SELECT p.product_name, SUM(oi.quantity) AS units_sold
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_date BETWEEN ? AND ? AND oi.quantity > 0
        GROUP BY p.product_name
        ORDER BY units_sold DESC
        LIMIT 3
        """,
        (start_date.strftime("%Y-%m-%d 00:00:00"), end_date.strftime("%Y-%m-%d 23:59:59")),
    ).fetchall()

    def pct_change(cur, prev):
        if prev == 0:
            return "N/A" if cur == 0 else "+inf"
        return f"{((cur - prev) / prev) * 100:+.2f}%"

    print(f"\n{report_type.upper()} SUMMARY REPORT")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"(Previous period for comparison: {prev_start.date()} to {prev_end.date()})")
    print("-" * 55)
    print_table(
        ["Metric", "Current Period", "Previous Period", "% Change"],
        [
            ["Total Orders", current["orders"], previous["orders"], pct_change(current["orders"], previous["orders"])],
            ["Revenue", f"{current['revenue']:.2f}", f"{previous['revenue']:.2f}", pct_change(current["revenue"], previous["revenue"])],
            ["Unique Customers", current["customers"], previous["customers"], pct_change(current["customers"], previous["customers"])],
        ],
    )

    print("\nTop 3 Products (by units sold):")
    if top_products:
        print_table(["Product", "Units Sold"], top_products)
    else:
        print("  (no orders in this period)")


# ------------------------------------------------------------------ #
# Report: top customers
# ------------------------------------------------------------------ #
def top_customers_report(conn, limit=10):
    rows = conn.execute(
        """
        SELECT o.customer_id, c.customer_name,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_percent / 100.0)), 2) AS total_value
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        LEFT JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.customer_id <> 'UNKNOWN' AND oi.quantity > 0
        GROUP BY o.customer_id, c.customer_name
        ORDER BY total_value DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    print(f"\nTOP {limit} CUSTOMERS BY TOTAL ORDER VALUE")
    print("-" * 55)
    print_table(["Customer ID", "Customer Name", "Total Value"], rows)


# ------------------------------------------------------------------ #
# Report: retention (cohort-based, month 0-3)
# ------------------------------------------------------------------ #
def retention_report(conn):
    rows = conn.execute(
        """
        WITH cohorts AS (
            SELECT customer_id, strftime('%Y-%m', registration_date) AS cohort_month,
                   DATE(registration_date) AS reg_date
            FROM customers
        ),
        customer_order_months AS (
            SELECT o.customer_id, DATE(o.order_date) AS order_date
            FROM orders o WHERE o.customer_id <> 'UNKNOWN'
        ),
        cohort_activity AS (
            SELECT c.cohort_month, c.customer_id,
                   CAST((strftime('%Y', co.order_date) - strftime('%Y', c.reg_date)) * 12
                        + (strftime('%m', co.order_date) - strftime('%m', c.reg_date)) AS INTEGER) AS month_offset
            FROM cohorts c JOIN customer_order_months co ON co.customer_id = c.customer_id
        ),
        cohort_sizes AS (
            SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size FROM cohorts GROUP BY cohort_month
        ),
        month_activity AS (
            SELECT cohort_month, month_offset, COUNT(DISTINCT customer_id) AS active_customers
            FROM cohort_activity WHERE month_offset BETWEEN 0 AND 3
            GROUP BY cohort_month, month_offset
        )
        SELECT ma.cohort_month, ma.month_offset, ma.active_customers, cs.cohort_size,
               ROUND(100.0 * ma.active_customers / cs.cohort_size, 2) AS retention_pct
        FROM month_activity ma JOIN cohort_sizes cs ON cs.cohort_month = ma.cohort_month
        ORDER BY ma.cohort_month, ma.month_offset
        LIMIT 30
        """
    ).fetchall()
    print("\nCOHORT RETENTION REPORT (month 0-3, first 30 rows)")
    print("-" * 55)
    print_table(["Cohort Month", "Month Offset", "Active Customers", "Cohort Size", "Retention %"], rows)


# ------------------------------------------------------------------ #
# CLI
# ------------------------------------------------------------------ #
def parse_args():
    parser = argparse.ArgumentParser(description="E-Commerce Analytics CLI Reporting Tool")
    parser.add_argument(
        "--report",
        choices=["summary", "top_customers", "retention"],
        help="Which report to generate",
    )
    parser.add_argument(
        "--type",
        choices=["daily", "weekly", "monthly"],
        default="monthly",
        help="Report granularity (only used by --report summary)",
    )
    parser.add_argument("--start", type=str, help="Start date YYYY-MM-DD (for --report summary)")
    parser.add_argument("--end", type=str, help="End date YYYY-MM-DD (for --report summary)")
    return parser.parse_args()


def interactive_prompt():
    print("E-Commerce Analytics CLI (interactive mode)")
    report = input("Report type [summary/top_customers/retention]: ").strip().lower()
    if report not in ("summary", "top_customers", "retention"):
        print("[error] invalid report type.")
        sys.exit(1)
    if report == "summary":
        rtype = input("Granularity [daily/weekly/monthly]: ").strip().lower() or "monthly"
        start = input("Start date (YYYY-MM-DD): ").strip()
        end = input("End date (YYYY-MM-DD): ").strip()
        return report, rtype, start, end
    return report, None, None, None


def main():
    args = parse_args()

    if args.report is None:
        report, rtype, start, end = interactive_prompt()
    else:
        report, rtype, start, end = args.report, args.type, args.start, args.end

    conn = get_connection()

    try:
        if report == "summary":
            if not start or not end:
                print("[error] --start and --end are required for the summary report.")
                sys.exit(1)
            try:
                start_date = validate_date(start)
                end_date = validate_date(end)
            except argparse.ArgumentTypeError as e:
                print(f"[error] {e}")
                sys.exit(1)
            summary_report(conn, rtype, start_date, end_date)

        elif report == "top_customers":
            top_customers_report(conn)

        elif report == "retention":
            retention_report(conn)

        else:
            print("[error] unknown report type.")
            sys.exit(1)

    except sqlite3.Error as e:
        print(f"[error] database error: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
