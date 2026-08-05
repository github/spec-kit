"""Parity tests for composed runtime template resolution."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tests.conftest import requires_bash
from tests.parity_helpers import (
    HAS_POWERSHELL,
    bash_cmd,
    clean_env,
    install_composition_stack,
    install_scripts,
    json_stdout,
    make_repo,
    ps_cmd,
    py_cmd,
    run,
)

SCRIPT = "resolve-template"
TEMPLATE = "constitution-template"


def _setup_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = install_composition_stack(repo, TEMPLATE, "# Core\n")
    return repo, expected


@requires_bash
def test_all_variants_emit_composed_template_content(tmp_path: Path) -> None:
    repo, expected = _setup_repo(tmp_path)
    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(result.stderr == "" for result in results)
    assert all(
        json_stdout(result)
        == {"TEMPLATE_NAME": TEMPLATE, "TEMPLATE_CONTENT": expected}
        for result in results
    )


@requires_bash
@pytest.mark.parametrize(
    "without_registry,core_content",
    [
        (True, "# Core\n"),
        (False, "# Café ✓\n"),
    ],
    ids=["directory_fallback", "unicode"],
)
def test_all_variants_preserve_composition_parity(
    tmp_path: Path, without_registry: bool, core_content: str
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = install_composition_stack(repo, TEMPLATE, core_content)
    if without_registry:
        (repo / ".specify" / "presets" / ".registry").unlink()
        expected = (
            "# Prepended\n\n\n"
            "## Wrapper\n"
            f"{core_content}\n"
            "## End\n\n\n"
            "# Appended\n"
        )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == expected
        for result in results
    )


@requires_bash
def test_all_variants_read_utf8_registry_under_ascii_locale(
    tmp_path: Path,
) -> None:
    """Registry/manifest reads must force UTF-8, not the process locale.

    With UTF-8 mode disabled and a C locale, the interpreter's default text
    encoding is ASCII. Non-ASCII *metadata* in the registry or a manifest must
    still resolve, because the resolvers open those files as UTF-8 explicitly.
    Template content stays ASCII so the pure-Python variant can emit it on the
    ASCII stdout this configuration forces.
    """
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = install_composition_stack(repo, TEMPLATE, "# Core\n")

    # Inject non-ASCII metadata into the preset registry and a manifest so a
    # locale-dependent decode would raise instead of resolving cleanly.
    registry = repo / ".specify" / "presets" / ".registry"
    registry_data = json.loads(registry.read_text(encoding="utf-8"))
    registry_data["presets"]["wrap-pack"]["description"] = "Café ✓ wrapper"
    registry.write_text(
        json.dumps(registry_data, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    manifest = repo / ".specify" / "presets" / "wrap-pack" / "preset.yml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + '      description: "Café ✓"\n',
        encoding="utf-8",
    )

    env = clean_env()
    # Force the interpreter's default text encoding to ASCII so an unqualified
    # open() would fail on the non-ASCII metadata above.
    env["PYTHONUTF8"] = "0"
    env["PYTHONCOERCECLOCALE"] = "0"
    env["LC_ALL"] = "C"
    env["LANG"] = "C"

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo, env),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo, env),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo, env))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == expected
        for result in results
    )


@requires_bash
@pytest.mark.parametrize(
    "template_name",
    ["missing-template", "../../../outside"],
    ids=["missing", "path_traversal"],
)
def test_all_variants_reject_unresolvable_template(
    tmp_path: Path, template_name: str
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    (repo / "outside.md").write_text("sensitive content\n", encoding="utf-8")

    results = [
        run(bash_cmd(repo, SCRIPT, template_name, "--json"), repo),
        run(py_cmd(repo, SCRIPT, template_name, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, template_name, "-Json"), repo))

    assert all(result.returncode == 1 for result in results)
    assert all(result.stdout == "" for result in results)
    assert all("sensitive content" not in result.stderr for result in results)


@requires_bash
def test_all_variants_ignore_traversing_preset_registry_ids(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    outside = repo.parent / "outside"
    outside.mkdir()
    (outside / f"{TEMPLATE}.md").write_text("sensitive content\n", encoding="utf-8")
    presets = repo / ".specify" / "presets"
    presets.mkdir(parents=True)
    (presets / ".registry").write_text(
        '{"presets":{"../../../outside":{"enabled":true,"priority":1}}}\n',
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 1 for result in results)
    assert all("sensitive content" not in result.stdout for result in results)


@requires_bash
def test_all_variants_support_root_level_preset_convention(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    preset = repo / ".specify" / "presets" / "root-pack"
    preset.mkdir(parents=True)
    (preset / f"{TEMPLATE}.md").write_text("# Root convention\n", encoding="utf-8")
    (repo / ".specify" / "presets" / ".registry").write_text(
        '{"presets":{"root-pack":{"enabled":true,"priority":1}}}\n',
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == "# Root convention\n"
        for result in results
    )


@requires_bash
def test_all_variants_honor_extension_registry_state_and_priority(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    extensions = repo / ".specify" / "extensions"
    for extension_id, content in (
        ("disabled-ext", "# Disabled\n"),
        ("low-priority", "# Low priority\n"),
        ("high-priority", "# High priority\n"),
    ):
        template_dir = extensions / extension_id / "templates"
        template_dir.mkdir(parents=True)
        (template_dir / f"{TEMPLATE}.md").write_text(content, encoding="utf-8")
    (extensions / ".registry").write_text(
        '{"extensions":{'
        '"disabled-ext":{"enabled":null,"priority":1},'
        '"low-priority":{"enabled":true,"priority":20},'
        '"high-priority":{"enabled":true,"priority":5}'
        "}}\n",
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == "# High priority\n"
        for result in results
    )


@requires_bash
def test_all_variants_support_root_level_extension_convention(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    extension = repo / ".specify" / "extensions" / "root-extension"
    extension.mkdir(parents=True)
    (extension / f"{TEMPLATE}.md").write_text(
        "# Root extension\n",
        encoding="utf-8",
    )
    (repo / ".specify" / "extensions" / ".registry").write_text(
        '{"extensions":{"root-extension":{"enabled":true,"priority":1}}}\n',
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == "# Root extension\n"
        for result in results
    )


@requires_bash
def test_all_variants_treat_extension_registry_ids_case_sensitively(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    extension = repo / ".specify" / "extensions" / "foo" / "templates"
    extension.mkdir(parents=True)
    (extension / f"{TEMPLATE}.md").write_text(
        "# Lowercase extension\n",
        encoding="utf-8",
    )
    (repo / ".specify" / "extensions" / ".registry").write_text(
        '{"extensions":{"FOO":{"enabled":true,"priority":1}}}\n',
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == "# Lowercase extension\n"
        for result in results
    )


@requires_bash
@pytest.mark.parametrize(
    "registry_content",
    ["{ not valid json", '{"extensions":[]}\n', "[]\n"],
    ids=["invalid_json", "non_mapping_extensions", "non_mapping_root"],
)
def test_all_variants_fail_for_malformed_extension_registry(
    tmp_path: Path, registry_content: str
) -> None:
    """A corrupt extension registry must fail closed, not silently enable
    every on-disk extension directory as unregistered."""
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    extensions = repo / ".specify" / "extensions"
    template_dir = extensions / "sneaky-ext" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / f"{TEMPLATE}.md").write_text(
        "# Should not be served\n", encoding="utf-8"
    )
    (extensions / ".registry").write_text(registry_content, encoding="utf-8")

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)
    assert all(
        "Should not be served" not in result.stdout for result in results
    )


@requires_bash
def test_all_variants_fail_when_registry_is_a_directory(
    tmp_path: Path,
) -> None:
    """A directory at the extension registry path must fail closed, not be
    treated as an absent registry that enables every on-disk extension."""
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    extensions = repo / ".specify" / "extensions"
    template_dir = extensions / "sneaky-ext" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / f"{TEMPLATE}.md").write_text(
        "# Should not be served\n", encoding="utf-8"
    )
    # Create ``.registry`` as a directory rather than a regular file.
    (extensions / ".registry").mkdir()

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)


@requires_bash
def test_all_variants_fail_when_registry_is_broken_symlink(
    tmp_path: Path,
) -> None:
    """A broken symlink at the extension registry path must fail closed across
    Bash, Python, and PowerShell resolvers rather than being treated as absent."""
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    extensions = repo / ".specify" / "extensions"
    template_dir = extensions / "sneaky-ext" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / f"{TEMPLATE}.md").write_text(
        "# Should not be served\n", encoding="utf-8"
    )
    (extensions / ".registry").symlink_to(extensions / "does-not-exist")

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)


@requires_bash
@pytest.mark.parametrize("base_kind", ["override", "preset"])
def test_all_variants_ignore_malformed_layers_below_replace_base(
    tmp_path: Path,
    base_kind: str,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    expected = "# Winning base\r\nBody\r\n"
    presets = repo / ".specify" / "presets"

    if base_kind == "override":
        override = repo / ".specify" / "templates" / "overrides"
        override.mkdir(parents=True)
        (override / f"{TEMPLATE}.md").write_bytes(expected.encode("utf-8"))
        registry = {"presets": {"broken-pack": {"enabled": True, "priority": 1}}}
    else:
        winning = presets / "winning-pack" / "templates"
        winning.mkdir(parents=True)
        (winning / f"{TEMPLATE}.md").write_bytes(expected.encode("utf-8"))
        registry = {
            "presets": {
                "winning-pack": {"enabled": True, "priority": 1},
                "broken-pack": {"enabled": True, "priority": 2},
            }
        }

    broken = presets / "broken-pack"
    broken.mkdir(parents=True)
    (broken / "preset.yml").write_text("provides: [\n", encoding="utf-8")
    (presets / ".registry").write_text(
        json.dumps(registry, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == expected
        for result in results
    )


@requires_bash
@pytest.mark.parametrize(
    ("entries", "expected"),
    [
        (
            [
                ("disabled-pack", {"enabled": False, "priority": 0}),
                ("numeric-pack", {"enabled": True, "priority": 2}),
                ("string-pack", {"enabled": True, "priority": "1"}),
            ],
            "# string-pack\n",
        ),
        (
            [
                ("z-pack", {"enabled": True}),
                ("a-pack", {"enabled": True}),
            ],
            "# a-pack\n",
        ),
        (
            [
                ("float-pack", {"enabled": True, "priority": 5.9}),
                ("six-pack", {"enabled": True, "priority": 6}),
            ],
            "# float-pack\n",
        ),
        (
            [
                ("a-huge-pack", {"enabled": True, "priority": 2147483648}),
                ("z-default-pack", {"enabled": True, "priority": "invalid"}),
            ],
            "# z-default-pack\n",
        ),
        (
            [
                ("decimal-string-pack", {"enabled": True, "priority": "5.9"}),
                ("exponent-string-pack", {"enabled": True, "priority": "1e3"}),
                ("hex-string-pack", {"enabled": True, "priority": "0x10"}),
                ("six-pack", {"enabled": True, "priority": 6}),
            ],
            "# six-pack\n",
        ),
    ],
    ids=[
        "mixed_priorities",
        "equal_priority_id_tiebreaker",
        "float_priority",
        "large_integer_priority",
        "non_integer_numeric_strings",
    ],
)
def test_all_variants_normalize_and_tiebreak_preset_priorities(
    tmp_path: Path,
    entries: list[tuple[str, dict[str, object]]],
    expected: str,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    presets = repo / ".specify" / "presets"
    registry: dict[str, object] = {"presets": {}}
    registry_presets = registry["presets"]
    assert isinstance(registry_presets, dict)
    for preset_id, metadata in entries:
        template_dir = presets / preset_id / "templates"
        template_dir.mkdir(parents=True)
        (template_dir / f"{TEMPLATE}.md").write_text(
            f"# {preset_id}\n",
            encoding="utf-8",
        )
        registry_presets[preset_id] = metadata
    (presets / ".registry").write_text(
        json.dumps(registry, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode == 0 for result in results)
    assert all(
        json_stdout(result)["TEMPLATE_CONTENT"] == expected
        for result in results
    )


@requires_bash
def test_all_variants_fail_when_wrap_placeholder_is_missing(
    tmp_path: Path,
) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    templates = repo / ".specify" / "templates"
    templates.mkdir(parents=True)
    (templates / f"{TEMPLATE}.md").write_text("# Core\n", encoding="utf-8")
    preset = repo / ".specify" / "presets" / "wrap-pack"
    (preset / "templates").mkdir(parents=True)
    (preset / "templates" / f"{TEMPLATE}.md").write_text(
        "# Broken wrapper\n", encoding="utf-8"
    )
    (preset / "preset.yml").write_text(
        "provides:\n"
        "  templates:\n"
        "    - type: template\n"
        f"      name: {TEMPLATE}\n"
        f"      file: templates/{TEMPLATE}.md\n"
        "      strategy: wrap\n",
        encoding="utf-8",
    )
    (repo / ".specify" / "presets" / ".registry").write_text(
        '{"presets":{"wrap-pack":{"enabled":true,"priority":1}}}\n',
        encoding="utf-8",
    )

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)


@requires_bash
def test_all_variants_fail_when_yaml_parser_is_unavailable(
    tmp_path: Path,
) -> None:
    repo, _ = _setup_repo(tmp_path)
    blocker = tmp_path / "blocker"
    blocker.mkdir()
    (blocker / "yaml.py").write_text(
        "raise ImportError('simulated missing PyYAML')\n",
        encoding="utf-8",
    )
    env = clean_env()
    env["PYTHONPATH"] = str(blocker)

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo, env),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo, env),
    ]
    if HAS_POWERSHELL:
        results.append(
            run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo, env)
        )

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)


@requires_bash
def test_bash_fails_when_override_read_fails(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    install_scripts(repo, SCRIPT)
    override = repo / ".specify" / "templates" / "overrides"
    override.mkdir(parents=True)
    (override / f"{TEMPLATE}.md").write_text("# Override\n", encoding="utf-8")
    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    cat_shim = shim_dir / "cat"
    cat_shim.write_text(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "  */.specify/templates/overrides/*) exit 1 ;;\n"
        "esac\n"
        "exec /bin/cat \"$@\"\n",
        encoding="utf-8",
    )
    cat_shim.chmod(0o755)
    env = clean_env()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"

    result = run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo, env)

    assert result.returncode != 0
    assert result.stdout == ""


@requires_bash
@pytest.mark.parametrize(
    "manifest_content",
    [
        "provides: [\n",
        "",
        "provides:\n  templates:\n    - null\n",
        "provides:\n  templates: {}\n",
        "preset:\n  id: wrap-pack\n",
        "provides:\n  templates: []\n",
        f"""provides:
  templates:
    - type: template
      name: {TEMPLATE}
      file: null
      strategy: wrap
