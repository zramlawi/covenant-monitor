# Covenant Monitor

A Streamlit application that turns standardized monthly or quarterly financial CSVs into a private-equity-style covenant, liquidity, and investment-committee risk report.

The included Summit Facility Services cases are fictional and illustrative. They do not represent an actual company or investment, and they are not financial, investment, or lending advice.

## What it does

- Validates uploaded monthly or quarterly financial data
- Calculates trailing EBITDA, net debt, net leverage, interest coverage, and receivable days
- Models base, downside, and recovery scenarios
- Forecasts the next six months for monthly uploads or four quarters for quarterly uploads
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

## Required CSV formats

Upload one CSV frequency at a time. Use exactly one date column:

- `month` for monthly financials
- `period_end` for quarterly financials

### Monthly CSV

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

### Quarterly CSV

```text
period_end,revenue,ebitda,cash,total_debt,interest_expense,accounts_receivable
```

| Column | Description |
| --- | --- |
| `period_end` | Quarter-end date, such as `2026-03-31` |
| `revenue` | Quarterly revenue in dollars |
| `ebitda` | Quarterly EBITDA in dollars |
| `cash` | Quarter-end cash balance in dollars |
| `total_debt` | Quarter-end gross debt in dollars |
| `interest_expense` | Quarterly cash interest expense in dollars |
| `accounts_receivable` | Quarter-end accounts receivable in dollars |

At least three quarterly observations are required. A standardized quarterly sample is available at `sample_data/summit_facility_services_quarterly.csv`.

Do not substitute `net_debt` for the separate `cash` and `total_debt` columns in real uploads. The app uses the direct inputs to calculate liquidity, net debt, and leverage.

## Calculation approach

### Monthly uploads

- **TTM EBITDA:** Rolling sum of monthly EBITDA, using available periods until 12 months exist.
- **TTM interest:** Rolling sum of monthly interest expense, using available periods until 12 months exist.
- **A/R days:** Accounts receivable divided by monthly revenue, multiplied by 30.
- **Forecast:** Six monthly periods, with annual revenue growth converted to a monthly rate.

### Quarterly uploads

- **LTM EBITDA:** Rolling sum of quarterly EBITDA, using available periods until four quarters exist.
- **LTM interest:** Rolling sum of quarterly interest expense, using available periods until four quarters exist.
- **A/R days:** Accounts receivable divided by quarterly revenue, multiplied by 90.
- **Forecast:** Four quarter-end periods, with annual revenue growth converted to a quarterly rate.

### Common calculations

- **Net debt:** Gross debt less cash, floored at zero.
- **Net leverage:** Net debt divided by trailing EBITDA.
- **Interest coverage:** Trailing EBITDA divided by trailing interest expense.

The forecast begins with recent average revenue, EBITDA margin, and interest expense. It applies the scenario assumptions entered in the sidebar. The downside case can increase A/R days to show the effect of slower collections on cash and leverage.

## Demo case

Summit Facility Services is a fictional lower-middle-market commercial facilities-maintenance provider. Its illustrative debt profile starts with a 4.75x maximum net-leverage covenant and a 2.00x minimum interest-coverage covenant.

The quarterly sample was standardized from a source file that originally contained `net_debt`, `current_assets`, and `inventory`. For **demo purposes only**, its values were derived as:

```text
cash = current_assets − accounts_receivable − inventory
total_debt = net_debt + cash
```

These illustrative derivations are not suitable for real borrower reporting. For production use, upload direct cash and gross-debt balances from the borrower’s financial statements or reporting package.

## Limitations

This starter app uses simplified forecasting and covenant definitions. Real credit agreements may include EBITDA add-backs, debt baskets, restricted payments, seasonal testing, cure rights, and more complex liquidity definitions. Validate all calculations against the governing credit documents before relying on them for a real financing decision.
