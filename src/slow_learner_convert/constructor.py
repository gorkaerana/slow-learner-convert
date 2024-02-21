import ast
from typing import Literal, TypeAlias, Type


Framework: TypeAlias = Literal["dataclass", "attrs", "msgspec", "pydantic"]

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


class BaseConstructor:
    def __init__(self, class_name: str):
        self.class_name: str = class_name
        self.lines_of_code: list[str] = self.initial_lines_of_code()

    def initial_lines_of_code(self, *args, **kwargs) -> list[str]:
        raise NotImplementedError

    def get_attribute_name(self, name: ast.AnnAssign) -> str:
        # TODO: need to support `ast.Name`, `ast.Attribute`, `ast.Subscript`
        # before removing type ignore below
        return name.target.id  # type: ignore

    def get_type_annotation(self, name: ast.AnnAssign) -> str:
        # TODO: need to support `ast.Constant`, and `ast.Name`
        # before removing type ignore below
        return name.annotation.id  # type: ignore

    def add_attribute(self, node: ast.AnnAssign):
        self.lines_of_code.append(
            f"{INDENT}{self.get_attribute_name(node)}: {self.get_type_annotation(node)}"
        )


class DataclassConstructor(BaseConstructor):
    def initial_lines_of_code(
        self,
        init: bool | None = None,
        repr: bool | None = None,
        eq: bool | None = None,
        order: bool | None = None,
        unsafe_hash: bool | None = None,
        frozen: bool | None = None,
        match_args: bool | None = None,
        kw_only: bool | None = None,
        slots: bool | None = None,
        weakref_slot: bool | None = None,
    ) -> list[str]:
        """Keyword arguments mimic those of `dataclasses.dataclass`. See
        https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass"""
        kwargs = (
            "init",
            "repr",
            "eq",
            "order",
            "unsafe_hash",
            "frozen",
            "match_args",
            "kw_only",
            "slots",
            "weakref_slot",
        )
        decorator = "@dataclass"
        decorator_kwargs = []
        for k in kwargs:
            if (value := locals()[k]) is not None:
                decorator_kwargs.append(f"{k}={value}")
        if decorator_kwargs:
            prettied_decorator_kwargs = "\n".join(decorator_kwargs)
            decorator = f"{decorator}({prettied_decorator_kwargs})"
        return [decorator, f"class {self.class_name}:"]


class AttrsConstructor(BaseConstructor):
    def initial_lines_of_code(
        self,
        these=None,
        repr=None,
        unsafe_hash=None,
        hash=None,
        init=None,
        slots=None,
        frozen=None,
        weakref_slot=None,
        str=None,
        auto_attribs=None,
        kw_only=None,
        cache_hash=None,
        auto_exc=None,
        eq=None,
        order=None,
        auto_detect=None,
        getstate_setstate=None,
        on_setattr=None,
        field_transformer=None,
        match_args=None,
    ):
        """Keyword arguments match those of `attrs.define`. See
        https://www.attrs.org/en/stable/api.html#attrs.define"""
        kwargs = (
            "these",
            "repr",
            "unsafe_hash",
            "hash",
            "init",
            "slots",
            "frozen",
            "weakref_slot",
            "str",
            "auto_attribs",
            "kw_only",
            "cache_hash",
            "auto_exc",
            "eq",
            "order",
            "auto_detect",
            "getstate_setstate",
            "on_setattr",
            "field_transformer",
            "match_args",
        )
        decorator = "@define"
        decorator_kwargs = []
        for k in kwargs:
            if (value := locals()[k]) is not None:
                decorator_kwargs.append(f"{k}={value}")
        if decorator_kwargs:
            prettied_decorator_kwargs = "\n".join(decorator_kwargs)
            decorator = f"{decorator}({prettied_decorator_kwargs})"
        return [decorator, f"class {self.class_name}:"]


class MsgspecConstructor(BaseConstructor):
    def initial_lines_of_code(self):
        return [f"class {self.class_name}(msgspec.Struct):"]


class PydanticConstructor(BaseConstructor):
    def initial_lines_of_code(self):
        return [f"class {self.class_name}(BaseModel):"]


CONSTRUCTORS: dict[Framework, Type[BaseConstructor]] = {
    "dataclass": DataclassConstructor,
    "attrs": AttrsConstructor,
    "msgspec": MsgspecConstructor,
    "pydantic": PydanticConstructor,
}


def make_class(framework: Framework, class_def: ast.ClassDef):
    constructor_class = CONSTRUCTORS.get(framework)
    if constructor_class is None:
        raise NotImplementedError(f"Framework '{framework}' is not supported.")
    constructor = constructor_class(class_def.name)
    for node in class_def.body:
        # TODO: might have to support different `ast` types
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and isinstance(node.annotation, ast.Name)
        ):
            constructor.add_attribute(node)
    return constructor.lines_of_code
