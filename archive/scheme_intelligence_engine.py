import re
import json
from pathlib import Path


def enrich_scheme(scheme):

    desc = str(scheme.get("description", "")).lower()
    name = str(scheme.get("scheme_name", "")).lower()
    eligibility = str(scheme.get("eligibility", "")).lower()
    sector = str(scheme.get("sector", "")).lower()
    state = str(scheme.get("state", "")).lower()

    full_text = f"{desc} {eligibility} {sector} {name}"

    # ⭐⭐⭐ TIMELINE INTELLIGENCE ⭐⭐⭐
    if any(k in full_text for k in ["cluster", "industrial park", "infrastructure"]):
        timeline = 150
    elif "capital subsidy" in full_text:
        timeline = 120
    elif "subsidy" in full_text:
        timeline = 90
    elif any(k in full_text for k in ["loan", "credit", "interest"]):
        timeline = 60
    elif any(k in full_text for k in ["startup", "seed", "innovation"]):
        timeline = 45
    else:
        timeline = 75

    # ⭐⭐⭐ SUBSIDY % DETECTION ⭐⭐⭐
    subsidy_match = re.search(r'(\d{1,3})\s?%', full_text)
    subsidy = subsidy_match.group(1) + "%" if subsidy_match else "Not Specified"

    # ⭐⭐⭐ FUNDING AMOUNT DETECTION ⭐⭐⭐
    fund_match = re.search(
        r'₹?\s?([\d,.]+)\s?(crore|cr|lakh|lac|million|billion)?',
        full_text
    )
    if fund_match:
        funding = f"₹{fund_match.group(1)} {fund_match.group(2) or ''}".strip()
    else:
        funding = "Not Mentioned"

    # ⭐⭐⭐ MINISTRY DETECTION ⭐⭐⭐
    ministry_map = {
        "msme": "Ministry of MSME",
        "startup india": "DPIIT",
        "export": "Ministry of Commerce",
        "solar": "MNRE",
        "renewable": "MNRE",
        "energy": "MNRE",
        "agriculture": "Ministry of Agriculture",
        "technology": "MeitY",
        "digital": "MeitY",
        "skill": "Ministry of Skill Development"
    }

    ministry = None
    for k, v in ministry_map.items():
        if k in full_text:
            ministry = v
            break

    if not ministry:
        ministry = f"{scheme.get('state','State')} Government"

    # ⭐⭐⭐ SCHEME TYPE ⭐⭐⭐
    if "grant" in full_text:
        scheme_type = "Grant"
    elif "subsidy" in full_text:
        scheme_type = "Subsidy"
    elif "loan" in full_text or "credit" in full_text:
        scheme_type = "Loan Support"
    elif "equity" in full_text or "venture" in full_text:
        scheme_type = "Equity Funding"
    else:
        scheme_type = "Mixed Support"

    # ⭐⭐⭐ CATEGORY ⭐⭐⭐
    if "cluster" in full_text:
        category = "Infrastructure"
    elif "technology" in full_text:
        category = "Technology Upgrade"
    elif "export" in full_text:
        category = "Export Promotion"
    elif "skill" in full_text:
        category = "Skill Development"
    else:
        category = "General MSME"

    # ⭐⭐⭐ BENEFICIARY TAGS ⭐⭐⭐
    tags = []

    if "women" in full_text:
        tags.append("Women")

    if "sc/st" in full_text or "scheduled caste" in full_text:
        tags.append("SC/ST")

    if "startup" in full_text:
        tags.append("Startup")

    if "manufacturing" in full_text:
        tags.append("Manufacturing")

    if "export" in full_text:
        tags.append("Exporter")

    if "green" in full_text or "solar" in full_text:
        tags.append("Green")

    # ⭐⭐⭐ ELIGIBILITY STRICTNESS SCORE ⭐⭐⭐
    score = 0
    if "only" in eligibility:
        score += 2
    if "must" in eligibility:
        score += 2
    if "minimum turnover" in eligibility:
        score += 2
    if "project cost" in eligibility:
        score += 1

    if score >= 4:
        strictness = "High"
    elif score >= 2:
        strictness = "Medium"
    else:
        strictness = "Low"

    # ⭐⭐⭐ PRIORITY SCORE ⭐⭐⭐
    priority = 0
    if scheme_type == "Grant":
        priority += 40
    if subsidy != "Not Specified":
        priority += 20
    if funding != "Not Mentioned":
        priority += 20
    if timeline <= 60:
        priority += 10
    if "startup" in full_text:
        priority += 10

    # ⭐⭐⭐ SEARCH TEXT ⭐⭐⭐
    search_text = f"{name} scheme {sector} {state} subsidy loan grant startup msme eligibility apply"

    # ⭐⭐⭐ WRITE BACK ⭐⭐⭐
    scheme["timeline_days"] = timeline
    scheme["subsidy_percent"] = subsidy
    scheme["funding_amount"] = funding
    scheme["ministry"] = ministry
    scheme["scheme_type"] = scheme_type
    scheme["category"] = category
    scheme["beneficiary_tags"] = tags
    scheme["eligibility_strictness"] = strictness
    scheme["priority_score"] = priority
    scheme["search_text"] = search_text

    return scheme


# ⭐⭐⭐ BATCH RUNNER ⭐⭐⭐
if __name__ == "__main__":

    INPUT_FILE = "frontend/data/schemes_correct_383.json"
    OUTPUT_FILE = "frontend/data/schemes_enriched_free.json"

    print("🚀 Loading schemes...")

    with open(INPUT_FILE, encoding="utf-8") as f:
        schemes = json.load(f)

    print("✅ Total:", len(schemes))

    enriched = [enrich_scheme(s) for s in schemes]

    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print("🔥 DONE")