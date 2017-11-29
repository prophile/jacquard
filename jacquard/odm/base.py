"""
Base model class.

Types in the ODM should derive from `Model`.
"""

import sys

from jacquard.odm import inflection


class ModelMeta(type):
    """Metaclass for models."""

    # Once Python 3.5 support is dropped, we should drop `ModelMeta` and
    # work directly on Model using `__init_subclass__`.

    def __init__(self, name, bases, namespace):
        """
        Standard constructor.

        This is overridden so that on Python <= 3.5, we can find all `Field`s
        in the class and set their names.
        """
        super().__init__(name, bases, namespace)
        self._dub_fields()

    def _dub_fields(self):
        if sys.version_info >= (3, 6):
            return

        # Emulate __set_name__
        for field_name, field in vars(self).items():
            try:
                set_name = field.__set_name__
            except AttributeError:
                continue

            set_name(self, field_name)

    @property
    def storage_name(self):
        """Base name used in storage."""
        return inflection.tableize(self.__name__)


class Model(object, metaclass=ModelMeta):
    """Object type, mapped into document store."""

    __slots__ = ('pk', '_fields', 'session')

    def __init__(self, pk, **fields):
        """
        Constructor.

        `pk` must be provided, optionally can be constructed with values for
        some or all of the fields.
        """
        self.pk = pk
        self._fields = {}
        self.session = None

        for field_name, value in fields.items():
            setattr(self, field_name, value)

    @classmethod
    def transitional_upgrade_raw_data(cls, data):
        """
        Upgrade mechanism to convert potentially old data formats.

        This is a basic, always-forwards-compatible transition mechanism which
        do arbitrary edits to the raw document JSON _before_ being read by the
        ODM. It was designed to fill a specific problem of transitioning the
        `buckets` structure into being handled as part of the ODM.

        Its use is not highly recommended for upgrades, though there is
        currently no strong alternative.
        """
        return data

    def mark_dirty(self):
        """
        Inform the attached session about changes.

        If there is no attached session, this is a no-op; if there is one,
        this will mean that at the next flush this object is written out.
        """
        if self.session:
            self.session.mark_instance_dirty(self)

    @classmethod
    def storage_key(cls, pk):
        """Key within the document store for a particular pk."""
        return '{storage_name}/{pk}'.format(
            storage_name=cls.storage_name,
            pk=pk,
        )

    def __repr__(self):  # noqa: D400
        """Python reproducer. Handy for debugging!"""
        cls = type(self)
        return "{class_name}(pk={pk!r}, {args})".format(
            class_name=cls.__name__,
            pk=self.pk,
            args=', '.join(
                '{field}={value!r}'.format(
                    field=field_name,
                    value=getattr(cls, field_name).transform_from_storage(
                        field_raw_value,
                    ),
                )
                for field_name, field_raw_value in self._fields.items()
            ),
        )
