"""SQLite-backed hymn library data access.

The repository deliberately keeps each verse in its own database row. This
allows live display navigation to fetch a specific, next, or previous verse
without splitting a larger text field at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
from collections.abc import Sequence


@dataclass(frozen=True)
class Verse:
    """One independently addressable hymn verse."""

    number: int
    lyrics: str


@dataclass(frozen=True)
class Hymn:
    """A hymn and its verses in display order."""

    id: int
    title: str
    number: str
    tune_name: str
    tags: str | None
    verses: tuple[Verse, ...]


@dataclass(frozen=True)
class HymnSummary:
    """Search result data used by the operator window."""

    id: int
    title: str
    number: str
    tune_name: str
    tags: str | None


class HymnRepository:
    """Small, explicit data-access layer for the local hymn database."""

    def __init__(self, database_path: str | Path = "churchley.db") -> None:
        self.database_path = str(database_path)
        self._connection = sqlite3.connect(self.database_path, timeout=10)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def close(self) -> None:
        """Close the underlying SQLite connection."""

        self._connection.close()

    def __enter__(self) -> "HymnRepository":
        return self

    def __exit__(self, _exception_type, _exception, _traceback) -> None:
        self.close()

    def _create_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS hymns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                number TEXT NOT NULL,
                tune_name TEXT NOT NULL DEFAULT '',
                tags TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hymn_id INTEGER NOT NULL,
                verse_number INTEGER NOT NULL,
                lyrics TEXT NOT NULL,
                FOREIGN KEY (hymn_id) REFERENCES hymns(id) ON DELETE CASCADE,
                UNIQUE (hymn_id, verse_number)
            );

            CREATE INDEX IF NOT EXISTS idx_hymns_number ON hymns(number);
            CREATE INDEX IF NOT EXISTS idx_hymns_title ON hymns(title);
            CREATE INDEX IF NOT EXISTS idx_verses_hymn_order
                ON verses(hymn_id, verse_number);
            """
        )
        self._connection.commit()

    def add_hymn(
        self,
        title: str,
        number: str | int,
        tune_name: str = "",
        tags: str | None = None,
        verses: Sequence[str] = (),
    ) -> int:
        """Add a hymn and return its database id.

        ``verses`` is stored in the supplied order and numbered from one.
        The entire hymn is inserted atomically.
        """

        clean_title = title.strip()
        clean_number = str(number).strip()
        clean_tune_name = tune_name.strip()
        clean_tags = tags.strip() if tags else None
        clean_verses = tuple(verse.strip() for verse in verses)

        if not clean_title:
            raise ValueError("Hymn title cannot be empty")
        if not clean_number:
            raise ValueError("Hymn number cannot be empty")
        if not clean_verses or any(not verse for verse in clean_verses):
            raise ValueError("A hymn must contain at least one non-empty verse")

        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO hymns (title, number, tune_name, tags)
                VALUES (?, ?, ?, ?)
                """,
                (clean_title, clean_number, clean_tune_name, clean_tags),
            )
            hymn_id = int(cursor.lastrowid)
            self._connection.executemany(
                """
                INSERT INTO verses (hymn_id, verse_number, lyrics)
                VALUES (?, ?, ?)
                """,
                ((hymn_id, verse_number, lyrics)
                 for verse_number, lyrics in enumerate(clean_verses, start=1)),
            )
        return hymn_id

    def search_hymns(self, query: str) -> list[HymnSummary]:
        """Search title and number by literal substring with deterministic ranking.

        Ranking priority is exact number, title prefix, number prefix, then
        any remaining title/number substring match. The function is isolated
        so fuzzy matching can replace it later without changing callers.
        """

        clean_query = query.strip().casefold()
        if not clean_query:
            return []

        rows = self._connection.execute(
            """
            SELECT id, title, number, tune_name, tags,
                CASE
                    WHEN lower(number) = ? THEN 0
                    WHEN lower(title) LIKE ? THEN 1
                    WHEN lower(number) LIKE ? THEN 2
                    ELSE 3
                END AS relevance
            FROM hymns
            WHERE instr(lower(title), ?) > 0
               OR instr(lower(number), ?) > 0
            ORDER BY relevance, lower(title), number, id
            """,
            (
                clean_query,
                f"{clean_query}%",
                f"{clean_query}%",
                clean_query,
                clean_query,
            ),
        ).fetchall()
        return [
            HymnSummary(
                id=int(row["id"]),
                title=row["title"],
                number=row["number"],
                tune_name=row["tune_name"],
                tags=row["tags"],
            )
            for row in rows
        ]

    def get_hymn(self, hymn_id: int) -> Hymn | None:
        """Return one complete hymn with verses in display order."""

        hymn_row = self._connection.execute(
            """
            SELECT id, title, number, tune_name, tags
            FROM hymns
            WHERE id = ?
            """,
            (hymn_id,),
        ).fetchone()
        if hymn_row is None:
            return None

        verse_rows = self._connection.execute(
            """
            SELECT verse_number, lyrics
            FROM verses
            WHERE hymn_id = ?
            ORDER BY verse_number
            """,
            (hymn_id,),
        ).fetchall()
        return Hymn(
            id=int(hymn_row["id"]),
            title=hymn_row["title"],
            number=hymn_row["number"],
            tune_name=hymn_row["tune_name"],
            tags=hymn_row["tags"],
            verses=tuple(
                Verse(number=int(row["verse_number"]), lyrics=row["lyrics"])
                for row in verse_rows
            ),
        )

    def get_verse(self, hymn_id: int, verse_number: int) -> Verse | None:
        """Fetch one verse directly by hymn id and verse number."""

        row = self._connection.execute(
            """
            SELECT verse_number, lyrics
            FROM verses
            WHERE hymn_id = ? AND verse_number = ?
            """,
            (hymn_id, verse_number),
        ).fetchone()
        if row is None:
            return None
        return Verse(number=int(row["verse_number"]), lyrics=row["lyrics"])

    def get_next_verse(self, hymn_id: int, verse_number: int) -> Verse | None:
        """Fetch the next verse after ``verse_number`` directly from SQLite."""

        row = self._connection.execute(
            """
            SELECT verse_number, lyrics
            FROM verses
            WHERE hymn_id = ? AND verse_number > ?
            ORDER BY verse_number
            LIMIT 1
            """,
            (hymn_id, verse_number),
        ).fetchone()
        if row is None:
            return None
        return Verse(number=int(row["verse_number"]), lyrics=row["lyrics"])

    def get_previous_verse(self, hymn_id: int, verse_number: int) -> Verse | None:
        """Fetch the previous verse before ``verse_number`` directly from SQLite."""

        row = self._connection.execute(
            """
            SELECT verse_number, lyrics
            FROM verses
            WHERE hymn_id = ? AND verse_number < ?
            ORDER BY verse_number DESC
            LIMIT 1
            """,
            (hymn_id, verse_number),
        ).fetchone()
        if row is None:
            return None
        return Verse(number=int(row["verse_number"]), lyrics=row["lyrics"])

    def delete_hymn(self, hymn_id: int) -> bool:
        """Delete a hymn and its verses, returning whether it existed."""

        with self._connection:
            cursor = self._connection.execute(
                "DELETE FROM hymns WHERE id = ?", (hymn_id,)
            )
        return cursor.rowcount > 0
