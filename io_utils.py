import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path


def print_output(transcript: str, soap_note: dict, print_transcript: bool) -> None:
    if print_transcript:
        print("\n=== Transcript ===\n")
        print(transcript)
    print("\n=== SOAP Note ===\n")
    for section in ["Subjective", "Objective", "Assessment", "Plan"]:
        print(f"{section}:\n{soap_note.get(section, '')}\n")


def save_output(audio_file: Path, transcript: str, soap_note: dict, output_file: Path) -> None:
    result = {
        "audio_file": str(audio_file),
        "transcript": transcript,
        "soap_note": soap_note,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def _soap_to_fhir_bundle(audio_file: Path, soap_note: dict, patient_id: str = "example-patient") -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def section(title: str, text: str) -> dict:
        safe_text = escape(str(text or ""))
        return {
            "title": title,
            "text": {
                "status": "generated",
                "div": f"<div xmlns='http://www.w3.org/1999/xhtml'><p>{safe_text}</p></div>",
            },
        }

    composition = {
        "resourceType": "Composition",
        "id": "soap-composition",
        "status": "final",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "34133-9",
                    "display": "Summarization of episode note",
                }
            ]
        },
        "subject": {"reference": f"Patient/{patient_id}"},
        "date": now,
        "title": f"SOAP Clinical Note for {audio_file.name}",
        "section": [
            section("Subjective", soap_note.get("Subjective", "")),
            section("Objective", soap_note.get("Objective", "")),
            section("Assessment", soap_note.get("Assessment", "")),
            section("Plan", soap_note.get("Plan", "")),
        ],
    }

    patient = {
        "resourceType": "Patient",
        "id": patient_id,
    }

    return {
        "resourceType": "Bundle",
        "type": "document",
        "timestamp": now,
        "entry": [
            {"fullUrl": f"urn:uuid:{composition['id']}", "resource": composition},
            {"fullUrl": f"urn:uuid:{patient_id}", "resource": patient},
        ],
    }


def save_fhir_output(audio_file: Path, soap_note: dict, output_file: Path) -> None:
    fhir_bundle = _soap_to_fhir_bundle(audio_file, soap_note)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(fhir_bundle, f, ensure_ascii=False, indent=2)
