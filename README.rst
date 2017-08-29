jacquard
========

.. image:: https://badge.fury.io/py/jacquard-split.svg
    :target: https://badge.fury.io/py/jacquard-split

.. image:: https://circleci.com/gh/prophile/jacquard.svg?style=shield
    :target: https://circleci.com/gh/prophile/jacquard

.. image:: https://readthedocs.org/projects/jacquard-split/badge/?version=latest
    :target: http://jacquard-split.readthedocs.io/en/latest/

Split-testing server.

Installation
------------

Jacquard can be installed through `pip`:

.. code:: bash

    pip install jacquard-split

Alternatively it can be built from `GitHub <https://github.com/prophile/jacquard>`_.

Documentation
-------------

Full documentation is available in `ReadTheDocs <http://jacquard-split.readthedocs.io/en/latest/>`_.


.. image:: https://pbs.twimg.com/media/C6_VTi0U4AEobsb.jpg
   :width: 400px
   :alt: advice for hacking

Contributing
------------

After cloning the repo you'll almost certainly want to install into a
`virtualenv <https://python-guide-pt-br.readthedocs.io/en/latest/dev/virtualenvs/>`_
in editable mode:

.. code:: bash

    cd jacquard
    pip install -e .

Since Jacquard requires a config file for all commands, you may also wish to export
the `JACQUARD_CONFIG` environment variable, pointed at a suitable file.

.. code:: bash

    cd jacquard
    export JACQUARD_CONFIG=$PWD/config.cfg

If you're using `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_
to manage your virtualenvs (and you probably want to be), and you've configured
the virtualenv to `cd` to the project directory when it loads, then you can add
the `export` line to your virtualenv's `postactivate` file to have it always
available when you're working on Jacquard.

Running tests
^^^^^^^^^^^^^

Jacquard has good test coverage. A great way to check that you're up and running
is to run the tests. Please ensure you also do this while developing new features
as pull requests without tests (or with failing) are unlikely to be accepted.

Jacquard is tested with py.test, you can run the tests with:

.. code:: bash

    python setup.py test

Linting
^^^^^^^

Jacquard uses `flake8` for linting. You can install the requirements using:

.. code:: bash

    pip install scripts/linting/requirements.txt

and run the linter with:

.. code:: bash

    ./scripts/linting/lint

Documenting
^^^^^^^^^^^

The docs are hosted on `readthedocs <https://readthedocs.org>`_ and built using
`sphinx <http://sphinx-doc.org>`_. The `sphinx-argparse` extension is also needed:

.. code:: bash

    pip install sphinx sphinx-argparse
    python setup.py build_sphinx
