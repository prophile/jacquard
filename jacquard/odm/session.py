"""ODM interaction sessions."""

import contextlib
import collections
import collections.abc

from .utils import method_dispatch
from .fields import BaseField

RAISE = object()
EMPTY = object()
CREATE = object()


class Session(object):
    """Single interaction session, for a document store."""

    @method_dispatch
    def __init__(self, get, put, delete):
        """
        Standard constructor.

        `get` is a callable which, given a string key, either returns the
        associated JSON-compatible data or raises a LookupError.

        `put` is a callable which takes a string key and JSON-compatible data.

        `delete` is a callable which takes a string key and either removes the
        corresponding entry or, if the entry does not exist, raises a
        LookupError.
        """
        self.store_get = get
        self.store_put = put
        self.store_delete = delete
        self._instances = collections.defaultdict(dict)
        self._dirty = collections.defaultdict(set)

    @__init__.register(collections.abc.MutableMapping)
    def _(self, store):
        """
        Constructor from mutable mappings.

        Passes through to the standard constructor with `__getitem__`,
        `__setitem__` and `__delitem__`.
        """
        self.__init__(
            get=store.__getitem__,
            put=store.__setitem__,
            delete=store.__delitem__,
        )
        self.store = store

    def add(self, instance):
        """Add a fresh instance to the session."""
        model_instances = self._instances[type(instance)]

        previous_instance = model_instances.get(instance.pk)

        if instance.session is not None and instance.session is not self:
            raise RuntimeError("Instance already belongs to another session")

        if previous_instance is instance:
            # For idempotence, no action
            return

        if previous_instance is not None:
            raise RuntimeError("Multiple instances for pk: %r" % instance.pk)

        model_instances[instance.pk] = instance
        instance.session = self
        self.mark_instance_dirty(instance)

    def remove(self, instance):
        """Disassociate an instance from the session and remove it."""
        if instance.session is None:
            # For idempotence, do nothing here
            return

        if instance.session is not self:
            raise RuntimeError("Instance belongs to a different session")

        instance.session = None
        del self._instances[type(instance)][instance.pk]

        self.mark_model_pk_dirty(type(instance), instance.pk)

    def get(self, model, pk, default=RAISE):
        """
        Look up an instance by PK.

        This guarantees that within one session, querying multiple times for
        the same model/pk will return the same object.
        """
        try:
            return self._instances[model][pk]
        except KeyError:
            pass

        storage_key = model.storage_key(pk)
        try:
            data = self.store_get(storage_key)
        except KeyError:
            if default is RAISE:
                raise  # Propagate the original KeyError

            if default is EMPTY:
                return model(pk)

            if default is CREATE:
                instance = model(pk)
                self.add(instance)
                return instance

            return default

        # Use the upgrade path such as it is
        data = model.transitional_upgrade_raw_data(data)

        instance = model(pk=pk)
        instance._fields = data
        instance.session = self

        self._instances[model][pk] = instance
        return instance

    def mark_instance_dirty(self, instance):
        """
        Mark an instance as needing to be written on flush.

        This generally won't need to be called directly.
        """
        self.mark_model_pk_dirty(type(instance), instance.pk)

    def mark_model_pk_dirty(self, model, pk):
        """
        Mark a model/pk pair as needing to be written on flush.

        This generally won't need to be called directly.
        """
        self._dirty[model].add(pk)

    def flush(self):
        """Write all pending changes to the document store."""
        for model, dirty_pks in self._dirty.items():
            model_instances = self._instances[model]
            model_storage_key = model.storage_key
            for pk in dirty_pks:
                storage_key = model_storage_key(pk)

                try:
                    instance = model_instances[pk]
                except KeyError:
                    try:
                        self.store_delete(storage_key)
                    except KeyError:
                        # It may not exist in storage if there has been no
                        # flush since the object's being `add`ed.
                        pass
                    continue

                # Validate all of the fields
                for field_name, field in vars(model).items():
                    if not isinstance(field, BaseField):
                        continue

                    try:
                        raw_value = instance._fields[field_name]
                    except KeyError:
                        continue

                    field.validate(raw_value)

                self.store_put(storage_key, dict(instance._fields))

        self._dirty.clear()


@contextlib.contextmanager
def transaction(storage, **kwargs):
    """Run a session for a given `StorageEngine`."""
    with storage.transaction(**kwargs) as store:
        session = Session(store)
        try:
            yield session
        except Exception:
            raise
        else:
            session.flush()
