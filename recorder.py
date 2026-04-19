"""Voice recording and transcription module."""

import os
import tempfile
import wave
import threading
import time
import sounddevice as sd
import scipy.io.wavfile as wavfile
import numpy as np
import speech_recognition as sr


SAMPLE_RATE = 16000
CHANNELS = 1


def record_audio(duration: int | None = None, silence_timeout: float = 3.0) -> str:
    """
    Record audio from microphone. If duration is None, records until silence.
    Returns path to saved WAV file.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()

    if duration:
        print(f"Recording for {duration} seconds... Press Ctrl+C to stop early.")
        frames = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
        )
        sd.wait()
    else:
        print("Recording... Speak now. Will stop after silence.")
        print("Press Enter to stop recording manually.")
        frames = []
        stop_event = threading.Event()

        def _record():
            chunk_size = int(SAMPLE_RATE * 0.5)  # 0.5s chunks
            silent_chunks = 0
            max_silent = int(silence_timeout / 0.5)

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16") as stream:
                while not stop_event.is_set():
                    chunk, _ = stream.read(chunk_size)
                    frames.append(chunk.copy())
                    rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
                    if rms < 300:
                        silent_chunks += 1
                    else:
                        silent_chunks = 0
                    if silent_chunks >= max_silent and len(frames) > 4:
                        print("\nSilence detected, stopping recording.")
                        stop_event.set()

        record_thread = threading.Thread(target=_record, daemon=True)
        record_thread.start()

        try:
            input()  # Wait for Enter key
        except EOFError:
            pass
        stop_event.set()
        record_thread.join(timeout=2)

        if not frames:
            raise RuntimeError("No audio recorded.")
        frames = np.concatenate(frames, axis=0)

    wavfile.write(tmp.name, SAMPLE_RATE, frames)
    print(f"Audio saved to: {tmp.name}")
    return tmp.name


def transcribe_whisper(audio_path: str, model_size: str = "base") -> str:
    """Transcribe audio using OpenAI Whisper (local, no API key required)."""
    try:
        import whisper
        print(f"Loading Whisper '{model_size}' model...")
        model = whisper.load_model(model_size)
        print("Transcribing...")
        result = model.transcribe(audio_path)
        return result["text"].strip()
    except ImportError:
        raise ImportError("openai-whisper not installed. Run: pip install openai-whisper")


def transcribe_google(audio_path: str) -> str:
    """Transcribe audio using Google Speech Recognition (free, requires internet)."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    print("Transcribing via Google Speech Recognition...")
    return recognizer.recognize_google(audio)


def transcribe(audio_path: str, method: str = "whisper") -> str:
    """Transcribe audio file. method: 'whisper' or 'google'."""
    if method == "google":
        return transcribe_google(audio_path)
    return transcribe_whisper(audio_path)
