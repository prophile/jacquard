Concepts
========

Settings
--------

The core concept of Jacquard is the settings map. This is a (JSON)
dictionary mapping free-form keys to free-form values, and is the only
aspect of Jacquard which client code needs to care about.

Imagine running an experiment—the classic split test experiment—of testing
conversion rate changes by altering the colour of a call to action. The basic
approach is to run some kind of migration to partition users between the two
groups, or pick groups randomly in a session key. On the page with the call to
action, code or templates would check which group a user is in and pick the
corresponding colour. This, in practice, is a lot of faff over a large number
of tests.

The Jacquard approach is to ask the Jacquard server for the user's settings,
which in this case would just tell client code what colour the CTA is:

.. code:: json

    {'cta_colour': 'green'}

Defaults
--------

The defaults are a global settings map, shared between all users. In general,
this will be the "current best" configuration of your product. Production
features are turned on, experimental features are turned off, colours and
tweakable numbers are set to best guesses or taken from the results of previous
A/B tests.

The defaults can be controlled through the `jacquard set-default` command.

Experiments
-----------

An experiment is an actual test to be run on users. Each experiment is defined
by a unique `id` (it is recommended to use slugs such as `"cta_colour_test_3"`)
and specifies a number of branches.

A branch has its own `id` (unique within the experiment but not globally
unique) and specifies the `settings` which take precedence over the defaults
for users on that branch.

By convention, the first branch is used as a control group and takes the `id`
`"control"`.

Overrides
---------

From time to time, it can be necessary to bypass the usual "defaults plus
experiments" model. The overrides system allows one to change specific settings
for specific users, which takes precedence over all other sources of settings.

There are any number of reasons to use overrides:

* Testing features by enabling the feature flags for specific testers,
* Emulating the settings of another user for testing purposes,
* Turning features on and off to fix specific users' issues,
* Appeasing those few high-value customers who like things *just so*.

Overrides can be controlled through the `jacquard override` command.

Storage
-------

Jacquard stores all of its data—defaults, overrides, the state of experiments—
in a persistant key-value store. This can be powered by one of several storage
engines (a system which is pluggable).

By default a local, file-based storage engine is used, but this doesn't scale
to having Jacquard running on multiple machines – and the recommended
deployment pattern is to run a Jacquard instance on the same machine as
anything which uses it.

To that end Jacquard is packed with an alternate storage engine,  backed by
Redis [#note1]_.

There are command-line tools for migrating between different storage engines,
so choosing one should not be considered a large commitment.

User directories
----------------

It's often useful not to run experiments on *all* users. We will want to
exclude those who aren't logged in, run tests on users who joined in particular
ranges, or exclude or include particular groups of users (for instance, those
who finished a registration flow, or staff users, or customers).

To this end one can specify a *user directory* – another pluggable system for
getting further information by user ID.

Jacquard ships with two user directory engines. One, the dummy engine, is the
default: it disavows any knowledge of any users. There is also a basic Django
engine for users of `django.contrib.auth`, which provides a tag for indicating
superusers by pulling data from the `auth_user` table of a connected database.

For more complicated use it will probably be useful to write a custom user
directory by creating a subclass of `Directory`.

.. rubric:: Footnotes

.. [#note1] There is also the experimental `redis-cloned` backend, technically.
