"""opencode integration."""

import errno
import os
import re
import stat
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import Any

import pathspec

from ...file_helper import FileHelper, SymlinkDeniedError, UnsupportedPathError
from ..base import IntegrationOption, MarkdownIntegration
from ..manifest import IntegrationManifest

# opencode 1.18.31 and 1.19.3 glob through ripgrep without ``--hidden``.
# Root ``.ignore`` rules ``!.specify/`` and ``!.specify/**`` make
# ``.specify/**/*`` return constitution, template, and script paths on
# that path (``opencode debug rg files --glob``, the same ``Ripgrep.glob``
# call the glob tool makes). ``!.specify/**`` alone does not. opencode 2.x
# was not part of that check.
_SPECIFY_IGNORE_RULES = ("!.specify/", "!.specify/**")
# ripgrep ranks ``.ignore`` above every ``.gitignore``, so the exceptions
# would also surface per-machine extension overrides that the managed
# ``.specify/.gitignore`` keeps out of version control and that can hold
# credentials, including the copies extension removal keeps under
# ``.specify/extensions/.backup/``. These rules must follow the last
# negation line. They only cover ripgrep runs without a matching
# ``--glob``: a positive glob that matches a file (``.specify/**/*``,
# ``**/*.yml``) overrides every ignore file, so opencode's glob tool still
# lists these paths once ``.specify`` is walked (ripgrep 15.2.0).
# Workflow run state (``state.json``, ``inputs.json``, ``log.jsonl``) holds
# resolved inputs and captured command output, so it stays out of plain
# searches as well.
_SPECIFY_PRIVATE_RULES = (
    ".specify/**/local-config.yml",
    ".specify/**/*-config.local.yml",
    ".specify/workflows/runs/",
)
# Extension removal backups and workflow run state are user state, not Spec
# Kit files to surface, so a user exclusion of them is allowed.
_UNPROBED_SPECIFY_DIRS = (
    ".specify/extensions/.backup/",
    ".specify/workflows/runs/",
)
# Representative private paths checked even before any exist.
_PRIVATE_SPECIFY_PROBES = (
    ".specify/extensions/example/local-config.yml",
    ".specify/extensions/example/example-config.local.yml",
    ".specify/extensions/.backup/example/local-config.yml",
    ".specify/workflows/runs/example/state.json",
)


class OpencodeIntegration(MarkdownIntegration):
    key = "opencode"
    multi_install_safe = True
    config = {
        "name": "opencode",
        "folder": ".opencode/",
        "commands_subdir": "commands",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    }
    registrar_config = {
        "dir": ".opencode/commands",
        "legacy_dir": ".opencode/command",
        "format": "markdown",
        "args": "$ARGUMENTS",
        "extension": ".md",
    }

    CANONICAL_TO_NATIVE = {
        "pre_tool_use": "tool.execute.before",
        "post_tool_use": "tool.execute.after",
        # session_start maps to the system-prompt transform hook (not the
        # session.created event) so the handler's stdout is injected into the
        # system prompt — session.created has no output channel. The hook
        # fires per LLM request, which keeps the context present across
        # compaction at the cost of running the handler per turn.
        "session_start": "experimental.chat.system.transform",
        # user_prompt_submit maps to chat.message so handler stdout is
        # injected as a synthetic text part on the user's message.
        "user_prompt_submit": "chat.message",
        "session_end": "session.deleted",
    }
    events_config_file = "opencode.json"
    events_format = "ts-plugin"

    @classmethod
    def options(cls) -> list[IntegrationOption]:
        opts = super().options()
        opts.append(
            IntegrationOption(
                "--configure-ignore-file",
                is_flag=True,
                default=False,
                help=(
                    "Append !.specify/ and !.specify/** to the project root "
                    ".ignore so opencode can glob hidden Spec Kit files, "
                    "excluding extension local-config.yml and "
                    "*-config.local.yml files and .specify/workflows/runs/ "
                    "from searches without a "
                    "matching glob (a glob that matches them still lists them). "
                    "Uninstall leaves .ignore in place."
                ),
            )
        )
        return opts

    def setup(
        self,
        project_root: Path,
        manifest: IntegrationManifest,
        parsed_options: dict[str, Any] | None = None,
        **opts: Any,
    ) -> list[Path]:
        """Validate an explicit ``.ignore`` opt-in, then render commands.

        Command files stay on the Markdown layout from ``super().setup()``.
        ``--configure-ignore-file`` appends missing ``!.specify/`` and
        ``!.specify/**`` rules, then the private-state exclusions, and
        records the root file as partial
        ownership. Without the flag the root ``.ignore`` is left alone.
        """
        configure = (parsed_options or {}).get("configure_ignore_file") is True
        script_type = opts.get("script_type")
        if configure:
            _preflight_root_ignore(manifest.project_root, script_type)
        created = super().setup(
            project_root, manifest, parsed_options=parsed_options, **opts
        )
        if configure:
            created.append(_configure_root_ignore(manifest, script_type))
        return created

    def preflight_setup(
        self,
        project_root: Path,
        parsed_options: dict[str, Any] | None = None,
        *,
        script_type: str | None = None,
    ) -> None:
        """Refuse an unusable ``.ignore`` before shared files are written."""
        if (parsed_options or {}).get("configure_ignore_file") is True:
            _preflight_root_ignore(project_root, script_type)

    def build_exec_args(
        self,
        prompt: str,
        *,
        model: str | None = None,
        output_json: bool = True,
        integration_args: Sequence[str] | None = None,
        integration_options: Mapping[str, Any] | None = None,
        project_root: Path | None = None,
    ) -> list[str] | None:
        self.validate_runtime_config(integration_args, integration_options)
        args = [self._resolve_executable(), "run"]
        # Apply operator-injected extra args before the prompt-derived
        # --command and the canonical --format/-m flags so Spec Kit's
        # later appends remain authoritative under repeated-flag CLI
        # semantics.
        self._apply_extra_args_env_var(args)

        message = prompt
        if prompt.startswith("/"):
            command, _, remainder = prompt[1:].partition(" ")
            if command:
                args.extend(["--command", command])
                message = remainder

        if model:
            args.extend(["-m", model])
        if output_json:
            args.extend(["--format", "json"])
        if message:
            args.append(message)
        return args


