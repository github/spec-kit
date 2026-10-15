"""Bounded subprocess capture and the captured ``dispatch_command`` contract."""

from __future__ import annotations

import signal
import subprocess
import sys
import threading
import time

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations import _capture
from specify_cli.integrations._capture import (
    DEFAULT_CAPTURE_MAX_BYTES,
    CapturedProcess,
    cancel_captures,
    run_captured,
)


def _python(source: str, *args: str) -> list[str]:
    return [sys.executable, "-u", "-c", source, *args]


# Writes to the heartbeat file every 0.1s until it is killed.
_HEARTBEAT = (
    "import sys, time\n"
    "while True:\n"
    "    with open(sys.argv[1], 'a') as f: f.write('.')\n"
    "    time.sleep(0.1)\n"
)


def _spawn_descendant(heartbeat, then: str) -> list[str]:
    """Return a CLI that starts a heartbeat descendant, then runs *then*.

    The descendant inherits stdout and stderr, so it also holds the pipes.
    """
    return _python(
        "import subprocess, sys, time\n"
        "subprocess.Popen([sys.executable, '-c', sys.argv[1], sys.argv[2]])\n"
        "while not __import__('os').path.exists(sys.argv[2]): time.sleep(0.05)\n"
        "print('started')\n" + then,
        _HEARTBEAT,
        str(heartbeat),
    )


def _assert_stopped(heartbeat) -> None:
    """Assert the heartbeat descendant is dead and no reader is left running."""
    time.sleep(0.5)
    size = heartbeat.stat().st_size
    time.sleep(1)
    assert heartbeat.stat().st_size == size, "descendant still running"
    assert not [
        thread
        for thread in threading.enumerate()
        if thread.name.endswith("(_drain)")
    ], "reader threads still running"


