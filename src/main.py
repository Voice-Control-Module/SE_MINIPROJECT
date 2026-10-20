from typing import Callable, Optional

from src.command_parser import parse_command
from src.common import Command, MediaController
from src.media_backend import OSMediaController
from src.playback import PlaybackControl
from src.track import TrackControl
from src.voice_input import VoiceInput
from src.volume import VolumeControl

UNKNOWN_MESSAGE = "Command not recognized"
DEFAULT_VOLUME_STEPS = 5


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
        return
    output(f'Heard: "{text}"')
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


def main() -> None:
    dispatcher = Dispatcher(OSMediaController())
    voice_input = VoiceInput()
    print("Voice assistant ready. Say a command (Ctrl+C to quit).")
    try:
        run(voice_input, dispatcher)
    except KeyboardInterrupt:
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
