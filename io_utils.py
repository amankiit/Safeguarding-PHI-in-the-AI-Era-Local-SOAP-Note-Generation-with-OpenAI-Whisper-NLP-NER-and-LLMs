import json
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
