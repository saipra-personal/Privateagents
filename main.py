#!/usr/bin/env python3
"""
Voice to PowerPoint: Record voice → transcribe → summarize → generate slides.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def save_transcription(text: str, output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    txt_path = output_dir / f"transcription_{timestamp}.txt"
    txt_path.write_text(text, encoding="utf-8")
    return txt_path


def run_pipeline(
    audio_file: str | None = None,
    text_file: str | None = None,
    transcription_method: str = "whisper",
    record_duration: int | None = None,
    output_dir: str = "output",
    api_key: str | None = None,
) -> None:
    from summarizer import summarize
    from slide_generator import generate_pptx

    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Get transcription text
    if text_file:
        print(f"Reading transcription from: {text_file}")
        transcription = Path(text_file).read_text(encoding="utf-8")
    elif audio_file:
        from recorder import transcribe
        print(f"Transcribing audio file: {audio_file}")
        transcription = transcribe(audio_file, method=transcription_method)
    else:
        from recorder import record_audio, transcribe
        audio_path = record_audio(duration=record_duration)
        transcription = transcribe(audio_path, method=transcription_method)

    print("\n--- TRANSCRIPTION ---")
    print(transcription)
    print("---------------------\n")

    # Step 2: Save transcription
    txt_path = save_transcription(transcription, out)
    print(f"Transcription saved: {txt_path}")

    # Step 3: Summarize with Claude
    presentation_data = summarize(transcription, api_key=api_key)

    # Save structured data as JSON
    json_path = out / f"presentation_{timestamp}.json"
    json_path.write_text(json.dumps(presentation_data, indent=2), encoding="utf-8")
    print(f"Presentation structure saved: {json_path}")

    # Step 4: Generate PowerPoint
    pptx_path = str(out / f"presentation_{timestamp}.pptx")
    generate_pptx(presentation_data, pptx_path)
    print(f"\nPowerPoint saved: {pptx_path}")
    print(f"\nDone! Files in: {out.resolve()}")
    print(f"  Transcription : {txt_path.name}")
    print(f"  Slide data    : {json_path.name}")
    print(f"  PowerPoint    : {Path(pptx_path).name}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert voice input to a summarised PowerPoint presentation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record from microphone (stop with Enter key)
  python main.py

  # Record for 60 seconds
  python main.py --duration 60

  # Use existing audio file
  python main.py --audio my_recording.wav

  # Use existing text file (skip recording/transcription)
  python main.py --text my_notes.txt

  # Use Google Speech Recognition instead of Whisper
  python main.py --method google

  # Specify output directory
  python main.py --output my_slides
        """,
    )
    parser.add_argument("--audio", "-a", help="Path to an existing audio file (WAV/MP3)")
    parser.add_argument("--text", "-t", help="Path to an existing text/transcription file")
    parser.add_argument(
        "--method",
        "-m",
        choices=["whisper", "google"],
        default="whisper",
        help="Speech recognition method (default: whisper)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        help="Record for N seconds (default: auto-stop on silence)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output",
        help="Output directory (default: output/)",
    )
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")

    args = parser.parse_args()

    if not args.api_key and not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: Anthropic API key required.")
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key flag.")
        print("Get your key at: https://console.anthropic.com/")
        sys.exit(1)

    run_pipeline(
        audio_file=args.audio,
        text_file=args.text,
        transcription_method=args.method,
        record_duration=args.duration,
        output_dir=args.output,
        api_key=args.api_key,
    )


if __name__ == "__main__":
    main()
