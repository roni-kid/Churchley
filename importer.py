"""Bulk hymn import parsing for Churchley's documented plain-text format."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ImportedHymn:
    title: str
    number: str
    tune_name: str
    tags: str | None
    verses: tuple[str, ...]


_HEADER_PATTERN = re.compile(r"^\[(?P<number>[^\]]+)\]\s+(?P<title>.+?)\s*$")
_VERSE_PATTERN = re.compile(r"^Verse\s+(?P<number>\d+)\s*:\s*$", re.IGNORECASE)


def parse_bulk_hymns(text: str) -> list[ImportedHymn]:
    """Parse the plain-text bulk import format into validated hymn records.

    Each block starts with ``[number] Title`` and ends at ``---`` or EOF.
    Optional metadata lines are ``Tune: ...`` and ``Tags: ...``. Verse content
    starts with ``Verse N:`` and continues until the next verse or block end.
    Verse numbers must be sequential starting at one.
    """

    blocks = _split_blocks(text)
    imported: list[ImportedHymn] = []
    seen_numbers: dict[str, int] = {}
    for block_number, block in enumerate(blocks, start=1):
        lines = [line.rstrip() for line in block.splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            continue

        header_match = _HEADER_PATTERN.match(lines[0].strip())
        if header_match is None:
            raise ValueError(
                f"Block {block_number} must start with '[number] Title'"
            )

        title = header_match.group("title").strip()
        number = header_match.group("number").strip()
        tune_name = ""
        tags: str | None = None
        verse_records: dict[int, str] = {}
        current_verse_number: int | None = None
        current_lines: list[str] = []

        def finish_verse() -> None:
            if current_verse_number is None:
                return
            lyrics = "\n".join(current_lines).strip()
            if not lyrics:
                raise ValueError(f"Block {block_number} has an empty verse")
            if current_verse_number in verse_records:
                raise ValueError(
                    f"Block {block_number} repeats verse {current_verse_number}"
                )
            verse_records[current_verse_number] = lyrics

        for raw_line in lines[1:]:
            line = raw_line.strip()
            if not line and current_verse_number is None:
                continue
            verse_match = _VERSE_PATTERN.match(line)
            if verse_match:
                finish_verse()
                current_verse_number = int(verse_match.group("number"))
                current_lines = []
                continue
            if current_verse_number is None and line.lower().startswith("tune:"):
                tune_name = line.split(":", 1)[1].strip()
                continue
            if current_verse_number is None and line.lower().startswith("tags:"):
                tags_value = line.split(":", 1)[1].strip()
                tags = tags_value or None
                continue
            if current_verse_number is None:
                raise ValueError(
                    f"Block {block_number} contains text before its first verse"
                )
            current_lines.append(raw_line)
        finish_verse()

        expected_numbers = list(range(1, len(verse_records) + 1))
        actual_numbers = sorted(verse_records)
        if actual_numbers != expected_numbers:
            raise ValueError(
                f"Block {block_number} verse numbers must be sequential from 1"
            )
        imported.append(
            ImportedHymn(
                title=title,
                number=number,
                tune_name=tune_name,
                tags=tags,
                verses=tuple(verse_records[number] for number in expected_numbers),
            )
        )
        if number in seen_numbers:
            raise ValueError(
                f"Duplicate hymn number [{number}] in block {block_number} "
                f"(first appeared in block {seen_numbers[number]})"
            )
        seen_numbers[number] = block_number
    if not imported:
        raise ValueError("The import file does not contain any hymns")
    return imported


def _split_blocks(text: str) -> list[str]:
    return re.split(r"^\s*---\s*$", text, flags=re.MULTILINE)
