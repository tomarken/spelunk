from typing import Hashable, Callable, Any
from types import MappingProxyType
from spelunk.utils import (
    print_object_graph,
    get_elements_of_obj,
    overwrite_elements_of_obj,
    _overwrite_elements_helper,
    hot_swap,
)
from tests.conftest import ComplexNestedStructure, get_hashable_primitive_objects
from pytest import CaptureFixture, MonkeyPatch
import pytest
from numbers import Real
from conftest import silence_logger, CollectionClass, propagate_logs
from spelunk import utils
from spelunk.graph import get_object_graph, AtomicCollections


@pytest.mark.parametrize("unravel_strings", [True, False])
@pytest.mark.parametrize(
    "accessor_filter",
    [
        lambda x: x == 0,
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
@pytest.mark.parametrize("obj", get_hashable_primitive_objects())
def test_print_object_graph(
    obj: Hashable,
    complex_structure_callable: Callable[[Hashable], ComplexNestedStructure],
    capsys: CaptureFixture,
    obj_filter: Callable[[Any], bool],
    accessor_filter: Callable[[Hashable], bool],
    unravel_strings: bool,
) -> None:
    complex_obj = complex_structure_callable(obj)
    print_object_graph(
        complex_obj,
        obj_filter=obj_filter,
        path_filter=accessor_filter,
        unravel_strings=unravel_strings,
    )

    def total_filter(obj: Any, acc: Hashable) -> bool:
        return obj_filter(obj) and accessor_filter(acc)

    captured = capsys.readouterr()
    correct_out = ""

    unraveled = None
    if unravel_strings and isinstance(obj, AtomicCollections):
        unraveled = tuple(f"'{char}'" if isinstance(char, str) else char for char in obj)

    obj = f"'{obj}'" if isinstance(obj, str) else obj

    if obj_filter(complex_obj):
        correct_out = f"ROOT -> {complex_obj}\n"
    if total_filter([obj], "list"):
        correct_out += f"ROOT.list -> [{obj}]\n"
    if total_filter(obj, 0):
        correct_out += f"ROOT.list[0] -> {obj}\n"
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += f"ROOT.list[0][{idx}] -> {char}\n"
    if total_filter((obj,), "tuple"):
        correct_out += f"ROOT.tuple -> ({obj},)\n"
    if total_filter(obj, 0):
        correct_out += f"ROOT.tuple[0] -> {obj}\n"
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += f"ROOT.tuple[0][{idx}] -> {char}\n"
    if total_filter({obj}, "set"):
        correct_out += "ROOT.set -> {" + f"{obj}" + "}\n"
    if total_filter(obj, obj):
        correct_out += "ROOT.set{==" + f"{obj}" + "} -> " + f"{obj}\n"
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += "ROOT.set{==" + f"{obj}" + "}" + f"[{idx}] -> {char}\n"
    if total_filter(frozenset({obj}), "frozenset"):
        correct_out += "ROOT.frozenset -> frozenset({" + f"{obj}" + "})\n"
    if total_filter(obj, obj):
        correct_out += "ROOT.frozenset{==" + f"{obj}" + "} -> " + f"{obj}\n"
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += "ROOT.frozenset{==" + f"{obj}" + "}" + f"[{idx}] -> {char}\n"
    if total_filter({obj: obj}, "mapping"):
        correct_out += "ROOT.mapping -> {" + f"{obj}: {obj}" + "}\n"
    if total_filter(obj, obj):
        correct_out += f"ROOT.mapping[{obj}] -> {obj}\n"
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += f"ROOT.mapping[{obj}][{idx}] -> {char}\n"
    if total_filter(MappingProxyType({obj: obj}), "mappingproxy"):
        correct_out += "ROOT.mapping_prox -> mappingproxy({" + f"{obj}: {obj}" + "})\n"
    if total_filter(obj, obj):
        correct_out += f"ROOT.mapping_prox[{obj}] -> {obj}\n"
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += f"ROOT.mapping_prox[{obj}][{idx}] -> {char}\n"
    if total_filter([{frozenset({obj})}, {obj: MappingProxyType({obj: obj})}], "nested"):
        correct_out += (
            "ROOT.nested -> [{frozenset({"
            + f"{obj}"
            + "})}, {"
            + f"{obj}: mappingproxy("
            + "{"
            + f"{obj}: {obj}"
            + "})}]\n"
        )
    if total_filter({frozenset({obj})}, 0):
        correct_out += "ROOT.nested[0] -> {frozenset({" + f"{obj}" + "})}\n"
    if total_filter(frozenset({obj}), frozenset({obj})):
        correct_out += (
            "ROOT.nested[0]{==frozenset({" + f"{obj}" + "})} -> frozenset({" + f"{obj}" + "})\n"
        )
    if total_filter(obj, obj):
        correct_out += (
            "ROOT.nested[0]{==frozenset({" + f"{obj}" + "})}{==" + f"{obj}" + "} -> " + f"{obj}\n"
        )
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += (
                    "ROOT.nested[0]{==frozenset({"
                    + f"{obj}"
                    + "})}{=="
                    + f"{obj}"
                    + "}"
                    + f"[{idx}] -> {char}\n"
                )
    if total_filter({obj: MappingProxyType({obj: obj})}, 1):
        correct_out += (
            "ROOT.nested[1] -> {" + f"{obj}: mappingproxy(" + "{" + f"{obj}: {obj}" + "})}\n"
        )
    if total_filter(MappingProxyType({obj: obj}), obj):
        correct_out += f"ROOT.nested[1][{obj}] -> mappingproxy(" + "{" + f"{obj}: {obj}" + "})\n"
    if total_filter(obj, obj):
        correct_out += f"ROOT.nested[1][{obj}][{obj}] -> {obj}\n"
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out += f"ROOT.nested[1][{obj}][{obj}][{idx}] -> {char}\n"
    assert captured.out == correct_out
    assert captured.err == ""


@pytest.mark.parametrize("unravel_strings", [True, False])
@pytest.mark.parametrize(
    "accessor_filter",
    [
        lambda x: x == 0,
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
@pytest.mark.parametrize("obj", get_hashable_primitive_objects())
def test_get_elements_of_obj(
    obj: Hashable,
    complex_structure_callable: Callable[[Hashable], ComplexNestedStructure],
    obj_filter: Callable[[Any], bool],
    accessor_filter: Callable[[Hashable], bool],
    unravel_strings: bool,
) -> None:
    complex_obj = complex_structure_callable(obj)

    def total_filter(obj: Any, acc: Hashable) -> bool:
        return obj_filter(obj) and accessor_filter(acc)

    unraveled = None
    if unravel_strings and isinstance(obj, AtomicCollections):
        unraveled = tuple(char for char in obj)

    correct_out = []
    if obj_filter(complex_obj):
        correct_out.append(complex_obj)
    if total_filter([obj], "list"):
        correct_out.append(complex_obj.list)
    if total_filter(obj, 0):
        correct_out.append(complex_obj.list[0])
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    if total_filter((obj,), "tuple"):
        correct_out.append(complex_obj.tuple)
    if total_filter(obj, 0):
        correct_out.append(complex_obj.tuple[0])
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    if total_filter({obj}, "set"):
        correct_out.append(complex_obj.set)
    if total_filter(obj, obj):
        correct_out.append(next(iter(complex_obj.set)))
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    if total_filter(frozenset({obj}), "frozenset"):
        correct_out.append(complex_obj.frozenset)
    if total_filter(obj, obj):
        correct_out.append(next(iter(complex_obj.frozenset)))
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    if total_filter({obj: obj}, "mapping"):
        correct_out.append(complex_obj.mapping)
    if total_filter(obj, obj):
        correct_out.append(obj)
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    if total_filter(MappingProxyType({obj: obj}), "mappingproxy"):
        correct_out.append(complex_obj.mapping_prox)
    if total_filter(obj, obj):
        correct_out.append(obj)
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    if total_filter([{frozenset({obj})}, {obj: MappingProxyType({obj: obj})}], "nested"):
        correct_out.append(complex_obj.nested)
    if total_filter({frozenset({obj})}, 0):
        correct_out.append(complex_obj.nested[0])
    if total_filter(frozenset({obj}), frozenset({obj})):
        correct_out.append(next(iter(complex_obj.nested[0])))
    if total_filter(obj, obj):
        correct_out.append(next(iter(next(iter(complex_obj.nested[0])))))
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    if total_filter({obj: MappingProxyType({obj: obj})}, 1):
        correct_out.append(complex_obj.nested[1])
    if total_filter(MappingProxyType({obj: obj}), obj):
        correct_out.append(complex_obj.nested[1][obj])
    if total_filter(obj, obj):
        correct_out.append(complex_obj.nested[1][obj][obj])
    if unraveled is not None:
        for idx, char in enumerate(unraveled):
            if total_filter(char, idx):
                correct_out.append(char)
    assert correct_out == get_elements_of_obj(
        complex_obj,
        obj_filter=obj_filter,
        path_filter=accessor_filter,
        unravel_strings=unravel_strings,
    )


@pytest.mark.parametrize("unravel_strings", [True, False])
@pytest.mark.parametrize(
    "accessor_filter",
    [
        lambda x: x == 0,
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
@pytest.mark.parametrize("overwrite", get_hashable_primitive_objects())
@pytest.mark.parametrize("obj", get_hashable_primitive_objects())
def test_overwrite_elements_of_obj(
    obj: Hashable,
    overwrite: Hashable,
    complex_structure_callable: Callable[[Hashable], ComplexNestedStructure],
    obj_filter: Callable[[Any], bool],
    accessor_filter: Callable[[Hashable], bool],
    unravel_strings: bool,
) -> None:
    complex_obj = complex_structure_callable(obj)

    def total_filter(obj: Any, acc: Hashable) -> bool:
        return obj_filter(obj) and accessor_filter(acc)

    with silence_logger(utils.__name__):
        overwrite_elements_of_obj(
            complex_obj,
            overwrite_callable=lambda x: overwrite,
            obj_filter=obj_filter,
            path_filter=accessor_filter,
            unravel_strings=unravel_strings,
        )
    if total_filter([obj], "list"):
        assert complex_obj.list == overwrite
    else:
        if total_filter(obj, 0):
            assert complex_obj.list[0] == overwrite
    if total_filter((obj,), "tuple"):
        assert complex_obj.tuple == overwrite
    if total_filter({obj}, "set"):
        assert complex_obj.set == overwrite
    else:
        if total_filter(obj, obj):
            assert next(iter(complex_obj.set)) == overwrite
    if total_filter(frozenset({obj}), "frozenset"):
        assert complex_obj.frozenset == overwrite
    if total_filter({obj: obj}, "mapping"):
        assert complex_obj.mapping == overwrite
    else:
        if total_filter(obj, obj):
            assert complex_obj.mapping[obj] == overwrite
    if total_filter(MappingProxyType({obj: obj}), "mappingproxy"):
        assert complex_obj.mapping_prox == overwrite
    if total_filter([{frozenset({obj})}, {obj: MappingProxyType({obj: obj})}], "nested"):
        assert complex_obj.nested == overwrite
    else:
        if total_filter({frozenset({obj})}, 0):
            assert complex_obj.nested[0] == overwrite
        elif total_filter(frozenset({obj}), frozenset({obj})):
            assert next(iter(complex_obj.nested[0])) == overwrite
        if total_filter({obj: MappingProxyType({obj: obj})}, 1):
            assert complex_obj.nested[1] == overwrite
        elif total_filter(MappingProxyType({obj: obj}), obj):
            assert complex_obj.nested[1][obj] == overwrite


def test_overwrite_elements_helper__continue_on_collection(
    collection_class_obj: CollectionClass,
) -> None:
    graph = get_object_graph(collection_class_obj)
    _overwrite_elements_helper(graph, overwrite_callable=lambda x: 1)


@pytest.mark.parametrize("raise_on_exception", [True, False])
@pytest.mark.parametrize("silent", [True, False])
def test_overwrite_elements_helper__exception_on_overwrite(
    silent: bool, raise_on_exception: bool, capsys: CaptureFixture, monkeypatch: MonkeyPatch
) -> None:
    with propagate_logs(logger_name=utils.__name__):
        graph = get_object_graph([1])
        monkeypatch.setattr(graph.child_links[0].accessor_type, "setter", lambda x, y, z: 1 / 0)
        if raise_on_exception:
            with pytest.raises(ZeroDivisionError):
                with silence_logger(logger_name=utils.__name__):
                    _overwrite_elements_helper(
                        graph,
                        overwrite_callable=lambda x: True,
                        silent=silent,
                        raise_on_exception=True,
                    )
        else:
            _overwrite_elements_helper(
                graph, overwrite_callable=lambda x: True, silent=silent, raise_on_exception=False
            )
            captured = capsys.readouterr()
            if silent:
                assert not captured.err
            else:
                assert "ZeroDivisionError" in captured.err


def test_overwrite_elements_helper__raise_on_no_setter(monkeypatch: MonkeyPatch) -> None:
    graph = get_object_graph([1])
    monkeypatch.setattr(graph.child_links[0].accessor_type, "setter", None)
    with pytest.raises(ValueError):
        _overwrite_elements_helper(graph, overwrite_callable=lambda x: [], raise_on_exception=True)


@pytest.mark.parametrize("unravel_strings", [True, False])
@pytest.mark.parametrize(
    "accessor_filter",
    [
        lambda x: x == 0,
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
@pytest.mark.parametrize("overwrite", get_hashable_primitive_objects())
@pytest.mark.parametrize("obj", get_hashable_primitive_objects())
def test_hot_swap(
    obj: Hashable,
    overwrite: Hashable,
    complex_structure_callable: Callable[[Hashable], ComplexNestedStructure],
    obj_filter: Callable[[Any], bool],
    accessor_filter: Callable[[Hashable], bool],
    unravel_strings: bool,
) -> None:
    complex_obj = complex_structure_callable(obj)

    def total_filter(obj: Any, acc: Hashable) -> bool:
        return obj_filter(obj) and accessor_filter(acc)

    with silence_logger(utils.__name__):
        with hot_swap(
            complex_obj,
            overwrite_callable=lambda x: overwrite,
            obj_filter=obj_filter,
            path_filter=accessor_filter,
            unravel_strings=unravel_strings,
        ) as new_obj:
            if total_filter([obj], "list"):
                assert new_obj.list == overwrite
            else:
                if total_filter(obj, 0):
                    assert new_obj.list[0] == overwrite
            if total_filter((obj,), "tuple"):
                assert new_obj.tuple == overwrite
            if total_filter({obj}, "set"):
                assert complex_obj.set == overwrite
            else:
                if total_filter(obj, obj):
                    assert next(iter(new_obj.set)) == overwrite
            if total_filter(frozenset({obj}), "frozenset"):
                assert new_obj.frozenset == overwrite
            if total_filter({obj: obj}, "mapping"):
                assert new_obj.mapping == overwrite
            else:
                if total_filter(obj, obj):
                    assert new_obj.mapping[obj] == overwrite
            if total_filter(MappingProxyType({obj: obj}), "mappingproxy"):
                assert new_obj.mapping_prox == overwrite
            if total_filter([{frozenset({obj})}, {obj: MappingProxyType({obj: obj})}], "nested"):
                assert new_obj.nested == overwrite
            else:
                if total_filter({frozenset({obj})}, 0):
                    assert new_obj.nested[0] == overwrite
                elif total_filter(frozenset({obj}), frozenset({obj})):
                    assert next(iter(new_obj.nested[0])) == overwrite
                if total_filter({obj: MappingProxyType({obj: obj})}, 1):
                    assert new_obj.nested[1] == overwrite
                elif total_filter(MappingProxyType({obj: obj}), obj):
                    assert new_obj.nested[1][obj] == overwrite

    new_complex_obj = complex_structure_callable(obj)
    assert complex_obj.list == new_complex_obj.list
    assert complex_obj.tuple == new_complex_obj.tuple
    assert complex_obj.set == new_complex_obj.set
    assert complex_obj.frozenset == new_complex_obj.frozenset
    assert complex_obj.mapping == new_complex_obj.mapping
    assert complex_obj.mapping_prox == new_complex_obj.mapping_prox
    assert complex_obj.nested == complex_obj.nested


def test_hot_swap__raise_on_degenerate_set_overwrite(monkeypatch: MonkeyPatch) -> None:
    obj = {1, 2}
    with pytest.raises(ValueError):
        with hot_swap(obj, overwrite_callable=lambda x: 2, obj_filter=lambda x: x == 1):
            pass