def _ignore_newline(raw: bytes) -> bytes:
    return b"\r\n" if b"\r\n" in raw else b"\n"


def _split_ignore_lines(raw: bytes) -> list[bytes]:
    lines = raw.split(b"\n")
    last = len(lines) - 1
    return [
        line[:-1] if index < last and line.endswith(b"\r") else line
        for index, line in enumerate(lines)
    ]


def _ignore_spec(raw: bytes) -> pathspec.GitIgnoreSpec:
    """Compile *raw* ignore lines, skipping lines pathspec cannot parse."""
    parsed = []
    for raw_line in _split_ignore_lines(raw):
        text = raw_line.decode("utf-8", errors="replace")
        try:
            pathspec.GitIgnoreSpec.from_lines([text])
        except (ValueError, re.error):
            continue
        parsed.append(text)
    return pathspec.GitIgnoreSpec.from_lines(parsed)


def _spec_decision(spec: pathspec.GitIgnoreSpec, candidate: str) -> bool | None:
    """Last matching rule for *candidate*: True ignores, False re-includes.

    A trailing ``/`` marks a directory. ``None`` means no rule matched.
    """
    if not candidate.endswith("/"):
        return spec.check_file(candidate).include
    state = None
    for pattern in spec.patterns:
        if pattern.include is not None and pattern.match_file(candidate) is not None:
            state = bool(pattern.include)
    return state


def _probe_steps(probe: str) -> list[str]:
    """Each directory ripgrep walks to reach *probe*, then *probe* itself."""
    parts = [part for part in probe.split("/") if part]
    steps, built = [], ""
    for index, part in enumerate(parts):
        built = f"{built}/{part}" if built else part
        is_dir = index < len(parts) - 1 or probe.endswith("/")
        steps.append(built + "/" if is_dir else built)
    return steps


def _spec_hides(spec: pathspec.GitIgnoreSpec, probe: str) -> bool:
    """Whether *spec* excludes *probe* or one of its parent directories."""
    return any(_spec_decision(spec, step) for step in _probe_steps(probe))


# ripgrep checks ``.rgignore`` before ``.ignore`` across every directory, and
# within each kind the file nearest the path wins (ripgrep 15.2.0).
_RG_IGNORE_NAMES = (".rgignore", ".ignore")


