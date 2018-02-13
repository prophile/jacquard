"""Specific exceptions for consumers of the buckets API."""

class NotEnoughBucketsException(ValueError):
    """Exception for insufficient buckets to release a setting."""

    def __init__(self, conflicts):
        """Constructor given a list of conflicting cases."""
        super().__init__(self, conflicts)
        self.conflicts = conflicts
