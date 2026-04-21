"""Tests for src/specify_cli/integrations/claude/question_transformer.py"""

import pytest
from specify_cli.integrations.claude.question_transformer import (
    parse_clarify,
    parse_checklist,
    transform_question_block,
)

# ---------------------------------------------------------------------------
# _parse_table_rows (tested indirectly via parse_clarify / parse_checklist)
# ---------------------------------------------------------------------------


class TestParseClarify:
    def test_basic_options(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | First option |\n"
            "| B | Second option |\n"
        )
        result = parse_clarify(block)
        assert len(result) == 2
        assert result[0] == {"label": "A", "description": "First option"}
        assert result[1] == {"label": "B", "description": "Second option"}

    def test_recommended_em_dash_placed_first(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | Plain option |\n"
            "| B | Recommended — best practice |\n"
            "| C | Another option |\n"
        )
        result = parse_clarify(block)
        assert result[0]["label"] == "B"
        assert "Recommended" in result[0]["description"]

    def test_recommended_hyphen_placed_first(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | Plain option |\n"
            "| B | Recommended - use this |\n"
        )
        result = parse_clarify(block)
        assert result[0]["label"] == "B"

    def test_no_recommended_preserves_order(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | Alpha |\n"
            "| B | Beta |\n"
            "| C | Gamma |\n"
        )
        result = parse_clarify(block)
        assert [r["label"] for r in result] == ["A", "B", "C"]

    def test_indented_table_rows(self):
        """Rows with leading spaces (as in clarify.md template) must still parse."""
        block = (
            "       | Option | Description |\n"
            "       |--------|-------------|\n"
            "       | A | Option A desc |\n"
            "       | B | Option B desc |\n"
        )
        result = parse_clarify(block)
        assert len(result) == 2
        assert result[0]["label"] == "A"

    def test_empty_block_returns_empty(self):
        assert parse_clarify("") == []

    def test_header_only_returns_empty(self):
        block = "| Option | Description |\n|--------|-------------|\n"
        assert parse_clarify(block) == []

    def test_rows_with_extra_whitespace_stripped(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "|  A  |  Spaced out  |\n"
        )
        result = parse_clarify(block)
        assert result[0] == {"label": "A", "description": "Spaced out"}


class TestParseChecklist:
    def test_basic_rows(self):
        block = (
            "| Option | Candidate | Why It Matters |\n"
            "|--------|-----------|----------------|\n"
            "| A | Unit tests | Catches regressions |\n"
            "| B | Integration tests | Validates contracts |\n"
        )
        result = parse_checklist(block)
        assert len(result) == 2
        assert result[0] == {"label": "Unit tests", "description": "Catches regressions"}
        assert result[1] == {"label": "Integration tests", "description": "Validates contracts"}

    def test_indented_rows(self):
        block = (
            "     | Option | Candidate | Why It Matters |\n"
            "     |--------|-----------|----------------|\n"
            "     | A | Scope refinement | Focuses the checklist |\n"
        )
        result = parse_checklist(block)
        assert result[0]["label"] == "Scope refinement"

    def test_skips_rows_with_fewer_than_3_cells(self):
        block = (
            "| Option | Candidate | Why It Matters |\n"
            "|--------|-----------|----------------|\n"
            "| A | Only two cells |\n"
            "| B | Good | Has three |\n"
        )
        result = parse_checklist(block)
        assert len(result) == 1
        assert result[0]["label"] == "Good"

    def test_empty_block_returns_empty(self):
        assert parse_checklist("") == []


