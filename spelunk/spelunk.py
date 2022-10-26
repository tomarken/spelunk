"""Module containing recursive object exploration tools"""
from typing import (
    Any,
    Callable,
    Union,
    Optional,
    Generator,
)
from collections.abc import (
    Collection,
    Sequence,
    MutableSequence,
    Mapping,
    MutableMapping,
    Set,
    MutableSet,
    ValuesView,
    ByteString,
)
from numbers import Number
from enum import Enum
import reprlib
from contextlib import contextmanager


IgnoredCollections = (str, ByteString)
InternedPrimitives = (Number, str, ByteString)


class Address(Enum):
    """Enum for types of object dependencies"""

    ATTR = "Attribute"
    MUTABLE_SEQUENCE_IDX = "MutableSequenceIndex"
    IMMUTABLE_SEQUENCE_IDX = "ImmutableSequenceIndex"
    MUTABLE_MAPPING_KEY = "MutableMappingKey"
    IMMUTABLE_MAPPING_KEY = "ImmutableMappingKey"
    MUTABLE_SET_ID = "MutableSetID"
    IMMUTABLE_SET_ID = "ImmutableSetID"
    VALUES_VIEW_ID = "ValuesViewID"


def _get_paths(
    root_obj: Any,
    element_test: Callable[[Any], bool] = lambda x: True,
    path_test: Callable[[Union[str, int]], bool] = lambda x: True,
) -> list[list[tuple[Address, Union[str, int]]]]:
    """
    Get the paths of nested objects in root_obj that satisfy element_test and path_test.

    :param root_obj: The root object to search for attributes and containers
    :param element_test: Callable to determine whether an element within root_obj is interesting
    :param path_test: Callable to determine whether a path within root_obj is interesting
    :return: Collection of paths where each path is a collection of tuples describing the address
             type and value e.g
             [[(Address.MUTABLE_MAPPING_KEY, 'key'), (Address.MUTABLE_SEQUENCE_IDX, 0)]]
    """
    output = []
    _get_paths_helper(
        root_obj,
        element_test=element_test,
        path_test=path_test,
        paths=output,
        current_path=None,
        memo=None,
    )
    return output


def _get_paths_helper(
    obj: Any,
    element_test: Callable[[Any], bool],
    path_test: Callable[[Union[str, int]], bool],
    paths: list[list[tuple[Address, Union[str, int]]]],
    current_path: Optional[list[tuple[Address, Union[str, int]]]] = None,
    memo: Optional[dict[int, bool]] = None,
) -> None:
    """Recursive function that inspects obj and recursively searches any attrs and containers."""
    if current_path is None:
        current_path = []

    if memo is None:
        memo = {}

    if id(obj) in memo and obj is not None and not isinstance(obj, InternedPrimitives):
        return
    else:
        memo[id(obj)] = True

    if current_path and current_path[-1]:
        path_to_test = current_path[-1][1]
    else:
        path_to_test = ""

    if element_test(obj) and path_test(path_to_test):
        paths.append([*current_path])

    if isinstance(obj, Collection) and not isinstance(obj, IgnoredCollections):
        if isinstance(obj, Mapping):
            if isinstance(obj, MutableMapping):
                address_type = Address.MUTABLE_MAPPING_KEY
            else:
                address_type = Address.IMMUTABLE_MAPPING_KEY
            for key in obj:
                elem = obj[key]
                current_path_copy = [*current_path]
                current_path_copy.append((address_type, key))
                _get_paths_helper(
                    elem,
                    element_test=element_test,
                    path_test=path_test,
                    paths=paths,
                    current_path=current_path_copy,
                    memo=memo,
                )
        elif isinstance(obj, Sequence):
            if isinstance(obj, MutableSequence):
                address_type = Address.MUTABLE_SEQUENCE_IDX
            else:
                address_type = Address.IMMUTABLE_SEQUENCE_IDX
            for idx, elem in enumerate(obj):
                current_path_copy = [*current_path]
                current_path_copy.append((address_type, idx))
                _get_paths_helper(
                    elem,
                    element_test=element_test,
                    path_test=path_test,
                    paths=paths,
                    current_path=current_path_copy,
                    memo=memo,
                )
        elif isinstance(obj, Set):
            if isinstance(obj, MutableSet):
                address_type = Address.MUTABLE_SET_ID
            else:
                address_type = Address.IMMUTABLE_SET_ID
            for elem in obj:
                current_path_copy = [*current_path]
                current_path_copy.append((address_type, id(elem)))
                _get_paths_helper(
                    elem,
                    element_test=element_test,
                    path_test=path_test,
                    paths=paths,
                    current_path=current_path_copy,
                    memo=memo,
                )
        elif isinstance(obj, ValuesView):
            for elem in obj:
                current_path_copy = [*current_path]
                current_path_copy.append((Address.VALUES_VIEW_ID, id(elem)))
                _get_paths_helper(
                    elem,
                    element_test=element_test,
                    path_test=path_test,
                    paths=paths,
                    current_path=current_path_copy,
                    memo=memo,
                )
    elif hasattr(obj, "__dict__") or hasattr(obj, "__slots__"):
        attrs = []
        if hasattr(obj, "__dict__"):
            dict_attrs = getattr(obj, "__dict__")
            for a in dict_attrs:
                if a not in attrs:
                    attrs.append(a)
        for cls in obj.__class__.__mro__:
            if hasattr(cls, "__slots__"):
                slots = getattr(cls, "__slots__")
                for a in slots:
                    if a not in attrs:
                        attrs.append(a)
        for attr in attrs:
            elem = getattr(obj, attr)
            current_path_copy = [*current_path]
            current_path_copy.append((Address.ATTR, attr))
            _get_paths_helper(
                elem,
                element_test=element_test,
                path_test=path_test,
                paths=paths,
                current_path=current_path_copy,
                memo=memo,
            )


