from __future__ import annotations

from typing import Callable

import speech_recognition as sr


class VoiceInput:
    """Capture one microphone phrase and convert it to text (FR1)."""

    def __init__(
        self,
        recognizer: sr.Recognizer | None = None,
        microphone_factory: Callable[[], sr.Microphone] | None = None,
        *,
        listen_timeout: float = 5.0,
        phrase_time_limit: float = 5.0,
        on_listening: Callable[[], None] | None = None,
    ) -> None:
        if listen_timeout <= 0:
            raise ValueError("listen_timeout must be greater than 0")
        if phrase_time_limit <= 0:
            raise ValueError("phrase_time_limit must be greater than 0")

        self._recognizer = recognizer or sr.Recognizer()
        self._recognizer.operation_timeout = 5.0
        self._microphone_factory = microphone_factory or sr.Microphone
        self._listen_timeout = listen_timeout
        self._phrase_time_limit = phrase_time_limit
        self._on_listening = on_listening
        self.last_error: str | None = None

    def capture(self) -> str | None:
        """Return the recognized phrase, or None when no usable phrase exists."""
        self.last_error = None
        try:
            with self._microphone_factory() as source:
                if isinstance(source, sr.Microphone) and source.stream is None:
                    raise OSError("Microphone stream did not open")
                if self._on_listening is not None:
                    self._on_listening()
                audio = self._recognizer.listen(
                    source,
                    timeout=self._listen_timeout,
                    phrase_time_limit=self._phrase_time_limit,
                )
            text = self._recognizer.recognize_google(audio)
        except sr.WaitTimeoutError:
            self.last_error = (
                f"No speech detected within {self._listen_timeout:g} seconds. "
                "Check the microphone selection, input level, and speech threshold."
            )
            return None
        except sr.UnknownValueError:
            self.last_error = "Speech was captured but not understood. Speak clearly and try again."
            return None
        except sr.RequestError:
            self.last_error = "Speech service request failed. Check your internet connection."
            return None
        except (AttributeError, OSError):
            self.last_error = (
                "Audio input or recognition failed. Check the microphone and its driver."
            )
            return None

        text = text.strip()
        if not text:
            self.last_error = "Recognition returned no text. Please try again."
        return text or None
