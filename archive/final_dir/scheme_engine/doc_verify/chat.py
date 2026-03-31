from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import requests
from pydantic import BaseModel, Field, ValidationError


@dataclass
class SchemeChatService:
    provider: str
    model: str
    api_key: str
    base_url: str
    karios_ai_api_key: str = ""
    karios_ai_base_url: str = ""
    karios_ai_model: str = ""
    strict_live: bool = False
    timeout_seconds: float | None = 120
    ollama_models: list[str] | None = None

    def answer(
        self,
        *,
        query: str,
        language: str = "English",
        schemes: list[dict[str, Any]],
        profile: dict[str, Any],
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        candidates = _rank_schemes(query, schemes)[:6]
        provider = (self.provider or "").strip().lower()
        history = history or []

        try:
            if provider == "karios_ai":
                return self._answer_karios_ai(
                    query=query,
                    language=language,
                    profile=profile,
                    candidates=candidates,
                    history=history,
                )
            if provider == "lmstudio":
                return self._answer_openai_compatible(
                    query=query,
                    language=language,
                    profile=profile,
                    candidates=candidates,
                    history=history,
                    mode_name="lmstudio",
                    base_url=self.base_url,
                    model=self.model,
                    api_key=self.api_key,
                    require_api_key=False,
                )
        except Exception as exc:
            return {"mode": "error", "error": f"Live provider failed: {exc}"}

        return {"mode": "error", "error": "Supported live providers: gemini, lmstudio."}

    def _answer_karios_ai(
        self,
        *,
        query: str,
        language: str,
        profile: dict[str, Any],
        candidates: list[dict[str, Any]],
        history: list[dict[str, str]],
    ) -> dict[str, Any]:
        api_key = self.karios_ai_api_key or self.api_key
        model = self.karios_ai_model or self.model or "gemini-1.5-flash"
        base_url = self.karios_ai_base_url or self.base_url or "https://generativelanguage.googleapis.com/v1beta"
        if not api_key:
            return {"mode": "error", "error": "KARIOS AI API key is missing."}

        prompt = _build_prompt(
            query=query,
            language=language,
            profile=profile,
            candidates=candidates,
            history=history,
        )
        request_json = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "You are a government scheme application assistant. "
                                "Return ONLY a valid JSON object matching the required schema keys. "
                                "No markdown, no extra prose, no code fences.\n\n"
                                f"{prompt}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
            },
        }
        response = requests.post(
            f"{base_url.rstrip('/')}/models/{model}:generateContent?key={api_key}",
            headers={"Content-Type": "application/json"},
            json=request_json,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        raw_content = _extract_gemini_text(payload).strip()
        structured = _parse_or_coerce_structured(raw_content=raw_content)
        if not structured:
            return {"mode": "error", "error": "gemini response was not parseable."}

        result = {
            "answer": _clean_answer_text(structured.answer or structured.recommendation or structured.summary),
            "summary": structured.summary,
            "recommendation": structured.recommendation,
            "application_steps": structured.application_steps,
            "required_documents": structured.required_documents,
            "youtube_links": structured.youtube_links,
            "profile_alignment": structured.profile_alignment,
            "suggested_actions": structured.suggested_actions,
            "citations": structured.citations
            or [s.get("Scheme_ID") or s.get("Scheme_Name") for s in candidates],
            "mode": "karios_ai",
        }
        return _ensure_response_quality(
            query=query,
            result=result,
            candidates=candidates,
            profile=profile,
        )

    def _answer_openai_compatible(
        self,
        *,
        query: str,
        language: str,
        profile: dict[str, Any],
        candidates: list[dict[str, Any]],
        history: list[dict[str, str]],
        mode_name: str,
        base_url: str,
        model: str,
        api_key: str,
        require_api_key: bool,
    ) -> dict[str, Any]:
        if require_api_key and not api_key:
            return {"mode": "error", "error": f"{mode_name} API key is missing."}

        prompt = _build_prompt(
            query=query,
            language=language,
            profile=profile,
            candidates=candidates,
            history=history,
        )
        request_json = {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a government scheme application assistant. "
                        "Return ONLY a valid JSON object matching the required schema keys. "
                        "No markdown, no extra prose, no code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=request_json,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        raw_content = (
            payload.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        ).strip()
        structured = _parse_or_coerce_structured(raw_content=raw_content)
        if not structured:
            return {"mode": "error", "error": f"{mode_name} response was not parseable."}

        result = {
            "answer": _clean_answer_text(structured.answer or structured.recommendation or structured.summary),
            "summary": structured.summary,
            "recommendation": structured.recommendation,
            "application_steps": structured.application_steps,
            "required_documents": structured.required_documents,
            "youtube_links": structured.youtube_links,
            "profile_alignment": structured.profile_alignment,
            "suggested_actions": structured.suggested_actions,
            "citations": structured.citations
            or [s.get("Scheme_ID") or s.get("Scheme_Name") for s in candidates],
            "mode": mode_name,
        }
        return _ensure_response_quality(
            query=query,
            result=result,
            candidates=candidates,
            profile=profile,
        )

def _extract_gemini_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return ""
    parts: list[str] = []
    for candidate in candidates:
        content = candidate.get("content", {}) if isinstance(candidate, dict) else {}
        candidate_parts = content.get("parts", []) if isinstance(content, dict) else []
        if not isinstance(candidate_parts, list):
            continue
        for part in candidate_parts:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
    return "\n".join(parts).strip()


def _tokenize(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if len(token) > 2}


def _rank_schemes(query: str, schemes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_tokens = _tokenize(query)
    scored: list[tuple[int, dict[str, Any]]] = []
    for scheme in schemes:
        text = " ".join(
            str(scheme.get(key, ""))
            for key in (
                "Scheme_Name",
                "Scheme_Category",
                "Ministry",
                "State_Applicable",
                "Target_Sector",
                "Target_Audience",
                "Application_Process",
            )
        )
        score = len(query_tokens.intersection(_tokenize(text)))
        scored.append((score, scheme))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored if item[0] > 0] or schemes[:5]


def _query_intent(query: str) -> str:
    text = query.lower()
    has_document_context = any(
        x in text
        for x in (
            "document",
            "documents",
            "certificate",
            "proof",
            "gst",
            "pan",
            "udyam",
            "cin",
            "aadhaar",
            "aadhar",
            "invoice",
            "quotation",
            "bank statement",
        )
    )
    has_apply_words = any(
        x in text
        for x in (
            "how to apply",
            "step by step",
            "application process",
            "how do i apply",
        )
    )
    if has_document_context and has_apply_words:
        return "documents"
    if any(x in text for x in ("how to apply", "step by step", "application process", "how do i apply")):
        return "apply"
    if any(x in text for x in ("document", "documents", "required docs", "required document", "certificate", "proof")):
        return "documents"
    if any(x in text for x in ("eligible", "eligibility", "criteria", "who can apply")):
        return "eligibility"
    return "general"


def _scheme_url(scheme: dict[str, Any]) -> str:
    return (
        str(scheme.get("Website_URL") or "").strip()
        or str(scheme.get("Official_URL") or "").strip()
        or "Official portal URL not listed; check concerned ministry website."
    )


def _build_application_steps(scheme: dict[str, Any], profile: dict[str, Any]) -> list[str]:
    website = _scheme_url(scheme)
    scheme_name = str(scheme.get("Scheme_Name") or "selected scheme").strip()
    ministry = str(scheme.get("Ministry") or "concerned department").strip()
    state_applicable = str(scheme.get("State_Applicable") or "concerned state").strip()
    process = str(scheme.get("Application_Process") or "").strip()
    process_l = process.lower()
    is_online = "online" in process_l
    is_offline = "offline" in process_l

    click_step = (
        f"Click: Locate '{scheme_name}' under {ministry} schemes and open latest notification/guideline."
    )
    create_login_step = (
        "Create/Login: Register applicant account on the portal and complete KYC/profile setup."
        if is_online
        else f"Create/Login: Contact nodal office/DIC in {state_applicable} for application form and instructions."
    )
    fill2_step = (
        f"Fill section 2: Enter scheme-specific details for '{scheme_name}' including technical/financial information."
    )
    upload_step = (
        "Upload: Submit required documents in portal-prescribed format and size."
        if is_online
        else "Upload: Attach self-attested copies with application file as per office checklist."
    )
    submit_step = (
        "Submit: Final submit on portal with OTP/eSign and declaration."
        if is_online
        else "Submit: Submit signed application at designated office/counter and collect stamped acknowledgement."
    )
    track_step = (
        "Track: Use portal dashboard/reference ID to track status and respond to deficiency notices."
        if is_online and not is_offline
        else "Track: Follow up via portal/office using acknowledgement number and respond to clarifications."
    )

    return [
        f"Go to: {website}",
        click_step,
        create_login_step,
        (
            f"Select scheme: Choose the exact scheme and verify profile fit (Entity: {profile.get('entity_type') or 'N/A'}, "
            f"State: {profile.get('state') or 'N/A'}, Sector: {profile.get('sector') or 'N/A'})."
        ),
        "Fill section 1: Enterprise/profile details exactly as per registration records.",
        fill2_step,
        upload_step,
        "Review: Validate all entries and fix portal errors before final submit.",
        submit_step,
        "After submit: Download acknowledgement and save application/reference number.",
        track_step,
        f"Final outcome: On approval for '{scheme_name}', complete post-approval formalities (agreement/bank linkage/inspection/disbursal) from {ministry}.",
    ]


def _build_required_documents(scheme: dict[str, Any]) -> list[str]:
    context = " ".join(
        str(scheme.get(k, ""))
        for k in ("Scheme_Category", "Target_Audience", "Application_Process", "Scheme_Name")
    ).lower()
    docs = [
        "PAN of applicant/entity - Obtain from Income Tax PAN services (NSDL/UTIITSL) or existing PAN card copy.",
        "Entity constitution/registration proof - Proprietorship/Partnership/LLP/Company registration certificate from relevant authority.",
        "Address proof of business and applicant - Aadhaar, utility bill, rental/ownership proof as permitted by scheme rules.",
        "Bank account proof - Cancelled cheque or recent bank statement in enterprise name.",
    ]
    if any(tok in context for tok in ("msme", "startup", "industry")):
        docs.append("Udyam registration certificate (if applicable) - Download from official Udyam portal.")
    if any(tok in context for tok in ("subsidy", "incentive", "grant")):
        docs.extend(
            [
                "Project report / business proposal",
                "Vendor quotation or invoice for eligible expenditure",
                "Proof of payment and CA-certified cost statement (if required)",
            ]
        )
    docs.append("GST registration certificate (if GST-registered) - Generate/download from GST portal dashboard.")
    docs.append("Scheme-specific annexure/form from official portal - Download latest version from scheme page.")
    return list(dict.fromkeys([d for d in docs if d.strip()]))


def _build_youtube_links(scheme: dict[str, Any]) -> list[str]:
    for key in ("Youtube_Link", "YouTube_Link", "youtube_url", "video_url"):
        link = scheme.get(key)
        if isinstance(link, str) and link.strip():
            return [link.strip()]
    scheme_name = str(scheme.get("Scheme_Name") or "scheme").strip()
    query = requests.utils.quote(f"{scheme_name} how to apply")
    return [f"https://www.youtube.com/results?search_query={query}"]


def _fallback_answer(query: str, profile: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidates:
        return {
            "answer": "No matching scheme context is available.",
            "summary": "No matching scheme context is available.",
            "recommendation": "Refine scheme selection and ask again.",
            "application_steps": [],
            "required_documents": [],
            "youtube_links": [],
            "profile_alignment": "",
            "suggested_actions": ["Refine filters and select relevant schemes."],
            "citations": [],
            "mode": "fallback",
        }

    top = candidates[0]
    scheme_name = top.get("Scheme_Name", "Unknown Scheme")
    website = _scheme_url(top)
    application_steps = _build_application_steps(top, profile)
    required_documents = _build_required_documents(top)
    intent = _query_intent(query)

    if intent == "apply":
        answer = f"Step-by-step application flow for {scheme_name} prepared."
    elif intent == "documents":
        answer = f"Required documents checklist for {scheme_name} prepared."
    elif intent == "eligibility":
        answer = f"Eligibility guidance prepared for {scheme_name}."
    else:
        answer = (
            f"Best match: {scheme_name}. "
            f"Apply through official portal: {website}."
        )

    return {
        "answer": answer,
        "summary": f"Top matched scheme: {scheme_name}.",
        "recommendation": "Use official portal flow and keep required documents ready before submission.",
        "application_steps": application_steps,
        "required_documents": required_documents,
        "youtube_links": _build_youtube_links(top),
        "profile_alignment": (
            f"State={profile.get('state') or 'N/A'}, "
            f"Sector={profile.get('sector') or 'N/A'}, "
            f"Entity={profile.get('entity_type') or 'N/A'}"
        ),
        "suggested_actions": [
            "Confirm eligibility in official notification.",
            "Prepare all required documents before submission.",
            "Submit through official portal only.",
        ],
        "citations": [s.get("Scheme_ID") or s.get("Scheme_Name") for s in candidates],
        "mode": "fallback",
    }


def _build_prompt(
    *,
    query: str,
    language: str,
    profile: dict[str, Any],
    candidates: list[dict[str, Any]],
    history: list[dict[str, str]],
) -> str:
    intent = _query_intent(query)
    scheme_lines = [
        (
            f"- {s.get('Scheme_Name')} | Ministry: {s.get('Ministry')} | "
            f"Category: {s.get('Scheme_Category')} | State: {s.get('State_Applicable')} | "
            f"Sector: {s.get('Target_Sector')} | Process: {s.get('Application_Process')} | "
            f"Website: {_scheme_url(s)}"
        )
        for s in candidates
    ]
    history_lines = [f"{h.get('role', 'user')}: {h.get('content', '')}" for h in history[-6:]]

    instructions = [
        "Return JSON only with keys:",
        "answer, summary, recommendation, application_steps, required_documents, youtube_links, profile_alignment, suggested_actions, citations",
        f"Intent={intent}",
        "If intent=apply: provide exactly 12 detailed ordered steps from official website to final submission.",
        "For apply intent, each step must begin with one of these labels in order:",
        "Go to:, Click:, Create/Login:, Select scheme:, Fill section 1:, Fill section 2:, Upload:, Review:, Submit:, After submit:, Track:, Final outcome:",
        "Steps must be scheme-specific: reference selected scheme name, ministry, state applicability, and actual application mode (online/offline/hybrid).",
        "If intent=documents: provide detailed required document checklist only (include how to obtain each document).",
        "If intent=eligibility: keep concise profile alignment and suggested actions.",
        "If intent=general: answer the user's exact doubt in 'answer' with plain conversational text.",
        f"Respond in language: {language}. Keep same language across all fields.",
        "Avoid generic repeated templates; use scheme-specific wording from candidate context and conversation history.",
        "Do not include markdown.",
    ]

    return (
        f"User profile: {profile}\n"
        f"Candidate schemes:\n{chr(10).join(scheme_lines)}\n"
        f"Conversation history:\n{chr(10).join(history_lines)}\n"
        f"Current user question: {query}\n"
        f"{chr(10).join(instructions)}"
    )


class StructuredSchemeChat(BaseModel):
    answer: str = Field(default="")
    summary: str = Field(default="")
    recommendation: str = Field(default="")
    application_steps: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    youtube_links: list[str] = Field(default_factory=list)
    profile_alignment: str = Field(default="")
    suggested_actions: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)


def _parse_or_coerce_structured(*, raw_content: str) -> StructuredSchemeChat | None:
    text = (raw_content or "").strip()
    if not text:
        return None
    parsed = _parse_structured_output(text)
    if parsed:
        return parsed
    return _coerce_to_structured_output(raw_content=text)


def _parse_structured_output(raw_content: str) -> StructuredSchemeChat | None:
    try:
        return StructuredSchemeChat.model_validate(json.loads(raw_content))
    except (json.JSONDecodeError, ValidationError):
        pass

    start = raw_content.find("{")
    end = raw_content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return StructuredSchemeChat.model_validate(json.loads(raw_content[start : end + 1]))
    except (json.JSONDecodeError, ValidationError):
        return None


def _coerce_to_structured_output(*, raw_content: str) -> StructuredSchemeChat | None:
    lines = [line.strip() for line in raw_content.splitlines() if line.strip()]
    bullets = [
        line.strip("-* ").strip()
        for line in lines
        if line.startswith(("-", "*")) or re.match(r"^\d+[\)\.]?\s+", line)
    ]
    app_steps = [x for x in bullets if re.search(r"apply|portal|submit|form|step", x.lower())]
    req_docs = [x for x in bullets if re.search(r"document|certificate|proof|pan|gst|udyam|cin|invoice", x.lower())]
    yt_links = [x for x in lines if re.match(r"^https?://", x) and ("youtube.com" in x or "youtu.be" in x)]

    data = {
        "answer": lines[0] if lines else "Guidance generated.",
        "summary": lines[0] if lines else "Scheme guidance generated.",
        "recommendation": lines[1] if len(lines) > 1 else "Use official portal and complete required steps.",
        "application_steps": app_steps,
        "required_documents": req_docs,
        "youtube_links": yt_links,
        "profile_alignment": "",
        "suggested_actions": [],
        "citations": [],
    }
    try:
        return StructuredSchemeChat.model_validate(data)
    except ValidationError:
        return None


def _merge_unique(primary: list[str], secondary: list[str], limit: int) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in primary + secondary:
        value = str(item or "").strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(value)
        if len(merged) >= limit:
            break
    return merged


def _clean_answer_text(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r'^\s*"answer"\s*:\s*', "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*answer\s*:\s*", "", text, flags=re.IGNORECASE)
    text = text.strip().strip('"').strip()
    return text


def _normalize_apply_steps(steps: list[str]) -> list[str]:
    labels = [
        "Go to:",
        "Click:",
        "Create/Login:",
        "Select scheme:",
        "Fill section 1:",
        "Fill section 2:",
        "Upload:",
        "Review:",
        "Submit:",
        "After submit:",
        "Track:",
        "Final outcome:",
    ]
    normalized: list[str] = []
    for i, label in enumerate(labels):
        base = steps[i] if i < len(steps) else ""
        text = str(base or "").strip()
        if not text:
            text = f"{label} Follow the official instruction for this step."
        elif not text.lower().startswith(label.lower()):
            text = f"{label} {text}"
        normalized.append(text)
    return normalized


def _ensure_response_quality(
    *,
    query: str,
    result: dict[str, Any],
    candidates: list[dict[str, Any]] | None = None,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intent = _query_intent(query)
    steps = [str(x).strip() for x in result.get("application_steps", []) if str(x).strip()]
    docs = [str(x).strip() for x in result.get("required_documents", []) if str(x).strip()]
    top = (candidates or [None])[0]

    if intent == "apply":
        if not steps and isinstance(top, dict):
            steps = _build_application_steps(top, profile or {})
        result["application_steps"] = _normalize_apply_steps(_merge_unique(steps, [], limit=12))
        result["required_documents"] = []
        result["answer"] = result.get("recommendation") or "Step-by-step application flow prepared."
    elif intent == "documents":
        if not docs and isinstance(top, dict):
            docs = _build_required_documents(top)
        result["required_documents"] = _merge_unique(docs, [], limit=20)
        result["youtube_links"] = []
        result["application_steps"] = []
        result["answer"] = result.get("recommendation") or "Required documents checklist prepared."

    if not result.get("summary"):
        result["summary"] = "Scheme guidance generated."
    if not result.get("recommendation"):
        result["recommendation"] = "Proceed via official portal guidance."
    if not result.get("profile_alignment"):
        result["profile_alignment"] = ""
    if not result.get("suggested_actions"):
        result["suggested_actions"] = []
    if not result.get("citations"):
        result["citations"] = []
    return result

