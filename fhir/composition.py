from datetime import datetime, timezone
from html import escape
from pathlib import Path
from uuid import uuid4

from config import SOAP_KEYS


def soap_to_fhir_bundle(audio_file: Path, soap_note: dict, patient_id: str = "example-patient") -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    composition_uuid = str(uuid4())
    patient_uuid = str(uuid4())

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
        "id": composition_uuid,
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
        "section": [section(key, soap_note.get(key, "")) for key in SOAP_KEYS],
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
            {"fullUrl": f"urn:uuid:{composition_uuid}", "resource": composition},
            {"fullUrl": f"urn:uuid:{patient_uuid}", "resource": patient},
        ],
    }
