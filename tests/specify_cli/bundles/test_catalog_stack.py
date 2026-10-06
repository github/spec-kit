"""Integration tests for the catalog stack: precedence, policy gating, search."""
from __future__ import annotations


import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundles.catalogs import CatalogSource, InstallPolicy, Scope
from specify_cli.bundles.catalog_stack import CatalogStack
from tests.specify_cli.bundles.helpers import catalog_entry_dict, catalog_payload


def _source(source_id, priority, policy, url="builtin://x"):
    return CatalogSource(
        id=source_id, url=url, priority=priority,
        install_policy=InstallPolicy(policy), scope=Scope.PROJECT,
    )


def _stack(sources, payloads):
    def fetcher(src):
        return payloads[src.id]
    return CatalogStack(sources, fetcher)


def test_resolve_prefers_highest_precedence_source():
    sources = [
        _source("low", 2, "install-allowed"),
        _source("high", 1, "discovery-only"),
    ]
    payloads = {
        "high": catalog_payload({"b": catalog_entry_dict("b", version="9.0.0")}),
        "low": catalog_payload({"b": catalog_entry_dict("b", version="1.0.0")}),
    }
    resolved = _stack(sources, payloads).resolve("b")
    assert resolved.source.id == "high"
    assert resolved.entry.version == "9.0.0"
    assert resolved.install_allowed is False


def test_explicit_catalog_shadows_builtin_community_at_default_priority():
    sources = [
        _source("community", 20, "discovery-only"),
        _source("explicit", 10, "install-allowed"),
    ]
    payloads = {
        "community": catalog_payload({
            "shared": catalog_entry_dict("shared", version="1.0.0"),
        }),
        "explicit": catalog_payload({
            "shared": catalog_entry_dict("shared", version="2.0.0"),
        }),
    }

    resolved = _stack(sources, payloads).resolve("shared")

    assert resolved.source.id == "explicit"
    assert resolved.entry.version == "2.0.0"
    assert resolved.install_allowed is True


def test_resolve_unknown_bundle_errors():
    stack = _stack(
        [_source("only", 1, "install-allowed")],
        {"only": catalog_payload({})},
    )
    with pytest.raises(BundlerError, match="not found"):
        stack.resolve("missing")


def _history_release(version: str) -> dict:
    return {
        "download_url": f"https://example.com/history-{version}.zip",
        "sha256": "a" * 64,
    }


def test_resolve_selects_historical_release_from_winning_source():
    sources = [
        _source("high", 1, "install-allowed"),
        _source("low", 2, "install-allowed"),
    ]
    high = catalog_entry_dict(
        "history", version="2.0.0", releases={"1.0.0": _history_release("1.0.0")}
    )
    low = catalog_entry_dict(
        "history", version="1.0.0", download_url="https://example.com/lower.zip"
    )
    stack = _stack(
        sources,
        {"high": catalog_payload({"history": high}), "low": catalog_payload({"history": low})},
    )

    resolved = stack.resolve("history", "1.0.0")

    assert resolved.source.id == "high"
    assert resolved.entry.download_url == "https://example.com/history-1.0.0.zip"
    assert resolved.entry.version == "1.0.0"
    assert resolved.entry.source_id == "high"
    assert stack.resolve("history").entry.version == "2.0.0"


def test_resolve_does_not_fall_through_to_lower_source_with_the_version():
    sources = [
        _source("high", 1, "install-allowed"),
        _source("low", 2, "install-allowed"),
    ]
    high = catalog_entry_dict(
        "history", version="2.0.0", releases={"1.0.0": _history_release("1.0.0")}
    )
    low = catalog_entry_dict(
        "history",
        version="1.0.0",
        download_url="https://example.com/lower.zip",
        releases={"0.9.0": _history_release("0.9.0")},
    )
    stack = _stack(
        sources,
        {"high": catalog_payload({"history": high}), "low": catalog_payload({"history": low})},
    )

    with pytest.raises(BundlerError) as excinfo:
        stack.resolve("history", "0.9.0")

    message = str(excinfo.value)
    assert "no release 0.9.0 in catalog source 'high'" in message
    assert "(advertised: 2.0.0, 1.0.0)" in message
    assert "highest-precedence source" in message


def test_resolve_keeps_discovery_only_winner_with_the_version():
    sources = [
        _source("high", 1, "discovery-only"),
        _source("low", 2, "install-allowed"),
    ]
    high = catalog_entry_dict(
        "history", version="2.0.0", releases={"1.0.0": _history_release("1.0.0")}
    )
    low = catalog_entry_dict(
        "history", version="1.0.0", download_url="https://example.com/lower.zip"
    )
    stack = _stack(
        sources,
        {"high": catalog_payload({"history": high}), "low": catalog_payload({"history": low})},
    )

    resolved = stack.resolve("history", "1.0.0")

    assert resolved.source.id == "high"
    assert resolved.install_allowed is False
    assert resolved.entry.download_url == "https://example.com/history-1.0.0.zip"


