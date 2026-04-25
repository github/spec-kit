"""Tests for the validate workflow step."""

from __future__ import annotations

import pytest

from specify_cli.workflows.base import StepContext, StepStatus
from specify_cli.workflows.steps.validate import (
    CustomRuleEngine,
    SchemaValidator,
    ValidateStep,
    ValidationError,
)


# ── SchemaValidator tests ───────────────────────────────────────────


class TestSchemaValidator:
    def setup_method(self):
        self.v = SchemaValidator()

    # -- type checks --

    def test_type_string_valid(self):
        errors = self.v.validate("hello", {"type": "string"})
        assert errors == []

    def test_type_string_invalid(self):
        errors = self.v.validate(42, {"type": "string"})
        assert len(errors) == 1
        assert errors[0].rule == "type"

    def test_type_integer_valid(self):
        assert self.v.validate(10, {"type": "integer"}) == []

    def test_type_number_accepts_int(self):
        assert self.v.validate(10, {"type": "number"}) == []

    def test_type_boolean(self):
        assert self.v.validate(True, {"type": "boolean"}) == []
        errors = self.v.validate("yes", {"type": "boolean"})
        assert len(errors) == 1

    def test_type_null(self):
        assert self.v.validate(None, {"type": "null"}) == []

    def test_type_array(self):
        assert self.v.validate([1, 2], {"type": "array"}) == []

    def test_type_object(self):
        assert self.v.validate({"a": 1}, {"type": "object"}) == []

    def test_unknown_type(self):
        errors = self.v.validate("x", {"type": "foobar"})
        assert len(errors) == 1
        assert "Unknown schema type" in errors[0].message

    # -- enum / const --

    def test_enum_valid(self):
        assert self.v.validate("a", {"enum": ["a", "b", "c"]}) == []

    def test_enum_invalid(self):
        errors = self.v.validate("z", {"enum": ["a", "b"]})
        assert len(errors) == 1
        assert errors[0].rule == "enum"

    def test_const_valid(self):
        assert self.v.validate(42, {"const": 42}) == []

    def test_const_invalid(self):
        errors = self.v.validate(43, {"const": 42})
        assert len(errors) == 1

    # -- string constraints --

    def test_minLength(self):
        assert self.v.validate("ab", {"type": "string", "minLength": 2}) == []
        errors = self.v.validate("a", {"type": "string", "minLength": 2})
        assert len(errors) == 1

    def test_maxLength(self):
        errors = self.v.validate("abcdef", {"type": "string", "maxLength": 3})
        assert len(errors) == 1

    def test_pattern_match(self):
        assert self.v.validate("v1.2.3", {"type": "string", "pattern": r"^\d+\.\d+"}) == []

    def test_pattern_no_match(self):
        errors = self.v.validate("abc", {"type": "string", "pattern": r"^\d+$"})
        assert len(errors) == 1

    # -- numeric constraints --

    def test_minimum(self):
        assert self.v.validate(5, {"type": "integer", "minimum": 5}) == []
        errors = self.v.validate(4, {"type": "integer", "minimum": 5})
        assert len(errors) == 1

    def test_maximum(self):
        errors = self.v.validate(11, {"type": "integer", "maximum": 10})
        assert len(errors) == 1

    def test_exclusive_minimum(self):
        errors = self.v.validate(5, {"type": "integer", "exclusiveMinimum": 5})
        assert len(errors) == 1
        assert self.v.validate(6, {"type": "integer", "exclusiveMinimum": 5}) == []

    def test_exclusive_maximum(self):
        errors = self.v.validate(10, {"type": "integer", "exclusiveMaximum": 10})
        assert len(errors) == 1

    def test_multiple_of(self):
        assert self.v.validate(9, {"type": "integer", "multipleOf": 3}) == []
        errors = self.v.validate(10, {"type": "integer", "multipleOf": 3})
        assert len(errors) == 1

    # -- array constraints --

    def test_min_items(self):
        errors = self.v.validate([], {"type": "array", "minItems": 1})
        assert len(errors) == 1

    def test_max_items(self):
        errors = self.v.validate([1, 2, 3], {"type": "array", "maxItems": 2})
        assert len(errors) == 1

    def test_unique_items(self):
        errors = self.v.validate([1, 2, 1], {"type": "array", "uniqueItems": True})
        assert len(errors) == 1

    def test_items_schema(self):
        schema = {"type": "array", "items": {"type": "integer"}}
        assert self.v.validate([1, 2, 3], schema) == []
        errors = self.v.validate([1, "x", 3], schema)
        assert len(errors) == 1
        assert "[1]" in errors[0].path

    # -- object constraints --

    def test_required_properties(self):
        schema = {"type": "object", "required": ["name"]}
        assert self.v.validate({"name": "foo"}, schema) == []
        errors = self.v.validate({}, schema)
        assert len(errors) == 1
        assert errors[0].rule == "required"

    def test_nested_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "minimum": 0},
            },
        }
        assert self.v.validate({"age": 25}, schema) == []
        errors = self.v.validate({"age": -1}, schema)
        assert len(errors) == 1
        assert "$.age" in errors[0].path

    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "properties": {"a": {"type": "string"}},
            "additionalProperties": False,
        }
        errors = self.v.validate({"a": "ok", "b": "nope"}, schema)
        assert len(errors) == 1
        assert errors[0].rule == "additionalProperties"

    # -- complex nested --

    def test_deeply_nested(self):
        schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["id"],
                        "properties": {
                            "id": {"type": "integer"},
                        },
                    },
                }
            },
        }
        data = {"users": [{"id": 1}, {"id": "bad"}]}
        errors = self.v.validate(data, schema)
        assert len(errors) == 1
        assert "$.users[1].id" in errors[0].path


