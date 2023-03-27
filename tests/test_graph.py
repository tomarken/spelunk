from typing import Any, Callable, Hashable
from types import MappingProxyType
from numbers import Real
import pytest
from frozendict import frozendict
from spelunk import graph
from spelunk.graph import (
    SequenceLike,
    MutableSequenceLike,
    MappingLike,
    MutableMappingLike,
    AccessorErrors,
    IterAccessorValue,
    obj_getter,
    obj_setter,
    obj_iterable,
    seq_getter,
    seq_setter,
    seq_iterable,
    map_getter,
    map_setter,
    map_iterable,
    set_getter,
    set_setter,
    set_iterable,
    col_getter,
    col_iterable,
    Accessor,
    Link,
    Node,
    has_attrs,
    get_object_graph,
)
from conftest import (
    silence_logger,
    EmptyClass,
    SlotsClass,
    MultiSlotsClass,
    SlotsDictClass,
    InheritedSlotsDictClass,
    CollectionClass,
    A,
    get_a_few_objects,
    get_assorted_objs,
    get_objects_with_attrs,
    StringEnum,
)
from copy import deepcopy
from numpy.typing import NDArray


def test_SequenceLike__monadic_int_getitem(seq_like_monadic_int_getitem: SequenceLike) -> None:
    for idx in range(len(seq_like_monadic_int_getitem)):
        _ = seq_like_monadic_int_getitem.__getitem__(idx) in seq_like_monadic_int_getitem
    _ = len(seq_like_monadic_int_getitem)
    assert isinstance(seq_like_monadic_int_getitem, SequenceLike)
    assert not isinstance(seq_like_monadic_int_getitem, MutableSequenceLike)


def test_SequenceLike__dyadic_int_getitem(seq_like_dyadic_int_getitem: SequenceLike) -> None:
    for idx in range(len(seq_like_dyadic_int_getitem)):
        with pytest.raises(AccessorErrors):
            seq_like_dyadic_int_getitem.__getitem__(idx)
    _ = len(seq_like_dyadic_int_getitem)
    assert isinstance(seq_like_dyadic_int_getitem, SequenceLike)
    assert not isinstance(seq_like_dyadic_int_getitem, MutableSequenceLike)


def test_SequenceLike__monadic_str_getitem(seq_like_monadic_str_getitem: SequenceLike) -> None:
    for idx in range(len(seq_like_monadic_str_getitem)):
        with pytest.raises(AccessorErrors):
            seq_like_monadic_str_getitem.__getitem__(idx)
    _ = len(seq_like_monadic_str_getitem)
    assert isinstance(seq_like_monadic_str_getitem, SequenceLike)
    assert not isinstance(seq_like_monadic_str_getitem, MutableSequenceLike)


def test_MutableSequenceLike__monadic_int_getitem(
    mutable_seq_like_monadic_int_getitem: MutableSequenceLike,
) -> None:
    for idx in range(len(mutable_seq_like_monadic_int_getitem)):
        _ = (
            mutable_seq_like_monadic_int_getitem.__getitem__(idx)
            in mutable_seq_like_monadic_int_getitem
        )
    _ = len(mutable_seq_like_monadic_int_getitem)
    for idx in range(len(mutable_seq_like_monadic_int_getitem)):
        mutable_seq_like_monadic_int_getitem.__setitem__(idx, True)
    assert isinstance(mutable_seq_like_monadic_int_getitem, MutableSequenceLike)


def test_MutableSequenceLike__dyadic_int_getitem(
    mutable_seq_like_dyadic_int_getitem: MutableSequenceLike,
) -> None:
    for idx in range(len(mutable_seq_like_dyadic_int_getitem)):
        with pytest.raises(AccessorErrors):
            mutable_seq_like_dyadic_int_getitem.__getitem__(idx)
    _ = len(mutable_seq_like_dyadic_int_getitem)
    for idx in range(len(mutable_seq_like_dyadic_int_getitem)):
        with pytest.raises(Exception):
            mutable_seq_like_dyadic_int_getitem.__setitem__(idx, True)

    assert isinstance(mutable_seq_like_dyadic_int_getitem, MutableSequenceLike)


def test_MutableSequenceLike__monadic_str_getitem(
    mutable_seq_like_monadic_str_getitem: MutableSequenceLike,
) -> None:
    for idx in range(len(mutable_seq_like_monadic_str_getitem)):
        with pytest.raises(AccessorErrors):
            mutable_seq_like_monadic_str_getitem.__getitem__(idx)
    _ = len(mutable_seq_like_monadic_str_getitem)
    for idx in range(len(mutable_seq_like_monadic_str_getitem)):
        with pytest.raises(Exception):
            mutable_seq_like_monadic_str_getitem.__setitem__(idx, True)

    assert isinstance(mutable_seq_like_monadic_str_getitem, MutableSequenceLike)


