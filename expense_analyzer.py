
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from contextlib import contextmanager


from expense_database import (
    initialize_database,
    get_all_expenses,
    replace_all_expenses,
)


# ----------------------------- FILES & SETTINGS -----------------------------

BASE_DIR = Path(__file__).resolve().parent
EXPENSE_FILE = BASE_DIR / "expenses.csv"  # Original CSV retained
BUDGET_FILE = BASE_DIR / "budget.csv"
REPORT_DIR = BASE_DIR / "reports"

EXPENSE_COLUMNS = ["ID", "Date", "Category", "Description", "Amount"]
BUDGET_COLUMNS = ["Month", "Budget"]

CATEGORIES = [
    "Food",
    "Transport",
    "Shopping",
    "Bills",
    "Entertainment",
    "Education",
    "Health",
    "Travel",
    "Other",
]


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

# ------------------------------- DATA STORAGE -------------------------------

def initialise_files():
    """Initialize SQLite and create required folders and budget CSV."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize the database and run its safe, one-time CSV migration.
    print(initialize_database())

    # Budgets remain CSV-based.
    if not BUDGET_FILE.exists():
        pd.DataFrame(columns=BUDGET_COLUMNS).to_csv(
            BUDGET_FILE, index=False
        )


def load_expenses():
    """Load expenses from SQLite into a Pandas DataFrame."""
    records = get_all_expenses()

    df = pd.DataFrame(records, columns=EXPENSE_COLUMNS)

    if df.empty:
        return pd.DataFrame({
            "ID": pd.Series(dtype="int64"),
            "Date": pd.Series(dtype="datetime64[ns]"),
            "Category": pd.Series(dtype="object"),
            "Description": pd.Series(dtype="object"),
            "Amount": pd.Series(dtype="float64"),
        })

    df["ID"] = pd.to_numeric(df["ID"], errors="raise").astype(int)
    df["Date"] = pd.to_datetime(
        df["Date"], format="%Y-%m-%d", errors="raise"
    )
    df["Amount"] = pd.to_numeric(df["Amount"], errors="raise")

    return df.sort_values(
        ["Date", "ID"]
    ).reset_index(drop=True)


def save_expenses(df):
    """Validate and transactionally replace the SQLite expense records."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Expenses must be supplied as a Pandas DataFrame.")

    missing = set(EXPENSE_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required expense columns: {sorted(missing)}"
        )

    output = df[EXPENSE_COLUMNS].copy()

    # Validate IDs.
    ids = pd.to_numeric(output["ID"], errors="raise")

    if ids.isna().any():
        raise ValueError("Expense IDs cannot be empty.")

    if not np.isfinite(ids.to_numpy(dtype=float)).all():
        raise ValueError("Expense IDs must be finite numbers.")

    if ((ids <= 0) | (ids % 1 != 0)).any():
        raise ValueError("Expense IDs must be positive integers.")

    output["ID"] = ids.astype(int)

    if output["ID"].duplicated().any():
        raise ValueError("Duplicate expense IDs are not allowed.")

    # Validate dates.
    dates = pd.to_datetime(output["Date"], errors="raise")

    if dates.isna().any():
        raise ValueError("Expense dates cannot be empty.")

    output["Date"] = dates.dt.strftime("%Y-%m-%d")

    # Validate categories and descriptions.
    for column in ["Category", "Description"]:
        if output[column].isna().any():
            raise ValueError(f"{column} cannot contain empty values.")

        output[column] = output[column].astype(str).str.strip()

        if output[column].eq("").any():
            raise ValueError(f"{column} cannot contain empty values.")

    # Validate amounts.
    amounts = pd.to_numeric(output["Amount"], errors="raise")

    if amounts.isna().any():
        raise ValueError("Expense amounts cannot be empty.")

    amount_values = amounts.to_numpy(dtype=float)

    if not np.isfinite(amount_values).all():
        raise ValueError("Expense amounts must be finite numbers.")

    if (amounts <= 0).any():
        raise ValueError("Expense amounts must be greater than zero.")

    output["Amount"] = amounts.astype(float)

    # The database module validates records and performs the transaction.
    records = list(output.itertuples(index=False, name=None))
    replace_all_expenses(records)


def load_budgets():
    """Load monthly budgets from CSV."""
    try:
        df = pd.read_csv(BUDGET_FILE)
    except (pd.errors.EmptyDataError, FileNotFoundError):
        df = pd.DataFrame(columns=BUDGET_COLUMNS)

    for column in BUDGET_COLUMNS:
        if column not in df.columns:
            df[column] = pd.Series(dtype="object")

    df = df[BUDGET_COLUMNS]
    df["Month"] = df["Month"].fillna("").astype(str)
    df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
    df = df.dropna(subset=["Budget"])
    df = df[
        df["Month"].str.fullmatch(r"\d{4}-\d{2}")
        & (df["Budget"] > 0)
    ]

    return df.drop_duplicates(
        subset=["Month"], keep="last"
    ).reset_index(drop=True)


