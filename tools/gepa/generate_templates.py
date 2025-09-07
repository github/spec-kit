#!/usr/bin/env python3
"""
GEPA-powered template generator for Spec Kit.

This script uses DSPy's GEPA optimizer to synthesize and iteratively
improve the instruction prompts that generate our markdown templates
under `templates/`. It can run in two modes:

- Offline mock mode (default): uses DSPy's MockLM and a rule-based metric
  to verify shape/sections. This is useful for development and CI.
- Real LM mode: configure via environment (e.g., OPENAI_API_KEY) and
  set --lm-provider and --lm-model to run with a real LLM for actual
  optimization.

Outputs are written to `templates/generated/` by default to avoid
overwriting the hand-written templates. Use --in-place to replace them
once you are satisfied.

Examples:
  python tools/gepa/generate_templates.py --use-mock --limit 1
  OPENAI_API_KEY=... python tools/gepa/generate_templates.py \
      --lm-provider openai --lm-model gpt-4o-mini --in-place
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple
from dotenv import load_dotenv


DEFAULT_MAX_METRIC_CALLS = 10


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


@dataclass
class TemplateSpec:
    name: str
    path: Path
    required_sections: List[str]
    must_contain: List[str]
    max_placeholders: int = 0  # e.g., occurrences of '<...>' or 'TODO'


def discover_templates(root: Path) -> List[TemplateSpec]:
    """Collect markdown templates and derive basic structural checks.

    We infer required sections from heading lines (#, ##, ###) and ensure
    some guardrails from the constitution guidelines if present.
    """
    template_dir = root / "templates"
    specs: List[TemplateSpec] = []

    constitution_text = (root / "memory" / "constitution.md").read_text(encoding="utf-8") if (root / "memory" / "constitution.md").exists() else ""
    guard_phrases = []
    for phrase in [
        "Don't guess",
        "Be explicit",
        "Capture assumptions",
        "List constraints",
    ]:
        if phrase.lower() in constitution_text.lower():
            guard_phrases.append(phrase)

    for path in sorted(template_dir.rglob("*.md")):
        if "/generated/" in str(path):
            continue
        name = path.relative_to(template_dir).as_posix()
        text = path.read_text(encoding="utf-8")
        headings = [ln.strip() for ln in text.splitlines() if re.match(r"^#{1,3}\s+", ln)]
        # Keep only the heading titles (strip leading #'s and whitespace)
        sections = [re.sub(r"^#{1,3}\s*", "", h) for h in headings]
        # A few non-heading anchors we want to enforce if we see them in the original
        anchors = []
        for token in ["Inputs", "Outputs", "Success Criteria", "Edge Cases", "Checklist"]:
            if re.search(rf"\b{re.escape(token)}\b", text):
                anchors.append(token)

        required = sorted(set(sections + anchors))

        specs.append(
            TemplateSpec(
                name=name,
                path=path,
                required_sections=required,
                must_contain=guard_phrases,
                max_placeholders=0,
            )
        )

    return specs


def build_requirements(ts: TemplateSpec) -> str:
    """Create a textual requirement description fed into the program."""
    parts = [
        f"Objective: Generate the markdown template `{ts.name}`.",
        "Constraints:",
        "- Preserve a clean, instruction-first style for an orchestration library.",
        "- Include these sections (as markdown headings):",
    ]
    for s in ts.required_sections:
        parts.append(f"  - {s}")
    if ts.must_contain:
        parts.append("- Ensure the following guardrails appear in guidance text:")
        for g in ts.must_contain:
            parts.append(f"  - {g}")
    parts += [
        "- Avoid placeholders like '<...>' or 'TODO'.",
        "- Use concise, actionable language.",
        "- Keep sections ordered logically.",
    ]
    return "\n".join(parts)


def section_score(text: str, required_sections: List[str]) -> Tuple[float, List[str]]:
    missing: List[str] = []
    lowered = text.lower()
    for sec in required_sections:
        if sec.strip() and sec.lower() not in lowered:
            missing.append(sec)
    score = 1.0 - (len(missing) / max(1, len(required_sections)))
    return score, missing


def placeholder_penalty(text: str, max_placeholders: int) -> Tuple[float, int]:
    count = len(re.findall(r"<[^>]+>|TODO|TBD", text, re.IGNORECASE))
    return (1.0 if count <= max_placeholders else max(0.0, 1.0 - 0.2 * (count - max_placeholders))), count


def make_metric(spec: TemplateSpec):
    """Construct a GEPA metric that rewards structural completeness and clarity.

    Returns a callable compatible with dspy.GEPA's GEPAFeedbackMetric.
    """

    def metric(gold, pred, trace=None, pred_name=None, pred_trace=None):  # GEPA expects 5 args
        # Support both dict-like and attr-like preds from DSPy
        output = None
        if isinstance(pred, dict):
            output = pred.get("template") or pred.get("output") or pred.get("text")
        else:
            output = getattr(pred, "template", None) or getattr(pred, "output", None) or str(pred)
        if not isinstance(output, str):
            return 0.0, "Prediction missing template text."

        s_score, missing = section_score(output, spec.required_sections)
        p_score, count = placeholder_penalty(output, spec.max_placeholders)

        guards_ok = 1.0
        feedbacks: List[str] = []
        for g in spec.must_contain:
            if g.lower() not in output.lower():
                guards_ok *= 0.9
                feedbacks.append(f"Missing guard phrase: {g}")

        score = max(0.0, min(1.0, 0.6 * s_score + 0.3 * p_score + 0.1 * guards_ok))

        if missing:
            feedbacks.append("Missing sections: " + ", ".join(missing))
        if count > spec.max_placeholders:
            feedbacks.append(f"Reduce placeholders (found {count}).")

        # Return only a numeric score to match DSPy v3 GEPA aggregators.
        # GEPA will auto-generate text feedback from the score if needed.
        return float(score)

    return metric


def configure_lm(args) -> None:
    import dspy

    if args.use_mock:
        # DSPy v3: use the built-in mock LM for offline runs
        dspy.configure(lm=dspy.LM('mock'))
        return

    provider = (args.lm_provider or os.getenv("DSPY_LM_PROVIDER") or "openai").lower()
    model = args.lm_model or os.getenv("DSPY_LM_MODEL") or "gpt-4o-mini"

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set; use --use-mock or export a key.")
        # DSPy v3 unified LM configuration
        dspy.configure(lm=dspy.LM(f'openai/{model}', api_key=api_key))
    else:
        raise RuntimeError(f"Unsupported lm provider: {provider}")


def optimize_and_generate(specs: List[TemplateSpec], out_dir: Path, args) -> List[Path]:
    import dspy

    class TemplateSignature(dspy.Signature):
        requirements: str = dspy.InputField()
        template: str = dspy.OutputField(desc="Complete markdown template text")

    class TemplateProgram(dspy.Module):
        def __init__(self):
            super().__init__()
            self.gen = dspy.Predict(TemplateSignature)

        def forward(self, requirements: str) -> dspy.Prediction:
            return self.gen(requirements=requirements)

    written: List[Path] = []
    out_dir.mkdir(parents=True, exist_ok=True)

    for idx, ts in enumerate(specs):
        if args.limit and idx >= args.limit:
            break
        eprint(f"[GEPA] Preparing optimization for {ts.name}")

        requirements = build_requirements(ts)

        # Trainset with the existing file as a soft target. This lets GEPA
        # reflect toward meeting the structure while still allowing improvements.
        gold = ts.path.read_text(encoding="utf-8")
        # Explicitly declare inputs/outputs for DSPy v3 teleprompters
        # In DSPy v3, specify inputs only; remaining keys are treated as labels/outputs.
        train_ex = dspy.Example(requirements=requirements, template=gold).with_inputs("requirements")
        trainset = [train_ex]

        # If running with a mock LM, skip heavy GEPA unless forced (dev verification).
        if (isinstance(dspy.settings.lm, dspy.LM)
            and getattr(dspy.settings.lm, "model", "") == "mock"
            and not args.force_gepa):
            text = f"<!-- Generated (mock) passthrough; replace via real GEPA run -->\n" + gold
        else:
            prog = TemplateProgram()
            metric = make_metric(ts)
            # Provide a reflection LM as required by GEPA. Reuse configured LM.
            reflection_lm = dspy.settings.lm
            # GEPA requires exactly one of auto/max_metric_calls/max_full_evals.
            gepa_kwargs = dict(metric=metric, track_stats=True, reflection_lm=reflection_lm)
            if args.max_metric_calls is not None:
                gepa = dspy.GEPA(max_metric_calls=args.max_metric_calls, **gepa_kwargs)
            else:
                gepa = dspy.GEPA(auto="light", **gepa_kwargs)

            try:
                optimized = gepa.compile(prog, trainset=trainset, valset=trainset)
                pred = optimized(requirements=requirements)
                text = getattr(pred, "template", None) or getattr(pred, "output", None)
                if not isinstance(text, str) or len(text.strip()) == 0:
                    eprint(f"[WARN] Empty output for {ts.name}; using original file content.")
                    text = gold
            except Exception as e:
                # Fall back to original if optimization fails
                eprint(f"[GEPA] Optimization failed for {ts.name}: {e}. Falling back to original.")
                text = gold

        if args.in_place:
            out_path = ts.path
        else:
            out_path = out_dir / ts.name
            out_path.parent.mkdir(parents=True, exist_ok=True)

        out_path.write_text(text, encoding="utf-8")
        written.append(out_path)
        eprint(f"[OK] Wrote {out_path}")

    return written


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate/optimize templates using DSPy GEPA")
    # Script is in tools/gepa/, so repo root is two levels up.
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out-dir", type=Path, default=None, help="Output dir; defaults to templates/generated")
    parser.add_argument("--in-place", action="store_true", help="Overwrite templates in place")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of templates processed")
    parser.add_argument("--use-mock", action="store_true", help="Use MockLM (offline/dev)")
    parser.add_argument("--lm-provider", type=str, default=None, help="e.g., openai")
    parser.add_argument("--lm-model", type=str, default=None, help="e.g., gpt-4o-mini")
    parser.add_argument("--force-gepa", action="store_true", help="Run GEPA even in mock mode for verification")
    parser.add_argument("--max-metric-calls", type=int, default=DEFAULT_MAX_METRIC_CALLS, help=f"GEPA budget (lower for quick runs) [default {DEFAULT_MAX_METRIC_CALLS}]")
    parser.add_argument("--env-file", type=Path, default=None, help="Optional path to a .env file (defaults to <repo-root>/.env if present)")

    args = parser.parse_args(argv)

    root = args.repo_root
    # Load environment variables from .env if present (explicit path or <repo-root>/.env)
    env_path = args.env_file or (root / ".env")
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    out_dir = args.out_dir or (root / "templates" / "generated")

    # Discover and build specs
    specs = discover_templates(root)
    if not specs:
        eprint("No templates found.")
        return 1

    # Configure LM and run optimization
    try:
        configure_lm(args)
    except Exception as e:
        eprint(f"[WARN] LM configuration failed: {e}. Using mock LM.")
        try:
            import dspy
            dspy.configure(lm=dspy.LM('mock'))
        except Exception as e2:
            eprint(f"[FATAL] Failed to initialize mock LM: {e2}")
            return 2

    written = optimize_and_generate(specs, out_dir, args)
    eprint(f"Done. Files written: {len(written)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