def test_MappingLike__monadic_getitem(mapping_like_monadic_getitem: MappingLike) -> None:
    for key in mapping_like_monadic_getitem.keys():
        _ = mapping_like_monadic_getitem.__getitem__(key)
    _ = len(mapping_like_monadic_getitem)

    assert isinstance(mapping_like_monadic_getitem, MappingLike)
    assert not isinstance(mapping_like_monadic_getitem, MutableMappingLike)


def test_MappingLike__dyadic_getitem(mapping_like_dyadic_getitem: MappingLike) -> None:
    for key in mapping_like_dyadic_getitem.keys():
        with pytest.raises(AccessorErrors):
            _ = mapping_like_dyadic_getitem.__getitem__(key)
    _ = len(mapping_like_dyadic_getitem)

    assert isinstance(mapping_like_dyadic_getitem, MappingLike)
    assert not isinstance(mapping_like_dyadic_getitem, MutableMappingLike)


def test_MutableMappingLike__monadic_getitem(
    mutable_mapping_like_monadic_getitem: MutableMappingLike,
) -> None:
    for key in mutable_mapping_like_monadic_getitem.keys():
        _ = mutable_mapping_like_monadic_getitem.__getitem__(key)
    _ = len(mutable_mapping_like_monadic_getitem)

    for key in mutable_mapping_like_monadic_getitem.keys():
        mutable_mapping_like_monadic_getitem.__setitem__(key, True)

    assert isinstance(mutable_mapping_like_monadic_getitem, MutableMappingLike)


def test_MutableMappingLike__dyadic_getitemm(
    mutable_mapping_like_dyadic_getitem: MutableMappingLike,
) -> None:
    for key in mutable_mapping_like_dyadic_getitem.keys():
        with pytest.raises(AccessorErrors):
            _ = mutable_mapping_like_dyadic_getitem.__getitem__(key)
    _ = len(mutable_mapping_like_dyadic_getitem)

    for key in mutable_mapping_like_dyadic_getitem.keys():
        with pytest.raises(AccessorErrors):
            mutable_mapping_like_dyadic_getitem.__setitem__(key, True)

    assert isinstance(mutable_mapping_like_dyadic_getitem, MutableMappingLike)


def test_obj_getter(empty_class_obj: EmptyClass) -> None:
    empty_class_obj.value = "value"
    assert obj_getter(empty_class_obj, "value") == "value"


def test_obj_getter__EmptyClass_None(empty_class_obj: EmptyClass) -> None:
    with silence_logger(graph.__name__):
        assert obj_getter(empty_class_obj, "value") is None


def test_obj_setter__EmptyClass(empty_class_obj: EmptyClass) -> None:
    empty_class_obj.value = "value"
    obj_setter(empty_class_obj, "value", "new_value")
    assert empty_class_obj.value == "new_value"


def test_obj_setter__SlotsClass(slots_class_obj: SlotsClass) -> None:
    slots_class_obj.slot = "value"
    obj_setter(slots_class_obj, "slot", "new_value")
    assert slots_class_obj.slot == "new_value"


def test_obj_setter__MultiSlotsClass(multi_slots_class_obj: MultiSlotsClass) -> None:
    multi_slots_class_obj.slot = "value"
    obj_setter(multi_slots_class_obj, "slot", "new_value")
    assert multi_slots_class_obj.slot == "new_value"


def test_obj_setter__SlotsDictClass(slots_dict_class_obj: SlotsDictClass) -> None:
    slots_dict_class_obj.slot = "value"
    slots_dict_class_obj.var = "var"
    obj_setter(slots_dict_class_obj, "slot", "new_value")
    obj_setter(slots_dict_class_obj, "var", "new_var")
    assert slots_dict_class_obj.slot == "new_value"
    assert slots_dict_class_obj.var == "new_var"


def test_obj_setter__InheritedSlotsDictClass(
    inherited_slots_dict_class_obj: InheritedSlotsDictClass,
) -> None:
    inherited_slots_dict_class_obj = InheritedSlotsDictClass()
    inherited_slots_dict_class_obj.slot = "value"
    inherited_slots_dict_class_obj.slot2 = "value2"
    inherited_slots_dict_class_obj.var = "var"
    obj_setter(inherited_slots_dict_class_obj, "slot", "new_value")
    obj_setter(inherited_slots_dict_class_obj, "slot2", "new_value2")
    obj_setter(inherited_slots_dict_class_obj, "var", "new_var")
    assert inherited_slots_dict_class_obj.slot == "new_value"
    assert inherited_slots_dict_class_obj.slot2 == "new_value2"
    assert inherited_slots_dict_class_obj.var == "new_var"