class TestTransformQuestionBlock:
    def _clarify_fenced(self, rows: str) -> str:
        return (
            "<!-- speckit:question-render:begin -->\n"
            "| Option | Description |\n"
            "|--------|-------------|\n"
            + rows
            + "<!-- speckit:question-render:end -->"
        )

    def _checklist_fenced(self, rows: str) -> str:
        return (
            "<!-- speckit:question-render:begin -->\n"
            "| Option | Candidate | Why It Matters |\n"
            "|--------|-----------|----------------|\n"
            + rows
            + "<!-- speckit:question-render:end -->"
        )

    # --- no-op passthrough ---

    def test_no_markers_returns_identical(self):
        text = "hello world, no markers here"
        assert transform_question_block(text) is not text or transform_question_block(text) == text

    def test_no_markers_byte_identical(self):
        text = "some content\nwith multiple lines\n"
        assert transform_question_block(text) == text

    # --- clarify schema ---

    def test_clarify_markers_replaced(self):
        content = self._clarify_fenced("| A | Option A |\n| B | Option B |\n")
        out = transform_question_block(content)
        assert "speckit:question-render" not in out

    def test_clarify_options_present(self):
        content = self._clarify_fenced("| A | Option A |\n| B | Option B |\n")
        out = transform_question_block(content)
        assert '"label": "A"' in out
        assert '"label": "B"' in out

    def test_clarify_other_appended(self):
        content = self._clarify_fenced("| A | Option A |\n")
        out = transform_question_block(content)
        assert '"label": "Other"' in out
        assert "Provide my own short answer" in out

    def test_clarify_recommended_first(self):
        content = self._clarify_fenced(
            "| A | Plain |\n"
            "| B | Recommended — best choice |\n"
        )
        out = transform_question_block(content)
        b_pos = out.index('"label": "B"')
        a_pos = out.index('"label": "A"')
        assert b_pos < a_pos

    def test_clarify_json_structure_valid(self):
        import json
        content = self._clarify_fenced("| A | Option A |\n")
        out = transform_question_block(content)
        # Extract JSON block
        json_str = out.split("```json\n")[1].split("\n```")[0]
        parsed = json.loads(json_str)
        assert parsed["multiSelect"] is False
        assert isinstance(parsed["options"], list)
        assert parsed["options"][-1]["label"] == "Other"

    # --- checklist schema ---

    def test_checklist_detected_by_candidate_column(self):
        content = self._checklist_fenced("| A | Unit tests | Catches bugs |\n")
        out = transform_question_block(content)
        assert '"label": "Unit tests"' in out
        assert '"description": "Catches bugs"' in out

    def test_checklist_other_appended(self):
        content = self._checklist_fenced("| A | Unit tests | Catches bugs |\n")
        out = transform_question_block(content)
        assert '"label": "Other"' in out

    # --- surrounding content preserved ---

    def test_content_before_markers_preserved(self):
        content = "Before text\n" + self._clarify_fenced("| A | Opt |\n") + "\nAfter text"
        out = transform_question_block(content)
        assert out.startswith("Before text")
        assert out.endswith("After text")

    def test_multiselect_false(self):
        import json
        content = self._clarify_fenced("| A | Option A |\n")
        out = transform_question_block(content)
        json_str = out.split("```json\n")[1].split("\n```")[0]
        assert json.loads(json_str)["multiSelect"] is False

    # --- special characters ---

    def test_quotes_in_description_escaped(self):
        content = self._clarify_fenced('| A | Say "hello" |\n')
        out = transform_question_block(content)
        # Should not produce invalid JSON
        import json
        json_str = out.split("```json\n")[1].split("\n```")[0]
        json.loads(json_str)  # must not raise


class TestEdgeCases:
    """Edge cases and robustness checks."""

    def test_duplicate_labels_deduplicated(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | First |\n"
            "| A | Duplicate |\n"
            "| B | Second |\n"
        )
        result = parse_clarify(block)
        labels = [r["label"] for r in result]
        assert labels.count("A") == 1
        assert result[0]["description"] == "First"  # first occurrence wins

    def test_empty_description_included(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | |\n"
        )
        result = parse_clarify(block)
        assert len(result) == 1
        assert result[0]["description"] == ""

    def test_recommended_case_insensitive(self):
        block = (
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | Plain |\n"
            "| B | recommended — lowercase |\n"
        )
        result = parse_clarify(block)
        assert result[0]["label"] == "B"

    def test_other_not_duplicated_if_already_present(self):
        """If table already has an 'Other' row, transformer must not add a second one."""
        fenced = (
            "<!-- speckit:question-render:begin -->\n"
            "| Option | Description |\n"
            "|--------|-------------|\n"
            "| A | Option A |\n"
            "| Other | My own answer |\n"
            "<!-- speckit:question-render:end -->"
        )
        out = transform_question_block(fenced)
        import json
        json_str = out.split("```json\n")[1].split("\n```")[0]
        parsed = json.loads(json_str)
        other_count = sum(1 for o in parsed["options"] if o["label"] == "Other")
        assert other_count == 1

    def test_output_is_valid_json(self):
        """Generated payload must always be parseable JSON."""
        import json
        fenced = (
            "<!-- speckit:question-render:begin -->\n"
            "| Option | Description |\n"
            "|--------|-------------|\n"
            '| A | Has "quotes" and \\backslash |\n'
            "<!-- speckit:question-render:end -->"
        )
        out = transform_question_block(fenced)
        json_str = out.split("```json\n")[1].split("\n```")[0]
        json.loads(json_str)  # must not raise

    def test_crlf_content_passthrough(self):
        """Content with CRLF line endings and no markers must be returned unchanged."""
        text = "line one\r\nline two\r\nno markers\r\n"
        assert transform_question_block(text) == text

    def test_checklist_duplicate_candidates_deduplicated(self):
        block = (
            "| Option | Candidate | Why It Matters |\n"
            "|--------|-----------|----------------|\n"
            "| A | Unit tests | First |\n"
            "| B | Unit tests | Duplicate |\n"
            "| C | Integration | Unique |\n"
        )
        result = parse_checklist(block)
        labels = [r["label"] for r in result]
        assert labels.count("Unit tests") == 1
        assert "Integration" in labels
