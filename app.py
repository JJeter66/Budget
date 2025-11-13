import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px

# -----------------------------
# Google Sheets setup
# -----------------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

CREDENTIALS_FILE = "credentials.json"  # Your Google API JSON file
SPREADSHEET_NAME = "budget_export"
SHEET_NAME = "Sheet1"

# Connect to Google Sheets
@st.cache_resource(ttl=3600)
def connect_gsheets():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)
    return sheet

sheet = connect_gsheets()

# Load data
@st.cache_data(ttl=300)
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    # Standardize column names
    df.columns = df.columns.str.strip()
    if 'Transaction Id' in df.columns:
        df.rename(columns={'Transaction Id': 'TransactionID'}, inplace=True)
    return df

df = load_data()

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")
accounts = st.sidebar.multiselect("Account", df['Account'].unique(), default=df['Account'].unique())
categories = st.sidebar.multiselect("Category", df['Category'].unique(), default=df['Category'].unique())
months = st.sidebar.multiselect("Month", df['Date'].apply(lambda x: x[:7]).unique(), default=df['Date'].apply(lambda x: x[:7]).unique())

filtered_df = df[
    (df['Account'].isin(accounts)) &
    (df['Category'].isin(categories)) &
    (df['Date'].str[:7].isin(months))
]

st.title("Interactive Budget Dashboard")
st.markdown("View and edit your transactions, categories, and monthly budget goals.")

# -----------------------------
# Editable Category/Subcategory
# -----------------------------
st.subheader("Edit Categories / Subcategories")
edited_df = filtered_df.copy()

for idx, row in edited_df.iterrows():
    cols = st.columns([2,2])
    with cols[0]:
        edited_category = st.text_input(f"Category for {row['CompanyName']} ({row['TransactionID']})", row['Category'], key=f"cat_{row['TransactionID']}")
        edited_df.at[idx, 'Category'] = edited_category
    with cols[1]:
        edited_subcat = st.text_input(f"Subcategory for {row['CompanyName']} ({row['TransactionID']})", row['Subcategory'], key=f"sub_{row['TransactionID']}")
        edited_df.at[idx, 'Subcategory'] = edited_subcat

# -----------------------------
# Monthly Budget Goals
# -----------------------------
st.subheader("Monthly Budget Goals")
if 'BudgetGoal' not in df.columns:
    df['BudgetGoal'] = 0

months_unique = df['Date'].apply(lambda x: x[:7]).unique()
budget_goals = {}

for month in months_unique:
    goal = st.number_input(f"Budget Goal for {month}", value=int(df[df['Date'].str[:7]==month]['BudgetGoal'].max()), key=f"goal_{month}")
    budget_goals[month] = goal

# -----------------------------
# Update Google Sheet
# -----------------------------
def update_sheet(edited_df, budget_goals):
    # Update Category and Subcategory
    all_records = sheet.get_all_records()
    sheet_df = pd.DataFrame(all_records)
    sheet_df.columns = sheet_df.columns.str.strip()
    if 'Transaction Id' in sheet_df.columns:
        sheet_df.rename(columns={'Transaction Id': 'TransactionID'}, inplace=True)
    
    for idx, row in edited_df.iterrows():
        transaction_id = row['TransactionID']
        # Find row number in Google Sheet
        try:
            g_row = sheet_df.index[sheet_df['TransactionID'] == transaction_id][0] + 2  # +2 because Sheets index starts at 1 and header
            sheet.update_cell(g_row, sheet_df.columns.get_loc('Category') + 1, row['Category'])
            sheet.update_cell(g_row, sheet_df.columns.get_loc('Subcategory') + 1, row['Subcategory'])
        except:
            pass
    # Update budget goals (we can store in Notes column for simplicity)
    for month, goal in budget_goals.items():
        month_rows = sheet_df[sheet_df['Date'].str[:7] == month].index.tolist()
        for g_row in [r+2 for r in month_rows]:
            sheet.update_cell(g_row, sheet_df.columns.get_loc('Notes') + 1, f"BudgetGoal:{goal}")

st.button("Save Changes", on_click=update_sheet, args=(edited_df, budget_goals))

# -----------------------------
# Summary & Charts
# -----------------------------
st.subheader("Spending vs Budget")
summary = filtered_df.groupby(filtered_df['Date'].str[:7]).agg({'Amount':'sum'}).reset_index()
summary['BudgetGoal'] = summary['Date'].map(budget_goals)

fig = px.bar(summary, x='Date', y=['Amount','BudgetGoal'], barmode='group', title="Monthly Spending vs Budget")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Filtered Transactions")
st.dataframe(filtered_df)
