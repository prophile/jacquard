from jacquard.directory.base import UserEntry
from jacquard.directory.dummy import DummyDirectory
from jacquard.directory.union import UnionDirectory


def test_union_returns_results_from_first_directory():
    user_1 = UserEntry(id=1, join_date=None, tags=())

    dir1 = DummyDirectory(users=[user_1])
    dir2 = DummyDirectory(users=[])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert union_directory.lookup(1) == user_1

def test_union_returns_results_from_second_directory():
    user_1 = UserEntry(id=1, join_date=None, tags=())

    dir1 = DummyDirectory(users=[])
    dir2 = DummyDirectory(users=[user_1])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert union_directory.lookup(1) == user_1

def test_union_returns_results_from_earlier_directories_first():
    user_1 = UserEntry(id=1, join_date=None, tags=('earlier',))
    user_2 = UserEntry(id=1, join_date=None, tags=('later',))

    dir1 = DummyDirectory(users=[user_1])
    dir2 = DummyDirectory(users=[user_2])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert union_directory.lookup(1).tags == ('earlier',)

def test_union_correctly_returns_none_for_double_misses():
    dir1 = DummyDirectory(users=[])
    dir2 = DummyDirectory(users=[])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert union_directory.lookup(1) is None

def test_union_enumerates_all_directories():
    user_1 = UserEntry(id=1, join_date=None, tags=())
    user_2 = UserEntry(id=2, join_date=None, tags=())

    dir1 = DummyDirectory(users=[user_1])
    dir2 = DummyDirectory(users=[user_2])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert list(union_directory.all_users()) == [user_1, user_2]

def test_union_enumeration_does_not_yield_duplicate_user_ids():
    user_1 = UserEntry(id=1, join_date=None, tags=('earlier',))
    user_2 = UserEntry(id=1, join_date=None, tags=('later',))

    dir1 = DummyDirectory(users=[user_1])
    dir2 = DummyDirectory(users=[user_2])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert list(union_directory.all_users()) == [user_1]

def test_null_union_always_returns_none():
    assert UnionDirectory(subdirectories=[]).lookup(1) is None

def test_null_union_yields_no_values_in_enumeration():
    assert list(UnionDirectory(subdirectories=[]).all_users()) == []
