from unittest import mock

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
    user_1 = UserEntry(id=1, join_date=None, tags=("earlier",))
    user_2 = UserEntry(id=1, join_date=None, tags=("later",))

    dir1 = DummyDirectory(users=[user_1])
    dir2 = DummyDirectory(users=[user_2])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert union_directory.lookup(1).tags == ("earlier",)


def test_union_correctly_returns_none_for_double_misses():
    dir1 = DummyDirectory(users=[])
    dir2 = DummyDirectory(users=[])

    union_directory = UnionDirectory(subdirectories=[dir1, dir2])

    assert union_directory.lookup(1) is None


def test_null_union_always_returns_none():
    assert UnionDirectory(subdirectories=[]).lookup(1) is None


def test_construction_from_config():
    user_1 = UserEntry(id=1, join_date=None, tags=("earlier",))
    user_2 = UserEntry(id=2, join_date=None, tags=("later",))

    dir1 = DummyDirectory(users=[user_1])
    dir2 = DummyDirectory(users=[user_2])

    config = object()

    with mock.patch(
        "jacquard.directory.union.open_directory", mock.Mock(side_effect=(dir1, dir2))
    ) as patched:
        union_directory = UnionDirectory.from_configuration(
            config,
            {
                "engine[0]": "dummy",
                "arg[0]": "arg0",
                "engine[1]": "dummy",
                "arg[1]": "arg1",
            },
        )
        patched.assert_has_calls(
            [
                mock.call(config, "dummy", {"arg": "arg0"}),
                mock.call(config, "dummy", {"arg": "arg1"}),
            ]
        )

        assert union_directory.lookup(1) is user_1
        assert union_directory.lookup(2) is user_2
