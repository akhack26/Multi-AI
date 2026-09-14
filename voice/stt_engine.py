"""
voice/stt_engine.py

Optional speech-to-text. Disabled by default (config: voice.stt_enabled).
Uses the `speech_recognition` package, which can run fully offline with a
local recognizer (e.g. Vosk/Whisper backends) or fall back to whatever
recognizer is installed. Kept intentionally minimal and lazily imported so
a base ISHA install has zero hard audio-stack dependencies.
"""

from typing import Optional

from core.logger import get_logger

log = get_logger("voice.stt")


class STTEngine:
    def __init__(self):
        self._available = False
        self._sr = None
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import speech_recognition as sr
            self._sr = sr
            self._available = True
        except ImportError:
            log.info(
                "speech_recognition not installed - STT disabled. "
                "(pip install SpeechRecognition, plus a mic backend like PyAudio, to enable)"
            )

    def is_available(self) -> bool:
        return self._available

    def listen_once(self, timeout: int = 5) -> Optional[str]:
        """
        Capture one utterance from the default microphone and transcribe it.
        Returns None (never raises) if unavailable or nothing could be
        transcribed - callers should treat that as "fall back to typed input".
        """
        if not self._available:
            return None
        try:
            recognizer = self._sr.Recognizer()
            with self._sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=timeout)
            # Uses the recognizer's configured engine; swap to an offline
            # engine (e.g. recognize_vosk) here if you install one.
            return recognizer.recognize_google(audio)
        except Exception as e:
            log.info("STT capture/transcription failed or timed out: %s", e)
            return None
