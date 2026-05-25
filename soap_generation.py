import json
import re
from pathlib import Path
from typing import Dict

from ollama import generate

from config import SYSTEM_PROMPT


def load_prompt_template(prompt_file: Path) -> str:
    if not prompt_file.exists():
        raise RuntimeError(f"Prompt file not found: {prompt_file}")
    content = prompt_file.read_text(encoding="utf-8").strip()
    if "{transcript}" not in content:
        raise RuntimeError("Prompt file must include '{transcript}' placeholder.")
    return content


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
    prompt = (
        "You are editing a SOAP note for spelling and grammar only.\n"
        "Do not add or remove clinical facts.\n"
        "Preserve placeholders like [REDACTED_NAME] exactly.\n"
        "Return valid JSON only with keys Subjective, Objective, Assessment, Plan.\n\n"
        f"SOAP JSON:\n{json.dumps(soap_note, ensure_ascii=False)}"
    )
    try:
        response = generate(model=model, prompt=prompt, format="json")
        polished_raw = response["response"].strip()
        polished = parse_soap_json(polished_raw)
        return polished
    except Exception:
        return soap_note
