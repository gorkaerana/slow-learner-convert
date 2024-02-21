import ast
from typing import Callable, Literal, TypeAlias, Type
import warnings

from attr._make import _CountingAttr
import attrs


Framework: TypeAlias = Literal["dataclasses", "attrs", "msgspec", "pydantic"]


class _Nothing:
    pass


class InvalidObjectAttribute(Warning):
    pass


INDENT = " " * 4


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


class BaseConstructor:
    def __init__(self, class_name: str):
        self.class_name: str = class_name
        self.lines_of_code: list[str] = self.initial_lines_of_code()

    def initial_lines_of_code(self, *args, **kwargs) -> list[str]:
        raise NotImplementedError

    def get_attribute_name(
        self, target: ast.Name | ast.Constant | ast.Attribute | ast.Subscript
    ):
        # ast.Attribute, and ast.Subscript pleases mypy
        if isinstance(target, ast.Name):
            return target.id
        elif isinstance(target, ast.Constant):
            return target.value
        else:
            raise NotImplementedError(f"{type(target)} not supported")

    def get_type_annotation(
        self, annotation: ast.Name | ast.Subscript | ast.expr
    ) -> str:
        # ast.expr pleases mypy
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Subscript):
            return format_ast_subscript(annotation)
        else:
            raise NotImplementedError(f"{type(annotation)} not supported.")

    def add_attribute_from_node(self, node: ast.AnnAssign):
        self.lines_of_code.append(
            f"{INDENT}{self.get_attribute_name(node.target)}: {self.get_type_annotation(node.annotation)}"
        )

    def add_attribute_from_elements(
        self,
        attribute_name: ast.Name | ast.Constant,
        type_annotation: ast.Name | ast.Subscript,
    ):
        self.lines_of_code.append(
            f"{INDENT}{self.get_attribute_name(attribute_name)}: {self.get_type_annotation(type_annotation)}"
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
        decorator = "@dataclasses.dataclass"
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
        decorator = "@attrs.define"
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
    # TODO: `typing.NotRequired` is not supported by Pydantic
    def initial_lines_of_code(self):
        return [f"class {self.class_name}(pydantic.BaseModel):"]


CLASS_DEF_CONSTRUCTORS: dict[Framework, Type[BaseConstructor]] = {
    "dataclasses": DataclassConstructor,
    "attrs": AttrsConstructor,
    "msgspec": MsgspecConstructor,
    "pydantic": PydanticConstructor,
}


def make_class_from_class_def(framework: Framework, class_def: ast.ClassDef):
    constructor_class = CLASS_DEF_CONSTRUCTORS.get(framework)
    if constructor_class is None:
        raise NotImplementedError(f"Framework '{framework}' is not supported.")
    constructor = constructor_class(class_def.name)
    for node in class_def.body:
        if isinstance(node, ast.AnnAssign):
            constructor.add_attribute_from_node(node)
        else:
            message = f"ast.ClassDef body element of type {type(node)} not supported."
            raise NotImplementedError(message)
    return constructor.lines_of_code


def make_class_from_assign(framework: Framework, assign: ast.Assign):
    constructor_class = CLASS_DEF_CONSTRUCTORS.get(framework)
    if constructor_class is None:
        raise NotImplementedError(f"Framework '{framework}' is not supported.")
    # TODO: don't please mypy by hacking
    assert isinstance(assign.targets[0], ast.Name)
    # Class name could also be `assign.value.args[0].id`
    constructor = constructor_class(assign.targets[0].id)
    # First element of `assign.value.args` is the class name
    assert isinstance(assign.value, ast.Call)
    assert isinstance(assign.value.args[1], ast.Dict)
    for key, value in zip(assign.value.args[1].keys, assign.value.args[1].values):
        if not isinstance(key, ast.Name | ast.Constant):
            message = f"ast.Assign.value.args[1].keys elements of type {type(key)} not supported."
            raise NotImplementedError(message)
        elif not isinstance(value, ast.Name | ast.Subscript):
            message = f"ast.Assign.value.args[1].values elements of type {type(key)} not supported."
            raise NotImplementedError(message)
        if (isinstance(key, ast.Name) and not key.id.isidentifier()) or (
            isinstance(key, ast.Constant) and not key.value.isidentifier()
        ):
            v = key.value if isinstance(key, ast.Constant) else key.id
            warnings.warn(
                f"{repr(v)} is not a valid object attribute name. Skipping it.",
                InvalidObjectAttribute,
            )
            continue
        constructor.add_attribute_from_elements(key, value)
    return constructor.lines_of_code
