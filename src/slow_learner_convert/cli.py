import ast
from pathlib import Path
from pprint import pprint

import click

from slow_learner_convert.constructor import (
    make_class_from_class_def,
    make_class_from_assign,
    Framework,
)


@click.command()
@click.option("--to", help="Framework to which to convert the input classes")
@click.option("--input-file", help="Input file to fetch input classes")
def cli(to: Framework, input_file: str):
    input_path = Path(input_file).resolve()
    for node in ast.walk(ast.parse(input_path.read_text())):
        if isinstance(node, ast.ClassDef):
            pprint(make_class_from_class_def(to, node))
            print()
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and (node.value.func.id == "TypedDict")
        ):
            pprint(make_class_from_assign(to, node))
            print()


if __name__ == "__main__":
    cli()
