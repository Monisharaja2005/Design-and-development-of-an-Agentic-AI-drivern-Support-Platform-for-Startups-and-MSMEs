import fitz  # PyMuPDF
from db.mongo import documents_col, eligibility_col

def extract_pdf_text():
    for doc in documents_col.find():
        try:
            pdf = fitz.open(doc["local_path"])
            full_text = ""

            for page in pdf:
                full_text += page.get_text()

            eligibility_col.insert_one({
                "scheme_name": doc["scheme"],
                "source_url": doc["source_url"],
                "eligibility_and_documents": full_text[:15000],
                "source_type": "PDF"
            })

            print(f"✅ Extracted PDF text for: {doc['scheme']}")

        except Exception as e:
            print(f"❌ PDF text extraction failed: {doc['file_name']} | {e}")
