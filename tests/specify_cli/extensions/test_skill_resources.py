"""Resource resolution and throwaway-manifest ownership tests."""

import os
import shutil
from pathlib import Path

import pytest

from specify_cli._install_ignore import load_install_ignore
from specify_cli.extensions import ValidationError
from specify_cli.extensions._skill_resources import (
    recorded_resource_hashes,
    remove_skill_resources,
    resolve_skill_resources,
    skills_resource_root,
    sync_skill_resources,
    track_skill_resource_writes,
    written_resource_hashes,
)
from specify_cli.integrations.manifest import _sha256


@pytest.mark.parametrize("metadata", [None, {}, {"skill_resource_hashes": []}])
def test_recorded_resource_hashes_ignores_missing_or_invalid_metadata(metadata):
    assert recorded_resource_hashes(metadata) == {}


def test_recorded_resource_hashes_copies_only_valid_buckets():
    metadata = {"skill_resource_hashes": {
        "project": {"skills/a": "hash"}, "home": [], "other": {"ignored": "hash"},
    }}
    hashes = recorded_resource_hashes(metadata)
    assert hashes == {"project": {"skills/a": "hash"}}
    hashes["project"]["skills/b"] = "new"
    assert metadata["skill_resource_hashes"]["project"] == {"skills/a": "hash"}


