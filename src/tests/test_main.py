import pytest

from src.common import Command, MediaController
from src.main import UNKNOWN_MESSAGE, Dispatcher, listen_once, run


class FakeController(MediaController):
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def _record(self, name):
        if self.fail:
            raise RuntimeError("backend unavailable")
        self.calls.append(name)

    def volume_up(self):
        self._record("volume_up")

    def volume_down(self):
        self._record("volume_down")

    def play(self):
        self._record("play")

    def pause(self):
        self._record("pause")

    def resume(self):
        self._record("resume")

    def next_track(self):
        self._record("next_track")

    def previous_track(self):
        self._record("previous_track")


class FakeVoice:
    def __init__(self, *texts):
        self._texts = list(texts)

    def capture(self):
        return self._texts.pop(0) if self._texts else None


@pytest.mark.parametrize(
    "text, expected_call",
    [
        ("volume up", "volume_up"),
        ("volume down", "volume_down"),
        ("play", "play"),
        ("pause", "pause"),
        ("resume", "resume"),
        ("next", "next_track"),
        ("previous", "previous_track"),
    ],
)
def test_command_reaches_backend(text, expected_call):
    controller = FakeController()
    Dispatcher(controller, volume_steps=1).handle_text(text)
    assert controller.calls == [expected_call]


def test_volume_steps_are_applied():
    controller = FakeController()
    Dispatcher(controller, volume_steps=3).handle_text("volume up")
    assert controller.calls == ["volume_up"] * 3


def test_unsupported_command_returns_message_and_does_nothing():
    controller = FakeController()
    assert Dispatcher(controller).handle_text("dance") == UNKNOWN_MESSAGE
    assert controller.calls == []


@pytest.mark.parametrize("text", [None, "", "   "])
def test_silence_is_ignored(text):
    controller = FakeController()
    assert Dispatcher(controller).handle_text(text) is None
    assert controller.calls == []


@pytest.mark.parametrize("command", list(Command))
def test_every_command_has_a_route(command):
    result = Dispatcher(FakeController()).handle_text(command.value)
    assert result is not None
    assert result != UNKNOWN_MESSAGE


def test_backend_failure_does_not_crash():
    result = Dispatcher(FakeController(fail=True)).handle_text("play")
    assert "failed" in result


def test_listen_once_reports_heard_text_and_result():
    outputs = []
    dispatcher = Dispatcher(FakeController())
    listen_once(FakeVoice("volume up"), dispatcher, output=outputs.append)
    assert outputs == ['Heard: "volume up"', "Volume increased"]


def test_listen_once_prints_nothing_on_silence():
    outputs = []
    listen_once(FakeVoice(), Dispatcher(FakeController()), output=outputs.append)
    assert outputs == []


def test_run_processes_phrases_until_stopped():
    controller = FakeController()
    stop_flags = iter([False, False, True])
    run(
        FakeVoice("play", "next"),
        Dispatcher(controller),
        output=lambda message: None,
        should_stop=lambda: next(stop_flags),
    )
    assert controller.calls == ["play", "next_track"]
