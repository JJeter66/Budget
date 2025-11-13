import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
import datetime

# -------------------------
# File paths
# -------------------------
EXCEL_FILE = "budget_export.xlsx"
CATEGORY_FILE = "categories.xlsx"

# -------------------------
# Load Excel data
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_excel(EXCEL_FILE)
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
# Main app
# -------------------------
st.title("📊 Interactive Budget Dashboard")

# Load data
df = load_data()
categories_df = load_categories()

# Apply categories
df['Category'] = df['Description'].apply(lambda x: assign_category(x, categories_df))

# Convert Date column
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

# -------------------------
# Compute week ranges (Sunday → Saturday)
# -------------------------
df['Week_Start'] = df['Date'] - pd.to_timedelta((df['Date'].dt.weekday + 1) % 7, unit='d')
df['Week_Start'] = df['Week_Start'].dt.date
df['Week_Range'] = df['Week_Start'].apply(lambda ws: f"{ws} → {ws + pd.Timedelta(days=6)}")

# Get unique week options
all_weeks = df[['Week_Start', 'Week_Range']].drop_duplicates().sort_values('Week_Start')
week_options = all_weeks['Week_Range'].tolist()
week_start_mapping = dict(zip(all_weeks['Week_Range'], all_weeks['Week_Start']))

# -------------------------
# Sidebar filters
# -------------------------
# Month filter (optional, can keep or remove if using all-weeks slider)
months = df['Date'].dt.to_period('M').dropna().unique()
selected_month = st.sidebar.selectbox("Select Month", sorted(months))

# Filter by month first
month_filtered_df = df[df['Date'].dt.to_period('M') == selected_month]

# Week slider (snaps to week starts)
selected_week_range = st.sidebar.select_slider(
    "Select Week (Sun → Sat)",
    options=[wr for wr in month_filtered_df['Week_Range'].sort_values().unique()],
    value=month_filtered_df['Week_Range'].sort_values().iloc[-1]  # default to last week
)

start_date = week_start_mapping[selected_week_range]
filtered_df = month_filtered_df[month_filtered_df['Week_Start'] == start_date]

# -------------------------
# Display
# -------------------------
st.subheader(f"Transactions for {selected_month} | Week: {selected_week_range}")
st.dataframe(filtered_df)

st.write(f"**Total Spent:** ${filtered_df['Amount'].sum():,.2f}")

category_totals = filtered_df.groupby('Category')['Amount'].sum().reset_index()
st.subheader("Spending by Category")
st.dataframe(category_totals)
