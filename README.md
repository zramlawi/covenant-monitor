# Covenant Monitor

A Streamlit application that turns a standardized monthly-financial CSV into a private-equity-style covenant, liquidity, and investment-committee risk report.

The included Summit Facility Services case is fictional and illustrative. It does not represent an actual company or investment, and it is not financial, investment, or lending advice.

## What it does

- Validates uploaded monthly financial data
- Calculates trailing-twelve-month EBITDA, net debt, net leverage, interest coverage, and receivable days
- Models base, downside, and recovery scenarios over the next six months
- Flags projected covenant breaches
- Produces an IC-ready plain-English risk summary
- Lets the user download the report as a text file

## Run locally

```bash
git clone https://github.com/zramlawi/covenant-monitor.git
cd covenant-monitor
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Required CSV format

Upload a CSV with one row per month and these exact columns:

```text
month,revenue,ebitda,cash,total_debt,interest_expense,accounts_receivable
```

| Column | Description |
| --- | --- |
| `month` | Month-end date, such as `2026-01-31` |
| `revenue` | Monthly revenue in dollars |
| `ebitda` | Monthly EBITDA in dollars |
| `cash` | Month-end cash balance in dollars |
| `total_debt` | Month-end gross debt in dollars |
| `interest_expense` | Monthly cash interest expense in dollars |
| `accounts_receivable` | Month-end accounts receivable in dollars |

At least three monthly observations are required. A sample file is available at `sample_data/summit_facility_services.csv`.

## Calculation approach

- **TTM EBITDA:** Rolling sum of monthly EBITDA, using available periods until 12 months exist.
- **Net debt:** Gross debt less cash, floored at zero.
- **Net leverage:** Net debt divided by TTM EBITDA.
- **Interest coverage:** TTM EBITDA divided by TTM interest expense.
- **A/R days:** Accounts receivable divided by monthly revenue, multiplied by 30.

The forecast begins with recent average revenue, EBITDA margin, and interest expense. It applies the scenario assumptions entered in the sidebar. The downside case can increase A/R days to show the effect of slower collections on cash and leverage.

## Demo case

Summit Facility Services is a fictional lower-middle-market commercial facilities-maintenance provider. Its illustrative debt profile starts with a 4.75x maximum net-leverage covenant and a 2.00x minimum interest-coverage covenant. Use the sample data to test the application, then upload your own standardized CSV.

## Limitations

This starter app uses simplified forecasting and covenant definitions. Real credit agreements may include EBITDA add-backs, debt baskets, restricted payments, seasonal testing, cure rights, and more complex liquidity definitions. Validate all calculations against the governing credit documents before relying on them for a real financing decision.
