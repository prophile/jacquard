Introduction
============

Jacquard is a server for powering `split tests`_.

.. _`split tests`: https://en.wikipedia.org/wiki/A/B_testing

Installation
------------

Jacquard can be installed from PyPI:

.. code:: bash

    pip install jacquard-split

Configuration
-------------

Example configuration:

.. literalinclude:: ../example.cfg
    :language: cfg

Running the service
-------------------

The command line control tool is available using `jacquard`. To actually run
the server, one must use a WSGI server such as `waitress` or `gunicorn`.

For waitress:

.. code:: bash

    pip install waitress
    waitress-serve --listen='[::1]:1212' jacquard.wsgi:app

For gunicorn:

.. code:: bash

    pip install gunicorn
    gunicorn -b '[::1]:1212' jacquard.wsgi:app
