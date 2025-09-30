from __future__ import annotations

from typing import Iterable, List


def normalize_words(text: str) -> List[str]:
    """Normalize text into lower-cased words, trimming punctuation."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    raw = text.strip().lower()
    word_chars = [c if c.isalnum() else " " for c in raw]
    return [w for w in "".join(word_chars).split() if w]


def count_words(lines: Iterable[str]) -> int:
    """Count total words across an iterable of lines."""
    total = 0
    for line in lines:
        total += len(normalize_words(line))
    return total


def main() -> None:
    sample = [
        "Hello, Qwen!",
        "This is a tiny module to practice @file-scoped edits.",
        "Refactor me into pure functions and add edge-case handling.",
    ]
    total = count_words(sample)
    print(f"Total words: {total}")


if __name__ == "__main__":
    main()



