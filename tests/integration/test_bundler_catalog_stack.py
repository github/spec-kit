"""Integration tests for the catalog stack: precedence, policy gating, search."""
from __future__ import annotations


import pytest

from specify_cli.bundler import BundlerError
from specify_cli.bundler.models.catalog import CatalogSource, InstallPolicy, Scope
from specify_cli.bundler.services.catalog_stack import CatalogStack
from tests.bundler_helpers import catalog_entry_dict, catalog_payload


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


def test_resolve_unknown_bundle_errors():
    stack = _stack(
        [_source("only", 1, "install-allowed")],
        {"only": catalog_payload({})},
    )
    with pytest.raises(BundlerError, match="not found"):
        stack.resolve("missing")


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


def test_unreachable_source_raises_named_error():
    def fetcher(src):
        raise RuntimeError("boom")
    stack = CatalogStack([_source("bad", 1, "install-allowed")], fetcher)
    with pytest.raises(BundlerError, match="bad"):
        stack.resolve("anything")
