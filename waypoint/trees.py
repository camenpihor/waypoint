from dataclasses import asdict, astuple, dataclass
from datetime import date
from typing import Optional

from psycopg2.extras import DictCursor

INSERT_KEYS = {
    "tree_id",
    "latin_name",
    "common_name",
    "latitude",
    "longitude",
    "source",
    "is_native",
}


@dataclass
class TreeLocation:
    location_id: int
    tree_id: int
    latin_name: str
    common_name: str
    latitude: float
    longitude: float
    source: str
    is_native: bool
    date_added: Optional[date] = None
    removed_by: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def to_tuple(self) -> tuple:
        return astuple(self)


def fetch_all(client: DictCursor) -> list[TreeLocation]:
    query = "SELECT * FROM tree_locations WHERE removed_by IS NULL;"
    client.execute(query)
    return [TreeLocation(**tree) for tree in client.fetchall()]


def mark_removed(location_id: int, removed_by: str, client: DictCursor) -> bool:
    query = """
UPDATE tree_locations
SET removed_by = %s
WHERE location_id = %s
RETURNING location_id;
"""
    client.execute(query, (removed_by, location_id))
    return client.rowcount > 0


def insert(
    client: DictCursor,
    tree_id: str,
    latin_name: str,
    common_name: str,
    latitude: float,
    longitude: float,
    source: str,
    is_native: bool,
    date_added: Optional[date] = None,
) -> TreeLocation:
    query = """
INSERT INTO tree_locations
(tree_id, latin_name, common_name, is_native, date_added, latitude, longitude, source)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
RETURNING *;
"""
    client.execute(
        query,
        (
            tree_id,
            latin_name,
            common_name,
            is_native,
            date_added,
            latitude,
            longitude,
            source,
        ),
    )
    return TreeLocation(**client.fetchone())
