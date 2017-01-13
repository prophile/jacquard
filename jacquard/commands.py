"""Command-line interface subclass base class."""

import abc


class BaseCommand(metaclass=abc.ABCMeta):
    """
    Abstract base class for subcommands.

    Subclasses *must* override `handle` and *may* also provide a `help` string
    and/or override `add_arguments`.
    """

    def add_arguments(self, parser):
        """Add argument definitions to a given argparse `ArgumentParser`."""
        pass

    @abc.abstractmethod
    def handle(self, config, options):
        """
        Run command.

        `config` is the system configuration from `jacquard.config` and
        `options` is a `Namespace`-like object of command-line options,
        generally defined from `add_arguments` with a few standard options
        such as `verbose` thrown in for good measure.
        """
        pass