def _increment_path(parent: str, child: tuple[Address, Union[str, int]]) -> str:
    """Increment the path depending on the address type."""
    entry_type, entry = child
    if entry_type == Address.ATTR:
        parent += f".{entry}"
    elif entry_type in [Address.MUTABLE_MAPPING_KEY, Address.IMMUTABLE_MAPPING_KEY]:
        parent += f"['{entry}']"
    elif entry_type in [Address.MUTABLE_SEQUENCE_IDX, Address.IMMUTABLE_SEQUENCE_IDX]:
        parent += f"[{entry}]"
    elif entry_type in [Address.MUTABLE_SET_ID, Address.IMMUTABLE_SET_ID]:
        parent += "{id=" + f"{entry}" + "}"
    elif entry_type == Address.VALUES_VIEW_ID:
        parent += "{" + f"ValuesView_id={entry}" + "}"
    return parent


def _increment_obj_pointer(parent: Any, child: tuple[Address, Union[str, int]]) -> Any:
    """Increment the object in memory based on the address type."""
    entry_type, entry = child
    if entry_type == Address.ATTR:
        return getattr(parent, entry)
    elif entry_type in [
        Address.MUTABLE_MAPPING_KEY,
        Address.IMMUTABLE_MAPPING_KEY,
        Address.MUTABLE_SEQUENCE_IDX,
        Address.IMMUTABLE_SEQUENCE_IDX,
    ]:
        return parent[entry]
    elif entry_type in [Address.MUTABLE_SET_ID, Address.IMMUTABLE_SET_ID, Address.VALUES_VIEW_ID]:
        for item in parent:
            if id(item) == entry:
                return item


def _get_elements_from_paths(
    root_obj: Any, paths: list[list[tuple[Address, Union[str, int]]]]
) -> dict[str, Any]:
    """Retrieve all object associated with the supplied paths."""
    output = {}
    root_name = "ROOT"
    for path in paths:
        key = root_name
        obj = root_obj
        for stem in path:
            key = _increment_path(key, stem)
            obj = _increment_obj_pointer(obj, stem)
        output[key] = obj
    return output


def _overwrite_element(
    parent: Any, child: tuple[Address, Union[str, int]], overwrite_value: Any = None
) -> Optional[bool]:
    """Overwrite the parent sub-element at address with overwrite_value."""
    entry_type, entry = child
    if entry_type == Address.ATTR:
        setattr(parent, entry, overwrite_value)
    elif entry_type in [Address.MUTABLE_MAPPING_KEY, Address.MUTABLE_SEQUENCE_IDX]:
        parent[entry] = overwrite_value
    elif entry_type == Address.MUTABLE_SET_ID:
        for item in parent:
            if id(item) == entry:
                parent.remove(item)
                parent.add(overwrite_value)
                break
    elif entry_type in [
        Address.IMMUTABLE_SEQUENCE_IDX,
        Address.IMMUTABLE_MAPPING_KEY,
        Address.IMMUTABLE_SET_ID,
    ]:
        raise TypeError("Cannot overwrite immutable collections.")
    else:
        raise ValueError(
            f"Address of child must correspond to an Address enum value, not {entry_type}."
        )


def _overwrite_elements_at_paths(
    root_obj: Any,
    paths: list[list[tuple[Address, Union[str, int]]]],
    overwrite_value: Any = None,
    silent: bool = False,
    raise_on_exception: bool = True,
) -> Optional[bool]:
    """Overwrite each elem at each path with overwrite_value."""
    root_name = "ROOT"
    for path in paths:
        key = root_name
        obj = root_obj
        try:
            for stem in path[:-1]:
                key = _increment_path(key, stem)
                obj = _increment_obj_pointer(obj, stem)
            _overwrite_element(obj, path[-1], overwrite_value)
        except Exception as e:
            if not silent:
                print(f"Failed to overwrite {path}. Exception:\n {e}")
            if raise_on_exception:
                raise e


