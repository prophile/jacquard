from jacquard.users import get_settings
from jacquard.storage.dummy import DummyStore


def test_empty_dict_with_no_configuration():
    store = DummyStore('', data={})
    assert get_settings(1, store) == {}


def test_uses_defaults():
    store = DummyStore('', data={'defaults': {'foo': 'bar'}})
    assert get_settings(1, store) == {'foo': 'bar'}


def test_respect_overrides():
    store = DummyStore('', data={
        'defaults': {'foo': 'bar'},
        'overrides/1': {'foo': 'bazz'},
    })
    assert get_settings(1, store) == {'foo': 'bazz'}


def test_ignores_overrides_for_different_users():
    store = DummyStore('', data={
        'defaults': {'foo': 'bar'},
        'overrides/2': {'foo': 'bazz'},
    })
    assert get_settings(1, store) == {'foo': 'bar'}


def test_does_not_use_inactive_experiment_definitions():
    store = DummyStore('', data={
        'experiments/foo': {'branches': [
            {'id': 'control', 'settings': {'foo': 'bar'}},
        ]},
    })
    assert get_settings(1, store) == {}


def test_uses_active_experiment_definitions():
    store = DummyStore('', data={
        'experiments/foo': {'branches': [
            {'id': 'control', 'settings': {'foo': 'bar'}},
        ]},
        'active-experiments': ['foo'],
    })
    assert get_settings(1, store) == {'foo': 'bar'}


def test_overrides_take_precedence_over_experiment_settings():
    store = DummyStore('', data={
        'experiments/foo': {'branches': [
            {'id': 'control', 'settings': {'foo': 'bar'}},
        ]},
        'active-experiments': ['foo'],
        'overrides/1': {'foo': 'bazz'},
    })
    assert get_settings(1, store) == {'foo': 'bazz'}
