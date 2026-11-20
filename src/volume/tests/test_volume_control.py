import pytest

from src.common import MediaController
from src.volume import VolumeControl


class FakeController(MediaController):
    def __init__(self, fail=False):
        self.up_calls = 0
        self.down_calls = 0
        self.fail = fail

    def volume_up(self):
        if self.fail:
            raise RuntimeError("backend unavailable")
        self.up_calls += 1

    def volume_down(self):
        if self.fail:
            raise RuntimeError("backend unavailable")
        self.down_calls += 1

    def play(self): ...
    def pause(self): ...
    def resume(self): ...
    def next_track(self): ...
    def previous_track(self): ...


def test_increase_calls_backend_once_by_default():
    fake = FakeController()
    msg = VolumeControl(fake).increase()
    assert fake.up_calls == 1
    assert msg == "Volume increased"


def test_decrease_calls_backend_once_by_default():
    fake = FakeController()
    msg = VolumeControl(fake).decrease()
    assert fake.down_calls == 1
    assert msg == "Volume decreased"


def test_step_size_repeats_backend_calls():
    fake = FakeController()
    VolumeControl(fake, steps=3).increase()
    assert fake.up_calls == 3


def test_backend_error_does_not_crash():
    msg = VolumeControl(FakeController(fail=True)).increase()
    assert msg.startswith("Volume change failed")


class FailsAfter(FakeController):
    """Backend that succeeds `ok_calls` times and then raises."""

    def __init__(self, ok_calls):
        super().__init__()
        self.ok_calls = ok_calls

    def _check(self):
        if self.up_calls + self.down_calls >= self.ok_calls:
            raise RuntimeError("player closed")

    def volume_up(self):
        self._check()
        self.up_calls += 1

    def volume_down(self):
        self._check()
        self.down_calls += 1


def test_partial_failure_reports_applied_steps():
    fake = FailsAfter(ok_calls=2)

    msg = VolumeControl(fake, steps=5).increase()

    assert fake.up_calls == 2
    assert msg == "Volume change failed after 2 of 5 steps: player closed"


def test_partial_failure_is_reported_for_decrease_too():
    msg = VolumeControl(FailsAfter(ok_calls=1), steps=3).decrease()

    assert msg == "Volume change failed after 1 of 3 steps: player closed"


def test_failure_on_first_step_keeps_the_short_message():
    msg = VolumeControl(FailsAfter(ok_calls=0), steps=3).increase()

    assert msg == "Volume change failed: player closed"


@pytest.mark.parametrize("steps", [0, -1])
def test_invalid_steps_rejected(steps):
    with pytest.raises(ValueError):
        VolumeControl(FakeController(), steps=steps)
