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
    ("__main__", "cli"),
    ("buckets", "commands"),
    ("buckets", "odm"),
    ("buckets", "storage"),
    ("buckets", "constraints"),
    ("cli", "commands"),
    ("cli", "plugin"),
    ("directory", "plugin"),
    ("directory", "commands"),
    ("experiments", "buckets"),
    ("experiments", "constraints"),
    ("odm", "storage"),
    ("service", "buckets"),
    ("service", "odm"),
    ("service", "users"),
    ("service", "experiments"),
    ("storage", "commands"),
    ("storage", "plugin"),
    ("users", "buckets"),
    ("users", "commands"),
    ("users", "storage"),
    ("wsgi", "service"),
)

EXCLUDED_COMPONENTS = (
    "utils",  # Allowed to be included from anywhere
    "commands_dev",  # Allowed to do whatever it wants
    "utils_dev",  # Allowed to be included from wherever
    "config",  # Excluded due to necessary cyclical behaviour
    "constants",  # Allowed to be included from anywhere
)


def build_dependency_graph():
    assert networkx is not None

    graph = networkx.DiGraph()
    for from_component, to_component in DEPENDENCIES:
        graph.add_edge(from_component, to_component)

    return graph


@pytest.mark.skipif(networkx is None, reason="networkx is not installed")
def test_layers_are_acyclic():
    graph = build_dependency_graph()

    try:
        cycle = networkx.find_cycle(graph)
    except networkx.NetworkXNoCycle:
        cycle = None

    if cycle:
        raise AssertionError(
            "Cycle in component graph: {cycle}".format(
                cycle=" → ".join([x[0] for x in cycle] + [cycle[-1][1]])
            )
        )


RE_JACQUARD_MODULE = re.compile("^jacquard.([a-zA-Z0-9_]+)")


@pytest.mark.skipif(networkx is None, reason="networkx is not installed")
def test_layers():
    root = pathlib.Path(jacquard.__file__).parent

    imports = set()

    forbidden_imports = []

    for source_file in root.glob("**/*.py"):
        if "tests" in source_file.parts:
            continue

        with source_file.open("r") as f:
            contents = f.read()

        relative_parts = list(source_file.relative_to(root).parts)

        # Remove .py from the last path component
        if relative_parts[-1].endswith(".py"):
            relative_parts[-1] = relative_parts[-1][:-3]

        # Remove __init__ if it's the last component
        if relative_parts[-1] == "__init__":
            relative_parts = relative_parts[:-1]

        relative_parts = ["jacquard"] + relative_parts
        module_name = ".".join(relative_parts)

        code = compile(contents, module_name, "exec")

        last_import_source = None

        for instruction in dis.get_instructions(code):
            if instruction.opname == "IMPORT_NAME":
                import_target = instruction.argval

                if not import_target.startswith("jacquard"):
                    continue

                target_elements = import_target.split(".")

                if len(target_elements) > 2 and target_elements[1] != relative_parts[1]:
                    forbidden_imports.append((module_name, import_target))

                imports.add((module_name, import_target))

                last_import_source = import_target
            elif instruction.opname == "IMPORT_FROM":
                if instruction.argval.startswith("_"):
                    raise AssertionError(
                        "Private-scope import: {importer} imports {symbol} "
                        "from {importee}".format(
                            importer=module_name,
                            symbol=instruction.argval,
                            importee=last_import_source,
                        )
                    )

    if forbidden_imports:
        raise AssertionError(
            "{count} forbidden import(s): {illegals}".format(
                count=len(forbidden_imports),
                illegals=", ".join(
                    "{importer} → {importee}".format(
                        importer=importer, importee=importee
                    )
                    for importer, importee in forbidden_imports
                ),
            )
        )

    dependency_graph = build_dependency_graph()

    for importer, importee in imports:
        importer_match = RE_JACQUARD_MODULE.match(importer)
        importee_match = RE_JACQUARD_MODULE.match(importee)

        if importer_match is None or importee_match is None:
            continue

        importer_component = importer_match.group(1)
        importee_component = importee_match.group(1)

        if importer_component in EXCLUDED_COMPONENTS:
            continue

        if importee_component in EXCLUDED_COMPONENTS:
            continue

        try:
            import_path = networkx.shortest_path(
                dependency_graph, importer_component, importee_component
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
                )
            ) from None
