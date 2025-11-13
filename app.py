import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import datetime

# -------------------------
# File paths (relative to app.py)
# -------------------------
EXCEL_FILE = "budget_export.xlsx"
CATEGORY_FILE = "categories.xlsx"

# -------------------------
# Load Excel data
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(EXCEL_FILE)
    # Ensure Description exists
    if 'Description' not in df.columns:
        df['Description'] = "No Description"
    else:
        df['Description'] = df['Description'].fillna('No Description')
    return df

# -------------------------
# Load categories
# -------------------------
@st.cache_data
def load_categories():
    if CATEGORY_FILE:
        categories = pd.read_excel(CATEGORY_FILE, usecols=[0,1], header=None)
        categories.columns = ['Keyword', 'Category']
        categories['Keyword'] = categories['Keyword'].astype(str).str.strip().str.lower()
        categories['Category'] = categories['Category'].astype(str).str.strip()
        return categories
    else:
        return pd.DataFrame(columns=['Keyword', 'Category'])

# -------------------------
# Assign category
# -------------------------
def assign_category(description, categories_df):
    keywords = categories_df['Keyword'].tolist()
    desc = str(description).strip().lower()
    for i, keyword in enumerate(keywords):
        if keyword in desc:
            return categories_df.loc[i, 'Category']
    if keywords:
        result = process.extractOne(desc, keywords, scorer=fuzz.partial_ratio)
        if result:
            match_keyword, score, idx = result
            if score >= 75:
                return categories_df.loc[idx, 'Category']
    return "Uncategorized"

# -------------------------
# Main Streamlit app
# -------------------------
st.title("📊 Interactive Budget Dashboard")

# Load data
df = load_data()
categories_df = load_categories()

# Apply categories
df['Category'] = df['Description'].apply(lambda x: assign_category(x, categories_df))

# Sidebar filter by month
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
df['Month'] = df['Date'].dt.to_period('M')
months = df['Month'].dropna().unique()
selected_month = st.sidebar.selectbox("Select Month", sorted(months))

filtered_df = df[df['Month'] == selected_month]

# Show budget table
st.subheader(f"Transactions for {selected_month}")
st.dataframe(filtered_df)

# Total spent for the month
st.write(f"**Total Spent:** ${filtered_df['Amount'].sum():,.2f}")

# Show breakdown by category
category_totals = filtered_df.groupby('Category')['Amount'].sum().reset_index()
st.subheader("Spending by Category")
st.dataframe(category_totals)
