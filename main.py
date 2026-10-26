
from datetime import date, datetime
import math

from flask import Flask, request, redirect, url_for, render_template_string

import expense_database as db
import expense_analyzer as ea

app = Flask(__name__)
CATEGORIES = ea.CATEGORIES

PAGE = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Expense Analyzer</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1050px;
               margin: 30px auto; padding: 0 16px; background: #f4f6f9; }
        h1 { color: #243b53; }
        section { background: white; padding: 18px; margin: 16px 0;
                  border-radius: 8px; }
        input, select, button { padding: 9px; margin: 5px 3px;
                                max-width: 100%; }
        button, .button { background: #2457a7; color: white;
                          border: 0; padding: 9px 12px;
                          border-radius: 4px; cursor: pointer;
                          text-decoration: none; }
        table { width: 100%; border-collapse: collapse; background: white; }
        th, td { padding: 10px; border-bottom: 1px solid #ddd;
                 text-align: left; }
        th { background: #e8eef7; }
        .stats { display: flex; flex-wrap: wrap; gap: 12px; }
        .stats section { flex: 1; min-width: 160px; }
        .error { color: #b42318; }
        .actions { white-space: nowrap; }
    </style>
</head>
<body>
    <h1>Expense Analyzer</h1>
    <p>Track expenses, review spending and manage your monthly budget.</p>

    {% if error %}<p class="error">{{ error }}</p>{% endif %}

    <div class="stats">
        <section>
            <h3>Total Spending</h3>
            <strong>₹{{ "%.2f"|format(total) }}</strong>
        </section>
        <section>
            <h3>Transactions</h3>
            <strong>{{ count }}</strong>
        </section>
        <section>
            <h3>{{ month }} Budget</h3>
            <strong>
                {% if budget %}₹{{ "%.2f"|format(budget) }}
                {% else %}Not set{% endif %}
            </strong>
            <p>Spent this month: ₹{{ "%.2f"|format(month_spent) }}</p>
            {% if budget %}
                <p>
                {% if month_spent > budget %}Budget exceeded
                {% else %}Remaining: ₹{{ "%.2f"|format(budget-month_spent) }}
                {% endif %}
                </p>
            {% endif %}
        </section>
    </div>

    <section>
        <h2>Add Expense</h2>
        <form method="post" action="{{ url_for('add_expense') }}">
            <input type="date" name="date" value="{{ today }}" required>
            <select name="category" required>
                {% for category in categories %}
                <option value="{{ category }}">{{ category }}</option>
                {% endfor %}
            </select>
            <input name="description" placeholder="Description"
                   maxlength="200" required>
            <input type="number" name="amount" min="0.01" step="0.01"
                   placeholder="Amount" required>
            <button type="submit">Add Expense</button>
        </form>
    </section>

    <section>
        <h2>Monthly Budget</h2>
        <form method="post" action="{{ url_for('set_budget') }}">
            <input type="month" name="month" value="{{ month }}" required>
            <input type="number" name="budget" min="0.01" step="0.01"
                   placeholder="Budget amount" required>
            <button type="submit">Save Budget</button>
        </form>
    </section>

    <section>
        <h2>Expenses</h2>
        <form method="get" action="{{ url_for('index') }}">
            <input name="q" value="{{ query }}"
                   placeholder="Search description or category">
            <button type="submit">Search</button>
            <a href="{{ url_for('index') }}">Clear</a>
        </form>

        <table>
            <thead>
                <tr><th>ID</th><th>Date</th><th>Category</th>
                    <th>Description</th><th>Amount</th><th>Actions</th></tr>
            </thead>
            <tbody>
            {% for e in expenses %}
                <tr>
                    <td>{{ e[0] }}</td><td>{{ e[1] }}</td>
                    <td>{{ e[2] }}</td><td>{{ e[3] }}</td>
                    <td>₹{{ "%.2f"|format(e[4]) }}</td>
                    <td class="actions">
                        <a href="{{ url_for('edit_expense', expense_id=e[0]) }}">
                            Edit
                        </a>
                        <form method="post"
                              action="{{ url_for('delete_expense',
                                                expense_id=e[0]) }}"
                              onsubmit="return confirm('Delete this expense?');">
                            <button type="submit">Delete</button>
                        </form>
                    </td>
                </tr>
            {% else %}
                <tr><td colspan="6">No expenses found.</td></tr>
            {% endfor %}
            </tbody>
        </table>
    </section>
