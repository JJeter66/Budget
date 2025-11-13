import streamlit as st
import pandas as pd
from openpyxl import load_workbook

# -------------------------
# File paths
# -------------------------
EXCEL_FILE = "C:/Users/jjete/OneDrive/1. Life Stuff/Budget/Bank Data Export/Dashboard.xlsx"
SHEET_NAME = "Quicklook"

# -------------------------
# Helper function to extract data and colors
# -------------------------
def extract_range(ws, start_row, end_row, start_col, end_col):
    data = []
    colors = []
    for r in range(start_row, end_row + 1):
        row_data = []
        row_colors = []
        for c in range(start_col, end_col + 1):
            cell = ws.cell(row=r, column=c)
            row_data.append(cell.value)
            
            # Handle cell fill color
            fill = cell.fill.start_color
            if fill and fill.type == "rgb" and fill.rgb is not None:
                hex_color = f"#{fill.rgb[-6:]}"  # Extract RRGGBB
            else:
                hex_color = "#FFFFFF"
            row_colors.append(hex_color)
        data.append(row_data)
        colors.append(row_colors)
    return pd.DataFrame(data), colors

# -------------------------
# Load Quicklook sheet with styles
# -------------------------
@st.cache_data
def load_quicklook_with_styles():
    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb[SHEET_NAME]

    # Extract ranges
    df_top, df_top_colors = extract_range(ws, 1, 4, 1, 6)    # Rows 1-4, cols A-F
    df_mid, df_mid_colors = extract_range(ws, 5, 18, 1, 4)   # Rows 5-18, cols A-D
    df_bot, df_bot_colors = extract_range(ws, 19, 19, 1, 3)  # Row 19, cols A-C
    e18_value = ws.cell(row=18, column=5).value              # E18

    return df_top, df_top_colors, df_mid, df_mid_colors, df_bot, df_bot_colors, e18_value

# -------------------------
# Display Quicklook in Streamlit
# -------------------------
st.set_page_config(page_title="📊 Budget Dashboard", layout="wide")
st.title("📊 Interactive Budget Dashboard")

df_top, df_top_colors, df_mid, df_mid_colors, df_bot, df_bot_colors, e18_value = load_quicklook_with_styles()

# Function to display styled DataFrame
def styled_df(df, colors):
    def color_cells(val, color_row):
        return [f'background-color: {c}; text-align: center;' if isinstance(v, (int, float)) else f'background-color: {c};' 
                for v, c in zip(val, color_row)]
    return df.style.apply(lambda row: color_cells(row, colors[row.name]), axis=1)

st.subheader("Top Section (Rows 1-4)")
st.dataframe(styled_df(df_top, df_top_colors), use_container_width=True)

st.subheader("Middle Section (Rows 5-18)")
st.dataframe(styled_df(df_mid, df_mid_colors), use_container_width=True)

st.subheader("Bottom Section (Row 19)")
st.dataframe(styled_df(df_bot, df_bot_colors), use_container_width=True)

st.subheader("E18 Value")
st.write(e18_value)
