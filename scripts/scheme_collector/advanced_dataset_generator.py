from pymongo import MongoClient
import random
import uuid

client = MongoClient("mongodb://localhost:27017/")
db = client["scheme_db"]
schemes_col = db["schemes"]
dataset_col = db["advanced_dataset"]

# Clear old advanced dataset
dataset_col.delete_many({})
print("🧹 Cleared old advanced_dataset")

STATES = ["Tamil Nadu","Karnataka","Kerala","Maharashtra","Delhi","Telangana"]
SECTORS = ["Manufacturing","Service","Tech","Agri"]
STAGES = ["Idea","Early","Growth"]
FUNDING = ["None","Seed","Angel","VC"]

TARGET = 3500
count = 0

for scheme in schemes_col.find():
    while count < TARGET:
        # ---------------- Business Profile ----------------
        business_id = f"BIZ_{uuid.uuid4().hex[:6]}"
        sector = random.choice(SECTORS)
        stage = random.choice(STAGES)
        turnover = round(random.uniform(2, 200), 2)   # in lakhs
        employees = random.randint(1, 100)
        funding = random.choice(FUNDING)
        state = random.choice(STATES)

        msme_reg = random.choice(["Yes","No"])
        startup_reg = random.choice(["Yes","No"])
        gst = random.choice(["Available","Missing"])
        itr = random.choice(["Available","Missing"])

        # ---------------- Document Readiness ----------------
        udyam = "Available" if msme_reg == "Yes" else "Missing"
        bank_stmt = random.choice(["Available","Missing"])
        business_plan = random.choice(["Available","Missing"])
        kyc = random.choice(["Available","Missing"])

        docs = [gst, udyam, bank_stmt, business_plan, kyc]
        doc_score = docs.count("Available") / len(docs)

        # ---------------- Rule-Based Eligibility ----------------
        eligible = True
        reasons = []

        if stage == "Growth" and turnover < 10:
            eligible = False
            reasons.append("Low turnover for Growth stage")

        if gst == "Missing":
            eligible = False
            reasons.append("GST not available")

        if itr == "Missing":
            eligible = False
            reasons.append("ITR not filed")

        eligibility_status = "Eligible" if eligible else "Not Eligible"
        eligibility_score = round(random.uniform(0.6, 0.95), 2) if eligible else round(random.uniform(0.1, 0.5), 2)

        # ---------------- Explainability ----------------
        if eligible:
            explanation = "Meets major eligibility and compliance requirements"
            recommended_action = "Proceed with application"
        else:
            explanation = "Rejected due to: " + ", ".join(reasons)
            recommended_action = "Complete missing compliance and documents"

        # ---------------- RL Feedback (Simulated) ----------------
        user_applied = random.choice(["Yes","No"])
        application_outcome = random.choice(["Approved","Rejected","Pending"]) if user_applied == "Yes" else "Not Applied"
        model_feedback = 1 if application_outcome == "Approved" else (-1 if application_outcome == "Rejected" else 0)

        record = {
            "record_id": str(uuid.uuid4()),
            "business_id": business_id,
            "sector": sector,
            "business_stage": stage,
            "turnover_lakhs": turnover,
            "employee_count": employees,
            "funding_history": funding,
            "location_state": state,
            "msme_registered": msme_reg,
            "startup_india_registered": startup_reg,
            "gst_certificate": gst,
            "itr_filed": itr,
            "udyam_certificate": udyam,
            "bank_statement": bank_stmt,
            "business_plan": business_plan,
            "kyc_documents": kyc,
            "document_readiness_score": round(doc_score, 2),

            "scheme_name": scheme["scheme_name"],
            "scheme_level": scheme["level"],
            "scheme_type": random.choice(["Grant","Loan","Subsidy","Incubation"]),

            "eligibility_status": eligibility_status,
            "eligibility_score": eligibility_score,
            "rejection_reason": ", ".join(reasons) if reasons else None,

            "explanation": explanation,
            "recommended_action": recommended_action,

            "user_applied": user_applied,
            "application_outcome": application_outcome,
            "model_feedback_score": model_feedback
        }

        dataset_col.insert_one(record)
        count += 1

        if count >= TARGET:
            break

print(f"✅ ADVANCED DATASET GENERATED: {count} records")
