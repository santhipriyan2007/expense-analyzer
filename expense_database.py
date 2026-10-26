import math
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
import csv
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "expenses.db"
CSV_PATH = BASE_DIR / "expenses.csv"

EXPENSE_COLUMNS = ["ID", "Date", "Category", "Description", "Amount"]


@contextmanager
def get_connection():
    """Open a database connection and always close it."""
    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
    finally:
        connection.close()


def initialize_database():
    """Create the table and safely migrate the original CSV once."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                ID INTEGER PRIMARY KEY,
                Date TEXT NOT NULL,
                Category TEXT NOT NULL,
                Description TEXT NOT NULL,
                Amount REAL NOT NULL CHECK (Amount > 0)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL,
                details TEXT NOT NULL
            )
        """)

        migration = connection.execute(
            "SELECT version FROM schema_migrations WHERE version = 1"
        ).fetchone()

        if migration is not None:
            return "Database initialized; CSV migration already checked."

        existing_count = connection.execute(
            "SELECT COUNT(*) FROM expenses"
        ).fetchone()[0]

        imported = 0
        skipped = 0

        if existing_count == 0 and CSV_PATH.exists():
            with CSV_PATH.open(
                "r", newline="", encoding="utf-8-sig"
            ) as csv_file:
                reader = csv.DictReader(csv_file)

                if reader.fieldnames is None or not set(
                    EXPENSE_COLUMNS
                ).issubset(reader.fieldnames):
                    raise ValueError(
                        "The original CSV does not contain the required columns."
                    )

                seen_ids = set()

                for row in reader:
                    try:
                        expense_id = int(row["ID"])
                        date_text = row["Date"].strip()
                        datetime.strptime(date_text, "%Y-%m-%d")

                        category = row["Category"].strip()
                        description = row["Description"].strip()
                        amount = float(row["Amount"])

                        if (
                            expense_id <= 0
                            or expense_id in seen_ids
                            or not category
                            or not description
                            or not amount > 0
                        ):
                            skipped += 1
                            continue

                        seen_ids.add(expense_id)

                        connection.execute("""
                            INSERT INTO expenses
                                (ID, Date, Category, Description, Amount)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            expense_id,
                            date_text,
                            category,
                            description,
                            amount,
                        ))
                        imported += 1

                    except (ValueError, TypeError, KeyError):
                        skipped += 1

        elif existing_count > 0:
            details = (
                "CSV migration skipped because the database "
                "already contains expense records."
            )
            connection.execute("""
                INSERT INTO schema_migrations
                    (version, applied_at, details)
                VALUES (1, ?, ?)
            """, (datetime.now().isoformat(timespec="seconds"), details))
            return details

        details = (
            f"CSV migration checked: {imported} imported, "
            f"{skipped} invalid or duplicate rows skipped."
        )

        connection.execute("""
            INSERT INTO schema_migrations
                (version, applied_at, details)
            VALUES (1, ?, ?)
        """, (datetime.now().isoformat(timespec="seconds"), details))

        return details


def get_all_expenses():
    """Retrieve expense records in date and ID order."""
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT ID, Date, Category, Description, Amount
            FROM expenses
            ORDER BY Date, ID
        """).fetchall()

    return rows


def replace_all_expenses(records):
    """Validate and atomically replace all expense records."""
    validated_records = []
    seen_ids = set()

    for record in records:
        if len(record) != 5:
            raise ValueError(
                "Each expense must contain ID, Date, Category, "
                "Description, and Amount."
            )

        expense_id, date_value, category, description, amount = record

        try:
            numeric_id = int(expense_id)
            if float(expense_id) != numeric_id or numeric_id <= 0:
                raise ValueError
        except (ValueError, TypeError, OverflowError):
            raise ValueError("Expense IDs must be positive integers.")

        if numeric_id in seen_ids:
            raise ValueError(f"Duplicate expense ID: {numeric_id}")

        date_text = str(date_value).strip()
        try:
            datetime.strptime(date_text, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid date for expense ID {numeric_id}: {date_text}"
            )

        category = str(category).strip()
        description = str(description).strip()

        if not category:
            raise ValueError(
                f"Category cannot be empty for expense ID {numeric_id}."
            )

        if not description:
            raise ValueError(
                f"Description cannot be empty for expense ID {numeric_id}."
            )

        try:
            numeric_amount = float(amount)
        except (ValueError, TypeError, OverflowError):
            raise ValueError(f"Invalid amount for expense ID {numeric_id}.")

        if not math.isfinite(numeric_amount) or numeric_amount <= 0:
            raise ValueError(
                f"Amount must be finite and positive for expense ID {numeric_id}."
            )

        seen_ids.add(numeric_id)
        validated_records.append(
            (
                numeric_id,
                date_text,
                category,
                description,
                numeric_amount,
            )
        )

    with get_connection() as connection:
        connection.execute("DELETE FROM expenses")
        connection.executemany(
            """
            INSERT INTO expenses (ID, Date, Category, Description, Amount)
            VALUES (?, ?, ?, ?, ?)
            """,
            validated_records,
        )

if __name__ == "__main__":
    print("Database:", DB_PATH)
    print(initialize_database())
    print("Imported database records:")

    for expense in get_all_expenses():
        print(expense)
