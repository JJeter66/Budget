import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles.colors import Color

# -------------------------
# File path
# -------------------------
EXCEL_FILE = "Dashboard.xlsx"

# -------------------------
# Helper: Get hex fill color
# -------------------------
def get_fill_hex(cell):
    fill = cell.fill
    if fill and fill.start_color:
        rgb = fill.start_color.rgb
        if rgb is not None:
            return f"#{rgb[-6:]}"  # Take last 6 chars in case of ARGB
    return "#FFFFFF"

# -------------------------
# Load Dashboard with styles
# -------------------------
@st.cache_data
def load_quicklook_with_styles():
    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active  # Assuming Quicklook is first sheet

    df_data = []
    df_colors = []

    for r, row in enumerate(ws.iter_rows(min_row=1, max_row=17, min_col=1, max_col=6)):
        row_values = []
        row_colors = []
        for c, cell in enumerate(row):
            value = cell.value
            if value is None and r >= 1 and c >= 1:
                value = ""  # Replace None with blank for rows 1-16
            row_values.append(value)
            row_colors.append(get_fill_hex(cell))
        df_data.append(row_values)
        df_colors.append(row_colors)

    # Apply special styles
    # Merge top row columns 0-4 visually (Streamlit can't literally merge, but we can show empty for columns 1-4)
    for c in range(1, 5):
        df_data[0][c] = ""

    # Dark background with light text for top row columns 4-5
    for c in [4, 5]:
        df_colors[0][c] = "#333333"  # Dark gray
        df_data[0][c] = str(df_data[0][c])  # Ensure text is string

    # Column 0 rows 1-16 same color as row 1 col 0
    col0_color = df_colors[1][0]
    for r in range(1, 17):
        df_colors[r][0] = col0_color

    df = pd.DataFrame(df_data)
    return df, df_colors

# -------------------------
# Streamlit App
# -------------------------
st.set_page_config(page_title="📊 Dashboard", layout="wide")
st.title("📊 Dashboard Overview")

df, df_colors = load_quicklook_with_styles()

# Style dataframe for Streamlit display
def style_df(df, df_colors):
    styled = df.style
    for r in range(len(df)):
        for c in range(len(df.columns)):
            styled = styled.set_properties(**{
                'background-color': df_colors[r][c],
                'text-align': 'center' if isinstance(df.iloc[r, c], (int, float)) else 'left',
                'color': '#FFFFFF' if df_colors[r][c] in ['#333333', '#000000'] else '#000000'
            }, subset=pd.IndexSlice[r, c])
    return styled

st.dataframe(style_df(df, df_colors), use_container_width=True)
