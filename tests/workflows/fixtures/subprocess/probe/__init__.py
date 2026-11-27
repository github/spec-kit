"""Installed fixture, deliberately imported afresh by the real worker."""
import os
from pathlib import Path
import time

from specify_cli.workflows.base import StepBase, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression
from .helpers import inspect


class BoundaryProbe(StepBase):
    type_key = "boundary-probe"

    def execute(self, config, context):
        root = Path(context.project_root)
        if config.get("wait_for"):
            deadline = time.monotonic() + 20
            while not Path(config["wait_for"]).exists():
                if time.monotonic() > deadline:
                    raise RuntimeError("Wait timed out")
                time.sleep(.02)
        if "effect" in config:
            with (root / config["effect"]).open("a") as stream:
                stream.write("effect\n")
        if config.get("rendezvous"):
            shared = Path(evaluate_expression(config["rendezvous"], context))
            (shared / root.name).write_text(str(os.getpid()))
            deadline = time.monotonic() + 10
            while len(list(shared.iterdir())) != 2:
                if time.monotonic() > deadline:
                    raise RuntimeError("Rendezvous timed out")
                time.sleep(.02)
        if config.get("flood"):
            os.write(1, b"native-out\n" + b"x" * 100000)
            os.write(2, b"native-err\n" + b"y" * 100000)
            print("python-print")
        if config.get("exception") == "exit":
            raise SystemExit(config.get("exit_code", 7))
        if config.get("exception") == "interrupt":
            raise KeyboardInterrupt
        if config.get("exception") == "base":
            raise BaseException("fixture base exception")
        if config.get("exception_input") and context.inputs.get(config["exception_input"]):
            raise RuntimeError("fixture unfinished effect")
        if config.get("exception"):
            raise RuntimeError("fixture worker exception")
        if config.get("sleep"):
            time.sleep(config["sleep"])
        if config.get("read_subprocess"):
            import subprocess
            import sys
            assert subprocess.run([sys.executable, "-B", "-c", "import sys; assert sys.stdin.read() == ''"],
                                  timeout=5).returncode == 0
        if config.get("capture"):
            from specify_cli.integrations._capture import run_captured
            import sys
            code = ("import sys, time; from pathlib import Path; p=Path(sys.argv[1]); "
                    "exec('while True: p.write_text(str(time.time_ns())); time.sleep(.03)')")
            run_captured([sys.executable, "-B", "-c", code, str(root / "heartbeat")])
        if config.get("detached_diagnostics"):
            import subprocess
            import sys
            helper = subprocess.Popen([sys.executable, "-B", "-c", "import time; time.sleep(30)"],
                                      start_new_session=True)
            (root / "helper.pid").write_text(str(helper.pid))
        if config.get("value_object"):
            return StepResult(output={"object": object()})
        value = evaluate_expression(config.get("value"), context)
        output = {**inspect(context, config.get("read_stdin", False)), "value": value}
        if config.get("home_origin"):
            from specify_cli.integrations.installer import _trust_store
            output.update(home=str(Path.home().absolute()),
                          trust=str(_trust_store(root / "nested-project")),
                          inherited=os.environ.get("BOUNDARY_ENV_SENTINEL"))
        if config.get("scaffold"):
            assert (root / ".specify/memory/constitution.md").is_file()
            assert (root / ".specify/init-options.json").is_file()
        if config.get("asset"):
            output["asset"] = (Path(context.workflow_dir) / "asset.txt").read_text()
        return StepResult(StepStatus(config.get("status", "completed")), output=output)
