"""Shared constants for compilation extensions (constitution injection, etc.).

Also contains shared markers for build metadata stabilization. We intentionally
avoid timestamps in generated artifacts to guarantee byte-level idempotency; a
deterministic Build ID (content hash) is substituted post-generation.
"""

# Constitution injection markers
CONSTITUTION_MARKER_BEGIN = "<!-- SPEC-KIT CONSTITUTION: BEGIN -->"
CONSTITUTION_MARKER_END = "<!-- SPEC-KIT CONSTITUTION: END -->"
CONSTITUTION_RELATIVE_PATH = ".specify/memory/constitution.md"  # repo-root relative

# Build ID placeholder & regex pattern (line-level). The placeholder line is
# inserted during initial template generation; after all transformations
# (constitution injection, link resolution, etc.) we compute a SHA256 of the
# final content with this line removed and then replace it with the truncated
# hash. This ensures the hash is not self-referential and remains stable.
BUILD_ID_PLACEHOLDER = "<!-- Build ID: __BUILD_ID__ -->"
