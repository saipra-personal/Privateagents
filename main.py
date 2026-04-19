#!/usr/bin/env python3
"""
Voice to Text: Record voice → transcribe → save as text file.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def run_pipeline(
    audio_file: str | None = None,
    transcription_method: str = "google",
    record_duration: int | None = None,
    output_dir: str = "output",
) -> None:
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Step 1: Get transcription
    if audio_file:
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

    # Step 2: Save to text file
    txt_path = out / f"transcription_{timestamp}.txt"
    txt_path.write_text(transcription, encoding="utf-8")

    print(f"Done! Transcription saved to: {txt_path.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="Record your voice and save the transcription as a text file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Record from microphone (press Enter to stop)
  python main.py

  # Record for exactly 60 seconds
  python main.py --duration 60

  # Transcribe an existing audio file
  python main.py --audio my_recording.wav

  # Save output to a specific folder
  python main.py --output my_folder
        """,
    )
    parser.add_argument("--audio", "-a", help="Path to an existing audio file (WAV)")
    parser.add_argument(
        "--method",
        "-m",
        choices=["whisper", "google"],
        default="google",
        help="Speech recognition method (default: google)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        help="Record for N seconds (default: press Enter to stop)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="output",
        help="Folder to save the transcription (default: output/)",
    )

    args = parser.parse_args()

    run_pipeline(
        audio_file=args.audio,
        transcription_method=args.method,
        record_duration=args.duration,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
