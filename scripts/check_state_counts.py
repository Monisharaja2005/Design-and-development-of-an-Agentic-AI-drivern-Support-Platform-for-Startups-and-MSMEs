import lancedb
import pandas as pd

db_path = r"d:\Main_project1\final\lancedb_backup"
db = lancedb.connect(db_path)
tbl = db.open_table("schemes")
df = tbl.to_pandas()

print(f"Total schemes: {len(df)}")
if 'state' in df.columns:
    print("\nSchemes by State:")
    print(df['state'].value_counts())
else:
    print("\n'state' column not found in table 'schemes'")

if 'Scheme_Name' in df.columns:
    print("\nSample schemes from Maharashtra (if any):")
    print(df[df['state'].str.contains('Maharashtra', case=False, na=False)][['Scheme_Name', 'state']].head())
