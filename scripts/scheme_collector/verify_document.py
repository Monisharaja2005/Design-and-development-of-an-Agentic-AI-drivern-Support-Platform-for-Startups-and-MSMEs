import argparse
import json

from engine.document_verifier import DocumentVerificationClient


def parse_args():
    parser = argparse.ArgumentParser(description="Verify a government-issued application document.")
    parser.add_argument("--file", required=True, help="Path to document file")
    parser.add_argument("--document-type", required=True, help="Document type, e.g. gst_certificate")
    parser.add_argument("--claimed-authority", default="", help="Claimed issuing authority")
    parser.add_argument("--enterprise-profile-json", default="{}", help="Enterprise profile JSON")
    parser.add_argument("--scheme-requirements-json", default="{}", help="Scheme requirements JSON")
    return parser.parse_args()


def main():
    args = parse_args()
    client = DocumentVerificationClient()
    report = client.verify_file(
        file_path=args.file,
        document_type=args.document_type,
        claimed_authority=args.claimed_authority,
        enterprise_profile=json.loads(args.enterprise_profile_json),
        scheme_requirements=json.loads(args.scheme_requirements_json),
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

