import re
import dis
import pathlib

import pytest

import jacquard

try:
    import networkx
except ImportError:
    networkx = None


DEPENDENCIES = (
    ('__main__', 'cli'),

    ('buckets', 'commands'),
    ('buckets', 'experiments'),
    ('buckets', 'odm'),
    ('buckets', 'storage'),

    ('cli', 'commands'),
    ('cli', 'config'),
    ('cli', 'plugin'),

    ('config', 'directory'),
    ('config', 'plugin'),
    ('config', 'storage'),

    ('directory', 'config'),
    ('directory', 'plugin'),

    ('experiments', 'buckets'),

    ('odm', 'storage'),

    ('plugin', 'config'),

    ('service', 'buckets'),
    ('service', 'odm'),
    ('service', 'users'),

    ('storage', 'commands'),
    ('storage', 'config'),
    ('storage', 'plugin'),

    ('users', 'buckets'),
    ('users', 'commands'),
    ('users', 'storage'),

    ('wsgi', 'service'),
)


def build_dependency_graph():
    assert networkx is not None

    graph = networkx.DiGraph()
    for from_component, to_component in DEPENDENCIES:
        graph.add_edge(from_component, to_component)

    return graph


@pytest.mark.skipif(networkx is None, reason="networkx is not installed")
@pytest.mark.xfail
def test_layers_are_acyclic():
    graph = build_dependency_graph()

    try:
        cycle = networkx.find_cycle(graph)
    except networkx.NetworkXNoCycle:
        cycle = None

    if cycle:
        raise AssertionError(
            "Cycle in component graph: {cycle}".format(
                cycle=' → '.join([x[0] for x in cycle] + [cycle[-1][1]]),
            ),
        )


RE_JACQUARD_MODULE = re.compile('^jacquard.([a-zA-Z0-9_]+)')


@pytest.mark.skipif(networkx is None, reason="networkx is not installed")
def test_layers():
    root = pathlib.Path(jacquard.__file__).parent

    imports = set()

    for source_file in root.glob('**/*.py'):
        if 'tests' in source_file.parts:
            continue

        with source_file.open('r') as f:
            contents = f.read()

        relative_parts = list(source_file.relative_to(root).parts)

        # Remove .py from the last path component
        if relative_parts[-1].endswith('.py'):
            relative_parts[-1] = relative_parts[-1][:-3]

        # Remove __init__ if it's the last component
        if relative_parts[-1] == '__init__':
            relative_parts = relative_parts[:-1]

        relative_parts = ['jacquard'] + relative_parts
        module_name = '.'.join(relative_parts)

        code = compile(contents, module_name, 'exec')

        for instruction in dis.get_instructions(code):
            if instruction.opname == 'IMPORT_NAME':
                import_target = instruction.argval

                if not import_target.startswith('jacquard'):
                    continue

                imports.add((module_name, import_target))

    dependency_graph = build_dependency_graph()

    for importer, importee in imports:
        importer_match = RE_JACQUARD_MODULE.match(importer)
        importee_match = RE_JACQUARD_MODULE.match(importee)

        if importer_match is None or importee_match is None:
            continue

        importer_component = importer_match.group(1)
        importee_component = importee_match.group(1)

        if importee_component == 'utils':
            # Utils is allowed to be imported globally
            continue

        try:
            import_path = networkx.shortest_path(
                dependency_graph,
                importer_component,
                importee_component,
            )
        except networkx.NetworkXNoPath:
            raise AssertionError(
                "Layering violation: {importer_component} cannot depend on "
                "{importee_component} ({importer_module} currently imports "
                "{importee_module})".format(
                    importer_component=importer_component,
                    importee_component=importee_component,
                    importer_module=importer,
                    importee_module=importee,
                ),
            )
