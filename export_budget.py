import gspread
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
import pandas as pd
import os
import datetime
from rapidfuzz import process, fuzz

# -------------------------
# Paths
# -------------------------
base_folder = r"C:\Users\jjete\OneDrive\1. Life Stuff\Budget\Bank Data Export"
excel_file = os.path.join(base_folder, "budget_export.xlsx")
category_file = os.path.join(base_folder, "categories.xlsx")
log_file = os.path.join(base_folder, "export_log.txt")
credentials_file = os.path.join(base_folder, 'credentials.json')
token_file = os.path.join(base_folder, 'token.json')

# -------------------------
# Logging
# -------------------------
def log(message):
    with open(log_file, "a") as f:
        f.write(f"{datetime.datetime.now()}: {message}\n")
    print(message)

log("Script started")

try:
    # -------------------------
    # Authenticate Google Sheets
    # -------------------------
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    flow = flow_from_clientsecrets(credentials_file, scope)
    storage = Storage(token_file)
    credentials = storage.get()
    if not credentials or credentials.invalid:
        credentials = run_flow(flow, storage)
    gc = gspread.authorize(credentials)

    # -------------------------
    # Open Google Sheet & Read Data
    # -------------------------
    spreadsheet_name = "Budget 2026"
    log(f"Opening spreadsheet: {spreadsheet_name}")
    sh = gc.open(spreadsheet_name)

    sheet_names = ["NFCU", "Chase", "USAA"]
    dfs = []

    for name in sheet_names:
        try:
            ws = sh.worksheet(name)
            data = ws.get_all_records()
            df = pd.DataFrame(data)
            log(f"Loaded {len(df)} rows from {name}")

            df['SourceSheet'] = name

            # Fill missing Description
            if 'Description' not in df.columns:
                df['Description'] = "No Description"
            else:
                df['Description'] = df['Description'].fillna('No Description')

            # Ensure Amount is numeric
            if 'Amount' in df.columns:
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            else:
                df['Amount'] = 0

            dfs.append(df)
        except Exception as e:
            log(f"Error reading {name}: {e}")

    if not dfs:
        log("No data found in any sheet.")
        raise Exception("No data to save.")

    combined_df = pd.concat(dfs, ignore_index=True)
    log(f"Total combined rows from sheets: {len(combined_df)}")
    log(f"Columns after concatenation: {combined_df.columns.tolist()}")

    # -------------------------
    # Standardize column names
    # -------------------------
    combined_df.columns = combined_df.columns.str.strip()  # remove extra spaces

    # Rename 'Transaction Id' to 'TransactionID'
    if 'Transaction Id' in combined_df.columns:
        combined_df.rename(columns={'Transaction Id': 'TransactionID'}, inplace=True)

    # -------------------------
    # Load Categories (Column A = Keyword, Column B = Category)
    # -------------------------
    if os.path.exists(category_file):
        categories = pd.read_excel(category_file, usecols=[0,1], header=None)
        categories.columns = ['Keyword', 'Category']
        categories['Keyword'] = categories['Keyword'].astype(str).str.strip().str.lower()
        categories['Category'] = categories['Category'].astype(str).str.strip()
        log(f"Loaded {len(categories)} category rules.")
    else:
        log(f"Category file not found: {category_file}")
        categories = pd.DataFrame(columns=["Keyword", "Category"])

    keywords = categories['Keyword'].tolist()

    # -------------------------
    # Categorization function using Description
    # -------------------------
    def assign_category(description):
        if pd.isna(description):
            return pd.Series(["Uncategorized", ""])
        desc = str(description).strip().lower()
        for i, keyword in enumerate(keywords):
            if keyword in desc:
                return pd.Series([categories.loc[i, 'Category'], keyword])
        if keywords:
            result = process.extractOne(desc, keywords, scorer=fuzz.partial_ratio)
            if result:
                match_keyword, score, idx = result
                if score >= 75:
                    return pd.Series([categories.loc[idx,'Category'], match_keyword])
        return pd.Series(["Uncategorized", ""])

    # -------------------------
    # Remove duplicates by TransactionID (if exists)
    # -------------------------
    if 'TransactionID' in combined_df.columns:
        combined_df = combined_df.drop_duplicates(subset=['TransactionID'], keep='first')

    # -------------------------
    # Apply categories to ALL rows
    # -------------------------
    combined_df[['Category', 'MatchedKeyword']] = combined_df['Description'].apply(assign_category)

    # -------------------------
    # Transform columns for Excel export
    # -------------------------
    combined_df['CompanyName'] = combined_df.get('Merchant', '')
    combined_df['Notes'] = combined_df['Date'].astype(str) + " | " + combined_df['MatchedKeyword']

    # Add Subcategory column (empty for now)
    combined_df['Subcategory'] = ""

    # Drop unnecessary columns
    columns_to_drop = ['Tags', 'Merchant', 'Currency', 'MatchedKeyword']
    combined_df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Ensure TransactionID exists; if not, create placeholder
    if 'TransactionID' not in combined_df.columns:
        combined_df['TransactionID'] = ""

    # Reorder columns exactly as requested, with TransactionID last
    desired_order = [
        'Account',
        'SourceSheet',
        'CompanyName',
        'Description',
        'Category',
        'Subcategory',
        'Date',
        'Amount',
        'Notes',
        'TransactionID'
    ]
    combined_df = combined_df[[col for col in desired_order if col in combined_df.columns]]

    # -------------------------
    # Save main Excel file only
    # -------------------------
    combined_df.to_excel(excel_file, index=False)
    log(f"Excel file updated with {len(combined_df)} total rows.")

    log("Script completed successfully.")

except Exception as e:
    log(f"Script failed with error: {e}")
