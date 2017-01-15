"""User directory miscellaneous utilities."""

from jacquard.plugin import plug


def open_directory(config, engine, kwargs):
    """
    Open a given directory, with engine and kwargs.

    Looks up the directory through the `jacquard.directory_engines` entry
    point group and instantiates the given class with `**kwargs`.
    """
    cls = plug('directory_engines', engine, config=config)()
    return cls(**kwargs)
