jacquard release process
========================

#. Do sanity checks: verify that the tests and linter pass, locally and
   on CI.
#. Update CHANGES:

   -  Update the version number
   -  Record the release date
   -  List major features, minor features, bugfixes, and
      removals/deprecations.

#. Update the version number in ``setup.py``
#. Update the version numbers (``version`` and ``release``) in
   ``doc/conf.py``.
#. Create an annotated tag for the version, with the version number as
   the name.
#. Push to ``master``, including the tag, which will ship a new release
   on PyPI.
#. If pushing a major version, consider creating the ``stable-<series>``
   branch to which fixes can be backported.

Releasing with aptnik
---------------------

For those using `aptnik <https://www.aptnik.com/>`_ to handle their releases,
there is an additional step. The CI build process creates a ``.deb`` as a build
artifact—take the ``.deb`` from the build corresponding to the *tag*, upload it
to ``aptnik``, and upgrade on any relevant machines with ``apt update``/
``apt upgrade``.
