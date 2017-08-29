Command-line interface
======================

jacquard is controlled via a command-line interface.

Information retrieval
---------------------

list
~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: list

show
~~~~

.. argparse::
   :module: jacquard.cli
   :func: argument_parser
   :prog: jacquard
   :path: show


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
   :prog: jacquard
   :path: rollout

Experiments
-----------

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
