"""Specific exceptions for consumers of the buckets API."""

import re


class NotEnoughBucketsException(ValueError):
    """Exception for insufficient buckets to release a setting."""

    def __init__(self, conflicts):
        """Constructor given a list of conflicting cases."""
        super().__init__(self, conflicts)
        self.conflicts = conflicts

    def human_readable_conflicts(self):
        """A human-readable description of the conflicts this represents."""
        return ", ".join(
            NotEnoughBucketsException._format_conflict(x)
            for x in sorted(self.conflicts)
        )

    @staticmethod
    def _format_conflict(conflict):
        # A bit of a layering violation, but this is only for UX purposes, and
        # does not stand part of the API contract.
        rollout_match = re.match('^rollout:(.+)$', conflict)
        if rollout_match is not None:
            return "rollout on key \"{key}\"".format(
                key=rollout_match.group(1),
            )

        return conflict
