# Expense Analyzer
### A Python-Based Personal Expense Tracking and Data Analysis System

**Course:** ICS 214 – IT Workshop III

## 1. Project Overview

Expense Analyzer is a Python-based application for recording, managing, and analyzing personal expenses. It provides a terminal-based interface, a local Flask web dashboard, statistical analysis, visualizations, and summary report exports.

Expense records are stored in an SQLite database. Pandas and NumPy support data processing and statistical calculations, while Matplotlib generates spending charts.

## 2. Problem Statement

Recording expenses manually makes it difficult to monitor total spending, understand spending patterns, compare expenses across categories, and track monthly budgets. This project provides a simple computerized system to organize expense records and summarize spending information.

## 3. Objectives

- Record, view, search, edit, and delete expenses.
- Store expense records persistently using SQLite.
- Set and check monthly budgets.
- Calculate useful expense statistics.
- Analyze spending by category, month, and day.
- Visualize spending patterns using charts.
- Export summaries as CSV reports.
- Provide both terminal and browser-based interfaces.

## 4. Features

- **Expense management:** Create, view, search, update, and delete expense records.
- **Data validation:** Validate expense inputs and reject invalid database records.
- **Statistical analysis:** Calculate total, average, median, minimum, maximum, and standard deviation.
- **Spending summaries:** Group expenses by category, month, and day.
- **Budget tracking:** Store monthly budgets and check budget status.
- **Data visualization:** Generate category expense, category distribution, monthly trend, and daily trend charts.
- **Report generation:** Export category, monthly, and budget summaries as CSV files.
- **Web dashboard:** Manage expenses and budgets using a local Flask application.
- **Notebook analysis:** Explore expense data using a Jupyter Notebook.

## 5. Technologies Used

- Python 3.13
- NumPy
- Pandas
- Matplotlib
- Seaborn
- Flask
- SQLite
- Jupyter Notebook
- CSV for budget storage and exported reports

## 6. Prerequisites

For a fresh setup, install Python 3.13 and ensure the Python launcher (`py`) is available.

The project uses a virtual environment to keep its dependencies separate from the system Python installation.

## 7. Environment Setup

Open PowerShell in the project directory:

```powershell
Set-Location "C:\Users\santh\OneDrive\Desktop\ExpenseAnalyzer"
```

Create a virtual environment if one does not already exist:

```powershell
py -3.13 -m venv .venv
```

Install the required packages in the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install numpy pandas matplotlib seaborn flask notebook
```

Verify the Python version and installed libraries:

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip list
```

If the virtual environment already exists and works, do not recreate it unnecessarily.

## 8. Running the Terminal Application

Run the following command from the project directory:

```powershell
.\.venv\Scripts\python.exe .\expense_analyzer.py
```

Use the displayed menu to manage expenses, view analysis, manage monthly budgets, generate charts, export reports, or exit the application.

## 9. Running the Flask Web Application

Start the local web application:

```powershell
.\.venv\Scripts\python.exe .\main.py
```

Open the following address in a browser:

http://127.0.0.1:5000/

The web interface provides a dashboard and routes for adding, searching, editing, and deleting expenses, as well as setting a monthly budget.

Stop the local server with `Ctrl+C` in the terminal.

The application uses Flask's development server and debug mode. It is intended for local project demonstration, not production deployment.

## 10. Running the Jupyter Notebook

Launch Jupyter Notebook using the project environment:

```powershell
.\.venv\Scripts\python.exe -m notebook
```

Open `Expense_Analyzer.ipynb` and run its cells in order.

The notebook demonstrates data loading, analysis using NumPy and Pandas, visualization, and interpretation of results.

## 11. Database and Data Files

### SQLite database

- `expenses.db` — persistent SQLite database containing expense records.
- `expense_database.py` — database initialization, connections, record retrieval, validation, and transactional replacement logic.

The expense table uses these fields:

| Field | Purpose |
|---|---|
| `ID` | Unique expense identifier |
| `Date` | Expense date |
| `Category` | Expense category |
| `Description` | Short description |
| `Amount` | Positive expense amount |

The database layer validates records and uses transactions to protect against incomplete replacements.

### CSV files

