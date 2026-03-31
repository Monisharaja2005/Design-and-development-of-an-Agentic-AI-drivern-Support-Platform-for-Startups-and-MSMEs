import random


STATE_POLICY_SCORE = {
    "andhra pradesh": 82,
    "arunachal pradesh": 70,
    "assam": 74,
    "bihar": 72,
    "chhattisgarh": 76,
    "goa": 80,
    "gujarat": 91,
    "haryana": 88,
    "himachal pradesh": 79,
    "jharkhand": 75,
    "karnataka": 92,
    "kerala": 86,
    "madhya pradesh": 83,
    "maharashtra": 94,
    "manipur": 68,
    "meghalaya": 67,
    "mizoram": 66,
    "nagaland": 65,
    "odisha": 81,
    "punjab": 85,
    "rajasthan": 84,
    "sikkim": 73,
    "tamil nadu": 93,
    "telangana": 90,
    "tripura": 69,
    "uttar pradesh": 82,
    "uttarakhand": 80,
    "west bengal": 83,

    # Union Territories
    "delhi": 95,
    "jammu and kashmir": 78,
    "ladakh": 72,
    "chandigarh": 88,
    "puducherry": 79,
    "andaman and nicobar": 68,
    "dadra and nagar haveli": 74,
    "daman and diu": 75,

    # Central
    "central": 96,
    "india": 96,
    "all india": 96,
    "pan india": 96,
    "national": 96
}


def compute_scheme_scores(profile, scheme):

    state = profile.state.lower()
    sector = profile.sector.lower()
    entity = profile.entityType.lower()

    scheme_state = str(scheme.get("state","")).lower()
    scheme_sector = str(scheme.get("sector","")).lower()
    eligibility = str(scheme.get("eligibility","")).lower()
    desc = str(scheme.get("description","")).lower()

    # ⭐ Eligibility Score
    eligibility_score = 0

    if entity in eligibility:
        eligibility_score += 40

    if sector in scheme_sector:
        eligibility_score += 30

    if state in scheme_state:
        eligibility_score += 30


    # ⭐ Sector Growth Intelligence
    if "manufacturing" in scheme_sector:
        sector_growth = 88
    elif "it" in scheme_sector or "digital" in scheme_sector:
        sector_growth = 92
    elif "agriculture" in scheme_sector:
        sector_growth = 78
    elif "textile" in scheme_sector:
        sector_growth = 81
    elif "export" in scheme_sector:
        sector_growth = 85
    else:
        sector_growth = 72


    # ⭐ Policy Strength
    policy_strength = 75
    for key in STATE_POLICY_SCORE:
        if key in scheme_state:
            policy_strength = STATE_POLICY_SCORE[key]
            break


    # ⭐ Funding Attractiveness
    if "grant" in desc:
        funding_score = 92
    elif "subsidy" in desc:
        funding_score = 88
    elif "capital" in desc:
        funding_score = 84
    elif "loan" in desc:
        funding_score = 72
    else:
        funding_score = 65


    # ⭐ Application Difficulty
    if "cluster" in desc:
        difficulty = "High"
    elif "startup" in desc or "innovation" in desc:
        difficulty = "Medium"
    else:
        difficulty = "Low"


    # ⭐ Success Probability
    success_probability = min(
        95,
        int((eligibility_score * 0.6 + policy_strength * 0.4))
    )


    # ⭐ Timeline Estimation (AI Heuristic)
    if difficulty == "High":
        timeline_days = random.randint(60, 120)
    elif difficulty == "Medium":
        timeline_days = random.randint(30, 60)
    else:
        timeline_days = random.randint(10, 30)


    # ⭐ Final Score
    overall_score = int(
        (eligibility_score * 0.35)
        + (sector_growth * 0.15)
        + (policy_strength * 0.15)
        + (funding_score * 0.15)
        + (success_probability * 0.20)
    )

    scheme["eligibility_score"] = eligibility_score
    scheme["sector_growth_score"] = sector_growth
    scheme["policy_strength_score"] = policy_strength
    scheme["funding_score"] = funding_score
    scheme["success_probability"] = success_probability
    scheme["application_difficulty"] = difficulty
    scheme["timeline_days"] = timeline_days
    scheme["overall_ai_score"] = overall_score

    return scheme