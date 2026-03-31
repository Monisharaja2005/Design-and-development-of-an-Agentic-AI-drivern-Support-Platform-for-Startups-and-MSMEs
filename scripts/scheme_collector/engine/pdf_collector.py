import os
from urllib.parse import urlparse

import requests

from db.mongo import doc_verifications_col, documents_col
from engine.document_verifier import DocumentVerificationClient

PDF_LINKS = [
    {
        "scheme": "PMEGP",
        "urls": [
            "https://www.kviconline.gov.in/pmegpeportal/docs/PMEGP_Guidelines.pdf",
            "https://www.kviconline.gov.in/kvicres/pmegp/pmegpweb/docs/PMEGP_Guidelines.pdf",
        ],
    }
]

SAVE_DIR = "documents/files"
os.makedirs(SAVE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


def _maybe_verify_document(local_path: str, scheme_name: str, source_url: str):
    if os.getenv("ENABLE_DOC_VERIFY", "false").lower() != "true":
        return

    client = DocumentVerificationClient()
    default_type = os.getenv("DOC_VERIFY_DEFAULT_TYPE", "generic_certificate")
    try:
        report = client.verify_file(
            file_path=local_path,
            document_type=default_type,
            claimed_authority=os.getenv("DOC_VERIFY_DEFAULT_AUTHORITY", "Government of India"),
            enterprise_profile={},
            scheme_requirements={"required_document_types": [default_type]},
        )
        doc_verifications_col.insert_one(
            {
                "scheme": scheme_name,
                "local_path": local_path,
                "source_url": source_url,
                "report_id": report.get("report_id"),
                "status": report.get("status"),
                "authenticity_score": report.get("authenticity_score"),
                "fraud_risk": report.get("fraud_risk"),
                "authority_verification": report.get("authority_verification"),
            }
        )
        print(f"Verification completed: {os.path.basename(local_path)} | {report.get('status')}")
    except Exception as exc:
        print(f"Verification skipped/failed for {os.path.basename(local_path)}: {exc}")


def collect_pdfs():
    for item in PDF_LINKS:
        source_urls = item.get("urls") or ([item["url"]] if item.get("url") else [])
        if not source_urls:
            print(f"PDF error: {item['scheme']} | no source URL configured")
            continue

        downloaded = False
        last_error: Exception | None = None
        for source_url in source_urls:
            try:
                filename = _filename_from_url(source_url)
                path = os.path.join(SAVE_DIR, filename)

                response = requests.get(
                    source_url,
                    headers=HEADERS,
                    timeout=40,
                    verify=True,
                )
                response.raise_for_status()

                with open(path, "wb") as file_handle:
                    file_handle.write(response.content)

                documents_col.insert_one(
                    {
                        "scheme": item["scheme"],
                        "file_name": filename,
                        "local_path": path,
                        "source_url": source_url,
                    }
                )

                print(f"PDF downloaded: {filename}")
                _maybe_verify_document(path, item["scheme"], source_url)
                downloaded = True
                break

            except Exception as exc:
                last_error = exc
                continue

        if not downloaded:
            print(f"PDF error: {item['scheme']} | all URLs failed | last_error={last_error}")


def _filename_from_url(url: str) -> str:
    name = os.path.basename(urlparse(url).path) or "document.pdf"
    return name.split("?")[0]
