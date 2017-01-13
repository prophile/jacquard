"""SQLite3-based file storage engine."""

import sqlite3

from .base import StorageEngine


class FileStore(StorageEngine):
    """Flat(ish)-file SQLite3-based storage engine."""

    def __init__(self, connection_string):
        """
        Open up connection.

        The connection string is given as a file: URL for the path to the
        database file. It needn't be absolute, and will be created if it
        does not already exist.
        """
        self.db = sqlite3.connect(
            connection_string,
            isolation_level=None,  # Explicit BEGIN
            uri=True,
        )
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS "configuration" (
                "key" TEXT NOT NULL PRIMARY KEY,
                "value" TEXT NOT NULL
            );
        """)

    def begin(self):
        """Begin transaction."""
        self.db.execute('BEGIN')
        self._transaction_keys = [
            row[0]
            for row in self.db.execute("""
                SELECT "key" FROM "configuration"
            """)
        ]

    def commit(self, changes, deletions):
        """Commit transaction."""
        # Insertions
        insertions = [
            (key, value)
            for key, value in changes.items()
            if key not in self._transaction_keys
        ]
        if insertions:
            self.db.executemany("""
                INSERT INTO "configuration"("key", "value") VALUES (?, ?)
            """, insertions)

        # Updates
        for key, value in changes.items():
            if key in self._transaction_keys:
                self.db.execute("""
                    UPDATE "configuration" SET "value" = ? WHERE "key" = ?
                """, (value, key))

        # Deletions
        for deletion in deletions:
            self.db.execute("""
                DELETE FROM "configuration" WHERE "key" = ?
            """, (deletion,))

        self.db.commit()
        del self._transaction_keys

    def rollback(self):
        """Roll back transaction."""
        self.db.rollback()
        del self._transaction_keys

    def get(self, key):
        """Get value."""
        rows = list(self.db.execute("""
            SELECT "value" FROM "configuration" WHERE "key" = ?
        """, (key,)))

        if len(rows) == 0:
            return None
        elif len(rows) > 1:
            raise RuntimeError("Duplicate config for key %r" % key)
        else:
            return rows[0][0]

    def keys(self):
        """All keys."""
        return self._transaction_keys
