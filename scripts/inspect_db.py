import lancedb
db_path = r"d:\Main_project1\final\lancedb_backup"
db = lancedb.connect(db_path)
print("Tables:", db.table_names())
for tname in db.table_names():
    tbl = db.open_table(tname)
    print(f"Table {tname} has {tbl.to_pandas().shape[0]} rows")
    print(f"Cols: {tbl.to_pandas().columns.tolist()}")
    print(f"First row: {tbl.to_pandas().iloc[0].to_dict() if not tbl.to_pandas().empty else 'N/A'}")
