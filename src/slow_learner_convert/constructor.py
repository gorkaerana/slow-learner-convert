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


def format_ast_subscript(node: ast.Subscript):
    value, slice_ = node.value, node.slice
    if isinstance(value, ast.Name):
        formatted_value = value.id
    else:
        raise NotImplementedError(
            f"`ast.Subscript.value` of type {type(value)} not supported"
        )
    if isinstance(slice_, ast.Name):
        formatted_slice = slice_.id
    elif isinstance(slice_, ast.Constant):
        formatted_slice = repr(slice_.value)
    elif isinstance(slice_, ast.Tuple):
        parts = []
        for e in slice_.elts:
            if isinstance(e, ast.Subscript):
                parts.append(format_ast_subscript(e))
            else:
                raise NotImplementedError(
                    f"Element for `ast.Subscript.slice.Tuple` of type {type(e)} not supported"
                )
        formatted_slice = ", ".join(parts)
    else:
        raise NotImplementedError(
            f"`ast.Subscript.slice` of type {type(value)} not supported"
        )
    return f"{formatted_value}[{formatted_slice}]"


class BaseClassDefConstructor:
    def __init__(self, class_name: str):
        self.class_name: str = class_name
        self.lines_of_code: list[str] = self.initial_lines_of_code()

    def initial_lines_of_code(self, *args, **kwargs) -> list[str]:
        raise NotImplementedError

    def get_attribute_name(self, node: ast.AnnAssign):
        # TODO: support more `ast` types for `node.target`
        if isinstance(node.target, ast.Name):
            return node.target.id
        else:
            message = (
                f"{type(node.target)} not supported. Full node:\n"
                f"{ast.dump(node, indent=4)}"
            )
            raise NotImplementedError(message)

    def get_type_annotation(self, node: ast.AnnAssign) -> str:
        # TODO: `ast` types for `node.annotation`. E.g., `ast.Constant`, `ast.Attribute`
        annotation = node.annotation
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            return format_ast_subscript(annotation)
        else:
            message = (
                f"{type(node.annotation)} not supported. Full node:\n"
                f"{ast.dump(node, indent=4)}"
            )
            raise NotImplementedError(message)

    def add_attribute(self, node: ast.AnnAssign):
        self.lines_of_code.append(
            f"{INDENT}{self.get_attribute_name(node)}: {self.get_type_annotation(node)}"
        )


class DataclassClassDefConstructor(BaseClassDefConstructor):
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


class AttrsClassDefConstructor(BaseClassDefConstructor):
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


class MsgspecClassDefConstructor(BaseClassDefConstructor):
    def initial_lines_of_code(self):
        return [f"class {self.class_name}(msgspec.Struct):"]


class PydanticClassDefConstructor(BaseClassDefConstructor):
    def initial_lines_of_code(self):
        return [f"class {self.class_name}(BaseModel):"]


CLASS_DEF_CONSTRUCTORS: dict[Framework, Type[BaseClassDefConstructor]] = {
    "dataclass": DataclassClassDefConstructor,
    "attrs": AttrsClassDefConstructor,
    "msgspec": MsgspecClassDefConstructor,
    "pydantic": PydanticClassDefConstructor,
}


def make_class_from_class_def(framework: Framework, class_def: ast.ClassDef):
    constructor_class = CLASS_DEF_CONSTRUCTORS.get(framework)
    if constructor_class is None:
        raise NotImplementedError(f"Framework '{framework}' is not supported.")
    constructor = constructor_class(class_def.name)
    for node in class_def.body:
        if isinstance(node, ast.AnnAssign):
            constructor.add_attribute(node)
        else:
            message = f"ast.ClassDef body element of type {type(node)} not supported."
            raise NotImplementedError(message)
    return constructor.lines_of_code
