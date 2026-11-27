from pathlib import Path
import os
import sys


def inspect(context, read_stdin=False):
    return {"pid": os.getpid(), "root": context.project_root, "cwd": str(Path.cwd()),
            "model": context.default_model, "integration": context.default_integration,
            "inputs": context.inputs, "item": context.item, "steps": sorted(context.steps),
            "workflow_dir": context.workflow_dir, "stdin": sys.stdin.read() if read_stdin else None}
