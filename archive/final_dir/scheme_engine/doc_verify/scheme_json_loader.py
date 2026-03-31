from pathlib import Path
import json
import csv
from typing import Any
from scheme_assistant import SchemeSemanticIndex


def csv_from_scheme_json(json_path: Path, csv_out: Path) -> None:
    """Convert schemes_correct_383.json → schemes.csv compatible format."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with json_path.open("r", encoding="utf-8") as f:
        schemes = json.load(f)
    
    # Map JSON fields to CSV headers expected by SchemeSemanticIndex
    csv_headers = [
        "Scheme_ID", "Scheme_Name", "Scheme_Category", "Ministry", 
        "State_Applicable", "Target_Sector", "Target_Audience", 
        "Application_Process", "Timeline_Days", "Status"
    ]
    
    csv_rows = []
    for s in schemes:
        row = {
            "Scheme_ID": s.get("scheme_id", ""),
            "Scheme_Name": s.get("scheme_name", ""),
            "Scheme_Category": s.get("sector", ""),
            "Ministry": s.get("state", ""),
            "State_Applicable": s.get("state", ""),
            "Target_Sector": s.get("sector", ""),
            "Target_Audience": s.get("eligibility", ""),
            "Application_Process": s.get("description", ""),
            "Timeline_Days": "90",  # Default
            "Status": "Active"
        }
        csv_rows.append(row)
    
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    with csv_out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(csv_rows)
    
    print(f"Converted {len(csv_rows)} schemes → {csv_out}")


def load_json_direct(index: SchemeSemanticIndex, json_path: Path) -> None:
    """Load schemes directly from JSON into semantic index (skip CSV step)."""
    with json_path.open("r", encoding="utf-8") as f:
        rows = json.load(f)
    
    # Map to _row_to_text format
    index.rows = rows
    index.row_texts = [f"{s.get('scheme_name', '')} | {s.get('state', '')} | {s.get('sector', '')} | {s.get('eligibility', '')} | {s.get('description', '')}" for s in rows]
    
    print(f"Loaded {len(rows)} schemes from {json_path} directly into semantic index")


if __name__ == "__main__":
    frontend_path = Path("d:/final/frontend/data/schemes_correct_383.json")
    backend_csv = Path("d:/final/final/scheme_engine/doc_verify/data/schemes.csv")
    
    # Option 1: Convert to CSV
    csv_from_scheme_json(frontend_path, backend_csv)
    
    # Option 2: Use directly (modify SchemeSemanticIndex __init__ to accept JSON)
    # load_json_direct(index, frontend_path)
