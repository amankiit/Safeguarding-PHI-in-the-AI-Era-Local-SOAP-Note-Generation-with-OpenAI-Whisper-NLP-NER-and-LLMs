import json
import re
from typing import Dict

from ollama import generate

from config import SOAP_POLISH_PROMPT_TEMPLATE, SYSTEM_PROMPT


def call_ollama(transcript: str, model: str, prompt_template: str) -> str:
    prompt = prompt_template.format(transcript=transcript)
    response = generate(
        model=model,
        prompt=prompt,
        system=SYSTEM_PROMPT,
        format="json",
    )
    content = response["response"].strip()
    if not content:
        raise RuntimeError("Ollama returned an empty response.")
    return content


def cleanup_transcript_text(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"\s+([,.;:?!])", r"\1", cleaned)
    cleaned = re.sub(r"([,.;:?!])([^\s])", r"\1 \2", cleaned)
    cleaned = re.sub(r"\b(uh|um|hmm)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def parse_soap_json(raw_text: str) -> dict:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if not match:
            raise RuntimeError("Could not parse SOAP note JSON from Llama output.")
        parsed = json.loads(match.group(0))

    expected_keys = ["Subjective", "Objective", "Assessment", "Plan"]
    soap = {}
    for key in expected_keys:
        value = parsed.get(key, "")
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        soap[key] = str(value).strip()
    return soap


def polish_soap_note(soap_note: Dict[str, str], model: str) -> Dict[str, str]:
    prompt = SOAP_POLISH_PROMPT_TEMPLATE.format(
        soap_json=json.dumps(soap_note, ensure_ascii=False)
    )
    try:
        response = generate(model=model, prompt=prompt, format="json")
        polished_raw = response["response"].strip()
        polished = parse_soap_json(polished_raw)
        return polished
    except Exception:
        return soap_note