def _ignore_layers(
    project_root: Path, root_ignore: bytes
) -> list[tuple[str, str, Path, pathspec.GitIgnoreSpec]]:
    """Ignore files that apply under ``.specify/``: (name, base dir, path, spec).

    The root ``.ignore`` uses *root_ignore*, the content about to be written.
    Symlinked ignore files are skipped.
    """
    layers = [(".ignore", "", project_root / ".ignore", _ignore_spec(root_ignore))]
    root_rg = project_root / ".rgignore"
    if root_rg.is_file() and not root_rg.is_symlink():
        layers.append(
            (".rgignore", "", root_rg, _ignore_spec(FileHelper(project_root).read_bytes(".rgignore")))
        )
    specify = project_root / ".specify"
    if specify.is_dir() and not specify.is_symlink():
        for name in _RG_IGNORE_NAMES:
            for nested in sorted(specify.rglob(name)):
                if not nested.is_file() or nested.is_symlink():
                    continue
                base = nested.parent.relative_to(project_root).as_posix()
                raw = FileHelper(nested.parent).read_bytes(name)
                layers.append((name, base, nested, _ignore_spec(raw)))
    return layers


def _rg_decisions(
    layers: Sequence[tuple[str, str, Path, pathspec.GitIgnoreSpec]], probe: str
) -> Iterator[tuple[Path, bool]]:
    """Each deciding ignore file and its decision as ripgrep walks to *probe*.

    ``True`` ignores the step and ripgrep stops there; ``False`` re-includes it.
    """
    for step in _probe_steps(probe):
        for name in _RG_IGNORE_NAMES:
            applicable = sorted(
                (
                    layer for layer in layers
                    if layer[0] == name
                    and (not layer[1] or step.startswith(layer[1] + "/"))
                ),
                key=lambda layer: layer[1].count("/") + bool(layer[1]),
                reverse=True,
            )
            decision = None
            for _, base, path, spec in applicable:
                relative = step[len(base) + 1:] if base else step
                decision = _spec_decision(spec, relative)
                if decision is not None:
                    break
            if decision is not None:
                yield path, decision
                if decision:
                    return
                break


def _rg_hiding_file(
    layers: Sequence[tuple[str, str, Path, pathspec.GitIgnoreSpec]], probe: str
) -> Path | None:
    """The ignore file that makes ripgrep skip *probe*, or ``None``."""
    for path, decision in _rg_decisions(layers, probe):
        if decision:
            return path
    return None


def _rg_exposing_file(
    layers: Sequence[tuple[str, str, Path, pathspec.GitIgnoreSpec]], probe: str
) -> Path | None:
    """The ignore file whose re-inclusion lets ripgrep list *probe*, or ``None``."""
    culprit = None
    for path, decision in _rg_decisions(layers, probe):
        if decision:
            return None
        culprit = path
    return culprit


def _reject_hidden_specify_paths(
    path: Path, updated: bytes, script_type: str | None = None
) -> None:
    """Fail when *updated* still hides Spec Kit paths, evaluated in file order.

    Bundled scripts are probed only for the variants *script_type* installs
    (every variant when it is unknown); files already under ``.specify/``
    are always probed. Each probe and its ancestors are evaluated the way
    ripgrep does: a root ``.rgignore`` and any ``.ignore`` or ``.rgignore``
    under ``.specify/`` can override the root exceptions. Private configs
    and workflow run state, existing or not, must stay hidden across those
    same layers, so a re-inclusion there fails too.
    """
    from ..._assets import _locate_core_pack, _repo_root
    from ...shared_infra import script_variant_dirs

    pack, repo = _locate_core_pack(), _repo_root()
    probes = {".specify/", ".specify/.gitignore", ".specify/memory/constitution.md"}
    variants = None if script_type is None else set(script_variant_dirs(script_type))
    for kind in ("templates", "scripts"):
        base = (pack if pack and (pack / kind).is_dir() else repo) / kind
        walk = () if not base.is_dir() else (base.iterdir() if kind == "templates" else base.rglob("*"))
        probes.update(
            f".specify/{kind}/{item.relative_to(base).as_posix()}"
            for item in walk
            if kind == "templates" or variants is None
            or item.relative_to(base).parts[0] in variants
            if item.is_file() and "__pycache__" not in item.parts
            and not item.name.startswith(".") and item.name != "vscode-settings.json"
        )
    specify = path.parent / ".specify"
    if specify.is_dir() and not specify.is_symlink():
        probes.update(f.relative_to(path.parent).as_posix() for f in specify.rglob("*") if f.is_file())
    private = pathspec.GitIgnoreSpec.from_lines(_SPECIFY_PRIVATE_RULES)
    visible = sorted(
        probe for probe in probes
        if not private.match_file(probe)
        and not probe.startswith(_UNPROBED_SPECIFY_DIRS)
    )
    layers = _ignore_layers(path.parent, updated)
    hidden = sorted(
        set(_PRIVATE_SPECIFY_PROBES)
        | {
            probe for probe in probes
            if private.match_file(probe) or probe.startswith(".specify/workflows/runs/")
        }
    )
    for probe in hidden:
        culprit = _rg_exposing_file(layers, probe)
        if culprit is not None:
            raise ValueError(
                f"A re-inclusion in {culprit} exposes private {probe}. "
                "Remove it from that file, then rerun."
            )
    for probe in visible:
        culprit = _rg_hiding_file(layers, probe)
        if culprit is None:
            continue
        if culprit == path:
            raise ValueError(
                f"A later exclusion in {path} hides {probe}. "
                "Move !.specify/ and !.specify/** below it, then rerun."
            )
        raise ValueError(
            f"An exclusion in {culprit} hides {probe}. "
            "Remove it from that file, then rerun."
        )