@pytest.mark.parametrize(
    "releases",
    [[], {"1.1.0": {"download_url": "https://example.com/x.zip"}}, {"1.0": {}}],
)
def test_malformed_history_fails_resolve_and_search_at_load(releases):
    entry = catalog_entry_dict("history", releases=releases)
    stack = _stack(
        [_source("only", 1, "install-allowed")],
        {"only": catalog_payload({"history": entry})},
    )

    with pytest.raises(BundlerError, match="Bundle 'history'"):
        stack.resolve("history")
    with pytest.raises(BundlerError, match="Bundle 'history'"):
        stack.search()


def test_resolve_skips_shadowed_malformed_lower_precedence_source():
    stack = _stack(
        [_source("high", 1, "install-allowed"), _source("low", 2, "install-allowed")],
        {
            "high": catalog_payload({"history": catalog_entry_dict("history")}),
            "low": catalog_payload(
                {"history": catalog_entry_dict("history", releases=[])}
            ),
        },
    )

    assert stack.resolve("history").source.id == "high"
    with pytest.raises(BundlerError, match="Bundle 'history'"):
        stack.search()


def test_search_output_is_unchanged_by_release_history():
    plain = catalog_entry_dict("history")
    with_history = catalog_entry_dict(
        "history", releases={"1.0.0": _history_release("1.0.0")}
    )
    source = _source("only", 1, "install-allowed")

    plain_result = _stack([source], {"only": catalog_payload({"history": plain})}).search()
    history_result = _stack(
        [source], {"only": catalog_payload({"history": with_history})}
    ).search()

    assert [r.entry for r in history_result] == [r.entry for r in plain_result]
    assert history_result[0].entry.version == "1.2.0"


def test_resolve_preserves_release_history_through_provenance():
    entry = catalog_entry_dict(
        "history",
        releases={
            "1.0.0": {
                "download_url": "https://example.com/history-1.0.0.zip",
                "sha256": "a" * 64,
            }
        },
    )
    stack = _stack(
        [_source("only", 1, "discovery-only")],
        {"only": catalog_payload({"history": entry})},
    )

    resolved = stack.resolve("history")

    assert resolved.entry.raw == entry
    assert resolved.source.install_allowed is False


def test_search_dedupes_by_precedence_and_filters():
    sources = [_source("a", 1, "install-allowed"), _source("b", 2, "install-allowed")]
    payloads = {
        "a": catalog_payload({
            "alpha": catalog_entry_dict("alpha", role="developer"),
        }),
        "b": catalog_payload({
            "alpha": catalog_entry_dict("alpha", version="0.0.1"),
            "beta": catalog_entry_dict("beta", role="qa"),
        }),
    }
    stack = _stack(sources, payloads)

    all_results = stack.search()
    ids = [r.entry.id for r in all_results]
    assert ids == ["alpha", "beta"]
    # alpha resolved from the higher-precedence source 'a'.
    alpha = next(r for r in all_results if r.entry.id == "alpha")
    assert alpha.source.id == "a"

    qa_only = stack.search("qa")
    assert [r.entry.id for r in qa_only] == ["beta"]


def test_search_does_not_surface_a_shadowed_lower_precedence_entry():
    """Search must resolve each id at its highest-precedence source, then
    filter — never fall through to a shadowed lower-precedence entry the query
    happens to match.

    If the query matched only the lower-precedence copy of an id, search used
    to return that copy, even though `resolve()`/install always use the
    higher-precedence one. That advertised a bundle (name/version/source) the
    user could never actually get.
    """
    sources = [_source("high", 1, "install-allowed"), _source("low", 2, "install-allowed")]
    payloads = {
        # Highest-precedence entry for 'shared' does NOT match "widget".
        "high": catalog_payload({
            "shared": catalog_entry_dict(
                "shared", name="Alpha Tool", role="developer",
                description="nothing relevant", version="2.0.0",
            ),
        }),
        # Lower-precedence entry for the same id DOES match "widget".
        "low": catalog_payload({
            "shared": catalog_entry_dict(
                "shared", name="Searchable Widget", version="1.0.0",
            ),
        }),
    }
    stack = _stack(sources, payloads)

    # resolve() uses the high-precedence entry.
    assert stack.resolve("shared").source.id == "high"

    # A query that only the shadowed low-precedence entry matches returns
    # nothing — search agrees with resolve().
    assert stack.search("widget") == []

    # And a query the high-precedence entry matches returns it (from 'high').
    alpha = stack.search("alpha tool")
    assert [r.entry.id for r in alpha] == ["shared"]
    assert alpha[0].source.id == "high"


def test_unreachable_source_raises_named_error():
    def fetcher(src):
        raise RuntimeError("boom")
    stack = CatalogStack([_source("bad", 1, "install-allowed")], fetcher)
    with pytest.raises(BundlerError, match="bad"):
        stack.resolve("anything")
