from unittest.mock import MagicMock

from src.common import MediaController
from src.media_backend import OSMediaController
from src.media_backend.os_backend import (
    VK_MEDIA_NEXT_TRACK,
    VK_MEDIA_PLAY_PAUSE,
    VK_MEDIA_PREV_TRACK,
    VK_VOLUME_DOWN,
    VK_VOLUME_UP,
)


def test_implements_media_controller_interface():
    backend = OSMediaController(key_sender=lambda _: None)
    assert isinstance(backend, MediaController)


def test_volume_up_sends_correct_key():
    mock_sender = MagicMock()
    backend = OSMediaController(key_sender=mock_sender)

    backend.volume_up()
    mock_sender.assert_called_once_with(VK_VOLUME_UP)


def test_volume_down_sends_correct_key():
    mock_sender = MagicMock()
    backend = OSMediaController(key_sender=mock_sender)

    backend.volume_down()
    mock_sender.assert_called_once_with(VK_VOLUME_DOWN)


def test_play_pause_resume_send_play_pause_key():
    mock_sender = MagicMock()
    backend = OSMediaController(key_sender=mock_sender)

    backend.play()
    backend.pause()
    backend.resume()

    assert mock_sender.call_count == 3
    mock_sender.assert_called_with(VK_MEDIA_PLAY_PAUSE)


def test_next_track_sends_correct_key():
    mock_sender = MagicMock()
    backend = OSMediaController(key_sender=mock_sender)

    backend.next_track()
    mock_sender.assert_called_once_with(VK_MEDIA_NEXT_TRACK)


def test_previous_track_sends_correct_key():
    mock_sender = MagicMock()
    backend = OSMediaController(key_sender=mock_sender)

    backend.previous_track()
    mock_sender.assert_called_once_with(VK_MEDIA_PREV_TRACK)


def test_default_initializer_without_arguments():
    backend = OSMediaController()
    assert isinstance(backend, MediaController)
