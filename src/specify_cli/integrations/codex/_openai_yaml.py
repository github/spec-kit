"""The YAML dialect and schema of Codex's ``agents/openai.yaml``.

Codex reads ``openai.yaml`` with serde_yaml, which follows the YAML 1.2 core
schema. PyYAML's YAML 1.1 rules would turn ``display_name: On`` into ``True``
and ``010`` into 8, changing user values on a round trip.
"""

from __future__ import annotations

import re
from typing import Any

import yaml

_YAML11_ONLY_TAGS = {
    f"tag:yaml.org,2002:{name}"
    for name in ("bool", "int", "float", "timestamp", "value", "merge")
}
_YAML12_RESOLVERS = (
    ("tag:yaml.org,2002:bool", r"true|True|TRUE|false|False|FALSE", "tTfF"),
    ("tag:yaml.org,2002:int", r"[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+", "-+0123456789"),
    (
        "tag:yaml.org,2002:float",
        r"[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?"
        r"|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN)",
        "-+0123456789.",
    ),
)


class Yaml12Loader(yaml.SafeLoader):
    """Safe loader that resolves plain scalars by the YAML 1.2 core schema."""

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        # A dict keeps one of two keys Python treats as equal, such as ``true``
        # and ``1``, or a key given twice; rewriting would drop the other.
        # serde_yaml rejects a repeated key too. Keys an explicit ``!!merge``
        # brings in may be overridden, so only the mapping's own keys count.
        if isinstance(node, yaml.MappingNode):
            seen: dict[Any, None] = {}
            for key_node, _ in node.value:
                if key_node.tag == "tag:yaml.org,2002:merge":
                    continue
                key = self.construct_object(key_node, deep=True)
                try:
                    collides = key in seen
                except TypeError:  # unhashable; the base constructor reports it
                    continue
                if collides:
                    raise yaml.constructor.ConstructorError(
                        None, None,
                        "found keys that collide, such as a repeated key or both true and 1",
                        key_node.start_mark,
                    )
                seen[key] = None
        return super().construct_mapping(node, deep=deep)


Yaml12Loader.yaml_implicit_resolvers = {
    first: [(tag, rx) for tag, rx in resolvers if tag not in _YAML11_ONLY_TAGS]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


class _Yaml12Dumper(yaml.SafeDumper):
    """Safe dumper that also quotes strings YAML 1.2 would read as non-strings."""


for _tag, _pattern, _first in _YAML12_RESOLVERS:
    for _cls in (Yaml12Loader, _Yaml12Dumper):
        _cls.add_implicit_resolver(_tag, re.compile(f"^(?:{_pattern})$"), list(_first))


_YAML12_INT = re.compile(_YAML12_RESOLVERS[1][1])
_YAML12_FLOAT = re.compile(_YAML12_RESOLVERS[2][1])


# Numbers remember their source text, so ``1.10`` or ``007`` is written back
# unchanged rather than as ``1.1`` or ``7``.
class Int(int):
    text: str


class Float(float):
    text: str


def _construct_int(loader: Yaml12Loader, node: yaml.ScalarNode) -> int:
    text = loader.construct_scalar(node)
    if not _YAML12_INT.fullmatch(text):  # an explicit ``!!int`` in another form
        return loader.construct_yaml_int(node)
    if text.startswith(("0o", "0x")):
        number = Int(int(text[2:], 8 if text[1] == "o" else 16))
    else:
        number = Int(int(text, 10))
    number.text = text
    return number


def _construct_float(loader: Yaml12Loader, node: yaml.ScalarNode) -> float:
    text = loader.construct_scalar(node)
    if not _YAML12_FLOAT.fullmatch(text):  # an explicit ``!!float`` in another form
        return loader.construct_yaml_float(node)
    number = Float(float(text.lower().replace(".inf", "inf").replace(".nan", "nan")))
    number.text = text
    return number


Yaml12Loader.add_constructor("tag:yaml.org,2002:int", _construct_int)
Yaml12Loader.add_constructor("tag:yaml.org,2002:float", _construct_float)
_Yaml12Dumper.add_representer(
    Int, lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:int", data.text)
)
_Yaml12Dumper.add_representer(
    Float, lambda dumper, data: dumper.represent_scalar("tag:yaml.org,2002:float", data.text)
)


def dump(data: dict[str, Any]) -> str:
    return yaml.dump(data, Dumper=_Yaml12Dumper, sort_keys=False, allow_unicode=True)


# Container shapes from Codex's ``SkillMetadataFile`` (codex-rs/skills/src/
# metadata.rs). A mismatch makes Codex ignore the whole file, policy included.
# Scalar leaves and ``products`` values are not checked, so a newer Codex value
# is never rejected here.
def schema_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def expect(value: Any, kind: type, label: str, *, optional: bool = True) -> bool:
        if (optional and value is None) or isinstance(value, kind):
            return value is not None
        name = "a mapping" if kind is dict else "a list"
        got = {Int: "int", Float: "float", type(None): "null"}.get(type(value), type(value).__name__)
        errors.append(f"'{label}' must be {name}, got {got}")
        return False

    expect(data.get("interface"), dict, "interface")
    dependencies = data.get("dependencies")
    if expect(dependencies, dict, "dependencies"):
        tools = dependencies.get("tools")
        if expect(tools, list, "dependencies.tools"):
            for index, tool in enumerate(tools):
                # A list item is required, so ``null`` is not an absent field.
                if expect(tool, dict, f"dependencies.tools[{index}]", optional=False):
                    expect(tool.get("oauth"), dict, f"dependencies.tools[{index}].oauth")
    policy = data.get("policy")
    if expect(policy, dict, "policy"):
        expect(policy.get("products"), list, "policy.products")
    return errors
