import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hospital KPI Dashboard", page_icon="🏥", layout="wide")

st.title("🏥 Hospital KPI Performance Dashboard")

# Google Sheet CSV Export URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dMdKb7zD4XMGyfYmRoApmXwQZee_fOwUZQTcwZb_TKY/export?format=csv"

@st.cache_data
def load_data():
    data = pd.read_csv(SHEET_URL)
    # Clean up column names right away (stripping whitespaces)
    data.columns = data.columns.str.strip()
    return data

try:
    df = load_data()

    # Dynamic Column Name Matching to prevent KeyErrors
    # This looks for columns that contain your keywords, ignoring case
    col_mapping = {}
    for standard_name, keyword in {
        "Particulars": "particular",
        "Department": "depart",
        "Target": "target",
        "MTD": "current"
    }.items():
        matched_col = [c for c in df.columns if keyword in c.lower()]
        if matched_col:
            col_mapping[matched_col[0]] = standard_name

    # Rename columns to standard names if found
    df = df.rename(columns=col_mapping)

    # Ensure required columns exist before proceeding
    required_cols = ["Particulars", "Department", "Target", "MTD"]
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"Error: Could not automatically map these columns from your sheet: {missing_cols}")
        st.info(f"Available columns in your sheet are: {list(df.columns)}")
        st.stop()

    # Clean and convert numeric columns
    numeric_cols = ["Target", "MTD"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace("%", "").str.replace(",", ""),
            errors="coerce"
        )

    # Drop rows where critical data is missing
    df = df.dropna(subset=["Particulars", "Department"])

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("Filters")

    # 1. Department Filter
    departments = sorted(df["Department"].dropna().unique())
    selected_dept = st.sidebar.multiselect("Select Department", departments, default=departments)
    
    # Filter data by department first
    filtered_df = df[df["Department"].isin(selected_dept)]

    # 2. KPI Filter (Changes dynamically based on selected departments)
    available_kpis = sorted(filtered_df["Particulars"].dropna().unique())
    selected_kpis = st.sidebar.multiselect("Select KPIs", available_kpis, default=available_kpis)
    
    # Final filtered dataframe based on both criteria
    filtered_df = filtered_df[filtered_df["Particulars"].isin(selected_kpis)]

    # --- DASHBOARD METRICS ---
    if not filtered_df.empty:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total KPIs Selected", len(filtered_df))
        c2.metric("Departments", filtered_df["Department"].nunique())
        
        avg_target = filtered_df["Target"].mean()
        c3.metric("Average Target", f"{avg_target:.2f}" if not pd.isna(avg_target) else "N/A")

        # Safely calculate achievement percentage
        valid_targets = filtered_df[filtered_df["Target"] > 0]
        if not valid_targets.empty:
            achievement = (valid_targets["MTD"] / valid_targets["Target"]).mean() * 100
            c4.metric("Achievement %", f"{achievement:.1f}%")
        else:
            c4.metric("Achievement %", "N/A")

        # --- VISUALIZATIONS ---
        st.subheader("Current vs Target")
        fig = px.bar(
            filtered_df, 
            x="Particulars", 
            y=["Current Month", "Target"], 
            barmode="group",
            labels={"value": "Values", "variable": "Metric"}
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("KPI Data Table")
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.warning("No data available for the selected filters. Please select at least one Department and KPI.")

except Exception as e:
    st.error("An error occurred while loading or processing the data.")
    st.exception(e)
