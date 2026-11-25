"""The YAML dialect and schema of Codex's ``agents/openai.yaml``.

Codex reads ``openai.yaml`` with serde_yaml, which follows the YAML 1.2 core
schema. PyYAML's YAML 1.1 rules would turn ``display_name: On`` into ``True``
and ``010`` into 8, changing user values on a round trip.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Any

import yaml

_YAML11_ONLY_TAGS = {
    f"tag:yaml.org,2002:{name}"
    for name in ("bool", "int", "float", "timestamp", "value", "merge")
}
_MERGE_TAG = "tag:yaml.org,2002:merge"
# Merging an anchored mapping copies its keys each time, so nested merges grow
# exponentially and repeated ones add up. A document's merges may produce this
# many key-value pairs in all, far beyond any real ``openai.yaml``.
_MAX_MERGED_KEYS = 10_000
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

    def __init__(self, stream: Any) -> None:
        super().__init__(stream)
        self._own_keys_checked: set[yaml.Node] = set()
        self._merged_sizes: dict[yaml.Node, int] = {}
        self._merged_total = 0

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        # A dict keeps one of two keys Python treats as equal, such as ``true``
        # and ``1``, or a key given twice; rewriting would drop the other.
        # serde_yaml rejects a repeated key too. A key an explicit ``!!merge``
        # brings in may be overridden by the same key, so the mapping's own
        # keys must be distinct, and once merged keys are added, keys that
        # are equal must also have the same type.
        if isinstance(node, yaml.MappingNode):
            self._check_own_keys(node)
            if any(key.tag == _MERGE_TAG for key, _ in node.value):
                self._merged_total += self._merged_size(node)
            if self._merged_total > _MAX_MERGED_KEYS:
                raise yaml.constructor.ConstructorError(
                    None, None,
                    f"found merges that expand to more than {_MAX_MERGED_KEYS} keys",
                    node.start_mark,
                )
            self.flatten_mapping(node)  # merged keys first, then the mapping's own
            self._check_keys(
                [key for key, _ in node.value],
                lambda previous, key_node: previous.tag != key_node.tag,
            )
        return super().construct_mapping(node, deep=deep)

    def flatten_mapping(self, node: yaml.MappingNode) -> None:
        """Put the keys ``node`` merges in ahead of its own, as the merge spec orders them.

        Pinned here rather than inherited: PyYAML 6.0.4 keeps only the first
        pair for each key object while merging, so a merged mapping that
        overrides a key from its own merge loses the override, unlike Codex.
        Later pairs win when the mapping is built, so the mapping's own keys
        override merged ones, and earlier mappings in a merge list override
        later ones.
        """
        merge: list[tuple[yaml.Node, yaml.Node]] = []
        index = 0
        while index < len(node.value):
            key_node, value_node = node.value[index]
            if key_node.tag != _MERGE_TAG:
                if key_node.tag == "tag:yaml.org,2002:value":
                    key_node.tag = "tag:yaml.org,2002:str"
                index += 1
                continue
            del node.value[index]
            if isinstance(value_node, yaml.MappingNode):
                self.flatten_mapping(value_node)
                merge.extend(value_node.value)
            elif isinstance(value_node, yaml.SequenceNode):
                merged = []
                for subnode in value_node.value:
                    if not isinstance(subnode, yaml.MappingNode):
                        raise yaml.constructor.ConstructorError(
                            "while constructing a mapping", node.start_mark,
                            f"expected a mapping for merging, but found {subnode.id}",
                            subnode.start_mark,
                        )
                    self.flatten_mapping(subnode)
                    merged.append(subnode.value)
                for value in reversed(merged):
                    merge.extend(value)
            else:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping", node.start_mark,
                    f"expected a mapping or list of mappings for merging, but found {value_node.id}",
                    value_node.start_mark,
                )
        if merge:
            node.value = merge + node.value

    def _check_own_keys(
        self, node: yaml.MappingNode, merging: frozenset[yaml.Node] = frozenset(),
    ) -> None:
        """Raise if ``node``, or a mapping merged into it, repeats a key.

        Runs before ``node`` is flattened, which adds the keys merged into it
        to its own, and only once per node, since an anchored node merged
        again later has been flattened by then.
        """
        if node in self._own_keys_checked:
            return
        self._own_keys_checked.add(node)
        merging |= {node}
        merge_keys = [key for key, _ in node.value if key.tag == _MERGE_TAG]
        if len(merge_keys) > 1:
            raise _collision(merge_keys[1])
        self._check_keys(
            [key for key, _ in node.value if key.tag != _MERGE_TAG],
            lambda previous, key_node: True,
        )
        # A mapping written inline as a merge value is never constructed on
        # its own, so nothing else checks its keys.
        for key, value in node.value:
            if key.tag != _MERGE_TAG:
                continue
            for merged in value.value if isinstance(value, yaml.SequenceNode) else [value]:
                if merged in merging:
                    # PyYAML would drop it, losing the keys; serde_yaml rejects it.
                    raise yaml.constructor.ConstructorError(
                        None, None, "found a mapping that merges itself", key.start_mark,
                    )
                if isinstance(merged, yaml.MappingNode):
                    self._check_own_keys(merged, merging)

    def _merged_size(self, node: yaml.MappingNode) -> int:
        """How many key-value pairs flattening ``node`` produces, counted before it runs.

        Only called after ``_check_own_keys``, which rejects a mapping that
        merges itself. A flattened node has no merge keys left, so its count is
        its length, the same as before it was flattened.
        """
        size = self._merged_sizes.get(node)
        if size is not None:
            return size
        size = 0
        for key, value in node.value:
            if key.tag != _MERGE_TAG:
                size += 1
                continue
            for merged in value.value if isinstance(value, yaml.SequenceNode) else [value]:
                if isinstance(merged, yaml.MappingNode):
                    size += self._merged_size(merged)
                    if size > _MAX_MERGED_KEYS:
                        self._merged_sizes[node] = size
                        return size
        self._merged_sizes[node] = size
        return size

    def _check_keys(
        self,
        key_nodes: list[yaml.Node],
        collide: Callable[[yaml.Node, yaml.Node], bool],
    ) -> None:
        """Raise if ``collide`` holds for two key nodes whose keys are equal."""
        seen: dict[Any, yaml.Node] = {}
        for key_node in key_nodes:
            key = self.construct_object(key_node, deep=True)
            try:
                previous = seen.get(key)
            except TypeError:  # unhashable; the base constructor reports it
                continue
            if previous is not None and collide(previous, key_node):
                raise _collision(key_node)
            seen.setdefault(key, key_node)


def _collision(key_node: yaml.Node) -> yaml.constructor.ConstructorError:
    return yaml.constructor.ConstructorError(
        None, None,
        "found keys that collide, such as a repeated key or both true and 1",
        key_node.start_mark,
    )


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


# Shapes from Codex's ``SkillMetadataFile`` (codex-rs/skills/src/metadata.rs)
# and ``SkillInterfaceFile`` (interface.rs). A mismatch makes Codex ignore the
# whole file, policy included. Text fields must be scalars, which serde_yaml
# reads as text whatever they resolve to; their length and content are not
# checked, since Codex drops just that field when they fail. ``products``
# values are not checked, so a newer Codex value is never rejected here.
_INTERFACE_TEXT = (
    "display_name", "short_description", "icon_small", "icon_large", "brand_color", "default_prompt",
)
_TOOL_TEXT = ("type", "value", "description", "transport", "command", "url")
# ``DependencyOAuth.callback_port`` is a ``u16``, read as ``callbackPort`` or,
# by alias, ``callback_port``; serde rejects both spellings in one mapping.
_CALLBACK_PORT_KEYS = ("callbackPort", "callback_port")
_MAX_PORT = 65535


def _type_name(value: Any) -> str:
    return {Int: "int", Float: "float", type(None): "null"}.get(type(value), type(value).__name__)


def schema_errors(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def expect(value: Any, kind: type, label: str, *, optional: bool = True) -> bool:
        if (optional and value is None) or isinstance(value, kind):
            return value is not None
        name = "a mapping" if kind is dict else "a list"
        errors.append(f"'{label}' must be {name}, got {_type_name(value)}")
        return False

    def expect_text(mapping: dict[Any, Any], fields: tuple[str, ...], prefix: str) -> None:
        for field in fields:
            value = mapping.get(field)
            if isinstance(value, (dict, list)):
                errors.append(f"'{prefix}.{field}' must be text, got {_type_name(value)}")

    def expect_port(oauth: dict[Any, Any], prefix: str) -> None:
        present = [key for key in _CALLBACK_PORT_KEYS if key in oauth]
        if len(present) > 1:
            errors.append(f"'{prefix}' must not set both callbackPort and callback_port")
        for key in present:
            value = oauth[key]
            if value is None:
                continue
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"'{prefix}.{key}' must be an integer port, got {_type_name(value)}")
            elif not 0 <= value <= _MAX_PORT:
                errors.append(f"'{prefix}.{key}' must be between 0 and {_MAX_PORT}, got {value}")

    interface = data.get("interface")
    if expect(interface, dict, "interface"):
        expect_text(interface, _INTERFACE_TEXT, "interface")
    dependencies = data.get("dependencies")
    if expect(dependencies, dict, "dependencies"):
        # ``tools`` and ``products`` may be missing, but Codex reads an
        # explicit null as a list of the wrong type.
        tools = dependencies.get("tools", [])
        if expect(tools, list, "dependencies.tools", optional=False):
            for index, tool in enumerate(tools):
                label = f"dependencies.tools[{index}]"
                # A list item is required, so ``null`` is not an absent field.
                if expect(tool, dict, label, optional=False):
                    expect_text(tool, _TOOL_TEXT, label)
                    oauth = tool.get("oauth")
                    if expect(oauth, dict, f"{label}.oauth"):
                        expect_port(oauth, f"{label}.oauth")
    policy = data.get("policy")
    if expect(policy, dict, "policy"):
        expect(policy.get("products", []), list, "policy.products", optional=False)
    return errors
