from typing import Callable, Optional
import argparse
from functools import partial
import math
import sys
import time

import speech_recognition as sr

from src.command_parser import parse_command
from src.common import Command, MediaController
from src.media_backend import OSMediaController
from src.playback import PlaybackControl
from src.track import TrackControl
from src.voice_input import VoiceInput
from src.volume import VolumeControl

UNKNOWN_MESSAGE = "Command not recognized"
DEFAULT_VOLUME_STEPS = 1


class Dispatcher:
    """Routes recognized text to the matching feature module (FR2 to FR5)."""

    def __init__(
        self, controller: MediaController, volume_steps: int = DEFAULT_VOLUME_STEPS
    ) -> None:
        volume = VolumeControl(controller, steps=volume_steps)
        playback = PlaybackControl(controller)
        track = TrackControl(controller)
        self._routes: dict[Command, Callable[[], str]] = {
            Command.VOLUME_UP: volume.increase,
            Command.VOLUME_DOWN: volume.decrease,
            Command.PLAY: playback.play,
            Command.PAUSE: playback.pause,
            Command.RESUME: playback.resume,
            Command.NEXT: track.next,
            Command.PREVIOUS: track.previous,
        }

    def handle_text(self, text: Optional[str]) -> Optional[str]:
        """Return a result message, or None when there was nothing to act on."""
        if text is None or not text.strip():
            return None
        command = parse_command(text)
        if command is None:
            return UNKNOWN_MESSAGE
        return self._routes[command]()


def listen_once(
    voice_input: VoiceInput,
    dispatcher: Dispatcher,
    output: Callable[[str], None] = print,
) -> None:
    """Capture one phrase, act on it and report what happened."""
    text = voice_input.capture()
    if text is None:
        output(
            getattr(voice_input, "last_error", None)
            or "No command heard or recognition unavailable. Try again."
        )
        return
    result = dispatcher.handle_text(text)
    if result:
        output(result)


def run(
    voice_input: VoiceInput,
    dispatcher: Dispatcher,
    output: Callable[[str], None] = print,
    should_stop: Callable[[], bool] = lambda: False,
) -> None:
    while not should_stop():
        listen_once(voice_input, dispatcher, output)
        time.sleep(0.1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Voice assistant for multimedia controls")
    parser.add_argument("--list-microphones", action="store_true", help="List audio device names")
    parser.add_argument("--microphone", help="Input device index or exact name, e.g. pulse")
    parser.add_argument(
        "--listen-timeout", type=float, default=5.0, help="Wait for speech in seconds"
    )
    parser.add_argument(
        "--energy-threshold", type=float, help="Speech sensitivity; try 150 if quiet"
    )
    args = parser.parse_args(argv)
    for value in (args.listen_timeout, args.energy_threshold):
        if value is not None and (not math.isfinite(value) or value <= 0):
            parser.error("Timeout and energy threshold must be finite numbers greater than zero")

    try:
        microphone_factory = None
        if args.list_microphones or args.microphone is not None:
            names = sr.Microphone.list_microphone_names()
            if args.list_microphones:
                for index, name in enumerate(names):
                    print(f"{index}: {name}")
                return 0
            if args.microphone.isdecimal():
                index = int(args.microphone)
            else:
                if args.microphone not in names:
                    raise ValueError(
                        "Unknown microphone. Use --list-microphones to choose an input"
                    )
                index = names.index(args.microphone)
            if index >= len(names):
                raise ValueError("Microphone index is outside the listed device range")
            microphone_factory = partial(sr.Microphone, device_index=index)
            print(f"Selected microphone: {names[index]}")
        dispatcher = Dispatcher(OSMediaController())
    except (RuntimeError, ValueError, AttributeError, OSError) as exc:
        print(f"Cannot start voice assistant: {exc}")
        return 1
    recognizer = sr.Recognizer()
    if args.energy_threshold is not None:
        recognizer.energy_threshold = args.energy_threshold
        recognizer.dynamic_energy_threshold = False
    voice_input = VoiceInput(
        recognizer=recognizer,
        microphone_factory=microphone_factory,
        listen_timeout=args.listen_timeout,
        on_listening=lambda: print("Listening... speak now.", flush=True),
    )
    print("Voice assistant ready. Say a command (Ctrl+C to quit).")
    try:
        run(voice_input, dispatcher)
    except KeyboardInterrupt:
        print("\nGoodbye.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
