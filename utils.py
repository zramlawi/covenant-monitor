import io

import pandas as pd


REQUIRED_COLUMNS = [
    "month",
    "revenue",
    "ebitda",
    "cash",
    "total_debt",
    "interest_expense",
    "accounts_receivable",
]


def csv_template_bytes():
    template = pd.DataFrame(
        [
            {
                "month": "2026-01-31",
                "revenue": 0,
                "ebitda": 0,
                "cash": 0,
                "total_debt": 0,
                "interest_expense": 0,
                "accounts_receivable": 0,
            }
        ],
        columns=REQUIRED_COLUMNS,
    )
    buffer = io.StringIO()
    template.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def data_diagnostics(raw_data, cleaned_data):
    warnings = []

    if len(cleaned_data) < 12:
        warnings.append(
            f"Only {len(cleaned_data)} monthly observations were provided. "
            "TTM metrics use available history until 12 months exist."
        )

    if raw_data["month"].duplicated().any():
        duplicates = int(raw_data["month"].duplicated().sum())
        warnings.append(
            f"{duplicates} duplicate month(s) were found. The app keeps the first record for each month."
        )

    month_dates = pd.to_datetime(raw_data["month"], errors="coerce")
    non_month_end = month_dates.notna() & ~month_dates.dt.is_month_end
    if non_month_end.any():
        warnings.append(
            "Some dates are not month-end dates. Use month-end reporting dates for consistent monthly analysis."
        )

    if (cleaned_data["ebitda"] < 0).any():
        warnings.append(
            "Negative EBITDA was detected. Leverage and interest-coverage ratios may be less meaningful."
        )

    if (cleaned_data["interest_expense"] <= 0).any():
        warnings.append(
            "Zero or negative interest expense was detected. Interest-coverage calculations may be unavailable."
        )

    return warnings
