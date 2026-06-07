# Celebal Summer Internship 2026 – Week 2 SQL Task

## Project Overview

This project was completed as part of the **Celebal Technologies Summer Internship 2026**.

The objective of this assignment was to design, query, and analyze an E-Commerce Sales Database using SQL concepts such as:

- SELECT Statements
- Filtering with WHERE
- Constraints and Keys
- Indexes
- Aggregate Functions
- GROUP BY and HAVING
- Joins
- CASE Statements
- Transactions
- ACID Properties

---

## Database Schema

The database consists of four tables:

### 1. Customers
Stores customer information.

### 2. Products
Stores product details including category, brand, price, and stock.

### 3. Orders
Stores customer order information.

### 4. Order_Items
Stores product-level details for each order.

### Entity Relationships

```text
customers ──(1:N)──▶ orders
orders ──(1:N)──▶ order_items
products ──(1:N)──▶ order_items
```

---

## Technologies Used

- SQL
- SQLite
- Python
- Pandas
- Jupyter Notebook

---

## Tasks Completed

### Section A – SQL Basics

- Display all records from customers table
- Retrieve selected customer columns
- Find unique product categories
- Identify Primary Keys
- Analyze constraints
- Test CHECK constraints

### Section B – Filtering & Optimization

- Filter orders by status
- Find products by category and price
- Retrieve customers by state and joining date
- Date range filtering
- Understand index usage
- Write SARGable queries

### Section C – Aggregation

- Count total orders
- Calculate revenue
- Average product prices
- Revenue by order status
- Most expensive and cheapest products
- HAVING clause usage

### Section D – Joins & Relationships

- INNER JOIN
- LEFT JOIN
- Multi-table JOINs
- Foreign Key analysis
- Understanding JOIN types

### Section E – Advanced SQL Concepts

- CASE statements
- ACID properties
- Transactions
- COMMIT and ROLLBACK

---

## Repository Structure

```text
├── Celebal_Week2.ipynb
├── README.md
```

---

## Sample Query

Retrieve all delivered orders:

```sql
SELECT *
FROM orders
WHERE status = 'Delivered';
```

---

## Learning Outcomes

Through this project, I gained practical experience in:

- Relational Database Design
- SQL Query Writing
- Data Filtering and Analysis
- Aggregate Functions
- Database Constraints
- Query Optimization
- Joins and Relationships
- Transaction Management

---

## Author

**Shanvi**

B.Tech CSE (Data Science)  
JECRC University, Jaipur

---

## Internship

Celebal Technologies Summer Internship 2026
