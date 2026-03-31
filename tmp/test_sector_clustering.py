def sector_matches(user_sector, scheme_sector):
    sl = user_sector.lower().strip()
    ss = scheme_sector.lower().strip()
    
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
            return False 
            
    return True

# Test cases
tests = [
    ("Food Processing", "Agriculture", True),
    ("Food Processing", "Drones", False),
    ("Textile", "Apparel", True),
    ("Textile", "Food", False),
    ("IT Services", "Technology", True),
    ("MSME", "Manufacturing", True), # Generic fallback
]

for u, s, expected in tests:
    res = sector_matches(u, s)
    print(f"User: {u:15} | Scheme: {s:12} | Match: {res} | Expected: {expected} | {'PASS' if res == expected else 'FAIL'}")
