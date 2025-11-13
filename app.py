# app.py
import streamlit as st
import pandas as pd
import os

# -------------------------
# Paths
# -------------------------
BASE_FOLDER = os.path.join(os.getcwd(), "Bank Data Export")  # Streamlit Cloud: use relative path
EXCEL_FILE = os.path.join(BASE_FOLDER, "budget_export.xlsx")
CATEGORY_FILE = os.path.join(BASE_FOLDER, "categories.xlsx")

# -------------------------
# Page setup
# -------------------------
st.set_page_config(page_title="Budget Dashboard", layout="wide")
st.title("💰 Budget Dashboard")

# -------------------------
# Load Data
# -------------------------
@st.cache_data
def load_data():
    # Read Excel file
    df = pd.read_excel(EXCEL_FILE)
    df.columns = [col.strip() for col in df.columns]  # clean column names
    return df

df = load_data()

# -------------------------
# Load Categories
# -------------------------
@st.cache_data
def load_categories():
    if os.path.exists(CATEGORY_FILE):
        cat_df = pd.read_excel(CATEGORY_FILE, usecols=[0, 1], header=None)
        cat_df.columns = ['Keyword', 'Category']
        cat_df['Keyword'] = cat_df['Keyword'].astype(str).str.strip().str.lower()
        cat_df['Category'] = cat_df['Category'].astype(str).str.strip()
        return cat_df
    else:
        return pd.DataFrame(columns=['Keyword', 'Category'])

categories = load_categories()
keywords = categories['Keyword'].tolist()

# -------------------------
# Categorization
# -------------------------
def assign_category(description):
    if pd.isna(description):
        return "Uncategorized"
    desc = str(description).strip().lower()
    for i, keyword in enumerate(keywords):
        if keyword in desc:
            return categories.loc[i, 'Category']
    return "Uncategorized"

if 'Category' not in df.columns:
    df['Category'] = df['Description'].apply(assign_category)

# -------------------------
# Sidebar Filters
# -------------------------
st.sidebar.header("Filters")
accounts = df['Account'].unique().tolist()
selected_accounts = st.sidebar.multiselect("Account", accounts, default=accounts)

categories_list = df['Category'].unique().tolist()
selected_categories = st.sidebar.multiselect("Category", categories_list, default=categories_list)

# Optional: Month filter
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Month'] = df['Date'].dt.to_period('M')
months = df['Month'].dropna().astype(str).unique().tolist()
selected_month = st.sidebar.selectbox("Month", ["All"] + months, index=0)

# -------------------------
# Filter Data
# -------------------------
filtered = df[df['Account'].isin(selected_accounts) & df['Category'].isin(selected_categories)]
if selected_month != "All":
    filtered = filtered[filtered['Month'].astype(str) == selected_month]

# -------------------------
# Display
# -------------------------
st.subheader(f"Transactions ({len(filtered)})")
st.dataframe(filtered)

# -------------------------
# Monthly Budget Goals
# -------------------------
st.sidebar.header("Monthly Budget Goals")
budget_goals = {}
for month in months:
    goal = st.sidebar.number_input(f"Budget for {month}", min_value=0, value=0)
    budget_goals[month] = goal

# Optional: show totals vs goal
if selected_month != "All":
    total_amount = filtered['Amount'].sum()
    goal = budget_goals[selected_month]
    st.metric(label=f"Month: {selected_month}", value=f"${total_amount:,.2f}", delta=f"${total_amount - goal:,.2f}")

# -------------------------
# Notes
# -------------------------
st.sidebar.markdown("You can update categories in `categories.xlsx` in your repo.")
st.sidebar.markdown("Transactions come from `budget_export.xlsx` in your repo.")