def test_obj_iterable__EmptyClass(empty_class_obj: EmptyClass) -> None:
    empty_class_obj.value = "value"
    obj_setter(empty_class_obj, "value", "new_value")
    assert empty_class_obj.value == "new_value"


def test_obj_iterable__SlotsClass(slots_class_obj: SlotsClass) -> None:
    assert obj_iterable(slots_class_obj) == ["slot"]


def test_obj_iterable__SlotsDictClass(slots_dict_class_obj: SlotsDictClass) -> None:
    slots_dict_class_obj.new = "new"
    assert obj_iterable(slots_dict_class_obj) == ["new", "slot", "__dict__"]


def test_obj_iterable__InheritedSlotsDictClass(
    inherited_slots_dict_class_obj: InheritedSlotsDictClass,
) -> None:
    inherited_slots_dict_class_obj.new = "new"
    assert obj_iterable(inherited_slots_dict_class_obj) == ["new", "slot2", "slot", "__dict__"]


def test_seq_getter__monadic_int_getitem(seq_like_monadic_int_getitem: SequenceLike) -> None:
    internal_array = getattr(seq_like_monadic_int_getitem, "array")
    for idx, el in enumerate(internal_array):
        assert seq_getter(seq_like_monadic_int_getitem, (idx, el)) == (el, True)


def test_seq_getter__dyadic_int_getitem(seq_like_dyadic_int_getitem: SequenceLike) -> None:
    internal_array = getattr(seq_like_dyadic_int_getitem, "array")
    for idx, el in enumerate(internal_array):
        assert seq_getter(seq_like_dyadic_int_getitem, (idx, el)) == (el, False)


def test_seq_getter__monadic_str_getitem(seq_like_monadic_str_getitem: SequenceLike) -> None:
    internal_array = getattr(seq_like_monadic_str_getitem, "array")
    for idx, el in enumerate(internal_array):
        assert seq_getter(seq_like_monadic_str_getitem, (idx, el)) == (el, False)


def test_seq_setter__monadic_int_getitem(
    mutable_seq_like_monadic_int_getitem: MutableSequenceLike,
) -> None:
    internal_array = getattr(mutable_seq_like_monadic_int_getitem, "array")
    for idx, el in enumerate(internal_array):
        assert seq_getter(mutable_seq_like_monadic_int_getitem, (idx, el)) == (el, True)
    for idx, new_val in zip(internal_array, range(-1, -len(internal_array) - 1, -1)):
        seq_setter(mutable_seq_like_monadic_int_getitem, idx, new_val)
        assert seq_getter(mutable_seq_like_monadic_int_getitem, (idx, new_val)) == (new_val, True)


def test_seq_setter__dyadic_int_getitem(
    mutable_seq_like_dyadic_int_getitem: MutableSequenceLike,
) -> None:
    internal_array = getattr(mutable_seq_like_dyadic_int_getitem, "array")
    for idx, el in enumerate(internal_array):
        assert seq_getter(mutable_seq_like_dyadic_int_getitem, (idx, el)) == (el, False)
    for idx, new_val in zip(internal_array, range(-1, -len(internal_array) - 1, -1)):
        with pytest.raises(AccessorErrors):
            seq_setter(mutable_seq_like_dyadic_int_getitem, idx, new_val)


def test_seq_setter__monadic_str_getitem(
    mutable_seq_like_monadic_str_getitem: MutableSequenceLike,
) -> None:
    internal_array = getattr(mutable_seq_like_monadic_str_getitem, "array")
    for idx, el in enumerate(internal_array):
        assert seq_getter(mutable_seq_like_monadic_str_getitem, (idx, el)) == (el, False)
    for idx, new_val in zip(internal_array, range(-1, -len(internal_array) - 1, -1)):
        with pytest.raises(AccessorErrors):
            seq_setter(mutable_seq_like_monadic_str_getitem, idx, new_val)


def test_seq_iterable__mondaic_int_getitem(seq_like_monadic_int_getitem: SequenceLike) -> None:
    for (idx, el), (jdx, it) in zip(
        seq_iterable(seq_like_monadic_int_getitem), enumerate(iter(seq_like_monadic_int_getitem))
    ):
        assert idx == jdx
        assert el == it


def test_seq_iterable__dyadic_int_getitem(seq_like_dyadic_int_getitem: SequenceLike) -> None:
    for (idx, el), (jdx, it) in zip(
        seq_iterable(seq_like_dyadic_int_getitem), enumerate(iter(seq_like_dyadic_int_getitem))
    ):
        assert idx == jdx
        assert el == it


def test_seq_iterable__monadic_str_getitem(seq_like_monadic_str_getitem: SequenceLike) -> None:
    for (idx, el), (jdx, it) in zip(
        seq_iterable(seq_like_monadic_str_getitem), enumerate(iter(seq_like_monadic_str_getitem))
    ):
        assert idx == jdx
        assert el == it