def get_elements(
    root_obj: Any,
    element_test: Callable[[Any], bool] = lambda x: True,
    path_test: Callable[[Union[int, str]], bool] = lambda x: True,
) -> dict[str, Any]:
    """
    Get all elements within root_obj that satisfy element_test and path_test.

    :param root_obj: Root object to search
    :param element_test: Callable to determine whether an element within root_obj is interesting
    :param path_test: Callable to determine whether a path within root_obj is interesting
    :return: Dict keyed by concatenated address path with values being the interesting objects
    """
    paths = _get_paths(root_obj, element_test=element_test, path_test=path_test)
    return _get_elements_from_paths(root_obj, paths)


def overwrite_elements(
    root_obj: Any,
    overwrite_value: Any = None,
    element_test: Callable[[Any], bool] = lambda x: True,
    path_test: Callable[[Union[int, str]], bool] = lambda x: True,
    silent: bool = False,
    raise_on_exception: bool = True,
) -> None:
    """
    Overwrite all elements (in-place) within root_obj that satisfy element_test and path_test.

    :param root_obj: Root object to search
    :param overwrite_value: Value to overwrite
    :param element_test: Callable to determine whether an element within root_obj is interesting
    :param path_test: Callable to determine whether a path within root_obj is interesting
    :param silent: Whether or not to print address paths that fail
    :param raise_on_exception: Whether or not to raise on exceptions during overwrite or suppress
    :return: None
    """
    paths = _get_paths(root_obj, element_test=element_test, path_test=path_test)
    _overwrite_elements_at_paths(
        root_obj,
        paths=paths,
        overwrite_value=overwrite_value,
        silent=silent,
        raise_on_exception=raise_on_exception,
    )


def print_obj_tree(
    root_obj: Any,
    element_test: Callable[[Any], bool] = lambda x: True,
    path_test: Callable[[Union[int, str]], bool] = lambda x: True,
    max: Optional[int] = None,
) -> None:
    """
    Print the elements and paths of root_obj that satisfy element_test and path_test.

    :param root_obj: Root object to search
    :param element_test: Callable to determine whether an element within root_obj is interesting
    :param path_test: Callable to determine whether a path within root_obj is interesting
    :param max: Maximum number of results to print
    """
    r = reprlib.Repr()
    r.maxstring = 100
    r.maxother = 100
    r.maxlist = 1
    r.maxdict = 1
    r.maxset = 1
    r.maxfrozenset = 1
    r.maxtuple = 1
    r.maxarray = 1
    r.maxdeque = 1

    relevant_content = get_elements(root_obj, element_test=element_test, path_test=path_test)
    idx = 0
    for key, value in relevant_content.items():
        if max is not None and idx >= max:
            break
        print(f"{key} -> {r.repr(value)}")
        idx += 1


@contextmanager
def hot_swap(
    root_obj: Any,
    overwrite_value: Any = None,
    element_test: Callable[[Any], bool] = lambda x: True,
    path_test: Callable[[Union[int, str]], bool] = lambda x: True,
    allow_mutable_set_mutations: bool = False,
) -> Generator[None, None, None]:
    """
    Generate a hot swapped object for manipulation that is restored upon close.

    This is a context manager that safely overwrites an object with replacement values
    and then restore them upon exit. This allows one to e.g. swap out all non-serializable
    content with safe fillers, dump to JSON, and then restore the original objects.

    :param root_obj: Root object to search
    :param overwrite_value: Value to overwrite
    :param element_test: Callable to determine whether an element within root_obj is interesting
    :param path_test: Callable to determine whether a path within root_obj is interesting
    :param allow_mutable_set_mutations: Whether or not to allow set content to be overwritten
                                        (can be unsafe)
    :return: Generator that yields None
    """
    original_elem_paths = _get_paths(root_obj, element_test=element_test, path_test=path_test)
    if any(
        x[-1][0]
        in [
            Address.IMMUTABLE_MAPPING_KEY,
            Address.IMMUTABLE_SEQUENCE_IDX,
            Address.IMMUTABLE_SET_ID,
            Address.VALUES_VIEW_ID,
        ]
        for x in original_elem_paths
    ):
        raise TypeError(
            "Cannot overwrite immutable collections. Original root_obj has not been changed."
        )
    if (
        any(x[-1][0] == Address.MUTABLE_SET_ID for x in original_elem_paths)
        and not allow_mutable_set_mutations
    ):
        raise TypeError(
            "Cannot safely hot swap items in mutable sets (e.g. swap int -> None in {1, 2, 3} ->"
            " {None}). To allow hot swapping sets, use the flag allow_mutable_set_mutations."
        )
    original_elems = _get_elements_from_paths(root_obj, original_elem_paths).values()
    _overwrite_elements_at_paths(
        root_obj,
        original_elem_paths,
        overwrite_value,
        silent=True,
        raise_on_exception=True,
    )
    yield
    for orig_path, orig_el in zip(original_elem_paths, original_elems):
        _overwrite_elements_at_paths(
            root_obj, [orig_path], orig_el, silent=True, raise_on_exception=False
        )
