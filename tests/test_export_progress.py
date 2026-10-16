"""Export feedback uses observed work and never claims premature success."""

from io import StringIO

import pytest

from faceless_champ import ExportProgress


class Terminal(StringIO):
    def isatty(self):
        return True


def test_progress_estimates_remaining_work_and_waits_for_encoder(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("faceless_champ.progress.time.monotonic", lambda: now[0])
    stream = Terminal()
    with ExportProgress(stream=stream) as progress:
        progress(0, 100)
        assert "ETA --:--" in stream.getvalue()
        now[0] += 10
        progress(25, 100)
        assert "25.0% 25/100 frames | elapsed 00:10 | ETA 00:30" in stream.getvalue()
        now[0] += 30
        progress(100, 100)
        assert "Finalizing" in stream.getvalue() and "Exported" not in stream.getvalue()
        now[0] += 2
    assert "Exported [########################] 100.0% 100/100 frames | elapsed 00:42 | ETA 00:00" in stream.getvalue()
    assert stream.getvalue().endswith("\n")


def test_encoder_failure_after_last_frame_never_reports_success():
    stream = Terminal()
    with pytest.raises(RuntimeError, match="encoder failed"), ExportProgress(stream=stream) as progress:
        progress(0, 2)
        progress(2, 2)
        raise RuntimeError("encoder failed")
    assert "Export stopped" in stream.getvalue() and "Exported" not in stream.getvalue()
    assert stream.getvalue().endswith("\n")


def test_redirected_progress_is_throttled_and_has_no_terminal_control_codes(monkeypatch):
    now = [0.0]
    monkeypatch.setattr("faceless_champ.progress.time.monotonic", lambda: now[0])
    stream = StringIO()
    with ExportProgress(stream=stream) as progress:
        progress(0, 100)
        for completed in range(1, 100):
            now[0] += 0.01
            progress(completed, 100)
        assert len(stream.getvalue().splitlines()) == 1
        now[0] = 6
        progress(99, 100)
        progress(100, 100)
    assert len(stream.getvalue().splitlines()) == 4
    assert "\r" not in stream.getvalue() and "ETA 00:01" in stream.getvalue()


def test_progress_handles_hours_and_cancellation(monkeypatch):
    now = [0.0]
    monkeypatch.setattr("faceless_champ.progress.time.monotonic", lambda: now[0])
    stream = Terminal()
    with pytest.raises(KeyboardInterrupt), ExportProgress(stream=stream) as progress:
        progress(0, 2)
        now[0] = 3661
        progress(1, 2)
        raise KeyboardInterrupt
    assert "elapsed 1:01:01 | ETA 1:01:01" in stream.getvalue()
    assert "Export stopped" in stream.getvalue() and "Exported" not in stream.getvalue()
