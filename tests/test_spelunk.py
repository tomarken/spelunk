"""pytest module for testing spelunk"""
import pytest
from _pytest.capture import CaptureFixture
from collections.abc import Collection, ValuesView, KeysView, ItemsView
from collections import deque, OrderedDict, defaultdict, Counter, namedtuple
from typing import Union, Any
from types import MappingProxyType
from copy import copy
from spelunk.spelunk import (
    Address,
    _get_paths,
    _get_paths_helper,
    _collect_all_attrs,
    _increment_path,
    _increment_obj_pointer,
    _get_elements_from_paths,
    _overwrite_element,
    _overwrite_elements_at_paths,
    print_obj_tree,
    get_elements,
    overwrite_elements,
    hot_swap,
)

PrimTypes = Union[str, bytes, bytearray, int, float, complex, bool, None]


class A:
    """Dummy class for testing"""

    def __init__(self, val: Any):
        self.val = val

    def __repr__(self):
        return repr(f"A({self.val})")


class B:
    """Dummy class for testing with __slots__"""

    __slots__ = ("val",)


class C(B):
    """Dummy class for testing with __slots__ and inheritance"""

    __slots__ = ("val2",)


class D(C):
    """Dummy class for testing with __slots__ and __dict__"""

    __slots__ = ("__dict__",)


def get_primitives() -> list[PrimTypes]:
    return [
        "",
        "string",
        bytes("string", encoding="utf-8"),
        bytearray("string", encoding="utf-8"),
        1,
        -1,
        1234,
        -2345,
        0,
        1.0,
        -1.0,
        1234.0,
        -1234.0,
        0.0,
        1e10,
        1e-10,
        True,
        False,
        None,
        1.0j,
        -1.0j,
        1.0 + 1.0j,
        1.0 - 1.0j,
    ]


def get_empty_containers() -> list[Collection]:
    Empty = namedtuple("Empty", [])
    return [
        list(),
        deque(),
        tuple(),
        Empty(),
        dict(),
        dict().values(),
        OrderedDict(),
        defaultdict(),
        Counter(),
        MappingProxyType({}),
        set(),
        frozenset(),
    ]


@pytest.fixture
def nested_list() -> list[list[list[list]]]:
    return [[[[]]]]


@pytest.fixture
def nested_tuple() -> tuple[tuple[tuple[tuple]]]:
    return (((tuple(),),),)


@pytest.fixture
def nested_dict() -> dict[str, dict[str, dict[str, dict[str, None]]]]:
    return {"dict": {"dict": {"dict": {"dict": None}}}}


NestedMPType = MappingProxyType[
    str, MappingProxyType[str, MappingProxyType[str, MappingProxyType[str, None]]]
]


@pytest.fixture
def nested_mapping_proxy() -> NestedMPType:
    return MappingProxyType(
        {
            "dict": MappingProxyType(
                {"dict": MappingProxyType({"dict": MappingProxyType({"dict": None})})}
            )
        }
    )


@pytest.fixture
def nested_frozenset() -> frozenset[frozenset[frozenset[frozenset]]]:
    return frozenset([frozenset([frozenset([frozenset()])])])


@pytest.fixture
def nested_A() -> A:
    a3 = A(val=None)
    a2 = A(val=a3)
    a1 = A(val=a2)
    a0 = A(val=a1)
    return a0


@pytest.fixture
def obj_1() -> A:
    a = A(val=[{123}])
    a.new = -1
    a.also = A(val=33)
    return a


@pytest.fixture
def obj_2() -> dict[str, Any]:
    a = A(4)
    return {"key": [1, (2,), [a]]}


@pytest.fixture
def obj_3() -> dict[str, Any]:
    a = A([1, 2])
    x = [1, 2, 3]
    y = {(1, 2)}
    return {"key1": a, "key2": a, "key3": x, "key4": x, "key5": y, "key6": y, "key7": [x, y]}


