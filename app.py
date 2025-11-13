import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
# Connect to Google Sheets
# -------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

@st.cache_data(show_spinner=False)
def connect_gsheets():
    # Load Service Account JSON from Streamlit Secrets
    creds_dict = dict(st.secrets["google"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    gc = gspread.authorize(creds)
    
    # Open your Google Sheet
    sheet = gc.open("budget_export").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Ensure numeric types
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    return df

# Load data
df = connect_gsheets()

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("📊 Budget Dashboard")

# Sidebar filters
st.sidebar.header("Filters")
accounts = df["Account"].dropna().unique().tolist()
selected_accounts = st.sidebar.multiselect("Select Accounts", accounts, default=accounts)

categories = df["Category"].dropna().unique().tolist()
selected_categories = st.sidebar.multiselect("Select Categories", categories, default=categories)

# Filter data
filtered_df = df[
    (df["Account"].isin(selected_accounts)) &
    (df["Category"].isin(selected_categories))
]

# Display main table
st.subheader("Transactions")
st.dataframe(filtered_df, use_container_width=True)

# Summary by Category
st.subheader("Category Totals")
summary = filtered_df.groupby(["Category"])["Amount"].sum().reset_index()
summary.rename(columns={"Amount": "Total Amount"}, inplace=True)
st.dataframe(summary, use_container_width=True)

# Monthly totals
st.subheader("Monthly Totals")
monthly = filtered_df.groupby(filtered_df["Date"].dt.to_period("M"))["Amount"].sum().reset_index()
monthly["Date"] = monthly["Date"].dt.to_timestamp()
monthly.rename(columns={"Amount": "Total Amount"}, inplace=True)
st.dataframe(monthly, use_container_width=True)
