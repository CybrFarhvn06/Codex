import sqlite3
import unittest
from pathlib import Path


class SchemaSqlTests(unittest.TestCase):
    def test_schema_executes_and_creates_tables(self):
        schema = Path("docs/schema.sql").read_text(encoding="utf-8")
        conn = sqlite3.connect(":memory:")
        conn.executescript(schema)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('students','research_logs')"
        )
        tables = {row[0] for row in cursor.fetchall()}
        self.assertEqual(tables, {"students", "research_logs"})


if __name__ == "__main__":
    unittest.main()
