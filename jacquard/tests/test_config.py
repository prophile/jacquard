import io
import sys
import tempfile
import textwrap

from jacquard.config import load_config

CONFIG_FILE = """
[storage]
engine = dummy
url = dummy

[directory]
engine = dummy

[test_section]
test_key = test_value
"""


def load_test_config(extra=''):
    f = io.StringIO(CONFIG_FILE + textwrap.dedent(extra))
    return load_config(f)


def test_load_config_smoke():
    load_test_config()


def test_load_config_from_file():
    with tempfile.NamedTemporaryFile('w') as f:
        f.write(CONFIG_FILE)
        f.flush()
        load_config(f.name)


def test_config_creates_storage_engine():
    config = load_test_config()

    with config.storage.transaction() as store:
        store['bees'] = 'pony'

    with config.storage.transaction() as store:
        assert store['bees'] == 'pony'


def test_config_creates_directory():
    config = load_test_config()

    assert list(config.directory.all_users()) == []


def test_config_can_iterate_over_sections():
    config = load_test_config()

    assert set(config) == {'storage', 'directory', 'test_section', 'DEFAULT'}


def test_config_can_query_subsections():
    config = load_test_config()

    assert config['test_section']['test_key'] == 'test_value'


def test_config_can_test_section_inclusion():
    config = load_test_config()

    assert 'test_section' in config
    assert 'test_section2' not in config


def test_config_section_len():
    config = load_test_config()

    assert len(config) == 4


def test_adds_extra_elements_to_path():
    try:
        sys.path.remove('/gravity')
    except ValueError:
        pass

    load_test_config("""
    [paths]
    a_path = /gravity
    """)

    assert '/gravity' in sys.path
