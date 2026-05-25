import json
from pathlib import Path

from config import SOAP_KEYS
from fhir.composition import soap_to_fhir_bundle


def print_output(transcript: str, soap_note: dict, print_transcript: bool) -> None:
    if print_transcript:
        print("\n=== Transcript ===\n")
        print(transcript)
    print("\n=== SOAP Note ===\n")
    for section in SOAP_KEYS:
        print(f"{section}:\n{soap_note.get(section, '')}\n")


def _write_json(data: dict, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_output(audio_file: Path, transcript: str, soap_note: dict, output_file: Path) -> None:
    result = {
        "audio_file": str(audio_file),
        "transcript": transcript,
        "soap_note": soap_note,
    }
    _write_json(result, output_file)


def save_fhir_output(audio_file: Path, soap_note: dict, output_file: Path) -> None:
    fhir_bundle = soap_to_fhir_bundle(audio_file, soap_note)
    _write_json(fhir_bundle, output_file)
