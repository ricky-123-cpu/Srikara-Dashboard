import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hospital KPI Dashboard", page_icon="🏥", layout="wide")

st.title("🏥 Hospital KPI Performance Dashboard")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dMdKb7zD4XMGyfYmRoApmXwQZee_fOwUZQTcwZb_TKY/export?format=csv"

# The specific KPIs to display for each department, in display order.
KPI_MAP = {
    "OP": [
        "Total OP Footfall",
        "New Patients",
        "Follow-up Patients",
        "OP → Diagnostics Conversion %",
        "OP → Admission Conversion %",
    ],
    "IP": [
        "Admissions Today",
        "Discharges Today",
        "IP Revenue Today (₹)",
    ],
    "Billing": [
        "Total Revenue Billed (₹)",
    ],
    "ER": [
        "ER to IP Conversion %",
    ],
    "OT": [
        "Surgeries Done",
    ],
}

NUMERIC_COLS = ["Today", "MTD", "Target", "Last Month", "Projection"]


@st.cache_data(ttl=300)
def load_data():
    return pd.read_csv(SHEET_URL)


def clean_data(df):
    df = df.copy()
    df.columns = df.columns.str.strip()
    df["Department"] = df["Department"].astype(str).str.strip()
    df["Particulars"] = df["Particulars"].astype(str).str.strip()

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False),
                errors="coerce",
            )

    # Drop blank separator rows from the sheet
    df = df[df["Particulars"].notna() & (df["Particulars"] != "") & (df["Particulars"] != "nan")]
    return df


def format_value(particular, value):
    if pd.isna(value):
        return "N/A"
    if "₹" in particular:
        return f"₹{value:,.0f}"
    if "%" in particular:
        return f"{value:.1f}%"
    if value == int(value):
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def format_delta(particular, diff):
    if diff is None:
        return None
    if "₹" in particular:
        return f"₹{diff:,.0f} vs target"
    if "%" in particular:
        return f"{diff:+.1f} pts vs target"
    return f"{diff:+,.1f} vs target"


# ---- Load & clean data ----
try:
    raw_df = load_data()
    df = clean_data(raw_df)
except Exception as e:
    st.error(f"Could not load data from the spreadsheet: {e}")
    st.stop()

available_depts = [d for d in KPI_MAP if d in df["Department"].unique()]

if not available_depts:
    st.error("None of the configured departments were found in the spreadsheet. "
              "Check that the Department names in the sheet match: " + ", ".join(KPI_MAP.keys()))
    st.stop()

# ---- Sidebar ----
st.sidebar.header("Filters")
selected_dept = st.sidebar.selectbox("Select Department", available_depts)

# ---- Filter to the chosen department's defined KPI list, in order ----
kpi_list = KPI_MAP[selected_dept]
filtered_df = df[(df["Department"] == selected_dept) & (df["Particulars"].isin(kpi_list))]
present = [k for k in kpi_list if k in filtered_df["Particulars"].tolist()]
filtered_df = filtered_df.set_index("Particulars").loc[present].reset_index()

if filtered_df.empty:
    st.warning(f"No matching KPI rows found for {selected_dept} in the spreadsheet.")
    st.stop()

st.subheader(f"{selected_dept} Department — Key KPIs")

# ---- KPI metric cards (one per KPI, value = Today, delta = vs Target) ----
cols = st.columns(len(filtered_df))
for col, row in zip(cols, filtered_df.itertuples()):
    diff = row.Today - row.Target if pd.notna(row.Today) and pd.notna(row.Target) else None
    col.metric(
        row.Particulars,
        format_value(row.Particulars, row.Today),
        format_delta(row.Particulars, diff),
    )

# ---- Summary row ----
valid = filtered_df.dropna(subset=["Today", "Target"])
valid = valid[valid["Target"] != 0]
achievement = (valid["Today"] / valid["Target"]).mean() * 100 if not valid.empty else None

st.divider()
s1, s2 = st.columns(2)
s1.metric("KPIs Tracked", len(filtered_df))
s2.metric("Avg. Achievement vs Target", f"{achievement:.1f}%" if achievement is not None else "N/A")

# ---- Chart: Today vs Target ----
st.subheader("Today vs Target")
fig = px.bar(
    filtered_df,
    x="Particulars",
    y=["Today", "Target"],
    barmode="group",
    labels={"value": "Value", "variable": "Metric", "Particulars": ""},
)
fig.update_layout(xaxis_tickangle=-15, legend_title_text="")
st.plotly_chart(fig, use_container_width=True)

# ---- Detail table ----
st.subheader("KPI Detail")
display_cols = [c for c in ["Particulars", "Today", "MTD", "Target", "Last Month", "Projection"] if c in filtered_df.columns]
st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)
