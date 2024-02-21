import ast
from pathlib import Path
import sys


INDENT = " " * 4


"""
TODO: given a variable assignment (after the type assignment), support adding that
value as default via library specific default. E.g., given
```
class Foo(TypedDict):
    bar: SomeType = instance_of_the_type
```
create
```
@dataclasses.dataclass
class Foo:
    bar: SomeType = dataclasses.field(default=instance_of_the_type)
```

TODO: given specific type assignments, support framework-specific features.
E.g., given
```
class Foo(TypedDict):
    bar: Literal["something"]
```
create
```
@dataclasses.dataclass
class Foo:
    bar: SomeType = dataclasses.field(default="something")
```
if type assignment `Literal[something]` maybe it would be useful
to define the attribute as `attrs.fields(default=something)`

"""


def ast_class_def_to_dataclass_code(node: ast.ClassDef) -> list[str]:
    # TODO: support `dataclasses.dataclass` arguments.
    # See https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass
    lines_of_code = ["@dataclass", f"class {node.name}:"]
    # Gather attributes and type assignments
    for n in node.body:
        attr_name: str | None = None
        type_: str | None = None
        # TODO: perhaps support other `ast` node types
        if isinstance(n, ast.AnnAssign):
            # TODO: perhaps support other `ast` node types
            if isinstance(n.target, ast.Name) and isinstance(n.annotation, ast.Name):
                attr_name, type_ = n.target.id, n.annotation.id
        if (attr_name is not None) and (type_ is not None):
            lines_of_code.append(f"{INDENT}{attr_name}: {type_}")
    return lines_of_code


def ast_class_def_to_attrs_code(node: ast.ClassDef) -> list[str]:
    # TODO: support `attrs.define` arguments or `attrs.mutable` or `attrs.frozen`
    # See https://www.attrs.org/en/stable/api.html#attrs.define
    lines_of_code = ["@define", f"class {node.name}:"]
    # Gather attributes and type assignments
    for n in node.body:
        attr_name: str | None = None
        type_: str | None = None
        # TODO: perhaps support other `ast` node types
        if isinstance(n, ast.AnnAssign):
            # TODO: perhaps support other `ast` node types
            if isinstance(n.target, ast.Name) and isinstance(n.annotation, ast.Name):
                attr_name, type_ = n.target.id, n.annotation.id
        if (attr_name is not None) and (type_ is not None):
            lines_of_code.append(f"{INDENT}{attr_name}: {type_}")
    return lines_of_code


def ast_class_def_to_msgspec_code(node: ast.ClassDef) -> list[str]:
    # TODO: support other `msgspec.Struct` arguments.
    # See https://jcristharif.com/msgspec/api.html#msgspec.Struct
    lines_of_code = [f"class {node.name}(msgspec.Struct):"]
    # Gather attributes and type assignments
    for n in node.body:
        attr_name: str | None = None
        type_: str | None = None
        # TODO: perhaps support other `ast` node types
        if isinstance(n, ast.AnnAssign):
            # TODO: perhaps support other `ast` node types
            if isinstance(n.target, ast.Name) and isinstance(n.annotation, ast.Name):
                attr_name, type_ = n.target.id, n.annotation.id
        if (attr_name is not None) and (type_ is not None):
            lines_of_code.append(f"{INDENT}{attr_name}: {type_}")
    return lines_of_code


def ast_class_def_to_pydantic_code(node: ast.ClassDef) -> list[str]:
    lines_of_code = [f"class {node.name}(BaseModel):"]
    # Gather attributes and type assignments
    for n in node.body:
        attr_name: str | None = None
        type_: str | None = None
        # TODO: perhaps support other `ast` node types
        if isinstance(n, ast.AnnAssign):
            # TODO: perhaps support other `ast` node types
            if isinstance(n.target, ast.Name) and isinstance(n.annotation, ast.Name):
                attr_name, type_ = n.target.id, n.annotation.id
        if (attr_name is not None) and (type_ is not None):
            lines_of_code.append(f"{INDENT}{attr_name}: {type_}")
    return lines_of_code


if __name__ == "__main__":
    from pprint import pprint

    input_path = Path(sys.argv[1]).resolve()
    for node in ast.walk(ast.parse(input_path.read_text())):
        if isinstance(node, ast.ClassDef):
            pprint(ast_class_def_to_dataclass_code(node))
            pprint(ast_class_def_to_attrs_code(node))
            pprint(ast_class_def_to_msgspec_code(node))
            pprint(ast_class_def_to_pydantic_code(node))
            print()