class TestRunCaptured:
    def test_captures_both_streams_and_exit_code(self):
        result = run_captured(
            _python(
                "import sys; print('out'); sys.stderr.write('err'); sys.exit(3)"
            )
        )
        assert result == CapturedProcess(exit_code=3, stdout="out\n", stderr="err")

    def test_default_limit_is_one_mebibyte(self):
        assert DEFAULT_CAPTURE_MAX_BYTES == 1024 * 1024

    def test_finite_limit_truncates_only_the_stream_that_exceeds_it(self):
        # 3 MB is far beyond any pipe buffer: the process only exits 0 if the
        # capped stream keeps being drained after the limit is reached.
        result = run_captured(
            _python(
                "import sys; sys.stdout.write('a' * 3_000_000); "
                "sys.stderr.write('e' * 10)"
            ),
            max_bytes=1000,
            timeout=60,
        )
        assert result.exit_code == 0
        assert result.stdout == "a" * 1000
        assert result.stdout_truncated is True
        assert result.stderr == "e" * 10
        assert result.stderr_truncated is False
        assert result.timed_out is False

    def test_output_exactly_at_the_limit_is_not_truncated(self):
        result = run_captured(
            _python("import sys; sys.stdout.write('a' * 64)"), max_bytes=64
        )
        assert result.stdout == "a" * 64
        assert result.stdout_truncated is False

    def test_unlimited_capture_retains_everything_without_flags(self):
        result = run_captured(
            _python("import sys; sys.stdout.write('a' * 3_000_000)"),
            max_bytes=-1,
            timeout=60,
        )
        assert len(result.stdout) == 3_000_000
        assert result.stdout_truncated is False
        assert result.stderr_truncated is False

    def test_limit_counts_raw_bytes_and_drops_a_split_character(self):
        # Two 3-byte characters with a 4-byte limit: the second is cut after
        # its first byte and dropped, not turned into a replacement character.
        result = run_captured(
            _python("import sys; sys.stdout.buffer.write('€€'.encode('utf-8'))"),
            max_bytes=4,
        )
        assert result.stdout == "€"
        assert result.stdout_truncated is True

    def test_invalid_utf8_is_replaced(self):
        result = run_captured(
            _python(r"import sys; sys.stdout.buffer.write(b'ok\xff\xfeend')")
        )
        assert result.stdout == "ok��end"
        assert result.stdout_truncated is False

    def test_complete_output_ending_mid_character_is_replaced_not_dropped(self):
        result = run_captured(
            _python("import sys; sys.stdout.buffer.write('€'.encode('utf-8')[:2])")
        )
        assert result.stdout == "�"

    def test_line_endings_are_normalised(self):
        result = run_captured(
            _python(r"import sys; sys.stdout.buffer.write(b'a\r\nb\rc\n')")
        )
        assert result.stdout == "a\nb\nc\n"

    def test_timeout_keeps_partial_output_and_is_not_size_truncation(self):
        started = time.monotonic()
        result = run_captured(
            _python("import time; print('partial'); time.sleep(60)"),
            timeout=1,
            max_bytes=-1,
        )
        assert time.monotonic() - started < 30
        assert result.timed_out is True
        assert result.exit_code == -1
        assert result.stdout == "partial\n"
        assert result.stdout_truncated is False
        assert result.interrupted is False

    def test_interrupt_kills_the_process_and_keeps_partial_output(
        self, monkeypatch
    ):
        class InterruptedOnce(subprocess.Popen):
            def wait(self, timeout=None):
                if not getattr(self, "_interrupt_raised", False):
                    self._interrupt_raised = True
                    # Let the child write before the simulated Ctrl+C.
                    time.sleep(1)
                    raise KeyboardInterrupt
                return super().wait(timeout)

        monkeypatch.setattr(_capture.subprocess, "Popen", InterruptedOnce)
        started = time.monotonic()
        result = run_captured(
            _python("import time; print('partial'); time.sleep(60)")
        )
        assert time.monotonic() - started < 30
        assert result.interrupted is True
        assert result.exit_code == 130
        assert result.stdout == "partial\n"
        assert result.timed_out is False

    def test_timeout_kills_descendants_and_stops_readers(self, tmp_path):
        heartbeat = tmp_path / "heartbeat"
        result = run_captured(
            _spawn_descendant(heartbeat, "time.sleep(60)"), timeout=5
        )
        assert result.timed_out is True
        assert result.stdout == "started\n"
        _assert_stopped(heartbeat)

    def test_descendant_holding_the_pipes_after_exit_is_killed(self, tmp_path):
        """The CLI exits, but its descendant keeps the pipes open."""
        heartbeat = tmp_path / "heartbeat"
        started = time.monotonic()
        result = run_captured(_spawn_descendant(heartbeat, ""), timeout=5)
        assert time.monotonic() - started < 30
        assert result.timed_out is True
        assert result.stdout == "started\n"
        _assert_stopped(heartbeat)

    def test_interrupt_kills_descendants_and_stops_readers(
        self, tmp_path, monkeypatch
    ):
        class InterruptedOnce(subprocess.Popen):
            def wait(self, timeout=None):
                if not getattr(self, "_interrupt_raised", False):
                    self._interrupt_raised = True
                    while not heartbeat.exists():
                        time.sleep(0.05)
                    raise KeyboardInterrupt
                return super().wait(timeout)

        heartbeat = tmp_path / "heartbeat"
        monkeypatch.setattr(_capture.subprocess, "Popen", InterruptedOnce)
        result = run_captured(_spawn_descendant(heartbeat, "time.sleep(60)"))
        assert result.interrupted is True
        assert result.exit_code == 130
        _assert_stopped(heartbeat)

    def test_interrupt_while_starting_the_readers_kills_descendants(
        self, tmp_path, monkeypatch
    ):
        class InterruptedStart(threading.Thread):
            def start(self):
                # Interrupt once the CLI is running and has a descendant.
                while not heartbeat.exists():
                    time.sleep(0.05)
                raise KeyboardInterrupt

        heartbeat = tmp_path / "heartbeat"
        monkeypatch.setattr(_capture.threading, "Thread", InterruptedStart)
        result = run_captured(_spawn_descendant(heartbeat, "time.sleep(60)"))
        assert result.interrupted is True
        assert result.exit_code == 130
        _assert_stopped(heartbeat)

    def test_interrupt_during_process_setup_is_reported_not_raised(
        self, monkeypatch
    ):
        class InterruptedSetup:
            def __init__(self, args, cwd):
                raise KeyboardInterrupt

        monkeypatch.setattr(_capture, "_ProcessTree", InterruptedSetup)
        result = run_captured(_python("pass"))
        assert result == CapturedProcess(
            exit_code=130, stdout="", stderr="", interrupted=True
        )

    def test_interrupt_right_after_the_process_starts_kills_it(self, monkeypatch):
        """Ctrl+C after Popen returns, before cleanup is set up, still kills."""
        spawned: list[subprocess.Popen] = []

        class InterruptedAfterSpawn(subprocess.Popen):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                spawned.append(self)
                signal.raise_signal(signal.SIGINT)

        monkeypatch.setattr(_capture.subprocess, "Popen", InterruptedAfterSpawn)
        started = time.monotonic()
        result = run_captured(_python("import time; time.sleep(60)"))
        assert time.monotonic() - started < 30
        assert result.interrupted is True
        assert result.exit_code == 130
        (proc,) = spawned
        assert proc.returncode is not None, "the CLI was left running"
        assert signal.getsignal(signal.SIGINT) is signal.default_int_handler

    def test_completed_process_is_not_killed(self, monkeypatch):
        def fail(self):
            raise AssertionError("a completed process must not be killed")

        monkeypatch.setattr(_capture._ProcessTree, "kill", fail)
        result = run_captured(_python("print('done')"), timeout=30)
        assert result == CapturedProcess(exit_code=0, stdout="done\n", stderr="")

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows job objects")
    def test_windows_cli_does_not_run_before_it_is_in_the_job(
        self, tmp_path, monkeypatch
    ):
        """The CLI starts suspended, so it cannot spawn outside the job."""
        marker = tmp_path / "ran"
        start_in_job = _capture._start_in_job
        ran_before_job: list[bool] = []

        def observe(proc):
            # A running CLI would create the marker well within this delay.
            time.sleep(1)
            ran_before_job.append(marker.exists())
            return start_in_job(proc)

        monkeypatch.setattr(_capture, "_start_in_job", observe)
        result = run_captured(
            _python(
                "import sys; open(sys.argv[1], 'w').close(); print('ran')",
                str(marker),
            ),
            timeout=60,
        )
        assert ran_before_job == [False]
        assert result.stdout == "ran\n"
        assert marker.exists()

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows job objects")
    def test_windows_interrupt_after_resume_kills_the_job(
        self, tmp_path, monkeypatch
    ):
        """Setup interrupted after the CLI was resumed still fails closed."""
        resume_threads = _capture._resume_threads

        def resume_then_interrupt(pid):
            resume_threads(pid)
            while not heartbeat.exists():
                time.sleep(0.05)
            raise KeyboardInterrupt

        heartbeat = tmp_path / "heartbeat"
        monkeypatch.setattr(_capture, "_resume_threads", resume_then_interrupt)
        result = run_captured(_spawn_descendant(heartbeat, "time.sleep(60)"))
        assert result.interrupted is True
        assert result.exit_code == 130
        _assert_stopped(heartbeat)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows job objects")
    def test_windows_cli_never_runs_without_a_job(self, tmp_path, monkeypatch):
        def fail(proc):
            raise OSError("job assignment failed")

        marker = tmp_path / "ran"
        monkeypatch.setattr(_capture, "_start_in_job", fail)
        with pytest.raises(OSError, match="job assignment failed"):
            run_captured(
                _python("import sys; open(sys.argv[1], 'w').close()", str(marker))
            )
        time.sleep(1)
        assert not marker.exists()

    @pytest.mark.parametrize("max_bytes", [0, -2, True, False, 1.5, "10", None])
    def test_invalid_limit_is_rejected_before_starting_a_process(
        self, max_bytes, monkeypatch
    ):
        def fail(*args, **kwargs):
            raise AssertionError("process must not start")

        monkeypatch.setattr(_capture.subprocess, "Popen", fail)
        with pytest.raises(ValueError, match="positive integer or -1"):
            run_captured(_python("pass"), max_bytes=max_bytes)

    def test_missing_executable_raises_oserror(self, tmp_path):
        with pytest.raises(OSError):
            run_captured([str(tmp_path / "no-such-cli")])