def test_map_getter__monadic_getitem(mapping_like_monadic_getitem: MappingLike) -> None:
    internal_map = getattr(mapping_like_monadic_getitem, "map")
    for k, v in internal_map.items():
        assert map_getter(mapping_like_monadic_getitem, (k, internal_map[k])) == (v, True)


def test_map_getter__dyadic_getitem(mapping_like_dyadic_getitem: MappingLike) -> None:
    internal_map = getattr(mapping_like_dyadic_getitem, "map")
    for k, v in internal_map.items():
        assert map_getter(mapping_like_dyadic_getitem, (k, internal_map[k])) == (v, False)


def test_map_setter__monadic_getitem(
    mutable_mapping_like_monadic_getitem: MutableMappingLike,
) -> None:
    internal_map = getattr(mutable_mapping_like_monadic_getitem, "map")
    for k, new_val in zip(internal_map, range(-1, -len(internal_map) - 1, -1)):
        map_setter(mutable_mapping_like_monadic_getitem, k, new_val)
        assert mutable_mapping_like_monadic_getitem.__getitem__(k) == new_val


def test_map_setter__dyadic_getitem(
    mutable_mapping_like_dyadic_getitem: MutableMappingLike,
) -> None:
    internal_map = getattr(mutable_mapping_like_dyadic_getitem, "map")
    for k, new_val in zip(internal_map, range(-1, -len(internal_map) - 1, -1)):
        with pytest.raises(AccessorErrors):
            map_setter(mutable_mapping_like_dyadic_getitem, k, new_val)


def test_map_iterable__mondaic_getitem(mapping_like_monadic_getitem: MappingLike) -> None:
    for (key, key_copy), it in zip(
        map_iterable(mapping_like_monadic_getitem), iter(mapping_like_monadic_getitem)
    ):
        assert key == key_copy == it


def test_map_iterable__dyadic_getitem(mapping_like_dyadic_getitem: MappingLike) -> None:
    for (key, key_copy), it in zip(
        map_iterable(mapping_like_dyadic_getitem), iter(mapping_like_dyadic_getitem)
    ):
        assert key == key_copy == it


def test_set_getter__example_frozen_set(example_frozenset) -> None:
    for el in example_frozenset:
        assert set_getter(example_frozenset, (el, None)) == (el, True)


def test_set_getter__example_set(example_set: set[Any]) -> None:
    for el in example_set:
        assert set_getter(example_set, (el, None)) == (el, True)


def test_set_getter__raises(example_set: set[Any]) -> None:
    with pytest.raises(ValueError):
        set_getter(example_set, (0.1, None))


def test_set_setter__example_set(example_set: set[Any]) -> None:
    for el, new_val in zip(example_set, ["other item not in set"] * len(example_set)):
        set_setter(example_set, el, new_val)
        assert set_getter(example_set, (new_val, None)) == (new_val, True)
        set_setter(example_set, new_val, el)


def test_set_setter__example_set_obj_already_present(example_set: set[Any]) -> None:
    deepcp = deepcopy(example_set)
    set_setter(example_set, 1, 1_000_000)
    deepcp.remove(1)
    assert deepcp == example_set


def test_set_setter__same_overwrite(example_set: set[Any]) -> None:
    dpcp = deepcopy(example_set)
    set_setter(example_set, 1, 1)
    assert dpcp == example_set


def test_set_setter__raises(example_set: set[Any]) -> None:
    with pytest.raises(ValueError):
        set_setter(example_set, "other item not in set", "filler")


def test_set_iterable__example_frozen_set(example_frozenset) -> None:
    seen_els = set()
    for el, filler in set_iterable(example_frozenset):
        assert el in example_frozenset
        assert filler is None
        seen_els.add(el)
    assert seen_els == set(example_frozenset)


def test_set_iterable__example_set(example_set: set[Any]) -> None:
    seen_els = set()
    for el, filler in set_iterable(example_set):
        assert el in example_set
        assert filler is None
        seen_els.add(el)
    assert seen_els == set(example_set)


def test_col_getter(collection_class_obj: CollectionClass) -> None:
    seen_elements = []
    for idx, it in zip(range(len(collection_class_obj)), collection_class_obj):
        el, flag = col_getter(collection_class_obj, (IterAccessorValue(idx), it))
        assert not flag
        seen_elements.append(el)
    assert set(seen_elements) == set(collection_class_obj)


def test_col_iterable(collection_class_obj: CollectionClass) -> None:
    seen_values = []
    for (null, val), idx in zip(
        col_iterable(collection_class_obj), range(len(collection_class_obj))
    ):
        assert null == IterAccessorValue(idx)
        assert val in collection_class_obj
        seen_values.append(val)
    assert len(seen_values) == len(collection_class_obj)


