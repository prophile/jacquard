"""Exceptions used in the storage subsystem."""


class Retry(Exception):
    """
    Raised in case of transaction commit failures.

    A request to re-try the transaction, in the hope that this time there are
    no conflicts.
    """

    pass
