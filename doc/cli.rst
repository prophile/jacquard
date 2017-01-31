Command-line interface
======================

jacquard is controlled via a command-line interface.

Storage tools
-------------

storage-import
~~~~~~~~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: storage-import

storage-export
~~~~~~~~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: storage-export

storage-flush
~~~~~~~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: storage-flush

Users and settings
------------------

set-default
~~~~~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: set-default

show
~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: show

override
~~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: override

rollout
~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :proc: jacquard
   :path: rollout

Experiments
-----------

list
~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: list

load-experiment
~~~~~~~~~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: load-experiment

launch
~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: launch

conclude
~~~~~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: conclude
