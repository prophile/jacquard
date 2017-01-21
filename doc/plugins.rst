Writing plugins
===============

A number of aspects of Jacquard are pluggable: the key ones right now being
storage engines and directories.

You will probably want to write a directory plugin to interface with your
database.

Directories
-----------

Declared in the `directory_entries` plugin group.

API
~~~

.. autoclass:: jacquard.directory.base.Directory
    :members:

.. autoclass:: jacquard.directory.base.UserEntry
    :members:

Declaring plugins
-----------------

Plugin entry points (such as new directory engines) can be declared in one of
two ways: *simplified* plugins, and *setuptools* plugins.

simplified plugins
~~~~~~~~~~~~~~~~~~

Simplified plugins are declared in the Jacquard configuration file. To add,
for instance, a directory engine called "my_directory_engine" which loads the
`Directory` subclass `MyDirectory` from a Python module `my_directory.py` one
would add:

.. code:: cfg

    [plugins:directory_engines]
    my_directory_engine = my_directory:MyDirectory

This will look for `my_directory.py` anywhere on the Python path, which for
Jacquard includes `/etc/jacquard/plugins`. This is the simplest way to add
plugins.

setuptools plugins
~~~~~~~~~~~~~~~~~~

For advanced use, or for plugins which are made for redistribution and/or
installation through pip and PyPI, you can declare plugins via the standard
Python `entry_points` mechanism.

Where this is normally used to declare entry points for command-line tools via
the `console_scripts` group, in this case entry points are declared for the
`jacquard.directory_engines` group.

Storage engines
---------------

Storage plugins can be added for new ways to store data, such as custom key/
value stores, or even a fast enough SQL database if you're feeling
particularly crazy.

Declared in the `storage_engines` plugin group.

API
~~~

.. autoclass:: jacquard.storage.base.StorageEngine
    :members:

Subcommands
-----------

Subcommand plugins add new subcommands to the `jacquard` command-line utility.

Declared in the `commands` plugin group.

.. note::

    Due to current technical restrictions, simplified plugins cannot add
    subcommands—only setuptools plugins.

API
~~~

.. autoclass:: jacquard.commands.BaseCommand
    :members:

HTTP endpoints
--------------

HTTP endpoint plugins add new URL handlers for the HTTP API.

Declared in the `http_endpoints` plugin group.

API
~~~

.. autoclass:: jacquard.service.base.Endpoint
    :members:
