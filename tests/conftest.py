from typing import Any, Iterable, Hashable, Callable, Generator
from types import MappingProxyType
import pytest
from frozendict import frozendict
from collections import namedtuple, deque, Counter, OrderedDict, defaultdict
import numpy as np
from numpy.typing import NDArray
from contextlib import contextmanager
from spelunk.logging import get_logger
from io import StringIO
from logging import StreamHandler
from enum import Enum


@contextmanager
def silence_logger(logger_name: str) -> Generator[None, None, None]:
    logger = get_logger(logger_name)
    for handler in logger.handlers:
        if isinstance(handler, StreamHandler):
            break
    else:
        raise TypeError("Could not find StreamHandler in logger.")
    old_stream = handler.stream
    handler.stream = StringIO()
    yield
    handler.stream = old_stream


@contextmanager
def propagate_logs(logger_name: str) -> Generator[None, None, None]:
    logger = get_logger(logger_name)
    logger.propagate = True
    yield
    logger.propagate = False


class SequenceLikeMonadicIntGetitem:
    array = [0, 1, 2]

    def __contains__(self, value: Any) -> bool:
        return value in self.array

    def __iter__(self) -> Iterable[Any]:
        return iter(self.array)

    def __len__(self) -> int:
        return len(self.array)

    def __getitem__(self, key: int) -> Any:
        return self.array[key]


class SequenceLikeDyadicIntGetitem:
    array = [[0, 0, 0], [1, 1, 1], [2, 2, 2]]

    def __contains__(self, value: Any) -> bool:
        return any(value in arr for arr in self.array)

    def __iter__(self) -> Iterable[Any]:
        return iter(self.array)

    def __len__(self) -> int:
        return len(self.array)

    def __getitem__(self, key1: int, key2: int) -> Any:
        return self.array[key1][key2]


class SequenceLikeMonadicStrGetitem:
    array = [0, 1, 2]
    indices = {"0": 0, "1": 1, "2": 2}

    def __contains__(self, value: Any) -> bool:
        return value in self.array

    def __iter__(self) -> Iterable[Any]:
        return iter(self.array)

    def __len__(self) -> int:
        return len(self.array)

    def __getitem__(self, key: str) -> Any:
        return self.array[self.indices[key]]


class MutableSequenceLikeMonadicIntGetitem:
    array = [0, 1, 2]

    def __contains__(self, value: Any) -> bool:
        return value in self.array

    def __iter__(self) -> Iterable[Any]:
        return iter(self.array)

    def __len__(self) -> int:
        return len(self.array)

    def __getitem__(self, key: int) -> Any:
        return self.array[key]

    def __setitem__(self, key: int, value: Any) -> None:
        self.array.__setitem__(key, value)


class MutableSequenceLikeDyadicIntGetitem:
    array = [[0, 0, 0], [1, 1, 1], [2, 2, 2]]

    def __contains__(self, value: Any) -> bool:
        return any(value in arr for arr in self.array)

    def __iter__(self) -> Iterable[Any]:
        return iter(self.array)

    def __len__(self) -> int:
        return len(self.array)

    def __getitem__(self, key1: int, key2: int) -> Any:
        return self.array[key1][key2]

    def __setitem__(self, key1: int, key2, value: Any) -> None:
        self.array.__getitem__(key1).__setitem__(key2, value)


class MutableSequenceLikeMonadicStrGetitem:
    array = [0, 1, 2]
    indices = {"0": 0, "1": 1, "2": 2}

    def __contains__(self, value: Any) -> bool:
        return value in self.array

    def __iter__(self) -> Iterable[Any]:
        return iter(self.array)

    def __len__(self) -> int:
        return len(self.array)

    def __getitem__(self, key: str) -> Any:
        return self.array[self.indices[key]]

    def __setitem__(self, key: str, value: Any) -> None:
        self.array.__setitem__(self.indices.__getitem__(key), value)


class MappingLikeMonadicGetitem:
    map = {"0": 0, "1": 1, "2": 2}

    def __contains__(self, value: Any) -> bool:
        return value in self.map

    def __iter__(self) -> Iterable[Any]:
        return iter(self.map)

    def __len__(self) -> int:
        return len(self.map)

    def keys(self) -> Iterable[str]:
        return self.map.keys()

    def __getitem__(self, key: str) -> Any:
        return self.map[key]


class MappingLikeDyadicGetitem:
    map = {
        "0": {"A": 0, "B": 0, "C": 0},
        "1": {"A": 1, "B": 1, "C": 1},
        "2": {"A": 2, "B": 2, "C": 2},
    }

    def __contains__(self, key: str) -> bool:
        return any(key in d for d in self.map)

    def __iter__(self) -> Iterable[str]:
        return iter(self.map)

    def __len__(self) -> int:
        return len(self.map)

    def keys(self) -> Iterable[tuple[str, str]]:
        return self.map.keys()

    def __getitem__(self, key1: str, key2: str) -> Any:
        return self.map[key1][key2]