# ── ValidationError tests ──────────────────────────────────────────


class TestValidationError:
    def test_to_dict(self):
        e = ValidationError("$.a", "oops", "required")
        d = e.to_dict()
        assert d == {"path": "$.a", "message": "oops", "rule": "required"}

    def test_to_dict_no_rule(self):
        e = ValidationError("$", "bad")
        d = e.to_dict()
        assert "rule" not in d

    def test_repr(self):
        e = ValidationError("$.x", "err")
        assert "$.x" in repr(e)


# ── ValidateStep tests ─────────────────────────────────────────────


class TestValidateStep:
    def setup_method(self):
        self.step = ValidateStep()

    def test_type_key(self):
        assert self.step.type_key == "validate"

    def test_valid_data_passes(self):
        ctx = StepContext(inputs={"name": "foo", "version": "1.0.0"})
        config = {
            "id": "check",
            "target": "{{ inputs }}",
            "schema": {
                "type": "object",
                "required": ["name", "version"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "version": {"type": "string"},
                },
            },
        }
        result = self.step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["valid"] is True
        assert result.output["error_count"] == 0

    def test_invalid_data_fails(self):
        ctx = StepContext(inputs={"name": ""})
        config = {
            "id": "check",
            "target": "{{ inputs }}",
            "schema": {
                "type": "object",
                "required": ["name", "version"],
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                },
            },
        }
        result = self.step.execute(config, ctx)
        assert result.status == StepStatus.FAILED
        assert result.output["valid"] is False
        assert result.output["error_count"] >= 1

    def test_fail_on_error_false_returns_completed(self):
        ctx = StepContext(inputs={"x": 1})
        config = {
            "id": "check",
            "target": "{{ inputs }}",
            "schema": {"type": "object", "required": ["missing"]},
            "fail_on_error": False,
        }
        result = self.step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["valid"] is False

    def test_validate_config_bad_schema(self):
        errors = self.step.validate({"id": "x", "schema": "not-a-dict"})
        assert any("schema" in e for e in errors)

    def test_validate_config_bad_custom_rules(self):
        errors = self.step.validate({"id": "x", "custom_rules": "not-a-list"})
        assert any("custom_rules" in e for e in errors)

    def test_validate_config_missing_id(self):
        errors = self.step.validate({})
        assert any("id" in e for e in errors)

    def test_literal_target(self):
        """When target is not an expression, use it directly."""
        ctx = StepContext()
        config = {
            "id": "check",
            "target": {"a": 1},
            "schema": {"type": "object", "required": ["a"]},
        }
        result = self.step.execute(config, ctx)
        assert result.status == StepStatus.COMPLETED
        assert result.output["valid"] is True
