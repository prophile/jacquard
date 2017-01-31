import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.sql.expression
import sqlalchemy.ext.declarative

from .base import StorageEngine

_METADATA = sqlalchemy.MetaData()

_Base = sqlalchemy.ext.declarative.declarative_base(metadata=_METADATA)


class _Entry(_Base):
    __tablename__ = 'entries'

    id = sqlalchemy.Column(
        sqlalchemy.Integer(),
        primary_key=True,
    )

    key = sqlalchemy.Column(
        sqlalchemy.String(length=200),
        nullable=False,
    )

    value = sqlalchemy.Column(
        sqlalchemy.Text(),
        nullable=True,
    )

    created = sqlalchemy.Column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        server_default=sqlalchemy.sql.expression.func.now(),
    )

    __table_args__ = (
        sqlalchemy.Index(
            'entries_by_key',
            key,
            id,
        ),
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
        self.session.add_all(
            _Entry(key=key, value=value)
            for key, value in changes.items()
        )

        self.session.add_all(
            _Entry(key=key, value=None)
            for key in deletions
        )

        # TODO: Intercept the need for Retry here since we're running with the
        # SERIALIZABLE isolation level.
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def get(self, key):
        node = self.session.query(
            _Entry,
        ).filter_by(
            key=key,
        ).order_by(
            sqlalchemy.desc(_Entry.id),
        ).first()

        if node is None:
            return None

        return node.value

    def keys(self):
        # This is a slightly fiddly top-n-per-group situation, but that's OK:
        # essentially we want to exclude any keys whose latest value is null.

        later_entry = sqlalchemy.orm.aliased(_Entry)

        query = self.session.query(
            _Entry.key,
        ).filter(
            _Entry.value != None,  # noqa: E711
            ~self.session.query(later_entry).filter(
                later_entry.key == _Entry.key,
                later_entry.id > _Entry.id,
            ).exists(),
        )

        return [x for (x,) in query]
