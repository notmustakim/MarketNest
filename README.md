# MarketNest database project

This package implements the multi-vendor marketplace database designed in the submitted ECE 2215 assignment. It is prepared for the ECE 2216 project requirements and uses MySQL 8.0.16 or later with InnoDB. The package contains the complete SQL implementation, deterministic sample data, 29 useful queries, three views, three stored procedures, thirteen triggers, a full-featured Streamlit operations dashboard, a test runner, and the final project report.

## Folder map

- `sql/01_schema.sql` creates the 18 relational tables, keys, indexes, and row-level constraints.
- `sql/02_seed_data.sql` loads synthetic demonstration data. Each relation has at least 10 rows.
- `sql/03_database_features.sql` creates reporting views, stored procedures, and integrity triggers.
- `sql/04_queries.sql` contains 29 labeled, problem-focused SQL queries.
- `sql/05_security_template.sql` gives an optional least-privilege role template for an administrator to adapt.
- `app/` contains a presentation-ready operations dashboard for create, search, update, guarded delete, checkout, shipment, returns, reviews, payments, payouts, and reporting workflows.
- `diagrams/` contains the conceptual ER and relational EER diagrams from the submitted MarketNest assignment.
- `tests/` contains 34 documented tests, a MySQL test runner, and the latest recorded test results.
- `report/MarketNest_Final_Report.pdf` is the final written report.

## Setup in MySQL Workbench

1. Install MySQL Server 8.0.16 or later and MySQL Workbench. The schema uses enforced `CHECK` constraints; older MySQL releases may parse but ignore them.
2. Open and run `sql/01_schema.sql`.
3. Run `sql/02_seed_data.sql` to load sample records.
4. Run `sql/03_database_features.sql` to install the views, triggers, and procedures.
5. Run `sql/04_queries.sql` to review and execute the query set.
6. Run `python tests/run_tests.py` after installing the project requirements. Replace `tests/test_results.csv` with the observed results from your own MySQL server before submission.

The test runner is a command-line script. Run it with Python; do not launch it with `streamlit run`.

To run the SQL scripts from Command Prompt in the project folder, use:

```bat
mysql -u root -p < sql\01_schema.sql
mysql -u root -p < sql\02_seed_data.sql
mysql -u root -p < sql\03_database_features.sql
```

Run each command from the project folder. These scripts create/select the `marketnest` database themselves. Do not run the seed script repeatedly on a populated database because it intentionally uses fixed sample IDs. For a clean reset, back up any data you need and recreate the `marketnest` database manually before repeating the setup.

## Launch the dashboard

From the project folder, install the listed Python packages and copy `.env.example` to `.env`. Edit the MySQL host, database, user, and password values for your local server. Create a dedicated local account with only the required privileges where possible; do not put real credentials in the ZIP you submit.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app/app.py --server.address 127.0.0.1
```

If an older dashboard is already running, stop that process with `Ctrl+C` and start this command again to load the updated interface. Customers use the schema's Active/Suspended status; there is no identity-verification feature.

The dashboard saves changes to MySQL and provides a manual `Refresh data` button to reload tables. Deletes are blocked when they would remove referenced order, shipment, or payout history; use Hidden or Suspended status to retire linked records. The interface does not authenticate users or store card details, and payment outcomes are recorded locally without an external gateway. Checkout reserves stock and creates order lines inside one application-managed transaction.

## Tests and result recording

The test plan covers row counts, CHECK constraints, unique values, foreign keys, stock reservation and restoration, review eligibility, the return lifecycle, order status transitions, report objects, payout generation, transaction rollback, and rejected credentials. The runner requires a live MySQL instance and writes observed outcomes to `tests/test_results.csv`; run it on your own installation and include the results before submission. `test_cases.csv` lists the test descriptions and expected outcomes.

## Design notes

- Order-line purchase prices are stored as historical values.
- Product variants have a composite primary key `(product_id, variant_no)` and a globally unique SKU.
- An order's composite foreign key ensures its selected address belongs to its customer.
- Sample customer and seller addresses use the reserved `.test` domain and synthetic data.
- Sample password values are salted PBKDF2 hashes; the dashboard does not perform sign-in.
- The report uses the submitted assignment's normalization example and summarizes the additional implementation work.
