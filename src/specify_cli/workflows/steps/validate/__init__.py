"""Validate step — JSON schema validation with custom rules.

Validates step context data (inputs, step outputs, or arbitrary JSON)
against a JSON-Schema-like rule set, then aggregates errors into a
detailed report stored in ``output``.
"""

from __future__ import annotations

import re
from typing import Any

from specify_cli.workflows.base import StepBase, StepContext, StepResult, StepStatus
from specify_cli.workflows.expressions import evaluate_expression


# ── Schema types ────────────────────────────────────────────────────

_VALID_TYPES = {"string", "integer", "number", "boolean", "array", "object", "null"}


def _python_type_name(value: Any) -> str:
    """Map a Python value to its JSON-schema type name."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


# ── Schema validator ────────────────────────────────────────────────

class ValidationError:
    """A single validation error with path and message."""

    __slots__ = ("path", "message", "rule")

    def __init__(self, path: str, message: str, rule: str = "") -> None:
        self.path = path
        self.message = message
        self.rule = rule

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {"path": self.path, "message": self.message}
        if self.rule:
            d["rule"] = self.rule
        return d

    def __repr__(self) -> str:
        return f"ValidationError(path={self.path!r}, message={self.message!r})"


class SchemaValidator:
    """Validate a value against a JSON-schema-like definition."""

    def __init__(self) -> None:
        self.errors: list[ValidationError] = []

    def validate(self, value: Any, schema: dict[str, Any], path: str = "$") -> list[ValidationError]:
        """Validate *value* against *schema* and return all errors."""
        self.errors = []
        self._validate_node(value, schema, path)
        return list(self.errors)

    def _add_error(self, path: str, message: str, rule: str = "") -> None:
        self.errors.append(ValidationError(path, message, rule))

    def _validate_node(self, value: Any, schema: dict[str, Any], path: str) -> None:
        # ── required check (handled at object level) ──
        # ── type check ──
        expected_type = schema.get("type")
        if expected_type is not None:
            if expected_type not in _VALID_TYPES:
                self._add_error(path, f"Unknown schema type: {expected_type!r}", "type")
                return
            actual = _python_type_name(value)
            # Allow integer where number is expected
            if expected_type == "number" and actual == "integer":
                actual = "number"
            if actual != expected_type:
                self._add_error(
                    path,
                    f"Expected type {expected_type!r} but got {actual!r}",
                    "type",
                )
                return  # skip further checks if type is wrong

        # ── enum ──
        if "enum" in schema:
            if value not in schema["enum"]:
                self._add_error(
                    path,
                    f"Value {value!r} is not one of {schema['enum']!r}",
                    "enum",
                )

        # ── const ──
        if "const" in schema:
            if value != schema["const"]:
                self._add_error(
                    path,
                    f"Value must be {schema['const']!r}",
                    "const",
                )

        # ── string constraints ──
        if isinstance(value, str):
            if "minLength" in schema and len(value) < schema["minLength"]:
                self._add_error(
                    path,
                    f"String length {len(value)} is less than minimum {schema['minLength']}",
                    "minLength",
                )
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                self._add_error(
                    path,
                    f"String length {len(value)} exceeds maximum {schema['maxLength']}",
                    "maxLength",
                )
            if "pattern" in schema:
                if not re.search(schema["pattern"], value):
                    self._add_error(
                        path,
                        f"String does not match pattern {schema['pattern']!r}",
                        "pattern",
                    )

        # ── numeric constraints ──
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in schema and value < schema["minimum"]:
                self._add_error(
                    path,
                    f"Value {value} is less than minimum {schema['minimum']}",
                    "minimum",
                )
            if "maximum" in schema and value > schema["maximum"]:
                self._add_error(
                    path,
                    f"Value {value} exceeds maximum {schema['maximum']}",
                    "maximum",
                )
            if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
                self._add_error(
                    path,
                    f"Value {value} must be > {schema['exclusiveMinimum']}",
                    "exclusiveMinimum",
                )
            if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
                self._add_error(
                    path,
                    f"Value {value} must be < {schema['exclusiveMaximum']}",
                    "exclusiveMaximum",
                )
            if "multipleOf" in schema and value % schema["multipleOf"] != 0:
                self._add_error(
                    path,
                    f"Value {value} is not a multiple of {schema['multipleOf']}",
                    "multipleOf",
                )

        # ── array constraints ──
        if isinstance(value, list):
            if "minItems" in schema and len(value) < schema["minItems"]:
                self._add_error(
                    path,
                    f"Array length {len(value)} is less than minimum {schema['minItems']}",
                    "minItems",
                )
            if "maxItems" in schema and len(value) > schema["maxItems"]:
                self._add_error(
                    path,
                    f"Array length {len(value)} exceeds maximum {schema['maxItems']}",
                    "maxItems",
                )
            if schema.get("uniqueItems") and len(value) != len(set(repr(v) for v in value)):
                self._add_error(path, "Array items are not unique", "uniqueItems")
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(value):
                    self._validate_node(item, items_schema, f"{path}[{i}]")

        # ── object constraints ──
        if isinstance(value, dict):
            required_keys = schema.get("required", [])
            for rk in required_keys:
                if rk not in value:
                    self._add_error(
                        f"{path}.{rk}",
                        f"Missing required property {rk!r}",
                        "required",
                    )
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                if prop_name in value:
                    self._validate_node(
                        value[prop_name], prop_schema, f"{path}.{prop_name}"
                    )
            additional = schema.get("additionalProperties")
            if additional is False:
                allowed = set(properties.keys())
                for k in value:
                    if k not in allowed:
                        self._add_error(
                            f"{path}.{k}",
                            f"Additional property {k!r} is not allowed",
                            "additionalProperties",
                        )


# ── Custom rule engine ──────────────────────────────────────────────

class CustomRuleEngine:
    """Evaluate custom validation rules expressed as simple predicates."""

    @staticmethod
    def evaluate_rules(
        rules: list[dict[str, Any]], data: Any, context: StepContext,
    ) -> list[ValidationError]:
        """Evaluate a list of custom rules against *data*.

        Each rule is a dict with:
        - ``expr``: a ``{{ }}``-style expression that should resolve truthy.
        - ``message``: error message if the rule fails.
        - ``path`` (optional): JSON path for the error.
        - ``severity`` (optional): ``error`` | ``warning`` (default ``error``).
        """
        errors: list[ValidationError] = []
        for rule in rules:
            expr = rule.get("expr", "")
            if not expr:
                continue
            try:
                result = evaluate_expression(expr, context)
            except Exception:
                result = None

            if not result:
                errors.append(
                    ValidationError(
                        path=rule.get("path", "$"),
                        message=rule.get("message", f"Custom rule failed: {expr}"),
                        rule="custom",
                    )
                )
        return errors


# ── Step implementation ─────────────────────────────────────────────

class ValidateStep(StepBase):
    """Workflow step that validates data against a JSON schema.

    YAML configuration::

        - id: check-inputs
          type: validate
          target: "{{ inputs }}"     # expression resolving to data
          schema:
            type: object
            required: [name, version]
            properties:
              name: { type: string, minLength: 1 }
              version: { type: string, pattern: "^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$" }
          custom_rules:
            - expr: "{{ inputs.name != inputs.version }}"
              message: "name and version must differ"
          fail_on_error: true        # default true
    """

    type_key = "validate"

    def execute(self, config: dict[str, Any], context: StepContext) -> StepResult:
        # ── Resolve the target data ──
        target_expr = config.get("target", "{{ inputs }}")
        if isinstance(target_expr, str) and "{{" in target_expr:
            try:
                target_data = evaluate_expression(target_expr, context)
            except Exception as exc:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Failed to resolve target expression: {exc}",
                    output={"valid": False, "errors": [], "error_count": 0},
                )
        else:
            target_data = target_expr

        all_errors: list[ValidationError] = []

        # ── JSON schema validation ──
        schema = config.get("schema")
        if schema:
            validator = SchemaValidator()
            all_errors.extend(validator.validate(target_data, schema))

        # ── Custom rules ──
        custom_rules = config.get("custom_rules", [])
        if custom_rules:
            all_errors.extend(
                CustomRuleEngine.evaluate_rules(custom_rules, target_data, context)
            )

        # ── Build result ──
        error_dicts = [e.to_dict() for e in all_errors]
        is_valid = len(all_errors) == 0
        fail_on_error = config.get("fail_on_error", True)

        output = {
            "valid": is_valid,
            "errors": error_dicts,
            "error_count": len(error_dicts),
        }

        if not is_valid and fail_on_error:
            summary = "; ".join(f"{e.path}: {e.message}" for e in all_errors[:5])
            if len(all_errors) > 5:
                summary += f" ... and {len(all_errors) - 5} more"
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Validation failed ({len(all_errors)} errors): {summary}",
                output=output,
            )

        return StepResult(status=StepStatus.COMPLETED, output=output)

    def validate(self, config: dict[str, Any]) -> list[str]:
        errors = super().validate(config)
        schema = config.get("schema")
        if schema is not None and not isinstance(schema, dict):
            errors.append(
                f"Validate step {config.get('id', '?')!r}: 'schema' must be a dict."
            )
        custom_rules = config.get("custom_rules")
        if custom_rules is not None and not isinstance(custom_rules, list):
            errors.append(
                f"Validate step {config.get('id', '?')!r}: 'custom_rules' must be a list."
            )
        return errors
