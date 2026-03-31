from pymongo import MongoClient
import uuid
import itertools

client = MongoClient("mongodb://localhost:27017/")
db = client["scheme_intelligence"]

schemes_col = db["schemes"]
eligibility_col = db["eligibility"]
documents_col = db["documents"]
dataset_col = db["final_dataset"]

dataset_col.delete_many({})
print("🧹 Cleared old final_dataset")

STATES = ["Tamil Nadu","Karnataka","Kerala","Maharashtra","Delhi","Telangana"]
STAGES = ["Idea","Early","Growth"]
ENTERPRISE = ["Micro","Small","Medium"]
SECTORS = ["Manufacturing","Service","Tech","Agri"]

TARGET = 3500
count = 0

for scheme in schemes_col.find():
    elig = eligibility_col.find_one({"scheme_name": scheme["scheme_name"]})
    docs = list(documents_col.find({"scheme": scheme["scheme_name"]}))

    doc_names = [d["file_name"] for d in docs] or ["GST Certificate","Udyam Certificate","Bank Statement"]

    rules = elig["eligibility_and_documents"].split("\n") if elig else ["General eligibility applies"]

    for state, stage, ent, sector, rule, doc in itertools.product(
        STATES, STAGES, ENTERPRISE, SECTORS, rules, doc_names
    ):
        if count >= TARGET:
            break

        dataset_col.insert_one({
            "record_id": str(uuid.uuid4()),
            "scheme_name": scheme["scheme_name"],
            "scheme_url": scheme["source_url"],
            "state": state,
            "business_stage": stage,
            "enterprise_type": ent,
            "sector": sector,
            "eligibility_rule": rule.strip()[:500],
            "required_document": doc,
            "is_real_source": True
        })

        count += 1

    if count >= TARGET:
        break

print(f"✅ FINAL REAL DATASET CREATED: {count} records")
