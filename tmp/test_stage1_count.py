import json

def sector_matches(user_sector, scheme_sector):
    if not user_sector or not scheme_sector: return True
    sl = user_sector.lower().strip()
    ss = scheme_sector.lower().strip()
    
    if ss in ["all", "general", "any"] or sl in ["all", "general", "any"]:
        return True

    if ss and sl and ss not in ["all", "general", "any"] and sl not in ["all", "general", "any"]:
        clusters = {
            "agri": {"agri", "food", "dairy", "poultry", "fishery", "animal", "horticulture", "apeda", "nabard", "farming"},
            "textile": {"textile", "apparel", "garment", "weaver", "silk", "handloom", "khadi", "cotton", "textiles"},
            "drone": {"drone", "uav"},
            "ev": {"electric vehicle", "ev", "battery", "automobile", "automotive"},
            "it": {"it ", "software", "technology", "digital", "ai ", "semiconductor", "electronics", "fintech"},
            "pharma": {"pharma", "medical", "healthcare", "biotech", "life sciences"}
        }
        
        user_clusters = {name for name, keywords in clusters.items() if any(k in sl for k in keywords)}
        scheme_clusters = {name for name, keywords in clusters.items() if any(k in ss for k in keywords)}
        
        if user_clusters and scheme_clusters and not (user_clusters & scheme_clusters):
            return False 
            
        for name, keywords in clusters.items():
            if name in user_clusters: continue
            if any(k in ss for k in keywords):
                return False # THIS IS THE SUSPECTED CULPRIY
            
        common_keywords = {"manufacturing", "service", "it ", "software", "export", "msme"}
        if any(k in sl and k in ss for k in common_keywords):
            return True
        if any(k in sl for k in common_keywords) and ss in ["all", "general"]:
            return True

    return True # Final fallback

# Load schemes
with open(r"d:\Main_project1\final\frontend\data\schemes_merged_final.json", "r", encoding="utf-8") as f:
    schemes = json.load(f)

user_sec = "Food Processing"
count = 0
for s in schemes:
    s_sec = s.get("sector", "")
    if sector_matches(user_sec, s_sec):
        count += 1
    else:
        # Print first few failures to see why
        if count < 50:
             pass
        # print(f"BLOCKED: {s.get('scheme_name')} | Sector: {s_sec}")

print(f"Total passing schemes for {user_sec}: {count}")
