import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.ext.declarative
import sqlalchemy.sql.expression

from .base import StorageEngine

_METADATA = sqlalchemy.MetaData()

_Base = sqlalchemy.ext.declarative.declarative_base(metadata=_METADATA)


class _Entry(_Base):
    __tablename__ = 'entries'

    key = sqlalchemy.Column(
        sqlalchemy.String(length=200),
        primary_key=True,
    )

    value = sqlalchemy.Column(
        sqlalchemy.Text(),
        nullable=False,
    )

    created = sqlalchemy.Column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.sql.expression.func.now(),
    )

    updated = sqlalchemy.Column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.sql.expression.func.now(),
        onupdate=sqlalchemy.sql.expression.func.now(),
    )


class DBStore(StorageEngine):
    def __init__(self, connection_string):
        self.engine = sqlalchemy.create_engine(
            connection_string,
            isolation_level='SERIALIZABLE',
        )
        _METADATA.create_all(bind=self.engine)
        self.session = sqlalchemy.orm.Session(self.engine)

    def begin(self):
        pass

    # TODO: Investigate `begin_read_only` with a lower isolation

    def commit(self, changes, deletions):
        for key, value in changes.items():
            node = self._get_node(key)
            node.value = value
        for deletion in deletions:
            node = self._get_node(deletion)
            if node is not None:
                self.session.delete(node)

        # TODO: Intercept the need for Retry here since we're running with the
        # SERIALIZABLE isolation level.
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def _get_node(self, key):
        node = self.session.query(_Entry).get(ident=key)

        if node is None:
            node = _Entry(key=key)
            self.session.add(node)

        return node

    def get(self, key):
        return self._get_node(key).value

    def keys(self):
        return [
            x
            for (x,) in self.session.query(_Entry.key)
        ]
