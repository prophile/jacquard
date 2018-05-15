import pytest

from jacquard.odm import Model, Session, TextField


class Example(Model):
    name = TextField()
    defaulted_field = TextField(null=False, default="Pony")


def test_builtin_model_key():
    assert Example.storage_key(1) == "examples/1"


def test_add():
    data = {}
    session = Session(data)
    ex1 = Example(pk=1)
    session.add(ex1)
    session.flush()

    assert data == {"examples/1": {}}


def test_add_is_idempotent():
    data = {}
    session = Session(data)
    ex1 = Example(pk=1)
    session.add(ex1)
    session.add(ex1)
    session.flush()

    assert data == {"examples/1": {}}


def test_add_with_field():
    data = {}
    session = Session(data)
    ex1 = Example(pk=1, name="Paul")
    session.add(ex1)
    session.flush()

    assert data == {"examples/1": {"name": "Paul"}}


def test_modify_with_field():
    data = {}
    session = Session(data)
    ex1 = Example(pk=1, name="Paul")
    session.add(ex1)
    session.flush()

    ex1.name = "Paula"
    session.flush()

    assert data == {"examples/1": {"name": "Paula"}}


def test_get():
    data = {"examples/1": {"name": "Paula"}}
    session = Session(data)

    ex1 = session.get(Example, 1)
    assert ex1.name == "Paula"


def test_get_twice_returns_same_instance():
    data = {"examples/1": {"name": "Paula"}}
    session = Session(data)

    ex1 = session.get(Example, 1)
    ex2 = session.get(Example, 1)
    assert ex1 is ex2


def test_get_missing_entity_raises_keyerror():
    data = {"examples/1": {"name": "Paula"}}
    session = Session(data)

    with pytest.raises(KeyError):
        session.get(Example, 2)


def test_get_then_edit_entity():
    data = {"examples/1": {"name": "Paula"}}
    session = Session(data)

    ex1 = session.get(Example, 1)
    ex1.name = "Paul"
    session.flush()

    assert data == {"examples/1": {"name": "Paul"}}


def test_get_then_remove_entity():
    data = {"examples/1": {"name": "Paula"}}
    session = Session(data)

    ex1 = session.get(Example, 1)
    session.remove(ex1)
    session.flush()

    assert data == {}


def test_remove_is_idempotent():
    data = {"examples/1": {"name": "Paula"}}
    session = Session(data)

    ex1 = session.get(Example, 1)
    session.remove(ex1)
    session.remove(ex1)
    session.flush()


def test_add_then_remove_entity_has_no_effect():
    data = {}
    session = Session(data)

    ex1 = Example(pk=1, name="Horse")
    session.add(ex1)
    session.remove(ex1)
    session.flush()

    assert data == {}


def test_error_when_adding_instance_to_two_sessions():
    session1, session2 = Session({}), Session({})

    ex1 = Example(pk=1, name="Horse")

    session1.add(ex1)
    with pytest.raises(RuntimeError):
        session2.add(ex1)


def test_error_when_instantiating_with_duplicate_id():
    session = Session({})

    session.add(Example(pk=1))
    with pytest.raises(RuntimeError):
        session.add(Example(pk=1))


def test_error_when_removing_from_different_instance():
    session1 = Session({"examples/1": {}})
    session2 = Session({})

    ex1 = session1.get(Example, 1)
    with pytest.raises(RuntimeError):
        session2.remove(ex1)


def test_fields_take_default_values_when_unspecified():
    instance = Example(pk=1)
    assert instance.defaulted_field == "Pony"


def test_non_nullable_fields_cannot_be_saved_with_null_values():
    instance = Example(pk=1)
    instance.defaulted_field = None
    session = Session({})
    session.add(instance)

    with pytest.raises(ValueError):
        session.flush()


def test_sessions_are_not_global():
    instance_session1 = Example(pk=1)
    session = Session({})
    session.add(instance_session1)
    session.flush()

    session2 = Session({})
    with pytest.raises(KeyError):
        instance_session2 = session2.get(Example, 1)


def test_basic_repr_functions_properly():
    instance = Example(pk=1)
    instance.name = "Bees"

    assert repr(instance) == "Example(pk=1, name='Bees')"
