"""Command-line utilities for user directories."""

from jacquard.commands import BaseCommand


class ListUsers(BaseCommand):
    """
    List all users from a directory.

    This is primarily a debugging command (hence the `plumbing` flag) when
    checking whether your directory is correctly configured. Its real-world
    uses are, uh, limited.
    """

    plumbing = True
    help = "list all users"

    def handle(self, config, options):
        """Run command."""
        for user in config.directory.all_users():
            print(user.id, str(user.join_date), ' '.join(user.tags))