def save_budgets(df):
    """Save monthly budgets to CSV."""
    df[BUDGET_COLUMNS].sort_values("Month").to_csv(
        BUDGET_FILE, index=False
    )


# --------------------------------- INPUTS -----------------------------------

def read_nonempty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")


def read_positive_amount(prompt):
    while True:
        try:
            amount = float(input(prompt).strip())

            if np.isfinite(amount) and amount > 0:
                return round(amount, 2)

            print("Enter an amount greater than zero.")

        except ValueError:
            print("Invalid amount. Enter a number such as 125.50.")


def read_date(prompt="Enter date (YYYY-MM-DD), or press Enter for today: "):
    while True:
        value = input(prompt).strip()

        if not value:
            return pd.Timestamp.today().normalize()

        try:
            date = pd.to_datetime(
                value, format="%Y-%m-%d", errors="raise"
            )

            if date > pd.Timestamp.today().normalize():
                print("Future expense dates are not allowed.")
                continue

            return date.normalize()

        except (ValueError, TypeError):
            print("Invalid date. Use YYYY-MM-DD, for example 2026-10-17.")


def read_month(prompt="Enter month (YYYY-MM): "):
    while True:
        month = input(prompt).strip()

        try:
            datetime.strptime(month, "%Y-%m")
            return month

        except ValueError:
            print("Invalid month. Use YYYY-MM, for example 2026-10.")


