import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

# Path to your Excel file
EXCEL_FILE = "Dashboard.xlsx"

# Helper function to extract cell fill color
def get_fill_hex(cell):
    if cell.fill and cell.fill.start_color:
        rgb = cell.fill.start_color.rgb
        if rgb is not None:
            # openpyxl may return ARGB or RGB
            rgb = rgb[-6:] if len(rgb) > 6 else rgb
            return f"#{rgb}"
    return "#FFFFFF"  # default white

def load_quicklook_with_styles():
    wb = load_workbook(EXCEL_FILE, data_only=True)
    ws = wb.active

    # Extract full range (combine all sections)
    max_row = ws.max_row
    max_col = ws.max_column

    data = []
    color_data = []

    # Save color of first data column for rows 1-16
    column0_color = get_fill_hex(ws.cell(row=2, column=1))

    for r in range(1, max_row + 1):
        row_values = []
        row_colors = []
        for c in range(1, max_col + 1):
            cell = ws.cell(row=r, column=c)
            row_values.append(cell.value)

            # Top row adjustments
            if r == 1 and 5 <= c <= 6:
                row_colors.append("#333333")  # dark background
            elif r == 2 and c == 6:
                row_colors.append("#FFFFFF")  # blank cell
            elif c == 1 and 2 <= r <= 17:
                row_colors.append(column0_color)  # column 0 rows 1-16
            else:
                row_colors.append(get_fill_hex(cell))
        data.append(row_values)
        color_data.append(row_colors)

    df = pd.DataFrame(data)
    df_colors = pd.DataFrame(color_data)

    return df, df_colors

def render_table_with_colors(df, df_colors):
    def color_func(row):
        return [df_colors.iat[row.name, col] for col in range(df.shape[1])]

    styled = df.style.apply(color_func, axis=1)
    styled = styled.set_properties(**{"text-align": "center"})
    return styled

# Streamlit UI
st.title("Quicklook Dashboard")
df, df_colors = load_quicklook_with_styles()
st.dataframe(render_table_with_colors(df, df_colors))
