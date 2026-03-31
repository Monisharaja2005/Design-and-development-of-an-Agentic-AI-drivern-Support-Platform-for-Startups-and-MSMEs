from pymongo import MongoClient
import csv

client = MongoClient("mongodb://localhost:27017/")
db = client["scheme_intelligence"]
col = db["final_dataset"]

with open("final_real_scheme_dataset_3500.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    first = col.find_one()
    writer.writerow(first.keys())

    for doc in col.find():
        writer.writerow(doc.values())

print("✅ Exported: final_real_scheme_dataset_3500.csv")
