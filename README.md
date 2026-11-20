# Voice Assistant for Multimedia Controls

A Python command-line assistant for Volume Up, Volume Down, Play, Pause, Resume,
Next, and Previous. Unsupported commands cause no media action.

## Setup

Use Python 3.12 (recommended) or 3.14. From the repository root:

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux, or
`.venv\Scripts\Activate.ps1` in Windows PowerShell. Then:

```bash
python -m pip install -r requirements-dev.txt
```

For a real microphone, also install:

```bash
python -m pip install -r requirements-audio.txt
```

On Debian/Ubuntu, building PyAudio may require `portaudio19-dev`, `python3-dev`,
and a compiler installed through your system package manager. Enable microphone
access in OS privacy settings. Recognition uses Google's online speech service:
audio leaves the device for recognition. This project does not intentionally
save recordings or transcripts, and the CLI prints outcomes rather than speech.
Provider processing/retention is outside the local application's guarantee.

## Platform prerequisites

- **Windows:** Volume and track actions use multimedia keys. Play/pause/resume
  use explicit `WM_APPCOMMAND` requests to the foreground application. Focus a
  compatible media-player window before speaking. Unsupported or unresponsive
  targets report failure. Real player compatibility requires manual testing.
- **Linux desktop:** Install `playerctl` through your package manager and open an
  MPRIS-compatible player in the same desktop/D-Bus session. For example, use VLC
  with a playlist. `playerctl --list-all` should list it. Volume changes the
  selected player's volume by five percentage points per default step, subject
  to that player's implementation.
- **Other platforms:** Startup fails with an explicit unsupported-platform error.

Run the read-only prerequisite check, then start the application:

```bash
python scripts/preflight.py
python -m src.main
```

Say one command at a time. Press Ctrl+C to quit. Aliases include Increase Volume,
Decrease Volume, Next Track, and Previous Track. Backend success means the
request was accepted; the application does not independently read playback state.

## Troubleshooting voice input

On Linux, PortAudio may print ALSA/JACK probing messages for unused devices.
Use the application's listening prompt and specific retry reason to identify
whether input opening, speech detection, or the recognition service failed.
No audio or transcript is included in these status messages.

```bash
python -m src.main --list-microphones
python -m src.main --microphone pulse --listen-timeout 10 --energy-threshold 150
```

`--microphone` accepts an exact device name or its listed index; select an input,
not a speaker/monitor. `pulse` uses the desktop audio service where available.
Wait for **Listening... speak now.** before speaking. A timeout means speech did
not cross the detection threshold; an unintelligible result means audio was
captured; a service failure indicates the recognition request failed. A hardware
stream that did not open is reported as an audio failure rather than asserted.

The optional energy threshold sets a fixed speech-detection threshold: lower
values are more sensitive, and background media/noise can trigger capture. Tune
it for the microphone and room. The default adaptive recognizer behavior and
five-second speech-start wait remain unchanged when no options are supplied.
These options need a real microphone test; passing mocked tests alone does not
establish physical recognition success.

## Verification and reports

```bash
python scripts/run_checks.py
python scripts/run_checks.py --audit
```

The second command also audits runtime, development, and optional audio dependencies against vulnerability advisories and requires
internet access. Both commands run Flake8, Bandit, pytest, and branch coverage.
Scanner errors and test/check failures produce a nonzero exit status. Test files
are excluded from production coverage. Coverage gates require at least 90% for
combined coverage, statement coverage, and branch coverage.

- `reports/checks.json`: gate results.
- `reports/pytest.xml`: test results.
- `reports/coverage.json` and `coverage.xml`: measured coverage.
- `reports/bandit.json`: source security findings and scan errors.
- `reports/audit.json`: dependency advisory results when `--audit` is used.
- `htmlcov/index.html`: browsable annotated coverage report.
- `reports/preflight.json`: local hardware/tool prerequisites.

GitHub Actions runs the same checks for Windows/Linux and Python 3.12/3.14 on
pull requests and pushes to `main`, and uploads reports. Hosted execution occurs
after the workflow is pushed. No automatic desktop deployment is configured.
Direct dependencies are pinned; transitive versions are resolved at installation
and should be reviewed when preparing a release.

## Architecture

```text
Microphone → VoiceInput/STT → Parser → Dispatcher
                                    → Volume / Playback / Track
                                    → MediaController → OS backend
```

`src/common/` defines the shared command enum and media-controller contract.
Feature tests inject fake recognizers/controllers and need no real microphone,
network, or active player. Native Windows calls and Linux subprocess interactions
are tested with mocks. These tests do not replace a physical system demonstration.

## Team workflow

- Branch from current `main`, using `feature/<name>` or `fix/<name>`.
- Link each PR to its Jira story and obtain another member's review.
- Run quality gates before merging and inspect CI artifacts.
- Update requirements, RTM, and tests when behavior changes.

## Documentation

- [Requirements and work allocation](REQUIREMENTS.md)
- [Software Requirements Specification and RTM](docs/SRS.md)
- [Architecture and design](docs/SAD.md)
- [Test plan](docs/Test_Plan.md)
- [Validation results and physical demo checklist](docs/VALIDATION.md)
