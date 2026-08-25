import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Covenant Monitor", page_icon="📊", layout="wide")

REQUIRED_COLUMNS = [
    "month",
    "revenue",
    "ebitda",
    "cash",
    "total_debt",
    "interest_expense",
    "accounts_receivable",
]


def format_money(value):
    if pd.isna(value):
        return "—"
    return f"${value / 1_000_000:,.2f}M"


def format_multiple(value):
    if pd.isna(value) or np.isinf(value):
        return "—"
    return f"{value:.2f}x"


def load_data(uploaded_file):
    data = pd.read_csv(uploaded_file)
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        st.error("Missing required columns: " + ", ".join(missing))
        return None

    data = data.copy()
    data["month"] = pd.to_datetime(data["month"], errors="coerce")
    for column in REQUIRED_COLUMNS[1:]:
        data[column] = pd.to_numeric(data[column], errors="coerce")

    if data[REQUIRED_COLUMNS].isna().any().any():
        st.error("The CSV has invalid or blank values in required fields.")
        return None

    data = data.sort_values("month").drop_duplicates("month").reset_index(drop=True)
    if len(data) < 3:
        st.error("Upload at least three monthly observations.")
        return None
            return data.rename(columns={"month": "period"}).rename(columns={"month": "period"})


def calculate_metrics(data):
    result = data.copy()
    result["ttm_ebitda"] = result["ebitda"].rolling(12, min_periods=3).sum()
    result["net_debt"] = (result["total_debt"] - result["cash"]).clip(lower=0)
    result["net_leverage"] = result["net_debt"] / result["ttm_ebitda"].replace(0, np.nan)
    result["ttm_interest"] = result["interest_expense"].rolling(12, min_periods=3).sum()
    result["interest_coverage"] = result["ttm_ebitda"] / result["ttm_interest"].replace(0, np.nan)
    result["ar_days"] = result["accounts_receivable"] / result["revenue"].replace(0, np.nan) * 30
    return result


def forecast(data, revenue_growth, margin_change_bps, ar_days_change, months=6):
    latest = data.iloc[-1]
    recent = data.tail(min(3, len(data)))
    revenue = float(recent["revenue"].mean())
    margin = float(recent["ebitda"].sum() / recent["revenue"].sum())
    ar_days = float(recent["ar_days"].mean())
    cash = float(latest["cash"])
    debt = float(latest["total_debt"])
    interest = float(recent["interest_expense"].mean())
    history_ebitda = list(data["ebitda"].tail(11))
    rows = []

    for step in range(1, months + 1):
        revenue *= 1 + revenue_growth / 12
        scenario_margin = max(0.01, margin + margin_change_bps / 10_000)
        ebitda = revenue * scenario_margin
        target_ar = revenue * (ar_days + ar_days_change) / 30
        prior_ar = float(latest["accounts_receivable"]) if step == 1 else rows[-1]["accounts_receivable"]
        working_capital_use = target_ar - prior_ar
        cash = cash + ebitda - interest - working_capital_use
        net_debt = max(0, debt - cash)
        ttm_ebitda = sum((history_ebitda + [row["ebitda"] for row in rows] + [ebitda])[-12:])
        ttm_interest = interest * min(12, len(data) + step)
        rows.append({
            "period": latest["period"] + pd.offsets.MonthEnd(step),
            "revenue": revenue,
            "ebitda": ebitda,
            "cash": cash,
            "total_debt": debt,
            "interest_expense": interest,
            "accounts_receivable": target_ar,
            "ttm_ebitda": ttm_ebitda,
            "net_debt": net_debt,
            "net_leverage": net_debt / ttm_ebitda if ttm_ebitda else np.nan,
            "interest_coverage": ttm_ebitda / ttm_interest if ttm_interest else np.nan,
            "ar_days": ar_days + ar_days_change,
        })
    return pd.DataFrame(rows)


def breach_text(frame, leverage_limit, coverage_minimum):
    breaches = frame[(frame["net_leverage"] > leverage_limit) | (frame["interest_coverage"] < coverage_minimum)]
    if breaches.empty:
        return "No projected covenant breach in the forecast period."

    first = breaches.iloc[0]
    reasons = []
    if first["net_leverage"] > leverage_limit:
        reasons.append(f"net leverage of {first['net_leverage']:.2f}x exceeds the {leverage_limit:.2f}x limit")
    if first["interest_coverage"] < coverage_minimum:
        reasons.append(f"interest coverage of {first['interest_coverage']:.2f}x is below the {coverage_minimum:.2f}x minimum")
    return f"Projected breach in {first['month'].strftime('%B %Y')}: " + "; ".join(reasons) + "."


st.title("Covenant Monitor")
st.caption("Upload standardized monthly financials to assess leverage, liquidity, and debt-covenant risk.")

