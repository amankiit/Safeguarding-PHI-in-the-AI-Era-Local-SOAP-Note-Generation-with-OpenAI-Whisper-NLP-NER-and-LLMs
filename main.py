#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

from config import SOAP_PROMPT_TEMPLATE
from io_utils import print_output, save_fhir_output, save_output
from phi import redact_phi
from soap_generation import call_ollama, cleanup_transcript_text, parse_soap_json, polish_soap_note
from transcription import check_ffmpeg, transcribe_audio



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transcribe medical dictation audio locally and generate a SOAP note.")
    parser.add_argument("audio_file", nargs="?", default="data/audio.mp3", help="Path to input audio file.")
    parser.add_argument("--output", default="output.json", help="Path to output JSON file.")
    parser.add_argument(
        "--whisper-model",
        default=os.getenv("WHISPER_MODEL", "base"),
        help="Local Whisper model size: tiny, base, small, medium, large, turbo.",
    )
    parser.add_argument("--ollama-model", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), help="Ollama model name.")
    parser.add_argument(
        "--no-redact-phi",
        action="store_true",
        help="Disable PHI redaction before SOAP generation/output (not recommended).",
    )
    parser.add_argument(
        "--print-transcript",
        action="store_true",
        help="Print transcript to stdout (disabled by default to reduce PHI exposure).",
    )
    return parser.parse_args()



def main() -> int:
    args = parse_args()
    audio_path = Path(args.audio_file)
    output_path = Path(args.output)
    fhir_output_path = output_path.with_name(f"{output_path.stem}.fhir.json")

    if not audio_path.exists():
        print(f"Error: audio file not found: {audio_path}", file=sys.stderr)
        return 1

    try:
        check_ffmpeg()
        transcript = transcribe_audio(audio_path, args.whisper_model)
        cleaned_transcript = cleanup_transcript_text(transcript)
        processed_transcript = redact_phi(cleaned_transcript) if not args.no_redact_phi else cleaned_transcript
        raw_soap = call_ollama(processed_transcript, args.ollama_model, SOAP_PROMPT_TEMPLATE)
        soap_note = parse_soap_json(raw_soap)
        soap_note = polish_soap_note(soap_note, args.ollama_model)
        print_output(processed_transcript, soap_note, args.print_transcript)
        save_output(audio_path, processed_transcript, soap_note, output_path)
        save_fhir_output(audio_path, soap_note, fhir_output_path)
        print(f"Saved JSON output to: {output_path}")
        print(f"Saved FHIR output to: {fhir_output_path}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