def test_Accessor__object() -> None:
    assert Accessor.OBJECT.getter is obj_getter
    assert Accessor.OBJECT.setter is obj_setter
    assert Accessor.OBJECT.iterable is obj_iterable


def test_Accessor__sequence() -> None:
    assert Accessor.SEQUENCE.getter is seq_getter
    assert Accessor.SEQUENCE.setter is None
    assert Accessor.SEQUENCE.iterable is seq_iterable


def test_Accessor__mutable_sequence() -> None:
    assert Accessor.MUTABLE_SEQUENCE.getter is seq_getter
    assert Accessor.MUTABLE_SEQUENCE.setter is seq_setter
    assert Accessor.MUTABLE_SEQUENCE.iterable is seq_iterable


def test_Accessor__mapping() -> None:
    assert Accessor.MAPPING.getter is map_getter
    assert Accessor.MAPPING.setter is None
    assert Accessor.MAPPING.iterable is map_iterable


def test_Accessor__mutable_mapping() -> None:
    assert Accessor.MUTABLE_MAPPING.getter is map_getter
    assert Accessor.MUTABLE_MAPPING.setter is map_setter
    assert Accessor.MUTABLE_MAPPING.iterable is map_iterable


def test_Accessor__set() -> None:
    assert Accessor.SET.getter is set_getter
    assert Accessor.SET.setter is None
    assert Accessor.SET.iterable is set_iterable


def test_Accessor__mutable_set() -> None:
    assert Accessor.MUTABLE_SET.getter is set_getter
    assert Accessor.MUTABLE_SET.setter is set_setter
    assert Accessor.MUTABLE_SET.iterable is set_iterable


def test_Accessor__collection() -> None:
    assert Accessor.COLLECTION.getter is col_getter
    assert Accessor.COLLECTION.setter is None
    assert Accessor.COLLECTION.iterable is col_iterable


@pytest.mark.parametrize("child_obj", get_a_few_objects())
@pytest.mark.parametrize("parent_obj", get_a_few_objects())
@pytest.mark.parametrize("accessor_type", list(Accessor))
@pytest.mark.parametrize("accessor_arg", ["attr", 0, (None, 1), 1132234])
def test_Link(accessor_arg: Any, accessor_type: Accessor, parent_obj: Any, child_obj: Any) -> None:
    parent = Node(parent_obj)
    child = Node(parent_obj)
    link = Link(accessor_type, accessor_arg, parent, child)
    link2 = Link(accessor_type, accessor_arg, parent, child)
    assert hash(link) == hash((accessor_type, accessor_arg, parent.id(), child.id()))
    assert link == link2
    assert repr(link) == f"Link(hash={hash(link)})"
    if accessor_type is Accessor.OBJECT:
        assert link.accessor_as_str() == f".{accessor_arg}"
        assert str(link) == repr(link.parent.obj) + f".{accessor_arg}" + "->" + repr(link.child.obj)
    elif accessor_type in [
        Accessor.MAPPING,
        Accessor.MUTABLE_MAPPING,
        Accessor.SEQUENCE,
        Accessor.MUTABLE_SEQUENCE,
    ]:
        assert link.accessor_as_str() == (
            f"['{accessor_arg}']" if isinstance(accessor_arg, str) else f"[{accessor_arg}]"
        )
        assert str(link) == repr(link.parent.obj) + (
            f"['{accessor_arg}']" if isinstance(accessor_arg, str) else f"[{accessor_arg}]"
        ) + "->" + repr(link.child.obj)
    elif accessor_type in [Accessor.SET, Accessor.MUTABLE_SET]:
        val = accessor_arg
        if isinstance(val, str):
            val = f"'{val}'"
        assert link.accessor_as_str() == "{" + f"=={val}" + "}"
        assert str(link) == repr(link.parent.obj) + "{" + f"=={val}" + "}" + "->" + repr(
            link.child.obj
        )
    elif accessor_type is Accessor.COLLECTION:
        assert link.accessor_as_str() == ".__iter__[...]"


def test_link__accessor_as_str_raises() -> None:
    link = Link(Accessor.SEQUENCE, 0, Node((0, 1)), Node(0))
    link.accessor_type = None
    with pytest.raises(TypeError):
        link.accessor_as_str()


def test_link__slots() -> None:
    link = Link(Accessor.SEQUENCE, 0, Node((0, 1)), Node(0))
    with pytest.raises(AttributeError):
        setattr(link, "value", "value")


