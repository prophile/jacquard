Writing plugins
===============

A number of aspects of Jacquard are pluggable: the key ones right now being
storage engines and directories.

You will probably want to write a directory plugin to interface with your
database.

Directories
-----------

API
~~~

.. autoclass:: jacquard.directory.base.Directory
    :members:

.. autoclass:: jacquard.directory.base.UserEntry
    :members:

Loading the plugin
~~~~~~~~~~~~~~~~~~

Storage engines
---------------

API
~~~

.. autoclass:: jacquard.storage.base.StorageEngine
    :members:

Advanced usage
--------------