class MutableMappingLikeMonadicGetitem:
    map = {"0": 0, "1": 1, "2": 2}

    def __contains__(self, value: Any) -> bool:
        return value in self.map

    def __iter__(self) -> Iterable[Any]:
        return iter(self.map)

    def __len__(self) -> int:
        return len(self.map)

    def keys(self) -> Iterable[str]:
        return self.map.keys()

    def __getitem__(self, key: str) -> Any:
        return self.map[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.map[key] = value


class MutableMappingLikeDyadicGetitem:
    map = {
        "0": {"A": 0, "B": 0, "C": 0},
        "1": {"A": 1, "B": 1, "C": 1},
        "2": {"A": 2, "B": 2, "C": 2},
    }

    def __contains__(self, key: str) -> bool:
        return any(key in d for d in self.map)

    def __iter__(self) -> Iterable[str]:
        return iter(self.map)

    def __len__(self) -> int:
        return len(self.map)

    def keys(self) -> Iterable[tuple[str, str]]:
        return zip(self.map.keys(), self.map["0"].keys())

    def __getitem__(self, key1: str, key2: str) -> Any:
        return self.map[key1][key2]

    def __setitem__(self, key1: str, key2: str, value: Any) -> None:
        self.map[key1][key2] = value


class EmptyClass:
    pass


class SlotsClass:
    __slots__ = "slot"


class MultiSlotsClass:
    __slots__ = "slot", "other_slot"


class SlotsDictClass:
    __slots__ = "slot", "__dict__"


class InheritedSlotsDictClass(SlotsDictClass):
    __slots__ = "slot2"


class CollectionClass:
    array = [0, 1, 2]

    def __contains__(self, value):
        return value in self.array

    def __iter__(self):
        return iter(self.array)

    def __len__(self):
        return len(self.array)


class A:
    b = None

    def __repr__(self) -> str:
        return "A()"


class B:
    a = None

    def __repr__(self) -> str:
        return "B()"


class ComplexNestedStructure:
    def __init__(self, obj: Hashable) -> None:
        self.list = [obj]
        self.tuple = (obj,)
        self.set = {obj}
        self.frozenset = frozenset({obj})
        self.mapping = {obj: obj}
        self.mapping_prox = MappingProxyType({obj: obj})
        self.nested = [({frozenset({obj})}), {obj: MappingProxyType({obj: obj})}]


class StringEnum(str, Enum):
    MEMBER = "MEMBER"


def get_assorted_objs() -> list[Any]:
    return [
        None,
        0,
        1,
        -1,
        1.0,
        -1.0,
        1_000_000,
        -1_000_000,
        1 + 1j,
        -1 - 1j,
        "",
        "a",
        "a longer string",
        bytes(),
        bytes("a", encoding="utf-8"),
        bytes("a longer string", encoding="utf-8"),
        bytearray("a byte array", encoding="utf-8"),
        type,
        object,
        list(),
        tuple(),
        set(),
        frozenset(),
        dict(),
        MappingProxyType(dict()),
        Any,
        ...,
        namedtuple("Empty", [])(),
        list(),
        [1, 2, 3],
        deque(),
        deque([-1, 10, 11]),
        tuple(),
        ("string", "string2"),
        dict(),
        {"a": 1, "b": 2},
        dict().values(),
        {"a": 1}.values(),
        OrderedDict(),
        OrderedDict({"key": "value", "key2": "value2"}),
        defaultdict(),
        defaultdict(None, {"key1": 1}),
        Counter(),
        Counter({"a": 2, "b": 3}),
        MappingProxyType({}),
        MappingProxyType({"a": 1, "b": 2}),
        set(),
        {1, 2, 3, "string"},
        frozenset(),
        frozenset({10, 11, "string"}),
    ]


def get_a_few_objects() -> list[Any]:
    return [
        None,
        1,
        -1.0,
        "",
        "a longer string",
        bytes(),
        bytes("a longer string", encoding="utf-8"),
        bytearray("a byte array", encoding="utf-8"),
        type,
        object,
        [0, 1, 2],
        {0, 1, 2},
        {"a": 1, "b": 2},
    ]


def get_hashable_primitive_objects() -> list[Any]:
    return [
        None,
        1,
        -1.0,
        "",
        "a longer string",
        bytes(),
        bytes("a longer string", encoding="utf-8"),
    ]


def get_objects_with_attrs() -> list[Any]:
    return [
        EmptyClass(),
        SlotsClass(),
        MultiSlotsClass(),
        SlotsDictClass(),
        InheritedSlotsDictClass(),
    ]


@pytest.fixture
def seq_like_monadic_int_getitem() -> SequenceLikeMonadicIntGetitem:
    return SequenceLikeMonadicIntGetitem()


@pytest.fixture
def seq_like_dyadic_int_getitem() -> SequenceLikeDyadicIntGetitem:
    return SequenceLikeDyadicIntGetitem()


@pytest.fixture
def seq_like_monadic_str_getitem() -> SequenceLikeMonadicStrGetitem:
    return SequenceLikeMonadicStrGetitem()


@pytest.fixture
def mutable_seq_like_monadic_int_getitem() -> MutableSequenceLikeMonadicIntGetitem:
    return MutableSequenceLikeMonadicIntGetitem()


@pytest.fixture
def mutable_seq_like_dyadic_int_getitem() -> MutableSequenceLikeDyadicIntGetitem:
    return MutableSequenceLikeDyadicIntGetitem()


@pytest.fixture
def mutable_seq_like_monadic_str_getitem() -> MutableSequenceLikeMonadicStrGetitem:
    return MutableSequenceLikeMonadicStrGetitem()


@pytest.fixture
def mapping_like_monadic_getitem() -> MappingLikeMonadicGetitem:
    return MappingLikeMonadicGetitem()


@pytest.fixture
def mapping_like_dyadic_getitem() -> MappingLikeDyadicGetitem:
    return MappingLikeDyadicGetitem()


@pytest.fixture
def mutable_mapping_like_monadic_getitem() -> MutableMappingLikeMonadicGetitem:
    return MutableMappingLikeMonadicGetitem()


@pytest.fixture
def mutable_mapping_like_dyadic_getitem() -> MappingLikeDyadicGetitem:
    return MutableMappingLikeDyadicGetitem()


@pytest.fixture
def empty_class_obj() -> EmptyClass:
    return EmptyClass()


@pytest.fixture
def slots_class_obj() -> SlotsClass:
    return SlotsClass()


@pytest.fixture
def multi_slots_class_obj() -> MultiSlotsClass:
    return MultiSlotsClass


@pytest.fixture
def slots_dict_class_obj() -> SlotsDictClass:
    return SlotsDictClass()


@pytest.fixture
def inherited_slots_dict_class_obj() -> InheritedSlotsDictClass:
    return InheritedSlotsDictClass()


@pytest.fixture
def example_tuple() -> tuple[Any]:
    return (None, 1, 1.0, 1_000_000, -1_000_000, "long string", "a", "")


@pytest.fixture
def example_list() -> list[Any]:
    return [None, 1, 1.0, 1_000_000, -1_000_000, "long string", "a", ""]


@pytest.fixture
def example_mapping_proxy() -> MappingProxyType[str, Any]:
    return MappingProxyType(
        {
            "a": None,
            "b": 1,
            "c": 1.0,
            "d": 1_000_000,
            "e": -1_000_000,
            "f": "long string",
            "g": "a",
            "h": "",
        }
    )


@pytest.fixture
def example_frozendict() -> frozendict[str, Any]:
    return frozendict(
        {
            "a": None,
            "b": 1,
            "c": 1.0,
            "d": 1_000_000,
            "e": -1_000_000,
            "f": "long string",
            "g": "a",
            "h": "",
        }
    )


@pytest.fixture
def example_dict() -> dict[str, Any]:
    return {
        "a": None,
        "b": 1,
        "c": 1.0,
        "d": 1_000_000,
        "e": -1_000_000,
        "f": "long string",
        "g": "a",
        "h": "",
    }


@pytest.fixture
def example_frozenset() -> frozenset[Any]:
    return frozenset({None, 1, 1.0, 1_000_000, -1_000_000, "long string", "a" ""})


@pytest.fixture
def example_set() -> set[Any]:
    return {None, 1, 1.0, 1_000_000, -1_000_000, "long string", "a", ""}


@pytest.fixture
def collection_class_obj() -> CollectionClass:
    return CollectionClass()


@pytest.fixture
def circular_attr_reference_obj() -> A:
    a = A()
    b = B()
    a.b = b
    b.a = a
    return a


@pytest.fixture
def some_strings() -> list[str]:
    return ["", "", "a", "a", "aa", "aa", "long complex string", ".", "!", ","]


@pytest.fixture
def some_bytes(some_strings: list[str]) -> list[bytes]:
    return [bytes(s, encoding="utf-8") for s in some_strings]


@pytest.fixture
def some_bytearrays(some_strings: list[str]) -> list[bytes]:
    return [bytearray(s, encoding="utf-8") for s in some_strings]


@pytest.fixture
def numpy_1darray() -> NDArray:
    return np.array([1, 2, 3, 4])


@pytest.fixture
def numpy_2darray() -> NDArray:
    return np.array([[1, 2, 3, 4], [5, 6, 7, 8]])


@pytest.fixture
def complex_structure_callable() -> Callable[[Hashable], ComplexNestedStructure]:
    return lambda obj: ComplexNestedStructure(obj)


@pytest.fixture
def string_enum() -> StringEnum:
    return StringEnum.MEMBER
