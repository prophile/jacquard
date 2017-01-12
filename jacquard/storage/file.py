import sqlite3

from .base import KVStore


class FileStore(KVStore):
    def __init__(self, connection_string):
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
        self.db.execute('BEGIN')
        self._transaction_keys = [
            row[0]
            for row in self.db.execute("""
                SELECT "key" FROM "configuration"
            """)
        ]

    def commit(self, changes, deletions):
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
        self.db.rollback()
        del self._transaction_keys

    def get(self, key):
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
        return self._transaction_keys