def put(path: Path, content: str = "source") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def link(path: Path, target: Path, *, directory: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")


def test_resolve_skill_resources_sorted_and_installed_ignore(tmp_path):
    source = tmp_path / "source"
    put(source / "assets/a.md")
    put(source / "assets/nested/b.md")
    put(source / "assets/ignored.md")
    put(source / "extension.yml")
    put(source / ".extensionignore", "assets/ignored.md\n")
    installed = tmp_path / "installed"
    shutil.copytree(source, installed, ignore=load_install_ignore(source, ".extensionignore", ValidationError))
    assert resolve_skill_resources(installed, ["assets/**", "assets/a.md", "assets/*.md"]) == [
        "assets/a.md", "assets/nested/b.md"
    ]
    assert resolve_skill_resources(installed, ["extension.yml"]) == ["extension.yml"]
    with pytest.raises(ValidationError, match="existing regular file"):
        resolve_skill_resources(installed, ["assets/ignored.md"])
    with pytest.raises(ValidationError, match="matches no files"):
        resolve_skill_resources(installed, ["assets/ignored*.md"])


def test_resolve_skill_resources_ignore_matches_copytree(tmp_path):
    source = tmp_path / "source"
    for name in ("a.md", "skipped/b.md", "kept/c.md", "kept/d.tmp", "kept/nested/e.md"):
        put(source / "assets" / name)
    put(source / ".extensionignore", "assets/skipped/\n*.tmp\n!assets/kept/d.tmp\nassets/kept/nested/\n")
    ignore = load_install_ignore(source, ".extensionignore", ValidationError)
    installed = tmp_path / "installed"
    shutil.copytree(source, installed, ignore=ignore)
    expected = sorted(
        p.relative_to(installed).as_posix() for p in (installed / "assets").rglob("*") if p.is_file()
    )
    assert resolve_skill_resources(source, ["assets/**"], ignore=ignore) == expected
    assert resolve_skill_resources(installed, ["assets/**"]) == expected
    assert "assets/skipped/b.md" not in expected and "assets/kept/nested/e.md" not in expected


@pytest.mark.parametrize("pattern", [
    "assets/skipped/b.md", "assets/skipped/*.md", "assets/kept/nested/e.md", ".extensionignore",
])
def test_resolve_skill_resources_ignore_excludes_unshipped_files(tmp_path, pattern):
    source = tmp_path / "source"
    put(source / "assets/skipped/b.md")
    put(source / "assets/kept/nested/e.md")
    put(source / ".extensionignore", "assets/skipped/\nassets/kept/nested/\n")
    ignore = load_install_ignore(source, ".extensionignore", ValidationError)
    with pytest.raises(ValidationError, match="excluded|matches no files"):
        resolve_skill_resources(source, [pattern], ignore=ignore)
    assert resolve_skill_resources(source, [pattern]) != []


def test_resolve_skill_resources_wildcards_skip_render_cache_and_manifest(tmp_path):
    ext = tmp_path / "ext"
    put(ext / "extension.yml")
    put(ext / "commands/run.md")
    put(ext / "assets/a.md")
    put(ext / ".specify-dev/agent-commands/claude/skill/SKILL.md")
    put(ext / "assets/extension.yml")  # only the root manifest is excluded
    assert resolve_skill_resources(ext, ["**"]) == [
        "assets/a.md", "assets/extension.yml", "commands/run.md",
    ]
    assert resolve_skill_resources(ext, ["**/*.md"]) == ["assets/a.md", "commands/run.md"]
    with pytest.raises(ValidationError, match="matches no files"):
        resolve_skill_resources(ext, [".specify-dev/**"])
    # An explicit manifest entry is a deliberate choice and still works.
    assert resolve_skill_resources(ext, ["extension.yml"]) == ["extension.yml"]
    with pytest.raises(ValidationError, match="internal render output"):
        resolve_skill_resources(ext, [".specify-dev/agent-commands/claude/skill/SKILL.md"])


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_resolve_skill_resources_wildcard_ignores_non_regular_files(tmp_path):
    ext = tmp_path / "ext"
    put(ext / "files/regular.md")
    os.mkfifo(ext / "files/pipe.md")
    assert resolve_skill_resources(ext, ["files/*.md"]) == ["files/regular.md"]
    with pytest.raises(ValidationError, match="existing regular file"):
        resolve_skill_resources(ext, ["files/pipe.md"])


@pytest.mark.parametrize("pattern", ["missing", "missing/*.md", "directory", "SKILL.md"])
def test_resolve_skill_resources_rejects_missing_or_reserved(tmp_path, pattern):
    ext = tmp_path / "ext"
    (ext / "directory").mkdir(parents=True)
    put(ext / "SKILL.md")
    with pytest.raises(ValidationError):
        resolve_skill_resources(ext, [pattern])
    assert sorted(p.name for p in ext.iterdir()) == ["SKILL.md", "directory"]


@pytest.mark.parametrize("pattern", ["assets/linked.md", "assets/*.md", "outside/file.md"])
def test_resolve_skill_resources_rejects_symlink_matches(tmp_path, pattern):
    ext = tmp_path / "ext"
    target = put(tmp_path / "outside/file.md")
    link(ext / "assets/linked.md", target)
    link(ext / "outside", target.parent, directory=True)
    with pytest.raises(ValidationError):
        resolve_skill_resources(ext, [pattern])
    assert target.read_text() == "source"


def test_sync_skill_resources_ownership_and_force(tmp_path):
    root = tmp_path / "project"
    skills = root / ".agent/skills"
    ext = tmp_path / "ext"
    for name in ("owned", "modified", "unowned", "new"):
        put(ext / name, "new-" + name)
    skill = skills / "skill-one"
    owned = put(skill / "owned", "old")
    modified = put(skill / "modified", "old")
    unowned = put(skill / "unowned", "user")
    previous = {p.relative_to(root).as_posix(): _sha256(p) for p in (owned, modified)}
    modified.write_text("user edit")

    hashes, written, warnings = sync_skill_resources(
        "ext", skills, root, "skill-one", ext, ["owned", "modified", "unowned", "new"], previous
    )
    assert owned.read_text() == "new-owned"
    assert modified.read_text() == "user edit"
    assert unowned.read_text() == "user"
    assert set(written) == {owned, skill / "new"}
    assert hashes[modified.relative_to(root).as_posix()] == previous[modified.relative_to(root).as_posix()]
    assert unowned.relative_to(root).as_posix() not in hashes
    assert hashes[owned.relative_to(root).as_posix()] == _sha256(owned)
    assert any("--force" in warning for warning in warnings)
    assert any("unowned" in warning for warning in warnings)

    again, written, warnings = sync_skill_resources(
        "ext", skills, root, "skill-one", ext, ["modified"], hashes
    )
    assert again == {modified.relative_to(root).as_posix(): previous[modified.relative_to(root).as_posix()]}
    assert not written and warnings and modified.read_text() == "user edit"

    hashes, written, warnings = sync_skill_resources(
        "ext", skills, root, "skill-one", ext, ["modified", "unowned"], hashes,
        overwrite_modified=True,
    )
    assert set(written) == {modified, unowned}
    assert modified.read_text() == "new-modified"
    assert unowned.read_text() == "new-unowned"
    assert hashes[unowned.relative_to(root).as_posix()] == _sha256(unowned)
    assert not warnings


def test_sync_skill_resources_does_not_follow_symlinked_destination(tmp_path):
    root = tmp_path / "project"
    ext = tmp_path / "ext"
    put(ext / "r")
    target = put(tmp_path / "outside/r", "untouched")
    skills = root / "skills"
    link(skills / "skill/r", target)
    hashes, written, warnings = sync_skill_resources(
        "ext", skills, root, "skill", ext, ["r"], {}, overwrite_modified=True
    )
    assert not hashes and not written and warnings
    assert target.read_text() == "untouched"


def test_sync_skill_resources_rejects_symlinked_skills_directory(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    target = tmp_path / "outside"
    target.mkdir()
    skills = root / "skills"
    link(skills, target, directory=True)
    with pytest.raises(ValueError):
        sync_skill_resources("ext", skills, root, "skill", tmp_path, [], {})
    assert list(target.iterdir()) == []


def test_remove_skill_resources_uses_recorded_paths_and_confines_names(tmp_path):
    root = tmp_path / "project"
    recorded = put(root / "old/skills/skill/references/a", "original")
    other = put(root / "old/skills/other/a", "other")
    target = put(tmp_path / "outside/target", "outside")
    leaf = root / "old/skills/skill/link"
    link(leaf, target)
    ancestor = root / "old/skills/skill/linked-dir"
    link(ancestor, target.parent, directory=True)
    hashes = {
        recorded.relative_to(root).as_posix(): _sha256(recorded),
        other.relative_to(root).as_posix(): _sha256(other),
        leaf.relative_to(root).as_posix(): "old-hash",
        (ancestor / "target").relative_to(root).as_posix(): "old-hash",
        "old/skills/skill/../other/a": "invalid",
        "old//skills/skill/a": "invalid",
        "../outside/target": "invalid",
    }
    recorded.write_text("modified")
    removed, skipped = remove_skill_resources("ext", root, hashes, {"skill"})
    assert set(removed) == {recorded, leaf}
    assert set(skipped) == {
        other, ancestor / "target", root / "old/skills/skill/../other/a",
        root / "old//skills/skill/a", root / "../outside/target",
    }
    assert other.read_text() == "other"
    assert target.read_text() == "outside"
    assert not leaf.is_symlink()


def test_remove_skill_resources_skips_symlinked_skills_directory(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    target = put(tmp_path / "outside/skill/a", "outside")
    link(root / "skills", target.parent.parent, directory=True)
    removed, skipped = remove_skill_resources(
        "ext", root, {"skills/skill/a": "old-hash"}, {"skill"}
    )
    assert not removed and skipped == [root / "skills/skill/a"]
    assert target.read_text() == "outside"


def test_home_resource_root_and_manifest(monkeypatch, tmp_path):
    home = tmp_path / "home"
    project = home / "project"
    skills = home / ".hermes/skills"
    project.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    assert skills_resource_root(project, project / ".agent/skills") == ("project", project)
    assert skills_resource_root(project, skills) == ("home", home)
    assert skills_resource_root(project, tmp_path / "elsewhere") is None
    ext = tmp_path / "ext"
    put(ext / "references/a")
    hashes, written, warnings = sync_skill_resources(
        "ext", skills, home, "skill", ext, ["references/a"], {}
    )
    dest = skills / "skill/references/a"
    assert written == [dest] and not warnings
    assert hashes == {".hermes/skills/skill/references/a": _sha256(dest)}
    removed, skipped = remove_skill_resources("ext", home, hashes, {"skill"})
    assert removed == [dest] and not skipped
    assert not (home / ".specify/integrations/ext.manifest.json").exists()


def test_sync_skill_resources_continues_after_record_file_failure(tmp_path, monkeypatch):
    root = tmp_path / "project"
    ext = tmp_path / "ext"
    put(ext / "bad")
    put(ext / "good")
    bad = root / "skills/skill/bad"
    previous = {bad.relative_to(root).as_posix(): "previous-hash"}
    from specify_cli.integrations.manifest import IntegrationManifest

    original = IntegrationManifest.record_file

    def record(self, rel, data, **kwargs):
        if rel.endswith("/bad"):
            raise OSError("destination changed")
        return original(self, rel, data, **kwargs)

    monkeypatch.setattr(IntegrationManifest, "record_file", record)
    hashes, written, warnings = sync_skill_resources(
        "ext", root / "skills", root, "skill", ext, ["bad", "good"], previous
    )
    assert hashes[bad.relative_to(root).as_posix()] == "previous-hash"
    assert written == [root / "skills/skill/good"]
    assert any("destination changed" in warning for warning in warnings)


@pytest.mark.parametrize("name", ["skill.md", "Skill.MD"])
def test_resolve_skill_resources_rejects_case_variants_of_reserved_name(tmp_path, name):
    ext = tmp_path / "ext"
    put(ext / name)
    put(ext / "sub/SKILL.md")
    assert resolve_skill_resources(ext, ["sub/SKILL.md"]) == ["sub/SKILL.md"]
    with pytest.raises(ValidationError, match="SKILL.md"):
        resolve_skill_resources(ext, [name])


def test_sync_skill_resources_continues_after_late_source_validation_failure(tmp_path, monkeypatch):
    from specify_cli.extensions import _skill_resources

    root = tmp_path / "project"
    ext = tmp_path / "ext"
    put(ext / "first", "first bytes")
    put(ext / "second", "second bytes")
    original = _skill_resources._validate_record_path

    def validate(path, trusted_root):
        if path == Path("second") and trusted_root == ext.resolve():
            raise ValueError("source changed")
        return original(path, trusted_root)

    monkeypatch.setattr(_skill_resources, "_validate_record_path", validate)
    hashes, written, warnings = sync_skill_resources(
        "ext", root / "skills", root, "skill", ext, ["first", "second"], {}
    )
    first = root / "skills/skill/first"
    assert first.read_text() == "first bytes"
    assert written == [first]
    assert hashes == {"skills/skill/first": _sha256(first)}
    assert any("second" in warning and "source changed" in warning for warning in warnings)
    assert not (root / "skills/skill/second").exists()


def test_retire_skill_resources_home_bucket_only_under_configured_skills_dir(monkeypatch, tmp_path):
    from specify_cli.extensions._skill_resources import retire_skill_resources

    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    name = "speckit-test-ext-run"
    owned = put(home / ".hermes/skills" / name / "references/r.md")
    unrelated = put(home / "Documents" / name / "notes.md")
    in_project = put(project / ".claude/skills" / name / "references/r.md")
    hashes = {
        "home": {
            owned.relative_to(home).as_posix(): "any",
            unrelated.relative_to(home).as_posix(): "any",
        },
        "project": {in_project.relative_to(project).as_posix(): "any"},
    }
    retire_skill_resources(project, "test-ext", hashes, {name})
    assert not owned.exists() and not in_project.exists()
    assert unrelated.read_text() == "source"
    assert hashes == {"home": {unrelated.relative_to(home).as_posix(): "any"}}


def test_retire_skill_resources_ignores_home_dirs_of_unflagged_agents(monkeypatch, tmp_path):
    from specify_cli.agents import CommandRegistrar
    from specify_cli.extensions._skill_resources import retire_skill_resources

    home, project = tmp_path / "home", tmp_path / "project"
    project.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    name = "speckit-test-ext-run"
    resource = put(home / ".other/skills" / name / "references/r.md")
    other = {"dir": "~/.other/skills", "extension": "/SKILL.md", "format": "markdown", "args": "$ARGUMENTS"}
    monkeypatch.setitem(CommandRegistrar.AGENT_CONFIGS, "other", other)
    hashes = {"home": {resource.relative_to(home).as_posix(): "any"}}
    retire_skill_resources(project, "test-ext", hashes, {name})
    assert resource.exists() and hashes["home"]

    monkeypatch.setitem(CommandRegistrar.AGENT_CONFIGS, "other", {**other, "home_scoped": True})
    retire_skill_resources(project, "test-ext", hashes, {name})
    assert not resource.exists() and hashes == {}


def test_written_resource_hashes_selects_only_files_written_in_the_attempt(tmp_path):
    root = tmp_path / "project"
    ext = tmp_path / "ext"
    skills = root / "skills"
    put(ext / "unchanged", "same")
    put(ext / "preserved", "package")
    put(ext / "unowned", "package")
    skill = skills / "skill-one"
    put(skill / "unchanged", "same")  # recorded, rewritten with identical bytes
    preserved = put(skill / "preserved", "package")
    put(skill / "unowned", "user")
    previous = {p.relative_to(root).as_posix(): _sha256(p) for p in (skill / "unchanged", preserved)}
    preserved.write_text("user edit")

    with track_skill_resource_writes() as written:
        hashes, _, _ = sync_skill_resources(
            "ext", skills, root, "skill-one", ext, ["unchanged", "preserved", "unowned"], previous,
        )
    key = lambda name: (skill / name).relative_to(root).as_posix()  # noqa: E731
    # The unchanged file keeps its digest but was written; the preserved one
    # keeps its record without being written; the unowned one is not recorded.
    assert hashes[key("unchanged")] == previous[key("unchanged")]
    assert key("preserved") in hashes and key("unowned") not in hashes
    assert written_resource_hashes(root, {"project": hashes}, written) == {
        "project": {key("unchanged"): hashes[key("unchanged")]}
    }


def test_track_skill_resource_writes_chains_the_outer_observer(tmp_path):
    from specify_cli.integrations._file_changes import file_change_observer

    seen = []
    token = file_change_observer.set(lambda path, before, removal: seen.append((path.name, before)))
    try:
        ext = tmp_path / "ext"
        put(ext / "r")
        with track_skill_resource_writes() as written:
            sync_skill_resources("ext", tmp_path / "project/skills", tmp_path / "project", "s", ext, ["r"], {})
        assert {path.name for path in written} == {"r"}
        assert ("r", True) in seen and ("r", False) in seen
        assert file_change_observer.get() is not None
    finally:
        file_change_observer.reset(token)
    assert file_change_observer.get() is None
