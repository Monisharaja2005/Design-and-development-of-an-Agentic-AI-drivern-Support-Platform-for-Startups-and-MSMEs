from db.mongo import schemes_col, eligibility_col
from ai.ollama_extractor import extract_info

def parse_schemes():
    for scheme in schemes_col.find():
        extracted = extract_info(scheme["raw_text"])

        eligibility_col.insert_one({
            "scheme_name": scheme["scheme_name"],
            "source_url": scheme["source_url"],
            "eligibility_and_documents": extracted
        })

        print(f"✅ Parsed eligibility for: {scheme['scheme_name']}")