""",
        f"""provides:
  templates:
    - type: template
      name: {TEMPLATE}
      file: templates/{TEMPLATE}.md
      strategy: 123
""",
        f"""provides:
  templates:
    - type: template
      name: {TEMPLATE}
      file: templates/{TEMPLATE}.md
      strategy: wrap
    - type: template
      name: unrelated-template
      file: null
      strategy: append
""",
        f"""provides:
  templates:
    - name: {TEMPLATE}
      file: templates/{TEMPLATE}.md
      strategy: wrap
    - type: template
      name: unrelated-template
      file: templates/other.md
""",
        f"""provides:
  templates:
    - type: template
      name: {TEMPLATE}
      file: templates/{TEMPLATE}.md
      strategy: wrap
    - type: template
      name: unrelated-template
""",
        f"""provides:
  templates:
    - type: template
      name: {TEMPLATE}
      file: templates/{TEMPLATE}.md
      strategy: wrap
    - type: bogus
      name: unrelated-template
      file: templates/other.md
""",
        f"""provides:
  templates:
    - type: template
      name: {TEMPLATE}
      file: templates/{TEMPLATE}.md
      strategy: wrap
    - type: template
      name: unrelated-template
      file: templates/other.md
      strategy: merge
""",
    ],
    ids=[
        "invalid_yaml",
        "empty_document",
        "non_mapping_template_entry",
        "non_list_templates",
        "missing_provides",
        "empty_templates",
        "non_string_file",
        "non_string_strategy",
        "malformed_entry_after_match",
        "entry_missing_type",
        "entry_missing_file",
        "unsupported_type",
        "unsupported_strategy",
    ],
)
def test_all_variants_fail_for_malformed_preset_manifest(
    tmp_path: Path,
    manifest_content: str,
) -> None:
    repo, _ = _setup_repo(tmp_path)
    (
        repo / ".specify" / "presets" / "wrap-pack" / "preset.yml"
    ).write_text(manifest_content, encoding="utf-8")

    results = [
        run(bash_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
        run(py_cmd(repo, SCRIPT, TEMPLATE, "--json"), repo),
    ]
    if HAS_POWERSHELL:
        results.append(run(ps_cmd(repo, SCRIPT, TEMPLATE, "-Json"), repo))

    assert all(result.returncode != 0 for result in results)
    assert all(result.stdout == "" for result in results)
