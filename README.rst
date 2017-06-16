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

Running tests
^^^^^^^^^^^^^

Jacquard has good test coverage. A great way to check that you're up and running
is to run the tests. Please ensure you also do this while developing new features
as pull requests without tests (or with failing) are unlikely to be accepted.

Jacquard is tested with py.test, you can run the tests with:

.. code:: bash

    python setup.py test