@pytest.mark.parametrize("obj", get_assorted_objs())
def test_Node(obj: Any) -> None:
    parent_obj = (obj,)
    parent_node = Node(parent_obj)
    node = Node(
        obj, parent_node=parent_node, parent_accessor_type=Accessor.SEQUENCE, parent_accessor_arg=0
    )
    parent_node.child_links.append(node.parent_link)

    assert node.obj is obj
    assert node.parent_link in parent_node.child_links
    assert node.interesting
    assert node.id() == id(obj)

    parent_node_copy = Node(parent_obj)
    node_copy = Node(
        obj,
        parent_node=parent_node_copy,
        parent_accessor_type=Accessor.SEQUENCE,
        parent_accessor_arg=0,
    )
    parent_node_copy.child_links.append(node_copy.parent_link)
    assert node == node_copy
    assert repr(node) == f"Node({repr(obj)}, len(child_links)={len(node.child_links)})"


@pytest.mark.parametrize("obj", get_assorted_objs())
def test_Node_raises(obj: Any) -> None:
    pnode = Node(None)
    with pytest.raises(TypeError):
        Node(obj, parent_node=pnode, parent_accessor_type=None)


@pytest.mark.parametrize("obj", get_assorted_objs())
def test_Node_not_eq_one_parent_None(obj: Any) -> None:
    pnode = Node([1])
    node = Node(
        obj,
        parent_node=pnode,
        parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
        parent_accessor_arg=0,
    )
    other = Node(obj)
    assert node != other


@pytest.mark.parametrize("obj", get_objects_with_attrs())
def test_has_attrs(obj: Any) -> None:
    assert has_attrs(obj)


def test_has_attrs_false_cases() -> None:
    assert not has_attrs(list())
    assert not has_attrs(tuple())
    assert not has_attrs(dict())
    assert not has_attrs(MappingProxyType(dict()))
    assert not has_attrs(set())
    assert not has_attrs(frozenset())


