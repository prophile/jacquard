"""The actual Bucket ODM model itself."""

from jacquard.odm import Model, ListField, EncodeDecodeField
from jacquard.buckets.entry import Entry, decode_entry, encode_entry


class Bucket(Model):
    """A single partition of user space, with associated settings."""

    entries = ListField(null=False, field=EncodeDecodeField(
        encode=encode_entry,
        decode=decode_entry,
        null=False,
        default=[],
    ), default=())

    @classmethod
    def transitional_upgrade_raw_data(cls, data):
        """Convert data from the old list format if needs be."""
        if isinstance(data, list):
            # Data is in the old "just entries" format, forward-convert it to
            # the ODM format.
            return {'entries': data}
        return data

    def get_settings(self, user_entry):
        """Look up settings by user entry."""
        settings = {}

        for entry in self.entries:
            if (
                not entry.constraints or
                entry.constraints.matches_user(user_entry)
            ):
                settings.update(entry.settings)

        return settings

    def affected_settings_by_constraints(self):
        """
        Get constraints and the settings under them in this bucket.

        All settings determined in this bucket, by the constraints that they
        apply under.
        """
        return {
            x.constraints: frozenset(x.settings.keys())
            for x in self.entries
        }

    def needs_constraints(self):
        """Whether any settings in this bucket involve constraint lookups."""
        return any(x.constraints for x in self.entries)

    def add(self, key, settings, constraints):
        """Add a new, keyed entry."""
        self.entries = self.entries + (Entry(
            key=key,
            settings=settings,
            constraints=constraints,
        ),)
        self.mark_dirty()

    def remove(self, key):
        """Remove any matching, keyed entry."""
        self.entries = [
            x
            for x in self.entries
            if x.key != key
        ]
        self.mark_dirty()

    def covers(self, key):
        """Whether a given key is covered under this bucket."""
        return any(
            x.key == key
            for x in self.entries
        )
