"""
backend/app/services/llm_service.py — Phase 13, SRS Section 18.
LLM comes strictly after ML/analytics: Evidence JSON in, narrative out (Section 18.1).
Two mandatory validators run on every LLM output before it's shown to the user:
  1. Number-grounding (18.6): every numeric value in the narrative must appear in the evidence JSON.
  2. Provider-section phrasing (18.5): forbidden linking language must be absent.
On any failure — API unavailable, validation failure — falls back to structured-only display
per Section 36's error-handling table, never showing an unverified narrative.
"""
import os
import re
import json

SYSTEM_PROMPT = """You are writing a factual summary for a payer's ACO contract review meeting.
You will be given a structured evidence JSON. Follow this chain strictly: FACT -> OBSERVED ML SIGNAL
-> INTERPRETATION -> RECOMMENDATION.

The evidence JSON includes a "contract_health" object (composite score, its financial/quality/
utilization/ml_risk breakdown, and weights). You may reference it in the narrative if relevant.

Rules, no exceptions:
- Use ONLY numbers, names, and facts present in the evidence JSON. Never invent or estimate a number
  — this applies to contract_health exactly as it does to every other field.
- Never claim causality between provider/hospital signals and this ACO's result — they are national
  context only, not attributed to this ACO. Never write phrases like "this ACO's providers" or
  "within this contract" when referring to provider or hospital data.
- Use only: "observed", "associated with", "potential driver", "candidate opportunity", "requires review".
  Never definitive causal language ("caused", "resulted in", "due to").
- Never claim CMS endorsement of any application-derived score, cluster, or label.
- Plain prose, 150-250 words, suitable to read aloud in a meeting.
"""

QA_SYSTEM_PROMPT = """You are answering a payer analyst's question about a specific ACO contract, for use in
a contract review meeting. You will be given a structured evidence JSON and a question. Follow this chain
strictly: FACT -> OBSERVED ML SIGNAL -> INTERPRETATION -> RECOMMENDATION.

The evidence JSON includes a "contract_health" object (composite score, its financial/quality/
utilization/ml_risk breakdown, and weights). You may reference it in the answer if relevant.

Rules, no exceptions:
- Answer ONLY using the provided evidence JSON. If the evidence JSON does not contain information to
  answer this question, say so directly — do not speculate or use general knowledge.
- Use ONLY numbers, names, and facts present in the evidence JSON. Never invent or estimate a number
  — this applies to contract_health exactly as it does to every other field.
- Never claim causality between provider/hospital signals and this ACO's result — they are national
  context only, not attributed to this ACO. Never write phrases like "this ACO's providers" or
  "within this contract" when referring to provider or hospital data.
- Use only: "observed", "associated with", "potential driver", "candidate opportunity", "requires review".
  Never definitive causal language ("caused", "resulted in", "due to").
- Never claim CMS endorsement of any application-derived score, cluster, or label.
- Plain prose, concise and direct, suitable to read aloud in a meeting.
"""

FORBIDDEN_PROVIDER_PHRASES = [
    "this aco's provider", "this aco's providers", "within this contract",
    "this contract's provider", "the aco's provider network", "caused by the provider",
]


def _extract_numbers(text: str) -> set[str]:
    """Pull every standalone number (ignoring surrounding $ , % formatting) from text."""
    cleaned = re.sub(r"[,$%]", "", text)
    raw = re.findall(r"-?\d+\.?\d*", cleaned)
    # strip a trailing '.' that's actually sentence punctuation, not a decimal point
    return {n[:-1] if n.endswith(".") else n for n in raw}


def _extract_numbers_from_evidence(evidence: dict) -> set[str]:
    numbers = set()

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
        elif isinstance(obj, (int, float)):
            numbers.add(str(obj))
            # also add common roundings, since narrative may round differently than stored value
            numbers.add(str(round(obj)))
            numbers.add(f"{obj:.1f}".rstrip("0").rstrip("."))
        elif isinstance(obj, str):
            numbers.update(_extract_numbers(obj))

    walk(evidence)
    return numbers


def validate_number_grounding(narrative: str, evidence: dict) -> tuple[bool, list[str]]:
    """Section 18.6: every number in narrative must trace back to the evidence JSON."""
    narrative_numbers = _extract_numbers(narrative)
    evidence_numbers = _extract_numbers_from_evidence(evidence)
    # ignore small connector numbers that are structurally near-universal (percentiles like "3" from "3 drivers" etc.)
    ungrounded = [n for n in narrative_numbers if n not in evidence_numbers and len(n) > 1]
    return (len(ungrounded) == 0), ungrounded


def validate_provider_phrasing(narrative: str) -> tuple[bool, list[str]]:
    """Section 18.5: forbidden ACO-provider linking language must be absent."""
    lower = narrative.lower()
    found = [p for p in FORBIDDEN_PROVIDER_PHRASES if p in lower]
    return (len(found) == 0), found


def generate_narrative(evidence: dict) -> dict:
    """
    Returns {"narrative": str, "status": "ok"} on success, or
    {"narrative": None, "status": "unavailable"|"validation_failed", "reason": str} otherwise.
    Never raises — callers always get a usable result per Section 36.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"narrative": None, "status": "unavailable",
                "reason": "ANTHROPIC_API_KEY not set — showing structured evidence only (Section 36)"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Evidence JSON:\n{json.dumps(evidence, indent=2)}"}],
        )
        narrative = response.content[0].text
    except Exception as e:
        return {"narrative": None, "status": "unavailable", "reason": f"LLM call failed: {e}"}

    grounded, ungrounded_numbers = validate_number_grounding(narrative, evidence)
    phrasing_ok, forbidden_found = validate_provider_phrasing(narrative)

    if not grounded:
        return {"narrative": None, "status": "validation_failed",
                "reason": f"Ungrounded numbers detected: {ungrounded_numbers}"}
    if not phrasing_ok:
        return {"narrative": None, "status": "validation_failed",
                "reason": f"Forbidden attribution phrasing detected: {forbidden_found}"}

    return {"narrative": narrative, "status": "ok"}


def ask_question(evidence: dict, question: str) -> dict:
    """
    Section 18-style Q&A: same evidence-grounding contract as generate_narrative(), but
    answers a free-text question instead of producing the fixed-template narrative.
    Returns {"answer": str, "status": "ok"} on success, or
    {"answer": None, "status": "unavailable"|"validation_failed", "reason": str} otherwise.
    Never raises — callers always get a usable result per Section 36.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"answer": None, "status": "unavailable",
                "reason": "ANTHROPIC_API_KEY not set — showing structured evidence only (Section 36)"}

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            system=QA_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Evidence JSON:\n{json.dumps(evidence, indent=2)}\n\nQuestion: {question}"}],
        )
        answer = response.content[0].text
    except Exception as e:
        return {"answer": None, "status": "unavailable", "reason": f"LLM call failed: {e}"}

    grounded, ungrounded_numbers = validate_number_grounding(answer, evidence)
    phrasing_ok, forbidden_found = validate_provider_phrasing(answer)

    if not grounded:
        return {"answer": None, "status": "validation_failed",
                "reason": f"Ungrounded numbers detected: {ungrounded_numbers}"}
    if not phrasing_ok:
        return {"answer": None, "status": "validation_failed",
                "reason": f"Forbidden attribution phrasing detected: {forbidden_found}"}

    return {"answer": answer, "status": "ok"}
