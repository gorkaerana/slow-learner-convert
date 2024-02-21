import ast
from typing import Callable, Literal, TypeAlias, Type

from attr._make import _CountingAttr
import attrs


Framework: TypeAlias = Literal["dataclass", "attrs", "msgspec", "pydantic"]


class _Nothing:
    pass


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


def get_function_argument_names(function: Callable) -> tuple[str, ...]:
    return function.__code__.co_varnames[: function.__code__.co_argcount]


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
        decorator = "@dataclass"
        decorator_kwargs = []
        for k in get_function_argument_names(self.initial_lines_of_code):
            if (k != "self") and ((value := locals()[k]) is not None):
                decorator_kwargs.append(f"{k}={value}")
        if decorator_kwargs:
            prettied_decorator_kwargs = ", ".join(decorator_kwargs)
            decorator = f"{decorator}({prettied_decorator_kwargs})"
        return [decorator, f"class {self.class_name}:"]


class AttrsConstructor(BaseConstructor):
    def initial_lines_of_code(
        self,
        these: dict[str, "_CountingAttr"] | None | Type[_Nothing] = _Nothing,
        repr: bool | None | Type[_Nothing] = _Nothing,
        unsafe_hash: bool | None | Type[_Nothing] = _Nothing,
        hash: bool | None | Type[_Nothing] = _Nothing,
        init: bool | None | Type[_Nothing] = _Nothing,
        slots: bool | None | Type[_Nothing] = _Nothing,
        frozen: bool | None | Type[_Nothing] = _Nothing,
        weakref_slot: bool | None | Type[_Nothing] = _Nothing,
        str: bool | None | Type[_Nothing] = _Nothing,
        auto_attribs: bool | None | Type[_Nothing] = _Nothing,
        kw_only: bool | None | Type[_Nothing] = _Nothing,
        cache_hash: bool | None | Type[_Nothing] = _Nothing,
        auto_exc: bool | None | Type[_Nothing] = _Nothing,
        eq: bool | None | Type[_Nothing] = _Nothing,
        order: bool | None | Type[_Nothing] = _Nothing,
        auto_detect: bool | None | Type[_Nothing] = _Nothing,
        getstate_setstate: bool | None | Type[_Nothing] = _Nothing,
        on_setattr: Callable
        | list[Callable]
        | "attrs.setters._NoOpType"
        | None
        | Type[_Nothing] = _Nothing,
        field_transformer: Callable | None | Type[_Nothing] = _Nothing,
        match_args: bool | None | Type[_Nothing] = _Nothing,
    ):
        """Keyword arguments match those of `attrs.define`. See
        https://www.attrs.org/en/stable/api.html#attrs.define"""
        decorator = "@define"
        decorator_kwargs = []
        for k in get_function_argument_names(self.initial_lines_of_code):
            if ((value := locals()[k]) is not _Nothing) and (k != "self"):
                decorator_kwargs.append(f"{k}={value}")
        if decorator_kwargs:
            prettied_decorator_kwargs = ", ".join(decorator_kwargs)
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
