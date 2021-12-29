"""Laboratory of Nitpick ideas."""
import json
from pathlib import Path
from pprint import pprint

import click
import jmespath

from nitpick.formats import TOMLFormat, YAMLFormat
from nitpick.generic import flatten, search_dict

workflow = YAMLFormat(path=Path(".github/workflows/python.yaml"))


def find(expression):
    """Find with JMESpath."""
    print(f"\nExpression: {expression}")
    rv = search_dict(jmespath.compile(expression), workflow.as_object, {})
    print(f"Type: {type(rv)}")
    pprint(rv)


def main():
    """Play around."""
    for path in sorted(Path("docs/ideas/yaml").glob("*.toml")):
        click.secho(str(path), fg="green")

        toml_format = TOMLFormat(path=path)
        config: dict = toml_format.as_object[".github/workflows/python.yaml"]

        # config.pop("contains")
        # config.pop("contains_sorted")

        click.secho("JSON", fg="yellow")
        print(json.dumps(config, indent=2))

        click.secho("Flattened JSON", fg="yellow")
        print(json.dumps(flatten(config), indent=2))

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
    main()
