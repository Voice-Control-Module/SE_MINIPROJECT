import sys
from typing import Callable

from src.common import MediaController

# Virtual Key Codes for Windows Multimedia Keys
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3


def _default_windows_key_sender(key_code: int) -> None:
    """Simulate a multimedia key press and release on Windows."""
    import ctypes

    # key down followed by key up (KEYEVENTF_KEYUP = 2)
    ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)


class OSMediaController(MediaController):
    """Platform media adapter implementing MediaController via OS key events."""

    def __init__(self, key_sender: Callable[[int], None] | None = None) -> None:
        if key_sender is not None:
            self._send_key = key_sender
        elif sys.platform == "win32":
            self._send_key = _default_windows_key_sender
        else:
            # Fallback handler for headless or non-Windows CI environments
            self._send_key = lambda key: None

    def volume_up(self) -> None:
        self._send_key(VK_VOLUME_UP)

    def volume_down(self) -> None:
        self._send_key(VK_VOLUME_DOWN)

    def play(self) -> None:
        self._send_key(VK_MEDIA_PLAY_PAUSE)

    def pause(self) -> None:
        self._send_key(VK_MEDIA_PLAY_PAUSE)

    def resume(self) -> None:
        self._send_key(VK_MEDIA_PLAY_PAUSE)

    def next_track(self) -> None:
        self._send_key(VK_MEDIA_NEXT_TRACK)

    def previous_track(self) -> None:
        self._send_key(VK_MEDIA_PREV_TRACK)
