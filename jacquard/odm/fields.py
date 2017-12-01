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
            raise ValueError("{field} is not nullable".format(field=self.name))

    def __get__(self, obj, owner):
        """Read descriptor."""
        if obj is None:
            return self

        try:
            raw_value = obj._fields[self.name]
        except KeyError:
            return copy.copy(self.default)

        return self.transform_from_storage(raw_value)

    def __set__(self, obj, value):
        """Write descriptor."""
        if value is None:
            obj._fields[self.name] = None
        else:
            obj._fields[self.name] = self.transform_to_storage(value)

        obj.mark_dirty()

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


class ListField(BaseField):
    """Arbitrary list, of another field type."""

    def __init__(self, *, field, **kwargs):
        """Construct with a given 'lower' field."""
        super().__init__(**kwargs)
        self.field = field

    def transform_to_storage(self, value):
        """Encode the value in JSON-compatible data types."""
        return [self.field.transform_to_storage(x) for x in value]

    def transform_from_storage(self, value):
        """Decode the value from JSON-compatible data types."""
        return tuple(self.field.transform_from_storage(x) for x in value)

    def validate(self, raw_value):
        """Recursively validate."""
        super().validate(raw_value)

        if raw_value is not None:
            for x in raw_value:
                self.field.validate(x)


class EncodeDecodeField(BaseField):
    """Field with callbacks for transforming in and out of storage."""

    def __init__(self, *, encode, decode, **kwargs):
        """Construct from encode/decode callbacks."""
        super().__init__(**kwargs)
        self.encode = encode
        self.decode = decode

    def transform_to_storage(self, value):
        """Encode the value in JSON-compatible data types."""
        return self.encode(value)

    def transform_from_storage(self, value):
        """Decode the value from JSON-compatible data types."""
        return self.decode(value)
