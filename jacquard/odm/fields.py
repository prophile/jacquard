"""Field declarations."""

import abc
import copy


class BaseField(object, metaclass=abc.ABCMeta):
    """
    Base class for all fields.

    Subclasses should override `transform_to_storage` and
    `transform_from_storage`. They may optionally also override `validate`,
    but should call `super().validate` if doing so.
    """

    def __init__(self, *, null=False, default=None):
        """
        Construct the field.

        If `null=True`, None is not permitted in this field. The naming is for
        consistency with the equivalent concept in relational algebra and ORMs.

        `default` does what it says on the tin.
        """
        self.null = null
        self.default = default

    @abc.abstractmethod
    def transform_to_storage(self, value):
        """Encode the value in JSON-compatible data types."""
        raise NotImplementedError()

    @abc.abstractmethod
    def transform_from_storage(self, value):
        """Decode the value from JSON-compatible data types."""
        raise NotImplementedError()

    def validate(self, raw_value):
        """
        Check that the value is 'permitted' before submission.

        Note that this operates on values _as they appear in the data store_,
        i.e. post JSON-encoding.
        """
        if not self.null and raw_value is None:
            raise ValueError("%s is not nullable" % self.name)

    def __get__(self, obj, owner):
        """Read descriptor."""
        if obj is None:
            return self

        try:
            raw_value = obj._fields[self.name]
        except KeyError:
            return self.default

        return self.transform_from_storage(raw_value)

    def __set__(self, obj, value):
        """Write descriptor."""
        if value is None:
            obj._fields[self.name] = None
        else:
            obj._fields[self.name] = self.transform_to_storage(value)

        if obj.session:
            obj.session.mark_instance_dirty(obj)

    def __set_name__(self, owner, name):
        """Inherit ownership pointer and name."""
        # Note that this is called automatically on Python 3.6+; on Python 3.5
        # this is done with some emulation by the `ModelMeta` metaclass.

        self.owner = owner
        self.name = name


class TextField(BaseField):
    """Plain text field."""

    def transform_to_storage(self, value):
        """Encode the value in JSON-compatible data types."""
        return str(value)

    def transform_from_storage(self, value):
        """Decode the value from JSON-compatible data types."""
        return value


class JSONField(BaseField):
    """Arbitrary JSON field."""

    def transform_to_storage(self, value):
        """Encode the value in JSON-compatible data types."""
        return copy.deepcopy(value)

    def transform_from_storage(self, value):
        """Decode the value from JSON-compatible data types."""
        return copy.deepcopy(value)
