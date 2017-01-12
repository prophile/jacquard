import abc
import collections


UserEntry = collections.namedtuple('UserEntry', 'id join_date tags')


class Directory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def lookup(self, user_id):
        pass

    @abc.abstractmethod
    def all_users(self):
        pass