@pytest.fixture
def obj_4() -> dict[str, Any]:
    a = A(4)
    return {"key": [1, [2], [a]]}


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
@pytest.mark.parametrize("unravel", [True, False])
def test_get_paths__primitives(prim: PrimTypes, memoize: bool, unravel: bool) -> None:
    if not isinstance(prim, str) or not unravel:
        assert _get_paths(
            prim,
            element_test=lambda x: isinstance(x, type(prim)),
            memoize=memoize,
            unravel_strings=unravel,
        ) == [[]]
    else:
        if prim:
            correct = [[]] + [[(Address.IMMUTABLE_SEQUENCE_IDX, i)] for i in range(len(prim))]
        else:
            correct = [[]]
        assert (
            _get_paths(
                prim,
                element_test=lambda x: isinstance(x, type(prim)),
                memoize=memoize,
                unravel_strings=unravel,
            )
            == correct
        )
    assert _get_paths(prim, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(prim, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("container", get_empty_containers())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__empty_collections(container: Collection, memoize: bool) -> None:
    assert _get_paths(
        container, element_test=lambda x: isinstance(x, type(container)), memoize=memoize
    ) == [[]]
    assert _get_paths(container, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(container, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__nested_lists(nested_list: list[list[list[list]]], memoize: bool) -> None:
    correct = [
        [],
        [(Address.MUTABLE_SEQUENCE_IDX, 0)],
        [(Address.MUTABLE_SEQUENCE_IDX, 0), (Address.MUTABLE_SEQUENCE_IDX, 0)],
        [
            (Address.MUTABLE_SEQUENCE_IDX, 0),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
        ],
    ]
    assert (
        _get_paths(nested_list, element_test=lambda x: isinstance(x, list), memoize=memoize)
        == correct
    )
    assert _get_paths(nested_list, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(nested_list, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__nested_tuples(nested_tuple: tuple[tuple[tuple[tuple]]], memoize: bool) -> None:
    correct = [
        [],
        [(Address.IMMUTABLE_SEQUENCE_IDX, 0)],
        [(Address.IMMUTABLE_SEQUENCE_IDX, 0), (Address.IMMUTABLE_SEQUENCE_IDX, 0)],
        [
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
        ],
    ]
    assert (
        _get_paths(nested_tuple, element_test=lambda x: isinstance(x, tuple), memoize=memoize)
        == correct
    )
    assert _get_paths(nested_tuple, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(nested_tuple, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__nested_dicts(nested_dict: dict[dict[dict[dict]]], memoize: bool) -> None:
    correct = [
        [],
        [(Address.MUTABLE_MAPPING_KEY, "dict")],
        [(Address.MUTABLE_MAPPING_KEY, "dict"), (Address.MUTABLE_MAPPING_KEY, "dict")],
        [
            (Address.MUTABLE_MAPPING_KEY, "dict"),
            (Address.MUTABLE_MAPPING_KEY, "dict"),
            (Address.MUTABLE_MAPPING_KEY, "dict"),
        ],
    ]
    assert (
        _get_paths(nested_dict, element_test=lambda x: isinstance(x, dict), memoize=memoize)
        == correct
    )
    assert _get_paths(nested_dict, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(nested_dict, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__nested_immutable_mappings(
    nested_mapping_proxy: NestedMPType, memoize: bool
) -> None:
    correct = [
        [],
        [(Address.IMMUTABLE_MAPPING_KEY, "dict")],
        [
            (Address.IMMUTABLE_MAPPING_KEY, "dict"),
            (Address.IMMUTABLE_MAPPING_KEY, "dict"),
        ],
        [
            (Address.IMMUTABLE_MAPPING_KEY, "dict"),
            (Address.IMMUTABLE_MAPPING_KEY, "dict"),
            (Address.IMMUTABLE_MAPPING_KEY, "dict"),
        ],
    ]
    assert (
        _get_paths(
            nested_mapping_proxy,
            element_test=lambda x: isinstance(x, MappingProxyType),
            memoize=memoize,
        )
        == correct
    )
    assert _get_paths(nested_mapping_proxy, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(nested_mapping_proxy, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__nested_frozensets(
    nested_frozenset: frozenset[frozenset[frozenset[frozenset]]], memoize: bool
) -> None:
    for item in nested_frozenset:
        id_1 = id(item)
        for subitem in item:
            id_2 = id(subitem)
            for subsubitem in subitem:
                id_3 = id(subsubitem)

    correct = [
        [],
        [(Address.IMMUTABLE_SET_ID, id_1)],
        [(Address.IMMUTABLE_SET_ID, id_1), (Address.IMMUTABLE_SET_ID, id_2)],
        [
            (Address.IMMUTABLE_SET_ID, id_1),
            (Address.IMMUTABLE_SET_ID, id_2),
            (Address.IMMUTABLE_SET_ID, id_3),
        ],
    ]
    assert (
        _get_paths(
            nested_frozenset, element_test=lambda x: isinstance(x, frozenset), memoize=memoize
        )
        == correct
    )
    assert _get_paths(nested_frozenset, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(nested_frozenset, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("container", get_empty_containers())
@pytest.mark.parametrize("memoize", [True, False])
@pytest.mark.parametrize("unravel", [True, False])
def test_get_paths__containers_with_primitives(
    prim: PrimTypes, container: Collection, memoize: bool, unravel: bool
) -> None:
    constructor = type(container)
    try:
        hash(prim)
        if constructor == dict:
            container = {"dict": prim}
        elif constructor == MappingProxyType:
            container = MappingProxyType({"immutable_mapping": prim})
        elif constructor == OrderedDict:
            container = OrderedDict({"ordered_dict": prim})
        elif constructor == defaultdict:
            container = defaultdict({"default_dict": prim})
        elif constructor == ValuesView:
            container = ValuesView({"dict": prim})
        else:
            prim_contained = [prim]
            container = constructor.__call__(prim_contained)
        assert _get_paths(
            container,
            element_test=lambda x: isinstance(x, type(container)),
            memoize=memoize,
            unravel_strings=unravel,
        ) == [[]]
        if constructor is list:
            if not isinstance(prim, str) or not unravel or not prim:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.MUTABLE_SEQUENCE_IDX, 0)]]
            else:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.MUTABLE_SEQUENCE_IDX, 0)]] + [
                    [(Address.MUTABLE_SEQUENCE_IDX, 0), (Address.IMMUTABLE_SEQUENCE_IDX, i)]
                    for i in range(len(prim))
                ]

        if constructor is tuple:
            if not isinstance(prim, str) or not unravel or not prim:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.IMMUTABLE_SEQUENCE_IDX, 0)]]
            else:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.IMMUTABLE_SEQUENCE_IDX, 0)]] + [
                    [(Address.IMMUTABLE_SEQUENCE_IDX, 0), (Address.IMMUTABLE_SEQUENCE_IDX, i)]
                    for i in range(len(prim))
                ]

        elif constructor is dict:
            if not isinstance(prim, str) or not unravel or not prim:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.MUTABLE_MAPPING_KEY, "dict")]]
            else:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.MUTABLE_MAPPING_KEY, "dict")]] + [
                    [(Address.MUTABLE_MAPPING_KEY, "dict"), (Address.IMMUTABLE_SEQUENCE_IDX, i)]
                    for i in range(len(prim))
                ]
        elif constructor is MappingProxyType:
            if not isinstance(prim, str) or not unravel or not prim:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.IMMUTABLE_MAPPING_KEY, "immutable_mapping")]]
            else:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.IMMUTABLE_MAPPING_KEY, "immutable_mapping")]] + [
                    [
                        (Address.IMMUTABLE_MAPPING_KEY, "immutable_mapping"),
                        (Address.IMMUTABLE_SEQUENCE_IDX, i),
                    ]
                    for i in range(len(prim))
                ]
        elif constructor is set:
            if not isinstance(prim, str) or not unravel or not prim:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.MUTABLE_SET_ID, id(list(container)[0]))]]
            else:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.MUTABLE_SET_ID, id(list(container)[0]))]] + [
                    [
                        (Address.MUTABLE_SET_ID, id(list(container)[0])),
                        (Address.IMMUTABLE_SEQUENCE_IDX, i),
                    ]
                    for i in range(len(prim))
                ]
        elif constructor == frozenset:
            if not isinstance(prim, str) or not unravel or not prim:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.IMMUTABLE_SET_ID, id(list(container)[0]))]]
            else:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.IMMUTABLE_SET_ID, id(list(container)[0]))]] + [
                    [
                        (Address.IMMUTABLE_SET_ID, id(list(container)[0])),
                        (Address.IMMUTABLE_SEQUENCE_IDX, i),
                    ]
                    for i in range(len(prim))
                ]
        elif constructor == ValuesView:
            if not isinstance(prim, str) or not unravel or not prim:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.VALUES_VIEW_ID, id(list(container)[0]))]]
            else:
                assert _get_paths(
                    container,
                    element_test=lambda x: isinstance(x, type(prim)),
                    memoize=memoize,
                    unravel_strings=unravel,
                ) == [[(Address.VALUES_VIEW_ID, id(list(container)[0]))]] + [
                    [
                        (Address.VALUES_VIEW_ID, id(list(container)[0])),
                        (Address.IMMUTABLE_SEQUENCE_IDX, i),
                    ]
                    for i in range(len(prim))
                ]

        assert _get_paths(container, element_test=lambda x: False, memoize=memoize) == []
    except TypeError:
        pass


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__nested_attrs(nested_A: A, memoize: bool) -> None:
    correct = [
        [],
        [(Address.ATTR, "val")],
        [(Address.ATTR, "val"), (Address.ATTR, "val")],
        [(Address.ATTR, "val"), (Address.ATTR, "val"), (Address.ATTR, "val")],
    ]
    assert _get_paths(nested_A, element_test=lambda x: isinstance(x, A), memoize=memoize) == correct
    assert _get_paths(nested_A, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(nested_A, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__attributes_with_primitives(prim: PrimTypes, memoize: bool) -> None:
    a = A(val=prim)
    assert _get_paths(a, element_test=lambda x: isinstance(x, A), memoize=memoize) == [[]]
    assert _get_paths(a, element_test=lambda x: isinstance(x, type(prim)), memoize=memoize) == [
        [(Address.ATTR, "val")]
    ]
    assert _get_paths(a, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(a, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__attributes_with_references(prim: PrimTypes, memoize: bool) -> None:
    a = A(val=[prim])
    a.val2 = a.val
    if memoize:
        assert _get_paths(a, element_test=lambda x: isinstance(x, type(prim)), memoize=memoize) == [
            [(Address.ATTR, "val"), (Address.MUTABLE_SEQUENCE_IDX, 0)]
        ]
    else:
        assert _get_paths(a, element_test=lambda x: isinstance(x, type(prim)), memoize=memoize) == [
            [(Address.ATTR, "val"), (Address.MUTABLE_SEQUENCE_IDX, 0)],
            [(Address.ATTR, "val2"), (Address.MUTABLE_SEQUENCE_IDX, 0)],
        ]


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__slots(prim: PrimTypes, memoize: bool) -> None:
    b = B()
    b.val = prim
    assert _get_paths(b, element_test=lambda x: isinstance(x, B), memoize=memoize) == [[]]
    assert _get_paths(b, element_test=lambda x: isinstance(x, type(prim)), memoize=memoize) == [
        [(Address.ATTR, "val")]
    ]
    assert _get_paths(b, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(b, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__slots_with_inheritance(prim: PrimTypes, memoize: bool) -> None:
    c = C()
    c.val = prim
    c.val2 = copy(prim)
    assert _get_paths(c, element_test=lambda x: isinstance(x, C), memoize=memoize) == [[]]
    assert _get_paths(c, element_test=lambda x: isinstance(x, type(prim)), memoize=memoize) == [
        [(Address.ATTR, "val2")],
        [(Address.ATTR, "val")],
    ]
    assert _get_paths(c, element_test=lambda x: False, memoize=memoize) == []
    assert _get_paths(c, path_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__slots_with_dict(prim: PrimTypes, memoize: bool) -> None:
    d = D()
    d.val = prim
    d.val2 = copy(prim)
    d.val3 = copy(prim)
    assert _get_paths(d, element_test=lambda x: isinstance(x, D), memoize=memoize) == [[]]
    correct = [
        [(Address.ATTR, "val3")],
        [(Address.ATTR, "__dict__"), (Address.MUTABLE_MAPPING_KEY, "val3")],
        [(Address.ATTR, "val2")],
        [(Address.ATTR, "val")],
    ]
    assert (
        _get_paths(d, element_test=lambda x: isinstance(x, type(prim)), memoize=memoize) == correct
    )
    assert _get_paths(d, element_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__values_view(prim: PrimTypes, memoize: bool) -> None:
    d = {"value": prim}
    assert _get_paths(
        d.values(), element_test=lambda x: isinstance(x, ValuesView), memoize=memoize
    ) == [[]]
    assert _get_paths(
        d.values(), element_test=lambda x: isinstance(x, type(prim)), memoize=memoize
    ) == [[(Address.VALUES_VIEW_ID, id(prim))]]


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__keys_view(prim: PrimTypes, memoize: bool) -> None:
    try:
        hash(prim)
        d = {prim: True}
        assert _get_paths(
            d.keys(), element_test=lambda x: isinstance(x, KeysView), memoize=memoize
        ) == [[]]
        assert _get_paths(
            d.keys(), element_test=lambda x: isinstance(x, type(prim)), memoize=memoize
        ) == [[(Address.IMMUTABLE_SET_ID, id(prim))]]
    except TypeError:
        pass


@pytest.mark.parametrize("prim", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__items_view(prim: PrimTypes, memoize: bool) -> None:
    # Can't test the id here because each time d.items() is called, the id changes
    try:
        hash(prim)
        d = {prim: prim}
        assert _get_paths(
            d.items(), element_test=lambda x: isinstance(x, ItemsView), memoize=memoize
        ) == [[]]
        paths = _get_paths(
            d.items(), element_test=lambda x: isinstance(x, type(prim)), memoize=memoize
        )
        assert len(paths) == 2
        assert paths[0][0][0] == Address.IMMUTABLE_SET_ID
        assert type(paths[0][0][1]) == int
        assert paths[0][1] == (Address.IMMUTABLE_SEQUENCE_IDX, 0)
        assert paths[1][0][0] == Address.IMMUTABLE_SET_ID
        assert type(paths[1][0][1]) == int
        assert paths[1][1] == (Address.IMMUTABLE_SEQUENCE_IDX, 1)
    except TypeError:
        d = {"key": prim}
        assert _get_paths(
            d.items(), element_test=lambda x: isinstance(x, ItemsView), memoize=memoize
        ) == [[]]
        paths = _get_paths(
            d.items(), element_test=lambda x: isinstance(x, type(prim)), memoize=memoize
        )
        assert len(paths) == 1
        assert paths[0][0][0] == Address.IMMUTABLE_SET_ID
        assert type(paths[0][0][1]) == int
        assert paths[0][1] == (Address.IMMUTABLE_SEQUENCE_IDX, 1)


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__obj_1(obj_1: A, memoize: bool) -> None:
    correct = [
        [
            (Address.ATTR, "val"),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
            (Address.MUTABLE_SET_ID, id(123)),
        ],
        [(Address.ATTR, "new")],
        [(Address.ATTR, "also"), (Address.ATTR, "val")],
    ]
    assert _get_paths(obj_1, element_test=lambda x: isinstance(x, int), memoize=memoize) == correct
    assert _get_paths(obj_1, element_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__obj_2(obj_2: dict[str, Any], memoize: bool) -> None:
    correct = [
        [(Address.MUTABLE_MAPPING_KEY, "key"), (Address.MUTABLE_SEQUENCE_IDX, 0)],
        [
            (Address.MUTABLE_MAPPING_KEY, "key"),
            (Address.MUTABLE_SEQUENCE_IDX, 1),
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key"),
            (Address.MUTABLE_SEQUENCE_IDX, 2),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
            (Address.ATTR, "val"),
        ],
    ]

    assert _get_paths(obj_2, element_test=lambda x: isinstance(x, int), memoize=memoize) == correct
    assert _get_paths(obj_2, element_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("memoize", [True, False])
def test_get_paths__obj_3(obj_3: dict[str, Any], memoize: bool) -> None:
    for item in obj_3["key5"]:
        item_id = id(item)

    correct_no_memo = [
        [
            (Address.MUTABLE_MAPPING_KEY, "key1"),
            (Address.ATTR, "val"),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key1"),
            (Address.ATTR, "val"),
            (Address.MUTABLE_SEQUENCE_IDX, 1),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key2"),
            (Address.ATTR, "val"),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key2"),
            (Address.ATTR, "val"),
            (Address.MUTABLE_SEQUENCE_IDX, 1),
        ],
        [(Address.MUTABLE_MAPPING_KEY, "key3"), (Address.MUTABLE_SEQUENCE_IDX, 0)],
        [(Address.MUTABLE_MAPPING_KEY, "key3"), (Address.MUTABLE_SEQUENCE_IDX, 1)],
        [(Address.MUTABLE_MAPPING_KEY, "key3"), (Address.MUTABLE_SEQUENCE_IDX, 2)],
        [(Address.MUTABLE_MAPPING_KEY, "key4"), (Address.MUTABLE_SEQUENCE_IDX, 0)],
        [(Address.MUTABLE_MAPPING_KEY, "key4"), (Address.MUTABLE_SEQUENCE_IDX, 1)],
        [(Address.MUTABLE_MAPPING_KEY, "key4"), (Address.MUTABLE_SEQUENCE_IDX, 2)],
        [
            (Address.MUTABLE_MAPPING_KEY, "key5"),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key5"),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 1),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key6"),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key6"),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 1),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key7"),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key7"),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
            (Address.MUTABLE_SEQUENCE_IDX, 1),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key7"),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
            (Address.MUTABLE_SEQUENCE_IDX, 2),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key7"),
            (Address.MUTABLE_SEQUENCE_IDX, 1),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key7"),
            (Address.MUTABLE_SEQUENCE_IDX, 1),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 1),
        ],
    ]
    correct_memo = [
        [
            (Address.MUTABLE_MAPPING_KEY, "key1"),
            (Address.ATTR, "val"),
            (Address.MUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key1"),
            (Address.ATTR, "val"),
            (Address.MUTABLE_SEQUENCE_IDX, 1),
        ],
        [(Address.MUTABLE_MAPPING_KEY, "key3"), (Address.MUTABLE_SEQUENCE_IDX, 0)],
        [(Address.MUTABLE_MAPPING_KEY, "key3"), (Address.MUTABLE_SEQUENCE_IDX, 1)],
        [(Address.MUTABLE_MAPPING_KEY, "key3"), (Address.MUTABLE_SEQUENCE_IDX, 2)],
        [
            (Address.MUTABLE_MAPPING_KEY, "key5"),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 0),
        ],
        [
            (Address.MUTABLE_MAPPING_KEY, "key5"),
            (Address.MUTABLE_SET_ID, item_id),
            (Address.IMMUTABLE_SEQUENCE_IDX, 1),
        ],
    ]

    if memoize:
        ans = correct_memo
    else:
        ans = correct_no_memo
    assert _get_paths(obj_3, element_test=lambda x: isinstance(x, int), memoize=memoize) == ans
    assert _get_paths(obj_3, element_test=lambda x: False, memoize=memoize) == []


@pytest.mark.parametrize("unravel", [True, False])
def test_get_paths__unravel_string(unravel: bool) -> None:
    s = "string"
    if unravel:
        correct = [[]] + [[(Address.IMMUTABLE_SEQUENCE_IDX, i)] for i in range(len(s))]
    else:
        correct = [[]]
    assert _get_paths(s, unravel_strings=unravel) == correct


@pytest.mark.parametrize("unravel", [True, False])
def test_get_paths__unravel_bytes(unravel: bool) -> None:
    s = bytes("string", encoding="utf-8")
    if unravel:
        correct = [[]] + [[(Address.IMMUTABLE_SEQUENCE_IDX, i)] for i in range(len(s))]
    else:
        correct = [[]]
    assert _get_paths(s, unravel_strings=unravel) == correct


@pytest.mark.parametrize("unravel", [True, False])
def test_get_paths__unravel_bytearray(unravel: bool) -> None:
    s = bytearray("string", encoding="utf-8")
    if unravel:
        correct = [[]] + [[(Address.MUTABLE_SEQUENCE_IDX, i)] for i in range(len(s))]
    else:
        correct = [[]]
    assert _get_paths(s, unravel_strings=unravel) == correct


def test_get_paths_helper() -> None:
    d = D()
    output = []
    _get_paths_helper(
        d,
        element_test=lambda x: True,
        path_test=lambda x: True,
        paths=output,
        current_path=None,
        memo=None,
        memoize=False,
    )
    assert output == [
        [],
        [(Address.ATTR, "__dict__")],
        [(Address.ATTR, "val2")],
        [(Address.ATTR, "val")],
    ]


def test_collect_all_attrs() -> None:
    d = D()
    d.other = "other"
    assert _collect_all_attrs(d) == ["other", "__dict__", "val2", "val"]


def test_increment_path__attr() -> None:
    assert _increment_path("root_obj", (Address.ATTR, "attr")) == "root_obj.attr"


def test_increment_path__mutable_seq() -> None:
    assert _increment_path("root_obj", (Address.MUTABLE_SEQUENCE_IDX, 0)) == "root_obj[0]"


def test_increment_path__immutable_seq() -> None:
    assert _increment_path("root_obj", (Address.IMMUTABLE_SEQUENCE_IDX, 0)) == "root_obj[0]"


def test_increment_path__mutable_mapping() -> None:
    assert _increment_path("root_obj", (Address.MUTABLE_MAPPING_KEY, "key")) == "root_obj['key']"


def test_increment_path__immutable_mapping() -> None:
    assert _increment_path("root_obj", (Address.IMMUTABLE_MAPPING_KEY, "key")) == "root_obj['key']"


def test_increment_path__mutable_set() -> None:
    assert _increment_path("root_obj", (Address.MUTABLE_SET_ID, 1010)) == "root_obj{id=1010}"


def test_increment_path__immutable_set() -> None:
    assert _increment_path("root_obj", (Address.IMMUTABLE_SET_ID, 1010)) == "root_obj{id=1010}"


def test_increment_path__values_view() -> None:
    assert (
        _increment_path("root_obj", (Address.VALUES_VIEW_ID, 1010))
        == "root_obj{ValuesView_id=1010}"
    )


def test_increment_obj_pointer__attr() -> None:
    a = A(val="test_val")
    assert _increment_obj_pointer(a, (Address.ATTR, "val")) == a.val


def test_increment_obj_pointer__mutable_seq() -> None:
    a = ["test_val"]
    assert _increment_obj_pointer(a, (Address.MUTABLE_SEQUENCE_IDX, 0)) == "test_val"


def test_increment_obj_pointer__immutable_seq() -> None:
    a = ("test_val",)
    assert _increment_obj_pointer(a, (Address.IMMUTABLE_SEQUENCE_IDX, 0)) == "test_val"


def test_increment_obj_pointer__mutable_mapping() -> None:
    a = {"key": "test_val"}
    assert _increment_obj_pointer(a, (Address.MUTABLE_MAPPING_KEY, "key")) == "test_val"


def test_increment_obj_pointer__immutable_mapping() -> None:
    a = MappingProxyType({"key": "test_val"})
    assert _increment_obj_pointer(a, (Address.IMMUTABLE_MAPPING_KEY, "key")) == "test_val"


def test_increment_obj_pointer__mutable_set() -> None:
    item = "test_val"
    a = {item}
    assert _increment_obj_pointer(a, (Address.MUTABLE_SET_ID, id(item))) == "test_val"


def test_increment_obj_pointer__immutable_set() -> None:
    item = "test_val"
    a = frozenset((item,))
    assert _increment_obj_pointer(a, (Address.IMMUTABLE_SET_ID, id(item))) == "test_val"


def test_increment_obj_pointer__values_view() -> None:
    item = "test_val"
    d = {"key": item}
    assert _increment_obj_pointer(d.values(), (Address.VALUES_VIEW_ID, id(item))) == "test_val"


@pytest.mark.parametrize("memoize", [True, False])
def test_get_objs_from_paths(obj_1: A, memoize: bool) -> None:
    correct = {
        "ROOT.val[0]{id=" + f"{id(123)}" + "}": 123,
        "ROOT.new": -1,
        "ROOT.also.val": 33,
    }
    paths = _get_paths(obj_1, element_test=lambda x: isinstance(x, int), memoize=memoize)
    assert _get_elements_from_paths(obj_1, paths) == correct


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__attr(obj_1: A, overwrite: PrimTypes) -> None:
    _overwrite_element(obj_1, (Address.ATTR, "new"), overwrite)
    assert obj_1.new == overwrite


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__slots(overwrite: PrimTypes) -> None:
    b = B()
    b.val = 1
    _overwrite_element(b, (Address.ATTR, "val"), overwrite)
    assert b.val == overwrite


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__slots_with_inheritance(overwrite: PrimTypes) -> None:
    c = C()
    c.val = 1
    c.val2 = 1
    _overwrite_element(c, (Address.ATTR, "val"), overwrite)
    _overwrite_element(c, (Address.ATTR, "val2"), overwrite)
    assert c.val == overwrite
    assert c.val2 == overwrite


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__slots_with_dict(overwrite: PrimTypes) -> None:
    d = D()
    d.val = 1
    d.val2 = 1
    d.val3 = 1
    _overwrite_element(d, (Address.ATTR, "val"), overwrite)
    _overwrite_element(d, (Address.ATTR, "val2"), overwrite)
    _overwrite_element(d, (Address.ATTR, "val3"), overwrite)
    assert d.val == overwrite
    assert d.val2 == overwrite
    d.val3 = 1
    _overwrite_element(d.__dict__, (Address.MUTABLE_MAPPING_KEY, "val3"), overwrite)
    assert d.val3 == overwrite


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__mutable_mapping(overwrite: PrimTypes) -> None:
    obj = {"key": 1}
    _overwrite_element(obj, (Address.MUTABLE_MAPPING_KEY, "key"), overwrite)
    assert obj["key"] == overwrite


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__mutable_seq(overwrite: PrimTypes) -> None:
    obj = [1]
    _overwrite_element(obj, (Address.MUTABLE_SEQUENCE_IDX, 0), overwrite)
    assert obj[0] == overwrite


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__mutable_set(overwrite: PrimTypes) -> None:
    num = 1
    obj = {num}
    try:
        hash(overwrite)
        _overwrite_element(obj, (Address.MUTABLE_SET_ID, id(num)), overwrite)
        assert obj == {overwrite}
    except TypeError:
        pass


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__immutable_mapping(overwrite: PrimTypes) -> None:
    obj = MappingProxyType({"key": 1})
    with pytest.raises(TypeError):
        _overwrite_element(obj, (Address.MUTABLE_MAPPING_KEY, "key"), overwrite)


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__immutable_seq(overwrite: PrimTypes) -> None:
    obj = (1,)
    with pytest.raises(TypeError):
        _overwrite_element(obj, (Address.IMMUTABLE_SEQUENCE_IDX, 0), overwrite)


@pytest.mark.parametrize("overwrite", get_primitives())
def test_overwrite_element__bad_address(overwrite: PrimTypes) -> None:
    obj = (1,)
    with pytest.raises(ValueError):
        _overwrite_element(obj, ("immutable_idx", 0), overwrite)


@pytest.mark.parametrize("overwrite", get_primitives())
@pytest.mark.parametrize("memoize", [True, False])
def test_overwrite_elements_at_paths(obj_1: A, overwrite: PrimTypes, memoize: bool) -> None:
    try:
        hash(overwrite)
        paths = _get_paths(obj_1, element_test=lambda x: isinstance(x, int), memoize=memoize)
        _overwrite_elements_at_paths(obj_1, paths, overwrite, silent=True, raise_on_exception=True)
        assert obj_1.val == [{overwrite}]
        assert obj_1.new == overwrite
        assert obj_1.also.val == overwrite
    except TypeError:
        pass


@pytest.mark.parametrize("memoize", [True, False])
def test_overwrite_elements_at_paths__raise_type_error(memoize: bool) -> None:
    obj = {1}
    paths = _get_paths(obj, element_test=lambda x: isinstance(x, int), memoize=memoize)
    with pytest.raises(TypeError):
        _overwrite_elements_at_paths(obj_1, paths, overwrite_value=[])


@pytest.mark.parametrize("memoize", [True, False])
def test_overwrite_elements_at_paths__raise_value_error(memoize: bool) -> None:
    obj = (1,)
    paths = _get_paths(obj, element_test=lambda x: isinstance(x, int), memoize=memoize)
    paths[0][0] = ("bad_value", paths[0][0][1])
    with pytest.raises(ValueError):
        _overwrite_elements_at_paths(obj_1, paths, overwrite_value=None)


@pytest.mark.parametrize("memoize", [True, False])
def test_get_elements__by_element(obj_1: A, memoize: bool) -> None:
    correct = {
        "ROOT.val[0]{id=" + f"{id(123)}" + "}": 123,
        "ROOT.new": -1,
        "ROOT.also.val": 33,
    }
    assert (
        get_elements(obj_1, element_test=lambda x: isinstance(x, int), memoize=memoize) == correct
    )


@pytest.mark.parametrize("memoize", [True, False])
def test_get_elements__by_path(obj_1: A, memoize: bool) -> None:
    correct = {"ROOT.new": -1}
    assert get_elements(obj_1, path_test=lambda x: x == "new", memoize=memoize) == correct


@pytest.mark.parametrize("memoize", [True, False])
def test_overwrite_elements__by_element(obj_4: dict[str, Any], memoize: bool) -> None:
    paths = list(
        get_elements(obj_4, element_test=lambda x: isinstance(x, int), memoize=memoize).keys()
    )
    overwrite_elements(
        obj_4, overwrite_value=None, element_test=lambda x: isinstance(x, int), memoize=memoize
    )
    assert (
        len(
            list(
                get_elements(
                    obj_4, element_test=lambda x: isinstance(x, int), memoize=memoize
                ).keys()
            )
        )
        == 0
    )
    assert (
        list(
            get_elements(
                obj_4, element_test=lambda x: isinstance(x, type(None)), memoize=memoize
            ).keys()
        )
        == paths
    )


@pytest.mark.parametrize("memoize", [True, False])
def test_overwrite_elements__by_path(obj_4: dict[str, Any], memoize: bool) -> None:
    paths = list(get_elements(obj_4, path_test=lambda x: x == 1, memoize=memoize).keys())
    overwrite_elements(obj_4, overwrite_value=None, path_test=lambda x: x == 1, memoize=memoize)
    assert len(
        list(get_elements(obj_4, path_test=lambda x: x == 1, memoize=memoize).keys())
    ) == len(paths)
    assert obj_4["key"][1] is None


@pytest.mark.parametrize("memoize", [True, False])
def test_print_object_tree(capsys: CaptureFixture, obj_2: dict[str, Any], memoize: bool) -> None:
    print_obj_tree(obj_2, memoize=memoize)
    out, err = capsys.readouterr()
    correct_output = "ROOT -> {'key': [1, (2,), ...]}\n"
    correct_output += "ROOT['key'] -> [1, (2,), ...]\n"
    correct_output += "ROOT['key'][0] -> 1\n"
    correct_output += "ROOT['key'][1] -> (2,)\n"
    correct_output += "ROOT['key'][1][0] -> 2\n"
    correct_output += "ROOT['key'][2] -> ['A(4)']\n"
    correct_output += "ROOT['key'][2][0] -> 'A(4)'\n"
    correct_output += "ROOT['key'][2][0].val -> 4\n"

    assert correct_output == out


@pytest.mark.parametrize("memoize", [True, False])
def test_print_object_tree_filter_types(
    capsys: CaptureFixture, obj_2: dict[str, Any], memoize: bool
) -> None:
    print_obj_tree(obj_2, element_test=lambda x: isinstance(x, list), memoize=memoize)
    out, err = capsys.readouterr()
    correct_output = "ROOT['key'] -> [1, (2,), ...]\n"
    correct_output += "ROOT['key'][2] -> ['A(4)']\n"

    assert correct_output == out


@pytest.mark.parametrize("memoize", [True, False])
def test_print_object_tree_max(
    capsys: CaptureFixture, obj_2: dict[str, Any], memoize: bool
) -> None:
    print_obj_tree(obj_2, max=3, memoize=memoize)
    out, err = capsys.readouterr()
    correct_output = "ROOT -> {'key': [1, (2,), ...]}\n"
    correct_output += "ROOT['key'] -> [1, (2,), ...]\n"
    correct_output += "ROOT['key'][0] -> 1\n"

    assert correct_output == out


@pytest.mark.parametrize("memoize", [True, False])
def test_hot_swap(obj_2: dict[str, Any], memoize: bool) -> None:
    original_paths = _get_paths(obj_2, element_test=lambda x: isinstance(x, A), memoize=memoize)
    with hot_swap(obj_2, None, element_test=lambda x: isinstance(x, A), memoize=memoize):
        assert not _get_paths(obj_2, element_test=lambda x: isinstance(x, A), memoize=memoize)
        assert (
            _get_paths(obj_2, element_test=lambda x: x is None, memoize=memoize) == original_paths
        )
    assert original_paths == _get_paths(
        obj_2, element_test=lambda x: isinstance(x, A), memoize=memoize
    )


@pytest.mark.parametrize("memoize", [True, False])
def test_hot_swap__with_immutable_obj(memoize: bool) -> None:
    obj = (1, 2, 3)
    with pytest.raises(TypeError):
        with hot_swap(obj, None, element_test=lambda x: isinstance(x, int), memoize=memoize):
            pass


@pytest.mark.parametrize("memoize", [True, False])
def test_hot_swap__with_set(memoize: bool) -> None:
    obj = {1, 2, 3}
    with pytest.raises(TypeError):
        with hot_swap(obj, None, element_test=lambda x: isinstance(x, int), memoize=memoize):
            pass


@pytest.mark.parametrize("memoize", [True, False])
def test_hot_swap__with_set_allow_mutations(memoize: bool) -> None:
    obj = {1, 2, 3}
    original_id = id(obj)
    with hot_swap(
        obj, None, element_test=lambda x: x == 1, memoize=memoize, allow_mutable_set_mutations=True
    ):
        assert obj == {None, 2, 3}
        assert id(obj) == original_id
    assert obj == {1, 2, 3}
    assert id(obj) == original_id
