Experiment files
================

Experiments are loaded from experiment files. These are YAML files.

A simple example:

.. code:: yaml

    id: cta-test
    name: CTA colour test
    branches:
      - id: control
        settings:
          cta-colour: green
      - id: test
        settings:
          cta-colour: red

The various keys are as follows:

id
  The unique experiment ID. By convention, all lowercase and separated by
  dashes.

name
  A human-readable name for the experiment. This key is optional but very
  strongly encouraged.

branches
  A list of the various branches of the experiment. Each has an id which is
  unique within the experiment and the settings which it entails.

constraints
  Restrictions, if any, on to whom this experiment can apply. The types of
  constraint are documented below.

Constraints
-----------

anonymous
  Whether users who are not in the directory can be part of this test. If
  so, this overrides all other constraints. True by default, but if you are
  specifying constraints there is a strong possibility you'll want to make
  this false.

named
  Whether users who *are* in the directory can be part of this test.

era
  Whether this applies to users who join before or after the start of the test,
  or (by default) both. Use the strings "new" or "old".

required_tags
  A list of tags which are required. Any user who is missing any of these tags
  is excluded from the test.

excluded_tags
  A list of tags which are forbidden. Any user who matches any of these tags
  is excluded from the test.
