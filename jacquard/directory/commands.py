from jacquard.commands import BaseCommand


class ListUsers(BaseCommand):
    help = "list all users"

    def handle(self, config, options):
        for user in config.directory.all_users():
            print(user.id, str(user.join_date), ' '.join(user.tags))