class TestDispatchCommandCapture:
    """``output_json`` and ``capture_max_bytes`` on ``dispatch_command``."""

    @pytest.fixture
    def claude(self, monkeypatch):
        impl = get_integration("claude")
        monkeypatch.setattr(
            type(impl),
            "build_exec_args",
            lambda self, prompt, *, output_json=True, **kwargs: _python(
                "import sys; print(sys.argv[1], sys.argv[2])",
                "json" if output_json else "text",
                prompt,
            ),
        )
        return impl

    def test_bounded_capture_returns_text_and_completeness_fields(self, claude):
        result = claude.dispatch_command(
            "speckit.plan",
            stream=False,
            output_json=False,
            capture_max_bytes=1024,
            timeout=60,
        )
        assert result == {
            "exit_code": 0,
            "stdout": "text /speckit-plan\n",
            "stderr": "",
            "stdout_truncated": False,
            "stderr_truncated": False,
            "timed_out": False,
            "interrupted": False,
        }

    def test_existing_captured_callers_keep_structured_output(self, claude):
        """``stream=False`` alone still requests JSON and returns three keys."""
        result = claude.dispatch_command("speckit.plan", stream=False, timeout=60)
        assert result == {
            "exit_code": 0,
            "stdout": "json /speckit-plan\n",
            "stderr": "",
        }

    def test_existing_captured_callers_still_raise_on_timeout(self, monkeypatch):
        impl = get_integration("claude")
        monkeypatch.setattr(
            type(impl),
            "build_exec_args",
            lambda self, prompt, **kwargs: _python("import time; time.sleep(60)"),
        )
        with pytest.raises(subprocess.TimeoutExpired):
            impl.dispatch_command("speckit.plan", stream=False, timeout=1)

    def test_bounded_capture_reports_timeout_instead_of_raising(self, monkeypatch):
        impl = get_integration("claude")
        monkeypatch.setattr(
            type(impl),
            "build_exec_args",
            lambda self, prompt, **kwargs: _python(
                "import time; print('partial'); time.sleep(60)"
            ),
        )
        result = impl.dispatch_command(
            "speckit.plan", stream=False, capture_max_bytes=-1, timeout=1
        )
        assert result["timed_out"] is True
        assert result["exit_code"] == -1
        assert result["stdout"] == "partial\n"

    def test_streaming_dispatch_still_requests_text(self, claude, capfd):
        result = claude.dispatch_command("speckit.plan")
        assert result == {"exit_code": 0, "stdout": "", "stderr": ""}
        printed = capfd.readouterr().out.replace("\r\n", "\n")
        assert printed == "text /speckit-plan\n"

    def test_capture_limit_with_streaming_is_rejected(self, claude):
        with pytest.raises(ValueError, match="requires stream=False"):
            claude.dispatch_command("speckit.plan", capture_max_bytes=1024)


