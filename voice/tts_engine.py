"""
voice/tts_engine.py

Offline text-to-speech using pyttsx3 (wraps SAPI5 on Windows, NSSpeech on
macOS, espeak on Linux - no internet/API key required). Import is lazy and
failures are non-fatal: if pyttsx3 or a native voice isn't available, ISHA
just runs silently with TTS disabled rather than crashing.
"""

from typing import Optional

from core.logger import get_logger

log = get_logger("voice.tts")


class TTSEngine:
    def __init__(self, rate: int = 175, voice_index: int = 0):
        self.rate = rate
        self.voice_index = voice_index
        self._engine = None
        self._available = False
        self._init_engine()

    def _init_engine(self) -> None:
        try:
            import pyttsx3
        except ImportError:
            log.info("pyttsx3 not installed - TTS disabled. (pip install pyttsx3 to enable)")
            return

        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            voices = self._engine.getProperty("voices")
            if voices and 0 <= self.voice_index < len(voices):
                self._engine.setProperty("voice", voices[self.voice_index].id)
            self._available = True
        except Exception as e:
            log.warning("TTS engine failed to initialize: %s", e)
            self._engine = None
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def speak(self, text: str) -> bool:
        """Speak text synchronously. Returns False silently if TTS is unavailable."""
        if not self._available or not text.strip():
            return False
        try:
            self._engine.say(text)
            self._engine.runAndWait()
            return True
        except Exception as e:
            log.warning("TTS speak() failed: %s", e)
            return False
