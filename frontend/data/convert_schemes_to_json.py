import pandas as pd
import json
import os
import uuid

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

excel_file = os.path.join(BASE_DIR, "India_Complete_MSME_Startup_Schemes_383.xlsx")
output_json = os.path.join(BASE_DIR, "schemes_correct_383.json")

# ===============================
# READ MASTER SHEET
# ===============================
df = pd.read_excel(excel_file, sheet_name="📋 All Schemes (383)")

print("Columns Found:")
print(df.columns)

# ===============================
# AUTO COLUMN DETECTION  ⭐ FIXED
# ===============================
scheme_code_col = None
scheme_name_col = None
state_col = None
desc_col = None
elig_col = None
sector_col = None

for col in df.columns:

    c = str(col).lower()

    if "scheme id" in c or "scheme_code" in c:
        scheme_code_col = col

    elif "scheme name" in c:
        scheme_name_col = col

    elif "state" in c or "region" in c:
        state_col = col

    elif "description" in c:
        desc_col = col

    elif "eligibility" in c:
        elig_col = col

    elif "sector" in c:
        sector_col = col

print("Detected Columns:")
print("Scheme Code:", scheme_code_col)
print("Scheme Name:", scheme_name_col)
print("State:", state_col)

# ===============================
# DROP EMPTY SCHEME NAME ROWS
# ===============================
df = df.dropna(subset=[scheme_name_col])

print("Valid Rows:", len(df))

df = df.fillna("Not Available")

# ===============================
# BUILD JSON  ⭐ FIXED SCHEME CODE EXTRACTION
# ===============================
schemes = []

for _, row in df.iterrows():

    code_value = row.get(scheme_code_col)

    if pd.isna(code_value):
        code_value = ""

    scheme_code = str(code_value).strip().upper()

    scheme = {
        "scheme_id": "SCH-" + str(uuid.uuid4())[:8],
        "scheme_code": scheme_code,
        "scheme_name": str(row.get(scheme_name_col)),
        "state": str(row.get(state_col)),
        "sector": str(row.get(sector_col)),
        "eligibility": str(row.get(elig_col)),
        "description": str(row.get(desc_col)),
    }

    scheme["semantic_text"] = (
        f"{scheme['scheme_name']} scheme in {scheme['state']} "
        f"for MSME or Startup in {scheme['sector']} sector. "
        f"Eligibility: {scheme['eligibility']}"
    )

    schemes.append(scheme)

# ===============================
# SAVE JSON
# ===============================
with open(output_json, "w", encoding="utf-8") as f:
    json.dump(schemes, f, indent=4, ensure_ascii=False)

print("🔥 FINAL JSON CREATED")
print("Total Schemes:", len(schemes))