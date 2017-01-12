from .base import Directory


class DummyDirectory(Directory):
    def __init__(self, users=()):
        self.users = {x.id: x for x in users}

    def lookup(self, user_id):
        return self.users.get(user_id)

    def all_users(self):
        return self.users.values()
