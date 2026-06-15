from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    name: str
    options: tuple[str, ...]


@dataclass(frozen=True)
class Page:
    name: str
    rows: tuple[Row, ...]
