import abc


class BaseCommand(metaclass=abc.ABCMeta):
    def add_arguments(self, parser):
        pass

    @abc.abstractmethod
    def handle(self, config, options):
        pass