</body>
</html>
"""

EDIT_PAGE = """
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Edit Expense</title></head>
<body style="font-family:Arial;max-width:600px;margin:40px auto">
<h1>Edit Expense #{{ expense[0] }}</h1>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
<form method="post">
    <p>Date: <input type="date" name="date"
       value="{{ expense[1] }}" required></p>
    <p>Category:
    <select name="category" required>
    {% for c in categories %}
        <option value="{{ c }}" {% if c == expense[2] %}selected{% endif %}>
            {{ c }}
        </option>
    {% endfor %}
    </select></p>
    <p>Description: <input name="description" maxlength="200"
       value="{{ expense[3] }}" required></p>
    <p>Amount: <input type="number" name="amount" min="0.01"
       step="0.01" value="{{ expense[4] }}" required></p>
    <button type="submit">Save Changes</button>
</form>
<p><a href="{{ url_for('index') }}">Back to dashboard</a></p>
</body>
</html>
"""


def get_records():
    """Return the current database records."""
    return db.get_all_expenses()


def validate_form(form):
    """Validate expense form fields before saving."""
    date_text = form.get("date", "").strip()
    category = form.get("category", "").strip()
    description = form.get("description", "").strip()

    try:
        datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Enter a valid date.")

    if category not in CATEGORIES:
        raise ValueError("Choose a valid category.")

    if not description or len(description) > 200:
        raise ValueError("Description must contain 1–200 characters.")

    try:
        amount = float(form.get("amount", ""))
    except (ValueError, TypeError):
        raise ValueError("Enter a valid amount.")

    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    return date_text, category, description, amount


@app.route("/")
def index():
    records = get_records()
    query = request.args.get("q", "").strip().casefold()

    month = date.today().strftime("%Y-%m")
    budgets = ea.load_budgets()
    matching_budget = budgets.loc[budgets["Month"] == month, "Budget"]
    budget = float(matching_budget.iloc[-1]) if not matching_budget.empty else None

    month_spent = sum(
        float(e[4]) for e in records if str(e[1]).startswith(month)
    )

    filtered = [
        e for e in records
        if query in str(e[2]).casefold()
        or query in str(e[3]).casefold()
    ]

    return render_template_string(
        PAGE,
        expenses=filtered,
        total=sum(float(e[4]) for e in records),
        count=len(records),
        month=month,
        budget=budget,
        month_spent=month_spent,
        today=date.today().isoformat(),
        categories=CATEGORIES,
        query=query,
        error=request.args.get("error", ""),
    )


@app.route("/add", methods=["POST"])
def add_expense():
    try:
        values = validate_form(request.form)
        records = get_records()
        new_id = max((int(e[0]) for e in records), default=0) + 1
        db.replace_all_expenses(records + [(new_id, *values)])
    except (ValueError, TypeError) as exc:
        return redirect(url_for("index", error=str(exc)))

    return redirect(url_for("index"))


@app.route("/edit/<int:expense_id>", methods=["GET", "POST"])
def edit_expense(expense_id):
    records = get_records()
    expense = next((e for e in records if int(e[0]) == expense_id), None)

    if expense is None:
        return "Expense not found", 404

    error = ""
    if request.method == "POST":
        try:
            values = validate_form(request.form)
            updated = [
                (int(e[0]), *values) if int(e[0]) == expense_id else e
                for e in records
            ]
            db.replace_all_expenses(updated)
            return redirect(url_for("index"))
        except (ValueError, TypeError) as exc:
            error = str(exc)

    return render_template_string(
        EDIT_PAGE, expense=expense, categories=CATEGORIES, error=error
    )


@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete_expense(expense_id):
    records = get_records()

    if not any(int(e[0]) == expense_id for e in records):
        return "Expense not found", 404

    remaining = [e for e in records if int(e[0]) != expense_id]
    db.replace_all_expenses(remaining)
    return redirect(url_for("index"))


@app.route("/budget", methods=["POST"])
def set_budget():
    month = request.form.get("month", "").strip()

    try:
        datetime.strptime(month, "%Y-%m")
        amount = float(request.form.get("budget", ""))
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Budget must be greater than zero.")
    except ValueError:
        return redirect(url_for("index", error="Enter a valid month and positive budget."))

    budgets = ea.load_budgets()
    budgets = budgets[budgets["Month"] != month]
    budgets = __import__("pandas").concat(
        [budgets, __import__("pandas").DataFrame(
            [{"Month": month, "Budget": amount}]
        )],
        ignore_index=True,
    )
    ea.save_budgets(budgets)
    return redirect(url_for("index"))


if __name__ == "__main__":
    db.initialize_database()
    app.run(debug=True)
