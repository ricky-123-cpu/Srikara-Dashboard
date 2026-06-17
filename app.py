import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Hospital KPI Dashboard", page_icon="🏥", layout="wide")

st.title("🏥 Hospital KPI Performance Dashboard")

SHEET_URL = "https://docs.google.com/spreadsheets/d/1dMdKb7zD4XMGyfYmRoApmXwQZee_fOwUZQTcwZb_TKY/export?format=csv"

@st.cache_data
def load_data():
    return pd.read_csv(SHEET_URL)

df = load_data()
df.columns = df.columns.str.strip()

numeric_cols = df.columns[3:]
for col in numeric_cols:
    df[col] = pd.to_numeric(
        df[col].astype(str).str.replace("%", "").str.replace(",", ""),
        errors="coerce"
    )

df = df[df["Particulars"].notna()]

st.sidebar.header("Filters")
departments = df["Department"].unique()
selected_dept = st.sidebar.multiselect("Select Department", departments, default=departments)
filtered_df = df[df["Department"].isin(selected_dept)]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total KPIs", len(filtered_df))
c2.metric("Departments", filtered_df["Department"].nunique())
c3.metric("Average Target", round(filtered_df["Target"].mean(), 2))

achievement = ((filtered_df["Current Month"] / filtered_df["Target"]).mean()) * 100
c4.metric("Achievement %", f"{achievement:.1f}%")

st.subheader("Current vs Target")
fig = px.bar(filtered_df, x="Particulars", y=["Current Month", "Target"], barmode="group")
st.plotly_chart(fig, use_container_width=True)

st.subheader("KPI Data")
st.dataframe(filtered_df, use_container_width=True)
