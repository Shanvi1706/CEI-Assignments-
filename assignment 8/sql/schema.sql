-- schema.sql
-- Schema for the E-Commerce Order Analytics System (SQLite dialect)
-- Run this before loading the cleaned CSVs.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id      INTEGER PRIMARY KEY,
    customer_name    TEXT NOT NULL,
    email            TEXT,
    registration_date TEXT NOT NULL,   -- YYYY-MM-DD HH:MM:SS
    customer_type    TEXT NOT NULL CHECK (customer_type IN ('REGULAR', 'PREMIUM', 'VIP'))
);

CREATE TABLE products (
    product_id    INTEGER PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    subcategory   TEXT,
    cost_price    REAL NOT NULL CHECK (cost_price >= 0)
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   TEXT,               -- 'UNKNOWN' allowed for missing customers
    order_date    TEXT NOT NULL,      -- YYYY-MM-DD HH:MM:SS
    status        TEXT NOT NULL CHECK (status IN ('PLACED','SHIPPED','DELIVERED','CANCELLED','RETURNED')),
    region_code   TEXT NOT NULL
);

CREATE TABLE order_items (
    item_id           INTEGER PRIMARY KEY,
    order_id          INTEGER NOT NULL,
    product_id        INTEGER NOT NULL,
    quantity          INTEGER NOT NULL,
    unit_price        REAL NOT NULL CHECK (unit_price >= 0),
    discount_percent  REAL NOT NULL CHECK (discount_percent BETWEEN 0 AND 100),
    is_return         INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_items_order ON order_items(order_id);
CREATE INDEX idx_items_product ON order_items(product_id);