- `expenses.csv` — original expense CSV and migration source.
- `budget.csv` — monthly budget data, using `YYYY-MM` month identifiers.
- `reports/` — generated charts and summary reports.

SQLite is the primary persistent store for application expense operations. The budget functionality uses CSV storage.

Do not delete or replace the existing database or CSV files when launching the application.

## 12. Statistical Analysis

The project calculates:

- **Total:** Sum of all expense amounts.
- **Mean:** Total expense amount divided by the number of transactions.
- **Median:** Middle expense amount after sorting the values.
- **Maximum and minimum:** Highest and lowest individual expense amounts.
- **Standard deviation:** A measure of variation in expense amounts.
- **Category-wise totals:** Spending grouped by expense category.
- **Monthly totals:** Spending grouped by month.
- **Daily totals:** Spending grouped by date.

NumPy and Pandas support the calculations and grouped summaries.

## 13. Charts and Exported Reports

The application generates the following chart files in `reports/`:

- `category_expenses.png`
- `category_distribution.png`
- `monthly_trend.png`
- `daily_trend.png`

The summary export functions generate these CSV reports:

- `category_summary.csv`
- `monthly_summary.csv`
- `budget_summary.csv`

The report files are generated by the application. They may not exist until the corresponding functions have been run.

## 14. Project Structure

```text
ExpenseAnalyzer/
├── .venv/                       # Python virtual environment
├── data/                        # Supporting data directory
├── notebooks/                   # Supporting notebook directory
├── reports/                     # Generated charts and reports
├── expenses.csv                 # Original expense CSV
├── budget.csv                   # Monthly budget CSV
├── expenses.db                  # SQLite database
├── Expense_Analyzer.ipynb       # Analysis notebook
├── expense_analyzer.py          # Terminal application and analysis
├── expense_database.py          # SQLite database layer
├── main.py                      # Flask web application
├── expense_analyzer.py.backup   # Preserved backup
├── expense_database.py.backup   # Preserved backup
└── README.md                    # Project documentation
```

The `.venv`, cache directories, and backup files are local development artifacts rather than required runtime features. Preserve the backups in the working project folder.

## 15. Testing and Verification

The following checks have been reported as successfully completed during development:

- Python source compilation.
- SQLite insertion and retrieval.
- Rejection of duplicate IDs and invalid expense records.
- Transaction rollback and preservation of existing records after failed replacement.
- Empty-database behavior.
- Monthly budget save and reload.
- Generation of all four charts.
- Export of the three summary reports.
- Statistical summary of the original expense records.
- Notebook JSON integrity and fresh-kernel execution.
- Flask dashboard loading.
- Flask expense creation, search, editing, and deletion using temporary test data.
- Flask monthly budget save and reload using temporary test files.
- Manual loading of the dashboard with the original expense records.

These results describe checks performed during development; they are not a guarantee that every environment will behave identically.

### Current dataset verification

Independent read-only verification confirmed that the CSV dataset and
SQLite database contain the same 10 unique transactions.

| Metric | Verified result |
|---|---:|
| Transaction count | 10 |
| Unique transaction IDs | 10 |
| Total expenditure | ?2,649.00 |
| Average transaction amount | ?264.90 |
| Expense categories | 7 |
| Date range | 20 March 2026 ? 18 October 2026 |

Category totals include Food (?630.00) and Shopping (?550.00).
Monthly totals are March (?400.00), August (?450.00),
September (?1,079.00), and October 2026 (?720.00).

The CSV and SQLite records were verified to match exactly.
These figures describe the dataset at the time of verification.

## 16. Limitations

- The web application is designed for local use.
- The project focuses on individual expense tracking rather than multi-user financial management.
- Budget information is stored separately from expense records.
- The quality of analysis depends on the completeness and accuracy of entered data.

## 17. Conclusion

Expense Analyzer demonstrates how Python can be used to build a practical expense management and data analysis application. SQLite provides persistent expense storage, Pandas and NumPy support analysis, Matplotlib visualizes spending patterns, and Flask provides a browser-based interface.

The project combines data management, statistical analysis, visualization, input validation, and a simple web interface in a college-level application.

## 18. Future Scope

Possible future improvements include downloadable PDF reports, additional date-range filters, and interactive visualizations.

These are potential extensions and are not claimed as currently implemented features.