def choose_category():
    print("\nCategories:")

    for index, category in enumerate(CATEGORIES, start=1):
        print(f"{index}. {category}")

    while True:
        choice = input("Choose a category number: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(CATEGORIES):
            return CATEGORIES[int(choice) - 1]

        print(f"Enter a number from 1 to {len(CATEGORIES)}.")


def read_id(df, prompt="Enter expense ID: "):
    while True:
        value = input(prompt).strip()

        if value.isdigit() and int(value) in df["ID"].tolist():
            return int(value)

        print("That ID was not found. Please enter an ID shown in the records.")


# ----------------------------- EXPENSE FEATURES -----------------------------

def add_expense():
    df = load_expenses()
    next_id = int(df["ID"].max()) + 1 if not df.empty else 1

    print("\n--- Add Expense ---")
    date = read_date()
    category = choose_category()
    description = read_nonempty("Description: ")
    amount = read_positive_amount("Amount (₹): ")

    new_row = pd.DataFrame([{
        "ID": next_id,
        "Date": date,
        "Category": category,
        "Description": description,
        "Amount": amount,
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    save_expenses(df)

    print(f"\nExpense added successfully. Expense ID: {next_id}")


def view_expenses(df=None):
    if df is None:
        df = load_expenses()

    print("\n--- Expense Records ---")

    if df.empty:
        print("No expenses found.")
        return

    display = df.copy()
    display["Date"] = display["Date"].dt.strftime("%Y-%m-%d")
    display["Amount"] = display["Amount"].map(lambda x: f"₹{x:,.2f}")

    print(display.to_string(index=False))


def search_expenses():
    df = load_expenses()

    if df.empty:
        print("\nNo expenses available to search.")
        return

    print("\n--- Search Expenses ---")
    print("1. Search by category")
    print("2. Search by description")
    print("3. Search by month")

    choice = input("Choose an option: ").strip()

    if choice == "1":
        term = read_nonempty("Category name: ").casefold()
        result = df[df["Category"].str.casefold() == term]

    elif choice == "2":
        term = read_nonempty("Description keyword: ").casefold()
        result = df[
            df["Description"].str.casefold().str.contains(
                term, regex=False
            )
        ]

    elif choice == "3":
        month = read_month()
        result = df[df["Date"].dt.strftime("%Y-%m") == month]

    else:
        print("Invalid option.")
        return

    view_expenses(result)

    if not result.empty:
        print(
            f"Matching records: {len(result)} | "
            f"Total: ₹{result['Amount'].sum():,.2f}"
        )


def edit_expense():
    df = load_expenses()

    if df.empty:
        print("\nNo expenses available to edit.")
        return

    view_expenses(df)
    expense_id = read_id(df)
    index = df.index[df["ID"] == expense_id][0]

    print("\nPress Enter to keep the current value.")

    current_date = df.at[index, "Date"].strftime("%Y-%m-%d")
    date_input = input(f"Date [{current_date}] (YYYY-MM-DD): ").strip()

    if date_input:
        try:
            new_date = pd.to_datetime(
                date_input, format="%Y-%m-%d"
            )

            if new_date > pd.Timestamp.today().normalize():
                print("Future expense dates are not allowed.")
                return

            df.at[index, "Date"] = new_date

        except ValueError:
            print("Invalid date. No changes saved.")
            return

    current_category = df.at[index, "Category"]
    print(f"Current category: {current_category}")

    change_category = input("Change category? (y/n): ").strip().lower()

    if change_category == "y":
        df.at[index, "Category"] = choose_category()

    current_description = df.at[index, "Description"]
    description = input(
        f"Description [{current_description}]: "
    ).strip()

    if description:
        df.at[index, "Description"] = description

    current_amount = df.at[index, "Amount"]
    amount = input(f"Amount [₹{current_amount:.2f}]: ").strip()

    if amount:
        try:
            new_amount = float(amount)

            if not np.isfinite(new_amount) or new_amount <= 0:
                raise ValueError

            df.at[index, "Amount"] = round(new_amount, 2)

        except ValueError:
            print("Invalid amount. No changes saved.")
            return

    save_expenses(df)
    print("Expense updated successfully.")


def delete_expense():
    df = load_expenses()

    if df.empty:
        print("\nNo expenses available to delete.")
        return

    view_expenses(df)
    expense_id = read_id(df)

    confirm = input(
        f"Delete expense ID {expense_id}? (y/n): "
    ).strip().lower()

    if confirm != "y":
        print("Deletion cancelled.")
        return

    df = df[df["ID"] != expense_id]
    save_expenses(df)

    print("Expense deleted successfully.")


# ------------------------------ ANALYSIS ------------------------------------

def show_summary(df=None):
    if df is None:
        df = load_expenses()

    print("\n--- Expense Summary ---")

    if df.empty:
        print("No expenses available for analysis.")
        return

    amounts = df["Amount"].to_numpy(dtype=float)

    print(f"Number of expenses : {len(df)}")
    print(f"Total spending     : ₹{np.sum(amounts):,.2f}")
    print(f"Average expense    : ₹{np.mean(amounts):,.2f}")
    print(f"Median expense     : ₹{np.median(amounts):,.2f}")
    print(f"Highest expense    : ₹{np.max(amounts):,.2f}")
    print(f"Lowest expense     : ₹{np.min(amounts):,.2f}")
    print(f"Standard deviation : ₹{np.std(amounts):,.2f}")

    highest_row = df.loc[df["Amount"].idxmax()]

    print(
        f"Largest transaction: ID {int(highest_row['ID'])} — "
        f"{highest_row['Description']} "
        f"(₹{highest_row['Amount']:,.2f})"
    )

    print("\nCategory-wise spending:")

    category_summary = (
        df.groupby("Category")["Amount"]
        .agg(["sum", "mean", "count"])
        .sort_values("sum", ascending=False)
    )

    category_summary.columns = [
        "Total (₹)", "Average (₹)", "Transactions"
    ]

    print(category_summary.round(2).to_string())

    print("\nMonthly spending:")

    monthly = df.assign(Month=df["Date"].dt.strftime("%Y-%m"))

    print(
        monthly.groupby("Month")["Amount"]
        .sum()
        .sort_index()
        .map(lambda value: f"₹{value:,.2f}")
        .to_string()
    )

    print("\nDaily spending:")

    daily = df.assign(Date=df["Date"].dt.strftime("%Y-%m-%d"))

    print(
        daily.groupby("Date")["Amount"]
        .sum()
        .sort_index()
        .map(lambda value: f"₹{value:,.2f}")
        .to_string()
    )


def set_monthly_budget():
    budgets = load_budgets()

    print("\n--- Set Monthly Budget ---")
    month = read_month()
    amount = read_positive_amount("Monthly budget (₹): ")

    budgets = budgets[budgets["Month"] != month]

    budgets = pd.concat(
        [
            budgets,
            pd.DataFrame([{"Month": month, "Budget": amount}]),
        ],
        ignore_index=True,
    )

    save_budgets(budgets)

    print(f"Budget for {month} set to ₹{amount:,.2f}.")


def budget_status():
    df = load_expenses()
    budgets = load_budgets()

    print("\n--- Monthly Budget Status ---")

    month_input = input(
        "Enter month (YYYY-MM), or press Enter for current month: "
    ).strip()

    if month_input:
        try:
            datetime.strptime(month_input, "%Y-%m")
            month = month_input

        except ValueError:
            print("Invalid month format.")
            return

    else:
        month = pd.Timestamp.today().strftime("%Y-%m")

    spent = float(
        df.loc[
            df["Date"].dt.strftime("%Y-%m") == month,
            "Amount",
        ].sum()
    )

    matching = budgets[budgets["Month"] == month]

    print(f"Month: {month}")
    print(f"Total spent: ₹{spent:,.2f}")

    if matching.empty:
        print("No budget has been set for this month.")
        print("Use the 'Set monthly budget' menu option first.")
        return

    budget = float(matching.iloc[0]["Budget"])
    remaining = budget - spent
    percentage = (spent / budget) * 100 if budget else 0

    print(f"Budget: ₹{budget:,.2f}")
    print(f"Spent: {percentage:.1f}% of budget")

    if remaining < 0:
        print(f"Over budget by: ₹{abs(remaining):,.2f}")
    else:
        print(f"Budget remaining: ₹{remaining:,.2f}")

    if percentage >= 100:
        print("ALERT: Monthly budget has been reached or exceeded.")
    elif percentage >= 80:
        print("WARNING: You have used at least 80% of your budget.")
    else:
        print("Status: Spending is within the budget.")


# ------------------------------- CHARTS -------------------------------------

def generate_charts():
    df = load_expenses()

    if df.empty:
        print("\nAdd some expenses before generating charts.")
        return

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    chart_df = df.copy()
    chart_df["Month"] = chart_df["Date"].dt.strftime("%Y-%m")
    chart_df["Day"] = chart_df["Date"].dt.strftime("%Y-%m-%d")

    category_totals = (
        chart_df.groupby("Category")["Amount"]
        .sum()
        .sort_values(ascending=False)
    )

    monthly_totals = (
        chart_df.groupby("Month")["Amount"].sum().sort_index()
    )

    daily_totals = (
        chart_df.groupby("Day")["Amount"].sum().sort_index()
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    category_totals.plot(kind="bar", ax=ax)
    ax.set_title("Expense by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount (₹)")
    ax.tick_params(axis="x", labelrotation=35)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "category_expenses.png", dpi=150)
    plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 7))
    category_totals.plot(kind="pie", autopct="%1.1f%%", ax=ax)
    ax.set_title("Expense Distribution by Category")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "category_distribution.png", dpi=150)
    plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    monthly_totals.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Monthly Spending Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount (₹)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "monthly_trend.png", dpi=150)
    plt.show()
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5))
    daily_totals.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Daily Spending Trend")
    ax.set_xlabel("Date")
    ax.set_ylabel("Amount (₹)")
    ax.tick_params(axis="x", labelrotation=35)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "daily_trend.png", dpi=150)
    plt.show()
    plt.close(fig)

    print(f"\nCharts saved in: {REPORT_DIR}")


