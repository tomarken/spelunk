from typing import Any, Optional, Callable, Hashable, Generator
from spelunk.graph import Node, Accessor, PrettyRepr, get_object_graph
from contextlib import contextmanager
from spelunk.logging import get_logger

logger = get_logger(__name__)

__all__ = ["print_object_graph", "get_elements_of_obj", "overwrite_elements_of_obj", "hot_swap"]


def print_object_graph(
    root_obj: Any,
    obj_filter: Optional[Callable[[Any], bool]] = None,
    path_filter: Optional[Callable[[Hashable], bool]] = None,
    unravel_strings: bool = False,
) -> None:
    graph = get_object_graph(
        root_obj=root_obj,
        obj_filter=obj_filter,
        accessor_filter=path_filter,
        unravel_strings=unravel_strings,
    )
    _print_object_graph_helper(graph, "ROOT")


def _print_object_graph_helper(current_node: Node, current_path: str) -> None:
    if current_node.interesting:
        print(current_path + " -> " + PrettyRepr.repr(current_node.obj))
    for child_link in current_node.child_links:
        new_path = f"{current_path}{child_link.accessor_as_str()}"
        _print_object_graph_helper(child_link.child, new_path)


def get_elements_of_obj(
    root_obj: Any,
    obj_filter: Optional[Callable[[Any], bool]] = None,
    path_filter: Optional[Callable[[Hashable], bool]] = None,
    unravel_strings: bool = False,
) -> list[Any]:
    graph = get_object_graph(
        root_obj=root_obj,
        obj_filter=obj_filter,
        accessor_filter=path_filter,
        unravel_strings=unravel_strings,
    )
    elements = []
    _get_elements_of_obj_helper(graph, elements)
    return elements


def _get_elements_of_obj_helper(
    current_node: Node,
    elements: list[Any],
) -> None:
    if current_node.interesting:
        elements.append(current_node.obj)

    for child_link in current_node.child_links:
        _get_elements_of_obj_helper(child_link.child, elements)


def overwrite_elements_of_obj(
    root_obj: Any,
    overwrite_callable: Callable[[Any], Any],
    obj_filter: Optional[Callable[[Any], bool]] = None,
    path_filter: Optional[Callable[[Hashable], bool]] = None,
    unravel_strings: bool = False,
    silent: bool = False,
    raise_on_exception: bool = False,
) -> None:
    graph = get_object_graph(
        root_obj=root_obj,
        obj_filter=obj_filter,
        accessor_filter=path_filter,
        unravel_strings=unravel_strings,
    )
    _overwrite_elements_helper(graph, overwrite_callable, silent, raise_on_exception)


def _overwrite_elements_helper(
    current_node: Node,
    overwrite_callable: Callable[[Any], Any],
    silent: bool = False,
    raise_on_exception: bool = False,
    check_for_reversibility=False,
) -> None:
    for child_link in current_node.child_links:
        if child_link.accessor_type is Accessor.COLLECTION:
            continue
        if child_link.child.interesting:
            overwrite_value = overwrite_callable(child_link.child.obj)
            _overwrite_obj(
                current_node.obj,
                child_link.accessor_type,
                child_link.accessor_arg,
                overwrite_value,
                silent,
                raise_on_exception,
                check_for_reversibility,
            )
        _overwrite_elements_helper(child_link.child, overwrite_callable, silent, raise_on_exception)


def _overwrite_obj(
    obj: Any,
    accessor_type: Accessor,
    overwrite_key: Hashable,
    overwrite_value: Any,
    silent: bool = False,
    raise_on_exception: bool = False,
    check_for_reversibility: bool = False,
) -> None:
    if accessor_type.setter is not None:
        if (
            check_for_reversibility
            and accessor_type is Accessor.MUTABLE_SET
            and overwrite_value in obj
            and overwrite_key != overwrite_value
        ):
            raise ValueError(
                f"Attempting to overwrite element {overwrite_key} of set {obj} with new "
                f"value {overwrite_value} which is already present. This operation cannot "
                f"be reversed safely."
            )
        try:
            accessor_type.setter(obj, overwrite_key, overwrite_value)
        except Exception:
            if not silent:
                logger.exception(f"Failed to overwrite {overwrite_value} in object {obj}.")
            if raise_on_exception:
                raise
    elif raise_on_exception:
        raise ValueError(
            f"Cannot overwrite {obj} because accessor_type lacks a valid "
            "setter(obj, key, accessor_arg) method."
        )
    elif not silent:
        logger.warning(
            f"Cannot overwrite {obj} because it lacks a valid "
            "setter(obj, key, accessor_arg) method."
        )


@contextmanager
def hot_swap(
    root_obj: Any,
    overwrite_callable: Callable[[Any], Any],
    obj_filter: Optional[Callable[[Any], bool]] = None,
    path_filter: Optional[Callable[[Hashable], bool]] = None,
    unravel_strings: bool = False,
    silent: bool = False,
    raise_on_exceptions: bool = False,
) -> Generator[Any, None, None]:
    graph = get_object_graph(root_obj, obj_filter, path_filter, unravel_strings)
    _overwrite_elements_helper(
        graph, overwrite_callable, silent, raise_on_exceptions, check_for_reversibility=True
    )
    yield root_obj
    _restore_obj_elements_from_graph(graph, overwrite_callable, silent, raise_on_exceptions)


def _restore_obj_elements_from_graph(
    graph: Node,
    overwrite_callable: Callable[[Any], Any],
    silent: bool = False,
    raise_on_exceptions: bool = False,
) -> None:
    for child_link in graph.child_links:
        if child_link.child.interesting:
            if child_link.accessor_type is Accessor.MUTABLE_SET:
                overwrite_key = overwrite_callable(child_link.accessor_arg)
            else:
                overwrite_key = child_link.accessor_arg
            _overwrite_obj(
                graph.obj,
                child_link.accessor_type,
                overwrite_key=overwrite_key,
                overwrite_value=child_link.child.obj,
            )
        _restore_obj_elements_from_graph(
            child_link.child, overwrite_callable, silent, raise_on_exceptions
        )
    return graph.obj
