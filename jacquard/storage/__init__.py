"""
Storage engines.

All persistent storage in `jacquard` is handled through pluggable,
transactional key-value stores. These see only occasional writes
but very heavy read load.

The system is pluggable, and new engines can be added by adding entry points
under the `jacquard.storage_engines` group.

Four engines are provided with jacquard:

dummy
  Keeps configuration in memory. Pretty useless outside of unit tests.

file
  SQLite3-based file storage. A sane default when running Jacquard on a
  single machine. Not hugely performant, but doesn't need to be! Also
  occasionally useful as a transport format.

redis
  Redis key-value backing. A next step when scaling up Jacquard. Requires
  little tinkering to be able to run in multi-machine setups.

etcd
  Shared data backed by etcd. This actually monitors etcd for changes and
  keeps the rest of the data in memory. etcd itself is fiddly to configure
  but this backend is by far the most scalable and (other than the dummy)
  the fastest to boot.
"""

from .utils import open_engine

__all__ = ('open_engine',)
