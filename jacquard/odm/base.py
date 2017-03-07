from . import inflection


class ModelMeta(type):
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