def test_get_object_graph__seq_like_monadic_int_getitem(
    seq_like_monadic_int_getitem: SequenceLike,
) -> None:
    graph = get_object_graph(seq_like_monadic_int_getitem)
    correct_graph = Node(seq_like_monadic_int_getitem)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__seq_like_dyadic_int_getitem(
    seq_like_dyadic_int_getitem: SequenceLike,
) -> None:
    graph = get_object_graph(seq_like_dyadic_int_getitem)
    correct_graph = Node(seq_like_dyadic_int_getitem)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.COLLECTION,
            parent_accessor_arg=IterAccessorValue(idx),
        )
        for jdx, el in enumerate(child_node.obj):
            child_child_node = Node(
                el,
                parent_node=child_node,
                parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
                parent_accessor_arg=jdx,
            )
            child_node.child_links.append(child_child_node.parent_link)
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__seq_like_monadic_str_getitem(
    seq_like_monadic_str_getitem: SequenceLike,
) -> None:
    graph = get_object_graph(seq_like_monadic_str_getitem)
    correct_graph = Node(seq_like_monadic_str_getitem)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.COLLECTION,
            parent_accessor_arg=IterAccessorValue(idx),
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mut_seq_like_monadic_int_getitem(
    mutable_seq_like_monadic_int_getitem: MutableSequenceLike,
) -> None:
    graph = get_object_graph(mutable_seq_like_monadic_int_getitem)
    correct_graph = Node(mutable_seq_like_monadic_int_getitem)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mut_seq_like_dyadic_int_getitem(
    mutable_seq_like_dyadic_int_getitem: MutableSequenceLike,
) -> None:
    graph = get_object_graph(mutable_seq_like_dyadic_int_getitem)
    correct_graph = Node(graph.obj)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.COLLECTION,
            parent_accessor_arg=IterAccessorValue(idx),
        )
        for jdx, el in enumerate(child_node.obj):
            child_child_node = Node(
                el,
                parent_node=child_node,
                parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
                parent_accessor_arg=jdx,
            )
            child_node.child_links.append(child_child_node.parent_link)
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mut_seq_like_monadic_str_getitem(
    mutable_seq_like_monadic_str_getitem: MutableSequenceLike,
) -> None:
    graph = get_object_graph(mutable_seq_like_monadic_str_getitem)
    correct_graph = Node(mutable_seq_like_monadic_str_getitem)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.COLLECTION,
            parent_accessor_arg=IterAccessorValue(idx),
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mapping_like_monadic_getitem(
    mapping_like_monadic_getitem: MappingLike,
) -> None:
    graph = get_object_graph(mapping_like_monadic_getitem)
    correct_graph = Node(mapping_like_monadic_getitem)
    for link in graph.child_links:
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MAPPING,
            parent_accessor_arg=link.accessor_arg,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mapping_like_dyadic_getitem(
    mapping_like_dyadic_getitem: MappingLike,
) -> None:
    graph = get_object_graph(mapping_like_dyadic_getitem)
    correct_graph = Node(mapping_like_dyadic_getitem)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.COLLECTION,
            parent_accessor_arg=IterAccessorValue(idx),
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mut_mapping_like_monadic_getitem(
    mutable_mapping_like_monadic_getitem: MutableMappingLike,
) -> None:
    graph = get_object_graph(mutable_mapping_like_monadic_getitem)
    correct_graph = Node(mutable_mapping_like_monadic_getitem)
    for key, link in zip(mutable_mapping_like_monadic_getitem, graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_MAPPING,
            parent_accessor_arg=key,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mut_mapping_like_dyadic_getitem(
    mutable_mapping_like_dyadic_getitem: MutableMappingLike,
) -> None:
    graph = get_object_graph(mutable_mapping_like_dyadic_getitem)
    correct_graph = Node(mutable_mapping_like_dyadic_getitem)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.COLLECTION,
            parent_accessor_arg=IterAccessorValue(idx),
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__tuple(example_tuple: tuple[Any]) -> None:
    graph = get_object_graph(example_tuple)
    correct_graph = Node(example_tuple)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__list(example_list: list[Any]) -> None:
    graph = get_object_graph(example_list)
    correct_graph = Node(example_list)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__mapping_proxy(example_mapping_proxy: MappingProxyType[str, Any]) -> None:
    graph = get_object_graph(example_mapping_proxy)
    correct_graph = Node(example_mapping_proxy)
    for key, link in zip(example_mapping_proxy, graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MAPPING,
            parent_accessor_arg=key,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__frozendict(example_frozendict: frozendict[str, Any]) -> None:
    graph = get_object_graph(example_frozendict)
    correct_graph = Node(example_frozendict)
    for key, link in zip(example_frozendict, graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MAPPING,
            parent_accessor_arg=key,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__dict(example_dict: dict[str, Any]) -> None:
    graph = get_object_graph(example_dict)
    correct_graph = Node(example_dict)
    for key, link in zip(example_dict, graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_MAPPING,
            parent_accessor_arg=key,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__frozenset(example_frozenset) -> None:
    graph = get_object_graph(example_frozenset)
    correct_graph = Node(example_frozenset)
    for link in graph.child_links:
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.SET,
            parent_accessor_arg=link.child.obj,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__set(example_set: set[Any]) -> None:
    graph = get_object_graph(example_set)
    correct_graph = Node(example_set)
    for link in graph.child_links:
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SET,
            parent_accessor_arg=link.child.obj,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__circular_reference_attrs(circular_attr_reference_obj: A) -> None:
    graph = get_object_graph(circular_attr_reference_obj)
    node_a = Node(circular_attr_reference_obj, parent_node=None)
    node_b = Node(
        circular_attr_reference_obj.b,
        parent_node=node_a,
        parent_accessor_type=Accessor.OBJECT,
        parent_accessor_arg="b",
    )
    node_a_from_b = Node(
        circular_attr_reference_obj,
        parent_node=node_b,
        parent_accessor_type=Accessor.OBJECT,
        parent_accessor_arg="a",
    )
    node_a.child_links = [Link(Accessor.OBJECT, "b", parent=node_a, child=node_b)]
    node_b.child_links = [Link(Accessor.OBJECT, "a", parent=node_b, child=node_a_from_b)]
    assert graph == node_a


@pytest.mark.parametrize("unravel", [False, True])
def test_get_object_graph__strings(some_strings: list[str], unravel: bool) -> None:
    graph = get_object_graph(some_strings, unravel_strings=unravel)
    correct_graph = Node(some_strings)
    for idx, string in enumerate(some_strings):
        child_node = Node(
            string,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
        if unravel and len(string) > 1:
            for jdx, char in enumerate(string):
                grand_child_node = Node(
                    char,
                    parent_node=child_node,
                    parent_accessor_type=Accessor.SEQUENCE,
                    parent_accessor_arg=jdx,
                )
                child_node.child_links.append(grand_child_node.parent_link)
    for child, other_child in zip(graph.child_links, correct_graph.child_links):
        print(child.child, other_child.child)
    assert graph == correct_graph


@pytest.mark.parametrize("unravel", [False, True])
def test_get_object_graph__bytes(some_bytes: list[bytes], unravel: bool) -> None:
    graph = get_object_graph(some_bytes, unravel_strings=unravel)
    correct_graph = Node(some_bytes)
    for idx, bytestring in enumerate(some_bytes):
        child_node = Node(
            bytestring,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
        if unravel:
            for jdx, char in enumerate(bytestring):
                grand_child_node = Node(
                    char,
                    parent_node=child_node,
                    parent_accessor_type=Accessor.SEQUENCE,
                    parent_accessor_arg=jdx,
                )
                child_node.child_links.append(grand_child_node.parent_link)
    assert graph == correct_graph


@pytest.mark.parametrize("unravel", [False, True])
def test_get_object_graph__byte_arrays(some_bytearrays: list[bytearray], unravel: bool) -> None:
    graph = get_object_graph(some_bytearrays, unravel_strings=unravel)
    correct_graph = Node(some_bytearrays)
    for idx, bt_array in enumerate(some_bytearrays):
        child_node = Node(
            bt_array,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
        if unravel:
            for jdx, char in enumerate(bt_array):
                grand_child_node = Node(
                    char,
                    parent_node=child_node,
                    parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
                    parent_accessor_arg=jdx,
                )
                child_node.child_links.append(grand_child_node.parent_link)

    assert graph == correct_graph


def test_get_object_graph__numpy_1darray(numpy_1darray: NDArray) -> None:
    graph = get_object_graph(numpy_1darray)
    correct_graph = Node(numpy_1darray)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_object_graph__numpy_2darray(numpy_2darray: NDArray) -> None:
    graph = get_object_graph(numpy_2darray)
    correct_graph = Node(numpy_2darray)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
        )
        correct_graph.child_links.append(child_node.parent_link)
        for jdx, sublink in enumerate(link.child.child_links):
            grandchild_node = Node(
                sublink.child.obj,
                parent_node=link.child,
                parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
                parent_accessor_arg=jdx,
            )
            child_node.child_links.append(grandchild_node.parent_link)

    assert graph == correct_graph


def test_get_obj_graph__pure_collection(collection_class_obj: CollectionClass) -> None:
    graph = get_object_graph(collection_class_obj)
    correct_graph = Node(collection_class_obj)
    for idx, link in enumerate(graph.child_links):
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.COLLECTION,
            parent_accessor_arg=IterAccessorValue(idx),
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


@pytest.mark.parametrize(
    "obj_filter",
    [
        lambda x: isinstance(x, str),
        lambda x: False,
        lambda x: True,
        lambda x: isinstance(x, Real),
        lambda x: isinstance(x, int),
    ],
)
def test_get_obj_graph__obj_filter(
    example_list: list[Any], obj_filter: Callable[[Any], bool]
) -> None:
    graph = get_object_graph(example_list, obj_filter=obj_filter)
    correct_graph = Node(example_list)
    correct_graph.interesting = obj_filter(correct_graph.obj)
    for idx, link in enumerate(graph.child_links):
        interesting = obj_filter(link.child.obj)
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
            interesting=interesting,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


@pytest.mark.parametrize(
    "accessor_filter",
    [
        lambda x: x == 0,
        lambda x: x < 4,
        lambda x: isinstance(x, Real),
        lambda x: isinstance(x, int),
        lambda x: False,
    ],
)
def test_get_obj_graph__accessor_filter(
    example_list: list[Any], accessor_filter: Callable[[Hashable], bool]
) -> None:
    graph = get_object_graph(example_list, accessor_filter=accessor_filter)
    correct_graph = Node(example_list)
    for idx, link in enumerate(graph.child_links):
        interesting = accessor_filter(link.accessor_arg)
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
            interesting=interesting,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


@pytest.mark.parametrize(
    "accessor_filter",
    [
        lambda x: x == 0,
        lambda x: x < 4,
        lambda x: isinstance(x, Real),
        lambda x: isinstance(x, int),
        lambda x: False,
    ],
)
@pytest.mark.parametrize(
    "obj_filter",
    [
        lambda x: isinstance(x, str),
        lambda x: False,
        lambda x: True,
        lambda x: isinstance(x, Real),
        lambda x: isinstance(x, int),
    ],
)
def test_get_obj_graph__obj_and_accessor_filters(
    example_list: list[Any],
    obj_filter: Callable[[Any], bool],
    accessor_filter: Callable[[Hashable], bool],
) -> None:
    graph = get_object_graph(example_list, obj_filter=obj_filter, accessor_filter=accessor_filter)
    correct_graph = Node(example_list)
    correct_graph.interesting = obj_filter(example_list)
    for idx, link in enumerate(graph.child_links):
        interesting = obj_filter(link.child.obj) and accessor_filter(link.accessor_arg)
        child_node = Node(
            link.child.obj,
            parent_node=correct_graph,
            parent_accessor_type=Accessor.MUTABLE_SEQUENCE,
            parent_accessor_arg=idx,
            interesting=interesting,
        )
        correct_graph.child_links.append(child_node.parent_link)
    assert graph == correct_graph


def test_get_obj_graph__obj_filter_raises(example_list: list[Any]) -> None:
    with pytest.raises(TypeError):
        get_object_graph(example_list, obj_filter=1)


def test_get_obj_graph__accessor_filter_raises(example_list: list[Any]) -> None:
    with pytest.raises(TypeError):
        get_object_graph(example_list, accessor_filter=1)


def test_get_obj_graph__enum_collection(string_enum: StringEnum) -> None:
    graph = get_object_graph(string_enum)
    for child_link in graph.child_links:
        assert child_link.accessor_type is Accessor.OBJECT