class TestCopilotDispatchCapture:
    """Copilot overrides ``dispatch_command`` and builds its own argv."""

    @pytest.fixture
    def recorded(self, monkeypatch):
        from specify_cli.integrations import copilot as copilot_module

        calls: list[tuple[list[str], dict]] = []

        def fake_run_captured(args, **kwargs):
            calls.append((list(args), kwargs))
            return CapturedProcess(exit_code=0, stdout="text", stderr="")

        def fake_run(args, **kwargs):
            calls.append((list(args), kwargs))
            return subprocess.CompletedProcess(args, 0, stdout="{}", stderr="")

        monkeypatch.setattr(copilot_module, "run_captured", fake_run_captured)
        monkeypatch.setattr("subprocess.run", fake_run)
        return calls

    def test_bounded_text_capture_omits_json_format(self, recorded):
        result = get_integration("copilot").dispatch_command(
            "speckit.plan",
            stream=False,
            output_json=False,
            capture_max_bytes=2048,
            timeout=7,
        )
        (args, kwargs), = recorded
        assert "--output-format" not in args
        assert kwargs["max_bytes"] == 2048
        assert kwargs["timeout"] == 7
        assert result["stdout"] == "text"
        assert result["stdout_truncated"] is False

    def test_existing_captured_callers_keep_json_format(self, recorded):
        result = get_integration("copilot").dispatch_command(
            "speckit.plan", stream=False
        )
        (args, kwargs), = recorded
        assert args[args.index("--output-format") + 1] == "json"
        assert kwargs["capture_output"] is True
        assert result == {"exit_code": 0, "stdout": "{}", "stderr": ""}

    def test_streaming_omits_json_format(self, recorded):
        get_integration("copilot").dispatch_command("speckit.plan")
        (args, kwargs), = recorded
        assert "--output-format" not in args
        assert "capture_output" not in kwargs

    def test_capture_limit_with_streaming_is_rejected(self, recorded):
        with pytest.raises(ValueError, match="requires stream=False"):
            get_integration("copilot").dispatch_command(
                "speckit.plan", capture_max_bytes=1024
            )
        assert recorded == []


class TestCancelCaptures:
    """Interrupting captures that run in worker threads."""

    @staticmethod
    def _in_thread(args):
        results: list[CapturedProcess] = []
        worker = threading.Thread(
            target=lambda: results.append(run_captured(args, timeout=60))
        )
        worker.start()
        return worker, results

    def test_running_capture_is_killed_and_reports_interrupted(self, tmp_path):
        heartbeat = tmp_path / "heartbeat"
        worker, results = self._in_thread(
            _spawn_descendant(heartbeat, "time.sleep(60)")
        )
        while not heartbeat.exists():
            time.sleep(0.05)
        started = time.monotonic()
        with cancel_captures():
            worker.join(30)
        assert not worker.is_alive()
        assert time.monotonic() - started < 30
        (result,) = results
        assert result.interrupted is True
        assert result.timed_out is False
        assert result.exit_code == 130
        _assert_stopped(heartbeat)

    def test_capture_started_while_cancelling_is_killed(self, tmp_path):
        with cancel_captures():
            worker, results = self._in_thread(
                _python("import time; time.sleep(60)")
            )
            worker.join(30)
        assert not worker.is_alive()
        (result,) = results
        assert result.interrupted is True

    def test_captures_after_the_block_run_normally(self):
        with cancel_captures():
            pass
        result = run_captured(_python("print('ok')"), timeout=30)
        assert result == CapturedProcess(exit_code=0, stdout="ok\n", stderr="")
