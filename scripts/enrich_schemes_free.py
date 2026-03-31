#!/usr/bin/env python3
"""
enrich_schemes_free.py
======================
FREE Intelligence Engine — Zero paid APIs.

For every scheme it generates:
  • detailed_description   — expanded from existing fields via template logic
  • youtube_video_1        — "What is [scheme]?" YouTube search URL  (free)
  • youtube_video_2        — "How to apply [scheme]?" YouTube search URL (free)
  • youtube_label_1 / 2   — human-readable button labels

Input  : frontend/data/schemes_correct_383.json
Output : frontend/data/schemes_enriched_free.json

Run:
    python enrich_schemes_free.py
"""

import json
import re
from pathlib import Path
from urllib.parse import quote_plus

# ── Paths ────────────────────────────────────────────────────────────────────
INPUT_PATH  = Path("frontend/data/schemes_correct_383.json")
OUTPUT_PATH = Path("frontend/data/schemes_enriched_free.json")

# ── Field resolvers (mirror ai_scheme_server logic) ──────────────────────────

def pick(*keys, obj):
    for k in keys:
        v = str(obj.get(k, "") or "").strip()
        if v:
            return v
    return ""

def scheme_name(s):
    return pick("scheme_name", "Scheme_Name", "name", obj=s)

def scheme_desc(s):
    return pick("description", "Scheme_Description", "benefits_summary", obj=s)

def scheme_eligibility(s):
    return pick("eligibility", "Eligibility_Criteria", obj=s)

def scheme_sector(s):
    return pick("sector", "Target_Sector", "target_sector", obj=s)

def scheme_state(s):
    return pick("state", "State_Applicable", obj=s)

def scheme_ministry(s):
    return pick("ministry", "Ministry", "authority", obj=s)

def scheme_audience(s):
    return pick("target_audience", "Target_Audience", "audience", obj=s)

def scheme_process(s):
    return pick("application_process", "Application_Process", obj=s)

def scheme_funding(s):
    return pick("funding_type", "Funding_Type", obj=s)

# ── YouTube URL builder (100% free — YouTube search page) ────────────────────

def yt_url(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"

def build_youtube_links(name: str, state: str, ministry: str):
    context = "India"
    if state and state.lower() not in ("india", "all", "pan india", ""):
        context = state

    # Video 1: What is this scheme
    q1 = f"what is {name} scheme {context}"
    # Video 2: How to apply
    q2 = f"how to apply {name} scheme {context} {ministry}".strip()

    return {
        "youtube_video_1":  yt_url(q1),
        "youtube_label_1":  f"What is {name}?",
        "youtube_video_2":  yt_url(q2),
        "youtube_label_2":  f"How to apply for {name}",
    }

# ── Detailed description builder ─────────────────────────────────────────────

def build_detailed_description(s: dict) -> str:
    """
    Construct a rich paragraph from existing structured fields.
    Uses ZERO external API calls — purely concatenation + templates.
    """
    name      = scheme_name(s)
    desc      = scheme_desc(s)
    elig      = scheme_eligibility(s)
    sector    = scheme_sector(s)
    state     = scheme_state(s)
    ministry  = scheme_ministry(s)
    audience  = scheme_audience(s)
    process   = scheme_process(s)
    funding   = scheme_funding(s)

    parts = []

    # Core description
    if desc:
        parts.append(desc.strip())

    # Who can apply
    if elig and elig.lower() != desc.lower():
        # Clean up repetition
        elig_clean = re.sub(r'\s+', ' ', elig).strip()
        if len(elig_clean) > 30:
            parts.append(f"Eligibility: {elig_clean}")

    # Implementing authority
    authority_parts = []
    if ministry:
        authority_parts.append(f"implemented by {ministry}")
    if state and state.lower() not in ("india", "all states", "pan india", ""):
        authority_parts.append(f"applicable in {state}")
    elif sector:
        authority_parts.append(f"for the {sector} sector")
    if authority_parts:
        parts.append(f"This scheme is {', '.join(authority_parts)}.")

    # Audience
    if audience:
        parts.append(f"Target beneficiaries: {audience}.")

    # Application process
    if process and len(process) > 20:
        parts.append(f"Application process: {process}.")

    # Funding type
    if funding:
        parts.append(f"Support type: {funding}.")

    # Fallback
    if not parts:
        parts.append(
            f"{name} is a government scheme providing support to eligible "
            f"{'businesses and entrepreneurs' if not audience else audience} "
            f"{'across India' if not state else f'in {state}'}."
        )

    return " ".join(parts)

# ── Main pipeline ─────────────────────────────────────────────────────────────

def enrich(s: dict) -> dict:
    enriched = dict(s)  # shallow copy — keep all original fields

    name     = scheme_name(s)
    state    = scheme_state(s)
    ministry = scheme_ministry(s)

    # Detailed description
    enriched["detailed_description"] = build_detailed_description(s)

    # YouTube links (free)
    yt = build_youtube_links(name, state, ministry)
    enriched.update(yt)

    return enriched

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input not found: {INPUT_PATH}")

    with open(INPUT_PATH, encoding="utf-8") as f:
        schemes = json.load(f)

    print(f"Loaded {len(schemes)} schemes from {INPUT_PATH}")

    enriched = []
    for i, s in enumerate(schemes):
        try:
            enriched.append(enrich(s))
        except Exception as e:
            print(f"  ⚠ [{i}] {scheme_name(s)}: {e}")
            enriched.append(s)  # keep original on error

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print(f"✅ Enriched {len(enriched)} schemes → {OUTPUT_PATH}")
    print(f"   Sample: {enriched[0].get('scheme_name','?')}")
    print(f"   YT1: {enriched[0].get('youtube_video_1','?')[:80]}")
    print(f"   YT2: {enriched[0].get('youtube_video_2','?')[:80]}")
    print(f"   Desc: {enriched[0].get('detailed_description','?')[:100]}…")

if __name__ == "__main__":
    main()
