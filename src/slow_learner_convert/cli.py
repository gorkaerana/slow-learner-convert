import ast
from pathlib import Path
import typing

import click

from slow_learner_convert.constructor import (
    make_class_from_class_def,
    make_class_from_assign,
    Framework,
)


def format_ast_alias(node: ast.alias) -> str:
    if node.asname is not None:
        return f"{node.name} as {node.asname}"
    return f"{node.name}"


def format_ast_import(node: ast.Import) -> str:
    return f"import {', '.join(format_ast_alias(n) for n in node.names)}"


def format_ast_import_from(node: ast.ImportFrom) -> str:
    return f"from {node.module} import {', '.join(format_ast_alias(n) for n in node.names)}"


@click.command()
@click.option(
    "--to",
    type=click.Choice(typing.get_args(Framework)),
    help="Framework to which to convert the input classes",
)
@click.option("--input-file", help="Input file to fetch input classes")
@click.option(
    "--output-file",
    default=None,
    help="Output file to write results. If empty, it defaults to {input_file}_{to}.py",
)
def cli(to: Framework, input_file: str, output_file: str | None):
    import_lines = [f"import {to}" if to != "dataclass" else "import dataclasses"]
    lines_of_code = []
    input_path = Path(input_file).resolve()
    output_path = Path(
        input_path.parent / f"{input_path.stem}_{to}.py"
        if output_file is None
        else output_file
    ).resolve()
    for node in ast.walk(ast.parse(input_path.read_text())):
        # print(ast.dump(node, indent=4))
        if isinstance(node, ast.Import):
            import_lines.append(format_ast_import(node))
        if isinstance(node, ast.ImportFrom):
            import_lines.append(format_ast_import_from(node))
        if isinstance(node, ast.ClassDef):
            lines_of_code.append("\n")
            lines_of_code.extend(make_class_from_class_def(to, node))
        if (
            isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and (node.value.func.id == "TypedDict")
        ):
            lines_of_code.append("\n")
            lines_of_code.extend(make_class_from_assign(to, node))
    output_path.write_text("\n".join(import_lines + lines_of_code))


if __name__ == "__main__":
    cli()
