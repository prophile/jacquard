import sys

from . import inflection


class ModelMeta(type):
    def __init__(self, name, bases, namespace):
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
        return inflection.tableize(self.__name__)


class Model(object, metaclass=ModelMeta):
    __slots__ = ('pk', '_fields', 'session')

    def __init__(self, pk, **fields):
        self.pk = pk
        self._fields = {}
        self.session = None

        for field_name, value in fields.items():
            setattr(self, field_name, value)

    @classmethod
    def storage_key(cls, pk):
        return '%s/%s' % (
            cls.storage_name,
            pk,
        )