with st.sidebar:
    st.header("Covenant assumptions")
    leverage_limit = st.number_input("Maximum net leverage (x)", min_value=1.0, max_value=15.0, value=4.75, step=0.25)
    coverage_minimum = st.number_input("Minimum interest coverage (x)", min_value=0.5, max_value=10.0, value=2.00, step=0.25)

    st.header("Scenario assumptions")
    base_growth = st.number_input("Base annual revenue growth (%)", value=6.0, step=1.0) / 100
    base_margin = st.number_input("Base EBITDA margin change (bps)", value=50, step=25)
    downside_growth = st.number_input("Downside annual revenue growth (%)", value=0.0, step=1.0) / 100
    downside_margin = st.number_input("Downside EBITDA margin change (bps)", value=-150, step=25)
    recovery_growth = st.number_input("Recovery annual revenue growth (%)", value=10.0, step=1.0) / 100
    recovery_margin = st.number_input("Recovery EBITDA margin change (bps)", value=150, step=25)
    ar_days_change = st.number_input("Downside A/R days increase", value=15.0, step=1.0)

uploaded_file = st.file_uploader("Upload monthly financials CSV", type="csv")
if uploaded_file is None:
    st.info("Use the included sample_data/summit_facility_services.csv file to explore the app.")
    st.stop()

data = load_data(uploaded_file)
if data is None:
    st.stop()

metrics = calculate_metrics(data)
latest = metrics.iloc[-1]
base = forecast(metrics, base_growth, base_margin, 0)
downside = forecast(metrics, downside_growth, downside_margin, ar_days_change)
recovery = forecast(metrics, recovery_growth, recovery_margin, 0)

st.subheader("Current position")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Revenue", format_money(latest["revenue"]))
col2.metric("TTM EBITDA", format_money(latest["ttm_ebitda"]))
col3.metric("Net leverage", format_multiple(latest["net_leverage"]), f"Headroom: {leverage_limit - latest['net_leverage']:.2f}x")
col4.metric("Interest coverage", format_multiple(latest["interest_coverage"]), f"Headroom: {latest['interest_coverage'] - coverage_minimum:.2f}x")

st.subheader("Scenario outlook")
scenario_frames = {"Base": base, "Downside": downside, "Recovery": recovery}

left_chart, right_chart = st.columns(2)
with left_chart:
    figure = go.Figure()
    for name, frame in scenario_frames.items():
        figure.add_trace(go.Scatter(x=frame["period"], y=frame["net_leverage"], mode="lines+markers", name=name))
    figure.add_hline(y=leverage_limit, line_dash="dash", line_color="red", annotation_text="Leverage covenant")
    figure.update_layout(title="Net leverage forecast", yaxis_title="x", xaxis_title="Month")
    st.plotly_chart(figure, use_container_width=True)

with right_chart:
    figure = go.Figure()
    for name, frame in scenario_frames.items():
        figure.add_trace(go.Scatter(x=frame["period"], y=frame["interest_coverage"], mode="lines+markers", name=name))
    figure.add_hline(y=coverage_minimum, line_dash="dash", line_color="red", annotation_text="Coverage covenant")
    figure.update_layout(title="Interest coverage forecast", yaxis_title="x", xaxis_title="Month")
    st.plotly_chart(figure, use_container_width=True)

st.subheader("Investment committee risk report")
base_end = base.iloc[-1]
downside_end = downside.iloc[-1]
recovery_end = recovery.iloc[-1]
current_status = (
    "within covenant"
    if latest["net_leverage"] <= leverage_limit and latest["interest_coverage"] >= coverage_minimum
    else "currently outside covenant"
)
report = f"""
**Current status:** The company is {current_status}. Current net leverage is {latest['net_leverage']:.2f}x versus a {leverage_limit:.2f}x maximum, and interest coverage is {latest['interest_coverage']:.2f}x versus a {coverage_minimum:.2f}x minimum.

**Base case:** {breach_text(base, leverage_limit, coverage_minimum)} By the end of the forecast, net leverage is {base_end['net_leverage']:.2f}x and cash is {format_money(base_end['cash'])}.

**Downside case:** {breach_text(downside, leverage_limit, coverage_minimum)} By the end of the forecast, net leverage is {downside_end['net_leverage']:.2f}x and cash is {format_money(downside_end['cash'])}.

**Recovery case:** {breach_text(recovery, leverage_limit, coverage_minimum)} By the end of the forecast, net leverage is {recovery_end['net_leverage']:.2f}x and cash is {format_money(recovery_end['cash'])}.

**Recommended focus:** Monitor monthly EBITDA delivery, cash collections, and covenant headroom. If the downside case approaches breach, prioritize pricing, labor utilization, receivables collection, and debt-reduction actions.
"""
st.markdown(report)

st.download_button(
    "Download IC risk report",
    report.replace("**", ""),
    file_name="ic_risk_report.txt",
    mime="text/plain",
)

with st.expander("Required CSV schema"):
    st.code("month,revenue,ebitda,cash,total_debt,interest_expense,accounts_receivable")
    st.dataframe(data, use_container_width=True)
