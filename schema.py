from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    """Represents a single row in the table, with a name and a set of options."""
    name: str
    options: tuple[str, ...]


@dataclass(frozen=True)
class Page:
    """Represents a single page in the table, with a name and a set of rows."""
    name: str
    rows: tuple[Row, ...]
