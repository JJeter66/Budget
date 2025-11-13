import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill

# -------------------------
# File path
# -------------------------
EXCEL_FILE = r"Dashboard.xlsx"
SHEET_NAME = "Quicklook"

# -------------------------
# Helper: Safe hex color from Excel cell
# -------------------------
def get_fill_hex(cell):
    fill = cell.fill
    if fill and fill.start_color:
        rgb = fill.start_color.rgb
        if rgb is not None:
            if isinstance(rgb, str):
                return f"#{rgb[-6:]}"  # ARGB string
            elif hasattr(rgb, 'rgb'):
                return f"#{rgb.rgb[-6:]}"  # RGB object
    return "#FFFFFF"

# -------------------------
# Load Quicklook with styles
# -------------------------
@st.cache_data
def load_quicklook_with_styles():
    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb[SHEET_NAME]

    # Combine all rows into one section: rows 0-16
    data = []
    colors = []

    for r in range(0, 17):
        row_values = []
        row_colors = []
        for c in range(0, 6):
            cell = ws.cell(row=r+1, column=c+1)
            # Values
            if r == 1 and c in [1,2,3,4,5]:
                row_values.append("")  # leave blank
            else:
                row_values.append(cell.value if cell.value is not None else "")
            # Colors
            if r == 0 and c in [4,5]:
                row_colors.append("#333333")  # dark background
            elif r == 0 and c in [0,1,2,3]:
                row_colors.append(get_fill_hex(cell))
            elif c == 0 and 1 <= r <= 16:
                row_colors.append(get_fill_hex(ws.cell(row=2, column=1)))  # match col 0 row 1
            else:
                row_colors.append(get_fill_hex(cell))
        data.append(row_values)
        colors.append(row_colors)

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df_colors = pd.DataFrame(colors)

    # Center align numbers
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x)

    return df, df_colors

# -------------------------
# Streamlit app
# -------------------------
st.set_page_config(page_title="📊 Dashboard", layout="wide")
st.title("📊 Dashboard Quicklook")

df, df_colors = load_quicklook_with_styles()

# Render table with background colors
def render_table_with_colors(df, df_colors):
    styled = df.style.apply(lambda r: df_colors.values, axis=None)
    # Center align all numbers
    styled = styled.set_properties(**{"text-align": "center"})
    return styled

st.subheader("Quicklook")
st.dataframe(render_table_with_colors(df, df_colors))
