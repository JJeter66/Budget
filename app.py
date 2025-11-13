import streamlit as st
import pandas as pd
from openpyxl import load_workbook

# Path to your Excel dashboard
EXCEL_FILE = "C:/Users/jjete/OneDrive/1. Life Stuff/Budget/Bank Data Export/Dashboard.xlsx"

def get_fill_hex(cell):
    """Return a valid CSS hex color for a cell."""
    if cell.fill and cell.fill.start_color:
        rgb = cell.fill.start_color.rgb
        if rgb:
            rgb = rgb[-6:] if len(rgb) > 6 else rgb  # handle ARGB
            if len(rgb) == 6:
                return f"#{rgb}"
    return "#FFFFFF"  # default to white

def load_dashboard_with_styles():
    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    data = []
    colors = []

    # Determine the range: all rows with data
    max_row = ws.max_row
    max_col = ws.max_column

    for r in range(max_row):
        row_data = []
        row_colors = []
        for c in range(max_col):
            cell = ws.cell(row=r+1, column=c+1)
            value = cell.value if cell.value is not None else ""
            row_data.append(value)

            # Apply your custom styles
            if r == 0 and 0 <= c <= 4:
                # Merge top-left section (just for color styling)
                row_colors.append(get_fill_hex(ws.cell(row=1, column=1)))
            elif r == 0 and c in [4,5]:
                # Dark background with light text
                row_colors.append("#333333")  # dark
            elif r == 1 and 5 <= c <= max_col-1:
                row_colors.append("#FFFFFF")  # leave blank as white
            elif 1 <= r <= 16 and c == 0:
                # Column 0 rows 1–16 same as column 0 row 1
                row_colors.append(get_fill_hex(ws.cell(row=2, column=1)))
            else:
                row_colors.append(get_fill_hex(cell))

        data.append(row_data)
        colors.append(row_colors)

    df = pd.DataFrame(data)
    df_colors = pd.DataFrame(colors)
    return df, df_colors

def render_table_with_colors(df, df_colors):
    """Apply colors to the DataFrame using pandas Styler."""
    def style_func(val):
        return val

    styler = df.style
    for r in range(df.shape[0]):
        for c in range(df.shape[1]):
            styler = styler.set_properties(
                subset=pd.IndexSlice[r, c],
                **{"background-color": df_colors.iat[r, c],
                   "color": "#FFFFFF" if df_colors.iat[r,c]=="#333333" else "#000000"}
            )
    return styler

# Streamlit display
st.title("Budget Dashboard")
df, df_colors = load_dashboard_with_styles()
st.dataframe(render_table_with_colors(df, df_colors))
