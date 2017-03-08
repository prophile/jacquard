import abc


class BaseField(object, metaclass=abc.ABCMeta):
    def __init__(self, null=False, default=None):
        self.null = null
        self.default = default

    @abc.abstractmethod
    def transform_to_storage(self, value):
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_from_storage(self, value):
        raise NotImplementedError()

    def _learn_from_owner(self, owner):
        if owner is None:
            return
        if hasattr(self, 'owner'):
            return

        self.owner = owner

        for field_name, value in vars(owner):
            if value is self:
                self.name = field_name

    def validate(self, raw_value):
        if not self.null and raw_value is None:
            raise ValueError("%s is not nullable" % self.name)

    def __get__(self, obj, owner):
        if obj is None:
            self._learn_from_owner(owner)
            return self
        try:
            raw_value = obj._fields[self.name]
        except KeyError:
            return self.default

        return self.transform_from_storage(raw_value)

    def __set__(self, obj, value):
        self._learn_from_owner(type(obj))

        if value is None:
            obj._fields[self.name] = None
        else:
            obj._fields[self.name] = self.transform_to_storage(value)

        if obj.session:
            obj.session.mark_instance_dirty(obj)

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name


class TextField(BaseField):
    def transform_to_storage(self, value):
        return value

    def transform_from_storage(self, value):
        return value
