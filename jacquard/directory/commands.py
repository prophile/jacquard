"""Directory-specific user commands."""

from jacquard.commands import BaseCommand, CommandError


class ShowDirectoryEntry(BaseCommand):
    """Display queried directory information for a given user ID."""

    help = "show directory entry for user"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            'user_id',
            help="user ID to show",
        )

    def handle(self, config, options):
        """Run command."""
        entry = config.directory.lookup(options.user_id)

        if entry is None:
            raise CommandError("No directory entry for ID: {0!r}".format(
                options.user_id,
            ))

        print("User ID:", entry.id)
        print("Join date:", entry.join_date)
        if not entry.tags:
            print("No tags")
        else:
            print("Tags: ", ", ".join(entry.tags))
