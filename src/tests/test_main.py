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


def test_backend_can_recover_after_failure():
    controller = FakeController(fail=True)
    dispatcher = Dispatcher(controller)
    assert "failed" in dispatcher.handle_text("play")
    controller.fail = False
    assert dispatcher.handle_text("play") == "Playback started"


def test_startup_reports_unavailable_backend(monkeypatch, capsys):
    from src.main import main

    def unavailable():
        raise RuntimeError("No supported backend")

    monkeypatch.setattr("src.main.OSMediaController", unavailable)
    assert main([]) == 1
    assert "Cannot start" in capsys.readouterr().out


def test_listen_once_reports_result_without_disclosing_transcript():
    outputs = []
    dispatcher = Dispatcher(FakeController())
    listen_once(FakeVoice("volume up"), dispatcher, output=outputs.append)
    assert outputs == ["Volume increased"]


def test_listen_once_reports_unavailable_input_without_a_transcript():
    outputs = []
    listen_once(FakeVoice(), Dispatcher(FakeController()), output=outputs.append)
    assert outputs == ["No command heard or recognition unavailable. Try again."]


def test_main_handles_keyboard_interrupt(monkeypatch, capsys):
    from src.main import main

    monkeypatch.setattr("src.main.OSMediaController", FakeController)
    monkeypatch.setattr("src.main.VoiceInput", lambda **kwargs: FakeVoice())

    def interrupted(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr("src.main.run", interrupted)
    assert main([]) == 0
    assert "Goodbye" in capsys.readouterr().out


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


@pytest.mark.parametrize("arguments", [
    ["--listen-timeout", "0"], ["--listen-timeout", "nan"],
    ["--energy-threshold", "-1"], ["--energy-threshold", "inf"],
])
def test_main_rejects_invalid_audio_settings(arguments):
    from src.main import main

    with pytest.raises(SystemExit) as error:
        main(arguments)
    assert error.value.code == 2


def test_main_lists_devices_without_starting_media_backend(monkeypatch, capsys):
    from src.main import main
    from unittest.mock import MagicMock

    monkeypatch.setattr("src.main.sr.Microphone.list_microphone_names", lambda: ["pulse"])
    backend = MagicMock()
    monkeypatch.setattr("src.main.OSMediaController", backend)
    assert main(["--list-microphones"]) == 0
    backend.assert_not_called()
    assert "0: pulse" in capsys.readouterr().out


@pytest.mark.parametrize("device", ["pulse", "1"])
def test_main_configures_selected_input_and_sensitivity(monkeypatch, capsys, device):
    from src.main import main
    from unittest.mock import MagicMock

    microphone = MagicMock()
    microphone.list_microphone_names.return_value = ["speaker", "pulse"]
    monkeypatch.setattr("src.main.sr.Microphone", microphone)
    monkeypatch.setattr("src.main.OSMediaController", FakeController)
    configured = {}

    def voice_factory(**kwargs):
        configured.update(kwargs)
        kwargs["microphone_factory"]()
        kwargs["on_listening"]()
        return FakeVoice()

    monkeypatch.setattr("src.main.VoiceInput", voice_factory)
    monkeypatch.setattr("src.main.run", lambda *args: None)
    assert main(["--microphone", device, "--listen-timeout", "10",
                 "--energy-threshold", "150"]) == 0
    microphone.assert_called_once_with(device_index=1)
    assert configured["listen_timeout"] == 10
    assert configured["recognizer"].energy_threshold == 150
    assert configured["recognizer"].dynamic_energy_threshold is False
    output = capsys.readouterr().out
    assert "Selected microphone: pulse" in output
    assert "Listening... speak now." in output


@pytest.mark.parametrize("device", ["missing", "9"])
def test_main_handles_invalid_microphone(monkeypatch, capsys, device):
    from src.main import main

    monkeypatch.setattr("src.main.sr.Microphone.list_microphone_names", lambda: ["pulse"])
    assert main(["--microphone", device]) == 1
    assert "Cannot start" in capsys.readouterr().out


def test_listen_once_reports_specific_capture_failure_without_transcript():
    voice = FakeVoice()
    voice.last_error = "Speech service request failed. Check your internet connection."
    outputs = []
    listen_once(voice, Dispatcher(FakeController()), output=outputs.append)
    assert outputs == [voice.last_error]
