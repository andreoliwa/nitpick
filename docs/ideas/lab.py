"""Laboratory of Nitpick ideas."""
import json
from pathlib import Path
from pprint import pprint

import click
import jmespath
import tomlkit
from flatten_dict import flatten
from icecream import ic
from identify import identify

from nitpick.blender import TomlDoc, YamlDoc, flatten_quotes, search_json

# from tomlkit import nl


workflow = YamlDoc(path=Path(".github/workflows/python.yaml"))


def find(expression):
    """Find with JMESpath."""
    print(f"\nExpression: {expression}")
    rv = search_json(workflow.as_object, jmespath.compile(expression), {})
    print(f"Type: {type(rv)}")
    pprint(rv)


@click.group()
def cli_lab():
    """Laboratory of experiments and ideas."""


@cli_lab.command()
@click.argument("path_from_root")
def convert(path_from_root: str):
    """Convert file to a TOML config."""
    tags = identify.tags_from_path(path_from_root)
    if "yaml" in tags:
        which_doc = YamlDoc(path=path_from_root)
    else:
        raise NotImplementedError(f"No conversion for these types: {tags}")

    toml_doc = TomlDoc(obj={path_from_root: which_doc.as_object}, use_tomlkit=True)
    print(toml_doc.reformatted)
    return toml_doc.reformatted


@cli_lab.command()
def dump():
    """Trying not to dump empty tables with tomlkit."""
    empty_table = {
        "section": {"key": "value"},
        "tool": {"black": {"line-length": 120}, "some": {"deep": {"nesting": [1, 2, 3]}}},
    }

    ic(flatten(empty_table))

    print("\n>>> tomlkit.dumps() from dict")
    print(tomlkit.dumps(empty_table))

    print("\n>>> tomlkit.dumps() from objects")
    doc = tomlkit.document()

    doc["section"] = {"key": "value"}
    # doc["section"].add(nl())

    doc["tool"] = tomlkit.table(is_super_table=True)
    doc["tool"]["black"] = {"line-length": 120}
    # doc["tool"]["black"].add(nl())

    doc["tool"]["some"] = tomlkit.table(is_super_table=True)
    doc["tool"]["some"]["deep"] = {"nesting": [1, 2, 3]}

    print(tomlkit.dumps(doc))


def main():
    """Play around."""
    for path in sorted(Path("docs/ideas/yaml").glob("*.toml")):
        click.secho(str(path), fg="green")

        toml_doc = TomlDoc(path=path)
        config: dict = toml_doc.as_object[".github/workflows/python.yaml"]

        # config.pop("contains")
        # config.pop("contains_sorted")

        click.secho("JSON", fg="yellow")
        print(json.dumps(config, indent=2))

        click.secho("Flattened JSON", fg="yellow")
        print(json.dumps(flatten_quotes(config), indent=2))

    # find("jobs.build")
    # find("jobs.build.strategy.matrix")
    # find('jobs.build.strategy.matrix."python-version"')
    # find("jobs.build.strategy.matrix.os")
    # find("jobs.build.steps[]")
    # find("jobs.build.steps[0]")
    # find("jobs.build.steps[1]")
    # find('jobs.build."runs-on"')
    # find("jobs.build.steps[].name")
    # find("jobs.build.steps[].uses")
    # find("jobs.build.steps[].[name, uses]")
    # find("jobs.build.steps[].{name: name, uses: uses}")


if __name__ == "__main__":
    cli_lab()
