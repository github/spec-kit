#!/usr/bin/env python3
"""Unit tests for the pipeline phase resolver. Stdlib unittest only; no pytest.

Run from the extension root:
    python3 -m unittest discover -s tests -p 'test_*.py'
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from phase_registry import (  # noqa: E402
    REGISTRY,
    DEFAULTS,
    INSERTABLE,
    DepBreak,
    NotInsertable,
    RequiredPhaseSkip,
    SkipAddConflict,
    UnknownPhase,
    resolve,
)


class TestPhaseRegistry(unittest.TestCase):
    def test_default_order(self):
        self.assertEqual(
            resolve(set(), set()),
            ["specify", "clarify", "plan", "tasks", "analyze", "implement"],
        )

    def test_skip_two_defaults_preserves_relative_order(self):
        self.assertEqual(
            resolve({"clarify", "analyze"}, set()),
            ["specify", "plan", "tasks", "implement"],
        )

    def test_add_out_of_order_lands_canonical(self):
        expected = ["constitution", "specify", "clarify", "plan", "tasks", "checklist", "analyze", "implement"]
        self.assertEqual(resolve(set(), {"constitution", "checklist"}), expected)
        self.assertEqual(resolve(set(), {"checklist", "constitution"}), expected)

    def test_permutation_invariance(self):
        outputs = []
        for order in ("clarify,analyze", "analyze,clarify"):
            cmd = [sys.executable, str(SCRIPTS_DIR / "resolve_phases.py"), "--skip", order, "--json"]
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SCRIPTS_DIR))
            self.assertEqual(r.returncode, 0, r.stderr)
            outputs.append(r.stdout)
        self.assertEqual(len(set(outputs)), 1)

    def test_unknown_name(self):
        with self.assertRaises(UnknownPhase) as cm:
            resolve(set(), {"nonexistent"})
        self.assertIn("nonexistent", cm.exception.names)
        self.assertEqual(set(cm.exception.valid), set(DEFAULTS) | set(INSERTABLE))

    def test_skip_add_conflict_first(self):
        with self.assertRaises(SkipAddConflict) as cm:
            resolve({"clarify"}, {"clarify"})
        self.assertIn("clarify", cm.exception.names)

    def test_add_non_insertable_rejected(self):
        with self.assertRaises(NotInsertable) as cm:
            resolve(set(), {"plan"})
        self.assertIn("plan", cm.exception.names)

    def test_skip_required_specify(self):
        with self.assertRaises(RequiredPhaseSkip):
            resolve({"specify"}, set())

    def test_skip_required_implement(self):
        with self.assertRaises(RequiredPhaseSkip):
            resolve({"implement"}, set())

    def test_skip_plan_collects_dep_breaks(self):
        with self.assertRaises(DepBreak) as cm:
            resolve({"plan"}, set())
        broken = {phase for phase, _ in cm.exception.violations}
        self.assertIn("tasks", broken)
        self.assertIn("analyze", broken)
        self.assertIn("implement", broken)
        ordered = [phase for phase, _ in cm.exception.violations]
        self.assertEqual(ordered, sorted(ordered, key=lambda p: REGISTRY[p].order))

    def test_skip_non_default_is_noop(self):
        self.assertEqual(resolve({"checklist"}, set()), resolve(set(), set()))

    def test_add_checklist_after_tasks(self):
        result = resolve(set(), {"checklist"})
        self.assertLess(result.index("tasks"), result.index("checklist"))
        self.assertLess(result.index("checklist"), result.index("analyze"))

    def test_cli_exit_codes(self):
        cases = [
            (["--skip", "nonexistent"], 10),
            (["--skip", "clarify", "--add", "clarify"], 11),
            (["--add", "plan"], 12),
            (["--skip", "specify"], 13),
            (["--skip", "plan"], 14),
            ([], 0),
        ]
        for args, code in cases:
            cmd = [sys.executable, str(SCRIPTS_DIR / "resolve_phases.py")] + args
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SCRIPTS_DIR))
            self.assertEqual(r.returncode, code, f"{args}: {r.stderr}")

    def test_json_shape(self):
        cmd = [sys.executable, str(SCRIPTS_DIR / "resolve_phases.py"), "--json"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SCRIPTS_DIR))
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertIsInstance(out, list)
        for item in out:
            for key in ("phase", "order", "command", "interactive", "description"):
                self.assertIn(key, item)
        orders = [item["order"] for item in out]
        self.assertEqual(orders, sorted(orders))

    def test_list_short_circuits(self):
        base = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "resolve_phases.py"), "--list"],
            capture_output=True, text=True, cwd=str(SCRIPTS_DIR),
        )
        self.assertEqual(base.returncode, 0)
        base_lines = base.stdout.strip().split("\n")
        self.assertEqual(len(base_lines), len(set(DEFAULTS) | set(INSERTABLE)))
        withargs = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "resolve_phases.py"), "--list", "--skip", "clarify", "--add", "constitution"],
            capture_output=True, text=True, cwd=str(SCRIPTS_DIR),
        )
        self.assertEqual(base_lines, withargs.stdout.strip().split("\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
