#!/usr/bin/env python3
"""Phase registry and resolver for the Spec Kit `pipeline` extension.

Pure function, zero I/O. Encodes every orderable Spec Kit phase with its
dependencies and the `/speckit.*` command it maps to, and resolves a
requested skip/add set into a single deterministic ordered plan.

This is the reusable core of the extension: the command prose calls
`resolve_phases.py` (a thin CLI over `resolve()` below) to decide which
phases run and in what order, then drives each `/speckit.*` command in turn.

No agent/model/vendor coupling lives here — the registry is portable to any
Spec Kit project and any AI coding agent.
"""

from collections import namedtuple

# Phase registry entry. `command` is the slash command the phase drives
# (agent-neutral: Spec Kit renders it as `/speckit.plan`, or the skills-mode
# equivalent `speckit-plan`, per the active integration).
Phase = namedtuple(
    "Phase",
    ["order", "default", "insertable", "required", "interactive", "deps", "command", "description"],
)

# Complete phase registry: id -> Phase.
REGISTRY = {
    "constitution": Phase(
        order=5,
        default=False,
        insertable=True,
        required=False,
        interactive=False,
        deps=[],
        command="speckit.constitution",
        description="Establish or update the project constitution before specifying.",
    ),
    "specify": Phase(
        order=10,
        default=True,
        insertable=False,
        required=True,
        interactive=False,
        deps=[],
        command="speckit.specify",
        description="Turn the feature description into a specification.",
    ),
    "clarify": Phase(
        order=20,
        default=True,
        insertable=False,
        required=False,
        interactive=True,
        deps=["specify"],
        command="speckit.clarify",
        description="Resolve underspecified areas. The single interactive human gate.",
    ),
    "plan": Phase(
        order=30,
        default=True,
        insertable=False,
        required=False,
        interactive=False,
        deps=["specify"],
        command="speckit.plan",
        description="Produce the implementation plan and design artifacts.",
    ),
    "tasks": Phase(
        order=40,
        default=True,
        insertable=False,
        required=False,
        interactive=False,
        deps=["plan"],
        command="speckit.tasks",
        description="Generate the dependency-ordered task list.",
    ),
    "checklist": Phase(
        order=45,
        default=False,
        insertable=True,
        required=False,
        interactive=False,
        deps=["tasks"],
        command="speckit.checklist",
        description="Generate a quality checklist for the feature.",
    ),
    "analyze": Phase(
        order=60,
        default=True,
        insertable=False,
        required=False,
        interactive=False,
        deps=["specify", "plan", "tasks"],
        command="speckit.analyze",
        description="Cross-artifact consistency and quality analysis before implementing.",
    ),
    "implement": Phase(
        order=70,
        default=True,
        insertable=False,
        required=True,
        interactive=False,
        deps=["plan", "tasks"],
        command="speckit.implement",
        description="Execute the plan and produce the change.",
    ),
}

# Orderable partitions.
DEFAULTS = {"specify", "clarify", "plan", "tasks", "analyze", "implement"}
INSERTABLE = {"constitution", "checklist"}
REQUIRED = {"specify", "implement"}


class UnknownPhase(Exception):
    """Exit code 10: unrecognized phase name(s)."""

    code = 10

    def __init__(self, names, valid):
        self.names = names
        self.valid = valid
        super().__init__(f"Unknown phase name(s): {', '.join(names)}. Valid: {', '.join(valid)}")


class SkipAddConflict(Exception):
    """Exit code 11: phase appears in both --skip and --add."""

    code = 11

    def __init__(self, names):
        self.names = names
        super().__init__(f"Phase(s) appear in both --skip and --add: {', '.join(names)}")


class NotInsertable(Exception):
    """Exit code 12: attempted to add a non-insertable phase."""

    code = 12

    def __init__(self, names, insertable_set):
        self.names = names
        self.insertable_set = insertable_set
        super().__init__(
            f"Cannot add non-insertable phase(s): {', '.join(names)}. "
            f"Insertable phases: {', '.join(sorted(insertable_set))}"
        )


class RequiredPhaseSkip(Exception):
    """Exit code 13: attempted to skip a required phase."""

    code = 13

    def __init__(self, names):
        self.names = names
        super().__init__(f"Cannot skip required phase(s): {', '.join(names)}")


class DepBreak(Exception):
    """Exit code 14: unmet dependencies in the effective set."""

    code = 14

    def __init__(self, violations):
        self.violations = violations  # list of (phase, missing_dep) tuples
        super().__init__(
            "Dependency broken. Phase(s) missing required input:\n"
            + "\n".join(f"  {phase} requires {dep}" for phase, dep in violations)
        )


def resolve(skip, add):
    """Deterministic phase resolver.

    Args:
        skip: set of phase names to exclude from the default set.
        add:  set of insertable phase names to include.

    Returns:
        list of phase names in canonical order.

    Raises:
        UnknownPhase (10), SkipAddConflict (11), NotInsertable (12),
        RequiredPhaseSkip (13), DepBreak (14) — checked in that order.

    Ordering is a pure function of the effective set (skip/add consumed as
    sets, order derived from the single fixed `order` key), so the output is
    invariant to the input ordering of --skip / --add.
    """
    orderable = set(DEFAULTS) | set(INSERTABLE)

    unknown = (skip | add) - orderable
    if unknown:
        raise UnknownPhase(sorted(unknown), valid=sorted(orderable))

    conflict = skip & add
    if conflict:
        raise SkipAddConflict(sorted(conflict))

    not_insertable = add - INSERTABLE
    if not_insertable:
        raise NotInsertable(sorted(not_insertable), INSERTABLE)

    required_hit = skip & REQUIRED
    if required_hit:
        raise RequiredPhaseSkip(sorted(required_hit))

    effective = (DEFAULTS - skip) | add

    violations = [
        (phase, dep)
        for phase in sorted(effective, key=lambda p: REGISTRY[p].order)
        for dep in REGISTRY[phase].deps
        if dep not in effective
    ]
    if violations:
        raise DepBreak(violations)

    return sorted(effective, key=lambda p: REGISTRY[p].order)
