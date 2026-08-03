"""Shared TOML string-escaping helpers.

Both TOML command renderers — ``TomlIntegration`` (gemini, tabnine) in
``specify_cli.integrations.base`` and ``CommandRegistrar.render_toml_command``
(extension/preset commands) in ``specify_cli.agents`` — need the same rules for
detecting characters TOML forbids literally and for emitting a fully-escaped
basic string. Keeping one implementation here avoids the two drifting apart if
the escaping rules change again.
"""
from __future__ import annotations


def has_illegal_toml_control(value: str) -> bool:
    """True when *value* contains a character TOML forbids literally.

    TOML basic/literal strings (single- or multi-line) allow tab and, in the
    multiline forms, newlines — but every other control character
    (``U+0000``–``U+001F`` and ``U+007F``) must be ``\\u``-escaped, which only a
    basic string can do. A bare carriage return counts too: a multiline basic
    string treats ``\\r`` as a newline only when paired into ``\\r\\n``; a lone
    ``\\r`` is an illegal control character.
    """
    length = len(value)
    for i, ch in enumerate(value):
        code = ord(ch)
        if ch == "\r":
            # Only a CR that is part of a CRLF newline is allowed literally.
            if i + 1 < length and value[i + 1] == "\n":
                continue
            return True
        if (code < 0x20 and ch not in ("\t", "\n")) or code == 0x7F:
            return True
    return False


def escape_toml_basic(value: str) -> str:
    """Render *value* as a single-line basic string, escaping everything.

    Always valid TOML: backslash/quote are escaped, the common control chars
    use their short escapes, and any remaining control character is emitted as
    a ``\\uXXXX`` sequence.
    """
    out: list[str] = []
    for ch in value:
        code = ord(ch)
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        elif code < 0x20 or code == 0x7F:
            out.append(f"\\u{code:04x}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'