def _with_specify_ignore_rules(raw: bytes) -> bytes:
    """Append missing Spec Kit rules, keeping *raw* as a byte prefix.

    Private rules are appended when they are not exact lines after the
    last negation line, so a later ``!`` rule cannot re-include them. New rules use the file's newline (``\\n`` when
    *raw* is empty) and a trailing newline. Exact ASCII lines are matched
    without decoding. Non-UTF-8 files are rejected before this runs and
    are not preserved.
    """
    if not raw:
        newline = b"\n"
        body = newline.join(
            rule.encode("ascii")
            for rule in _SPECIFY_IGNORE_RULES + _SPECIFY_PRIVATE_RULES
        )
        return body + newline

    lines = _split_ignore_lines(raw)
    exceptions = [rule.encode("ascii") for rule in _SPECIFY_IGNORE_RULES]
    missing = [rule for rule in exceptions if rule not in lines]
    last = max(
        (
            index for index, line in enumerate(lines)
            if line in exceptions or line.startswith(b"!")
        ),
        default=-1,
    )
    after = set() if missing else set(lines[last + 1:])
    missing += [
        rule.encode("ascii")
        for rule in _SPECIFY_PRIVATE_RULES
        if rule.encode("ascii") not in after
    ]
    if not missing:
        return raw

    newline = _ignore_newline(raw)
    addition = b"" if raw.endswith(b"\n") else newline
    addition += newline.join(missing) + newline
    return raw + addition


def _read_root_ignore(path: Path) -> bytes:
    """Read root ``.ignore`` without following a link swapped in at the leaf."""
    try:
        return FileHelper(path.parent).read_bytes(path.name)
    except FileNotFoundError:
        return b""
    except SymlinkDeniedError as exc:
        raise ValueError(f"Refusing to configure symlinked .ignore: {path}") from exc
    except UnsupportedPathError as exc:
        raise ValueError(
            f"Refusing to configure .ignore because it is not a regular file: {path}"
        ) from exc
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError(f"Refusing to configure symlinked .ignore: {path}") from exc
        raise OSError(f"Cannot read .ignore at {path}") from exc


def _preflight_root_ignore(
    project_root: Path, script_type: str | None = None
) -> tuple[Path, bytes, bytes]:
    path = project_root / ".ignore"
    raw = _read_root_ignore(path)
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"{path} is not UTF-8 ({exc.reason} at byte {exc.start}). "
            "Convert it to UTF-8 and rerun; ripgrep stops at the first invalid byte."
        ) from exc
    updated = _with_specify_ignore_rules(raw)
    _reject_hidden_specify_paths(path, updated, script_type)
    if updated != raw and path.exists() and not os.access(path, os.W_OK):
        raise PermissionError(f"Cannot update .ignore at {path}")
    if updated != raw and not os.access(path.parent, os.W_OK):
        if path.exists():
            raise PermissionError(f"Cannot update .ignore at {path}")
        raise PermissionError(f"Cannot create .ignore at {path}")
    return path, raw, updated


def _configure_root_ignore(
    manifest: IntegrationManifest, script_type: str | None = None
) -> Path:
    """Recheck root ``.ignore``, write it atomically, and record partial ownership."""
    path, raw, updated = _preflight_root_ignore(manifest.project_root, script_type)
    if updated == raw and path.is_file():
        from .._file_changes import before_file_change

        before_file_change(path)
        manifest.record_existing(".ignore", ownership="partial")
        return path

    from ...shared_infra import _write_shared_bytes

    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    if _read_root_ignore(path) != raw:
        raise ValueError(f"{path} changed while it was being configured; rerun.")
    _write_shared_bytes(manifest.project_root, path, updated, mode=mode)
    manifest.record_existing(".ignore", ownership="partial")
    return path
