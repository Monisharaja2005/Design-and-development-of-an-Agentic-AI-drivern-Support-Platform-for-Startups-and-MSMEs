from pymongo import MongoClient
import itertools
import csv
import uuid

# ------------------ MongoDB ------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["scheme_db"]
schemes_col = db["schemes"]
dataset_col = db["dataset_records"]

# ------------------ Dimensions ------------------
STATES_UTS = [
    "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh",
    "Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka",
    "Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram",
    "Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu",
    "Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal",
    "Delhi","Puducherry","Chandigarh","Jammu and Kashmir",
    "Ladakh","Lakshadweep","Andaman and Nicobar","Dadra and Nagar Haveli"
]

BUSINESS_STAGE = ["Idea", "Early", "Growth"]
ENTERPRISE_TYPE = ["Micro", "Small", "Medium"]
SECTOR = ["Manufacturing", "Service", "Tech", "Agri"]
GENDER = ["General", "Women", "SC-ST"]

TARGET_LIMIT = 3500   # 🔥 REQUIRED DATASET SIZE

# ------------------ Generator ------------------
records_created = 0

for scheme in schemes_col.find():
    combinations = itertools.product(
        STATES_UTS,
        BUSINESS_STAGE,
        ENTERPRISE_TYPE,
        SECTOR,
        GENDER
    )

    for combo in combinations:
        if records_created >= TARGET_LIMIT:
            break

        state, stage, enterprise, sector, gender = combo

        record = {
            "record_id": str(uuid.uuid4()),
            "scheme_name": scheme.get("scheme_name"),
            "scheme_level": scheme.get("level"),
            "state": state,
            "business_stage": stage,
            "enterprise_type": enterprise,
            "sector": sector,
            "gender_focus": gender,
            "base_scheme_id": scheme.get("_id")
        }

        dataset_col.insert_one(record)
        records_created += 1

    if records_created >= TARGET_LIMIT:
        break

print(f"✅ Dataset generation complete: {records_created} records created")