def export_summary():
    df = load_expenses()

    if df.empty:
        print("\nNo expenses available to export.")
        return

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    category_report = (
        df.groupby("Category")["Amount"]
        .agg(Total="sum", Average="mean", Transactions="count")
        .sort_values("Total", ascending=False)
        .round(2)
    )

    category_path = REPORT_DIR / "category_summary.csv"
    category_report.to_csv(category_path)

    monthly_df = df.assign(
        Month=df["Date"].dt.strftime("%Y-%m")
    )

    monthly_report = (
        monthly_df.groupby("Month")["Amount"]
        .sum()
        .rename("Total")
    )

    monthly_path = REPORT_DIR / "monthly_summary.csv"
    monthly_report.to_csv(monthly_path, header=True)

    budgets = load_budgets()
    budget_path = REPORT_DIR / "budget_summary.csv"
    budgets.to_csv(budget_path, index=False)

    print("\nSummary reports exported:")
    print(f"- {category_path}")
    print(f"- {monthly_path}")
    print(f"- {budget_path}")


# ---------------------------------- MENU -------------------------------------

def print_menu():
    print("\n" + "=" * 48)
    print("             EXPENSE ANALYZER")
    print("=" * 48)
    print("1.  Add expense")
    print("2.  View all expenses")
    print("3.  Search expenses")
    print("4.  Edit an expense")
    print("5.  Delete an expense")
    print("6.  View expense analysis")
    print("7.  Set monthly budget")
    print("8.  Check monthly budget")
    print("9.  Generate charts")
    print("10. Export summary reports")
    print("0.  Exit")
    print("=" * 48)


def main():
    initialise_files()

    print("Welcome to the Python Expense Analyzer!")
    print(f"Expense database: {BASE_DIR / 'expenses.db'}")

    actions = {
        "1": add_expense,
        "2": view_expenses,
        "3": search_expenses,
        "4": edit_expense,
        "5": delete_expense,
        "6": show_summary,
        "7": set_monthly_budget,
        "8": budget_status,
        "9": generate_charts,
        "10": export_summary,
    }

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "0":
            print("\nYour data has been saved. Thank you for using Expense Analyzer!")
            break

        action = actions.get(choice)

        if action is None:
            print("Invalid choice. Please enter a number from 0 to 10.")
            continue

        try:
            action()

        except (OSError, pd.errors.ParserError) as error:
            print(f"File or storage error: {error}")

        except KeyboardInterrupt:
            print("\nOperation cancelled.")

        except Exception as error:
            print(f"An unexpected error occurred: {error}")

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()
