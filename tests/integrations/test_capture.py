"""Bounded subprocess capture and the captured ``dispatch_command`` contract."""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

from specify_cli.integrations import get_integration
from specify_cli.integrations import _capture
from specify_cli.integrations._capture import (
    DEFAULT_CAPTURE_MAX_BYTES,
    CapturedProcess,
    run_captured,
)


def _python(source: str, *args: str) -> list[str]:
    return [sys.executable, "-u", "-c", source, *args]


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
        assert capfd.readouterr().out == "text /speckit-plan\n"

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
