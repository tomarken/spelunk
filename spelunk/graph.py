"""Module containing graph-based recursive object exploration classes and functions."""
import dataclasses
import reprlib
from collections.abc import (
    Collection,
    Sequence,
    MutableSequence,
    Mapping,
    MutableMapping,
    Set,
    MutableSet,
    ByteString,
)
from enum import Enum
from typing import (
    Optional,
    Generator,
    Hashable,
    Callable,
    Any,
    Iterable,
    Protocol,
    runtime_checkable,
    Literal,
)
from spelunk.logging import get_logger

logger = get_logger(__name__)

PrettyRepr = reprlib.Repr()
PrettyRepr.maxstring = 100
PrettyRepr.maxother = 100
PrettyRepr.maxlist = 2
PrettyRepr.maxdict = 2
PrettyRepr.maxset = 2
PrettyRepr.maxfrozenset = 2
PrettyRepr.maxtuple = 2
PrettyRepr.maxarray = 2
PrettyRepr.maxdeque = 2

# These types are collections that are treated as a single unit unless explicitly overridden
AtomicCollections = (str, ByteString)

# Objects that may be counted as collections but should be access with attr lookup not indexing
ObjectCollections = (Enum,)

AccessorErrors = (LookupError, KeyError, TypeError, StopIteration)


@runtime_checkable
class SequenceLike(Collection, Protocol):
    """Interface that implements a minimal getter like Sequence."""

    def __getitem__(self, key: int) -> Any:
        """Get sequence element using a single integer key."""


@runtime_checkable
class MutableSequenceLike(SequenceLike, Protocol):
    """Interface that implements a minimal getter and setter like MutableSequence."""

    def __setitem__(self, key: int, value: Any) -> None:
        """Set a sequence element using a single integer key and replacement  accessor_arg."""


@runtime_checkable
class MappingLike(Collection, Protocol):
    """Interface that implements a minimal getter and keys methods like Mapping."""

    def keys(self) -> Iterable[Hashable]:
        """Return mapping keys."""

    def __getitem__(self, key: Hashable) -> Any:
        """Get a mapping element using a single hashable key."""


@runtime_checkable
class MutableMappingLike(MappingLike, Protocol):
    """Interface that implements a minimal getter, keys, setter methods like MutableMapping."""

    def __setitem__(self, key: Hashable, value: Any) -> None:
        """Set a mapping element using a single hashable key and replacement accessor_arg."""


@dataclasses.dataclass(frozen=True)
class IterAccessorValue:
    """
    Accessor value dummy object for iteration.

    Objects that are collections but not any of abc.Sequence, abc.Mapping,
    or abc.Set don't have accessors and must be iterated through directly.
    This is used below when building Links so that we can assign a unique value
    to each element of the iterator.
    """

    id: int


def obj_getter(obj: Any, key: str) -> Any:
    """Get the attribute of an object and use None as a fallback."""
    try:
        return getattr(obj, key)
    except AttributeError:
        logger.warning(f"Failed to get attribute {key} of {obj}, returning None as fallback.")
        return None


def obj_setter(obj: Any, key: str, value: Any) -> None:
    """Set the attribute of an object."""
    setattr(obj, key, value)


def obj_iterable(obj: Any) -> Iterable[str]:
    """Return the contents of obj.__dict__ and cls.__slots__ for each cls in the MRO."""
    return _collect_all_attrs(obj)


"""The following accessors define fallback iterators in case of failure."""


def seq_getter(obj: SequenceLike, key: tuple[int, Any]) -> tuple[Any, bool]:
    """
    Get the sequence's value located at the accessor's key.

    Return the element from iteration upon failure. Return the flag
    True if success and False if fallback used.
    """
    idx, elem = key
    try:
        return obj.__getitem__(idx), True
    except AccessorErrors:
        return elem, False


def seq_setter(obj: MutableSequenceLike, key: int, value: Any) -> None:
    """Set the accessor_arg of a sequence at the index given by key."""
    return obj.__setitem__(key, value)


def seq_iterable(obj: SequenceLike) -> Iterable[tuple[int, Any]]:
    """
    Return an enumeration of the object.

    When getting from the sequence, the index from the enumeration
    is used and if failure is encountered, the value of the element
    is returned from an iterator instead.
    """
    return enumerate(obj)


def map_getter(obj: MappingLike, key: tuple[Hashable, Any]) -> tuple[Any, bool]:
    """
    Get the mappings's value located at the accessor's key.

    Return the element from iteration upon failure. Return the flag
    True if success and False if fallback used.
    """
    k, elem = key
    try:
        return obj.__getitem__(k), True
    except AccessorErrors:
        return elem, False


def map_setter(obj: MutableMappingLike, key: Hashable, value: Any) -> None:
    """Set the value associated with the key of a mapping."""
    obj.__setitem__(key, value)


def map_iterable(obj: MappingLike) -> Iterable[tuple[Hashable, Hashable]]:
    """
    Return a zipped iterable containing the mapping keys and the iterable itself.

    When getting from the mapping, the key from the enumeration
    is used and if failure is encountered, the key of the mapping
    iterable is returned from an iterator instead.
    """
    return zip(obj.keys(), obj)


def set_getter(obj: Set, key: tuple[Hashable, None]) -> tuple[Hashable, Literal[True]]:
    """
    Get the set's element.

    Because sets have no accessors, we can only get the elements through
    direct iteration and inspection. We return True if success and if
    failure we raise.
    """
    try:
        return next(el for el in obj if el == key[0]), True
    except AccessorErrors as e:
        raise ValueError(
            f"Attempted to access element {key[0]} of set, but no "
            f"object matching this element is found in the set."
        ) from e


def set_setter(obj: MutableSet, key: Hashable, value: Hashable) -> None:
    """
    Overwrite the element of a set with a particular key with a new value.

    The key is the element being overwritten and the value is its replacement.

    If inserting a new value into the set would change cardinality (by already
    existing in set), this will be irreversible. To keep this general, this
    behavior is not flagged, but anything calling this setter should be aware
    and guard accordingly.

    Reversible (safe) ex:
    set_setter({1, 2, 3}, 1, 4) -> {4, 2, 3}
    set_setter({4, 2, 3}, 4, 1) -> {1, 2, 3}

    Irreversible (dangerous) ex:
    set_setter({1, 2, 3}, 1, 2) -> {2, 3}
    set_setter({2, 3}, 2, 1) -> {1, 3}
    """
    # if we're overwriting an object with itself nothing to do
    if key == value:
        return

    try:
        obj.remove(key)
    except AccessorErrors as e:
        raise ValueError(f"Could not locate element {key} in set.") from e

    obj.add(value)


def set_iterable(obj: Set) -> Iterable[tuple[Hashable, None]]:
    """
    Return an iterable with each element of the set and a dummy None value.

    The None value is used because other accessors for sequence and mappings
    define a fallback value when using accessors fails. However, for sets,
    we must iterate to begin with so there's no fallback and this is a dummy
    value.
    """
    return ((el, None) for el in obj)


def col_getter(obj: Collection, key: tuple[IterAccessorValue, Any]) -> tuple[Any, Literal[False]]:
    """Get an item from a collection's iter using the element itself."""
    return key[1], False


def col_iterable(obj: Collection) -> Iterable[tuple[IterAccessorValue, Any]]:
    """
    Return an iterable with (None, idx) zipped with elements.

    We indicate None to show that there's no real key to be used for
    indexing, but we increment with an integer to allow generating unique
    Link hashes with objects that have the same id.
    """
    return zip((IterAccessorValue(idx) for idx in range(len(obj))), obj)


class Accessor(Enum):
    """
    Enumeration describing the accessors of one object in relation to a descendent.

    E.g. for A.b = "B", the accessor enum member is OBJECT. For [1] the accessor
    enum member is MUTABLE_SEQUENCE. The getter, setter, and iterables which
    included fallbacks are attributes:
    e.g. MUTABLE_SEQUENCE.getter([1], (0, 1)) -> 1, True
    """

    OBJECT = obj_getter, obj_setter, obj_iterable
    SEQUENCE = seq_getter, None, seq_iterable
    MUTABLE_SEQUENCE = seq_getter, seq_setter, seq_iterable
    MAPPING = map_getter, None, map_iterable
    MUTABLE_MAPPING = map_getter, map_setter, map_iterable
    SET = set_getter, None, set_iterable
    MUTABLE_SET = set_getter, set_setter, set_iterable
    COLLECTION = col_getter, None, col_iterable

    def __init__(
        self,
        getter: Callable[[Any, Any], Any],
        setter: Callable[[Any, Hashable, Any], None],
        iterable: Callable[[Any], Iterable[Any]],
    ) -> None:
        self.getter = getter
        self.setter = setter
        self.iterable = iterable


class Link:
    """
    Relationship that connects one object to another.

    The field value is the argument used during accessing. E.g. for a = [1] the
    Accessor enum member between `a` and `1` is MUTABLE_SEQUENCE and the value
    is the index 0.
    """

    __slots__ = "accessor_type", "accessor_arg", "parent", "child"

    def __init__(
        self, accessor_type: Accessor, accessor_arg: Hashable, parent: "Node", child: "Node"
    ) -> None:
        self.accessor_type = accessor_type
        self.accessor_arg = accessor_arg
        self.parent = parent
        self.child = child

    def __hash__(self) -> int:
        """
        Hash the link based on the Accessor enum member, accessor_arg, and the parent and child ids.
        This defines a unique value because for any two objects that are linked by
        either an attribute or collection relationship, there's no way for the same
        Accessor enum member and accessor arg (e.g. the attribute name or the sequence index) to
        exist multiply between the same child and parent objects. Note that it is possible to have
        pseudo-unique parents/children with the same ids for str and bytes due to
        interning. E.g. `'ab' is 'ab'` in CPython even though we'd like to treat these as unique
        objects from the perspective of e.g. ['ab', 'ab'].
        """
        return hash((self.accessor_type, self.accessor_arg, self.parent.id(), self.child.id()))

    def __eq__(self, other: "Link") -> bool:
        """Compare equality with another Link in a way consistent with __hash__."""
        if not isinstance(other, Link):
            return NotImplemented

        accessors_eq = self.accessor_type is other.accessor_type
        values_eq = self.accessor_arg == other.accessor_arg
        parent_eq = self.parent.id() == other.parent.id()
        child_eq = self.child.id() == other.child.id()
        interesting_eq = (
            self.parent.interesting == other.parent.interesting
            and self.child.interesting == other.child.interesting
        )
        return accessors_eq and values_eq and parent_eq and child_eq and interesting_eq

    def accessor_as_str(self) -> str:
        """Print a string representation of the relationship."""
        accessor = self.accessor_type
        value = self.accessor_arg
        if accessor is Accessor.OBJECT:
            return f".{value}"

        if isinstance(value, str):
            value = f"'{value}'"
        if accessor in [
            Accessor.MAPPING,
            Accessor.MUTABLE_MAPPING,
            Accessor.SEQUENCE,
            Accessor.MUTABLE_SEQUENCE,
        ]:
            return f"[{value}]"
        elif accessor in [Accessor.SET, Accessor.MUTABLE_SET]:
            return "{==" + f"{value}" + "}"
        elif accessor is Accessor.COLLECTION:
            return ".__iter__[...]"
        else:
            raise TypeError(f"Accessor must be a member of {Accessor}.")

    def __str__(self) -> str:
        """Print the parent object and accessor_type in relationship to the child."""
        return repr(self.parent.obj) + self.accessor_as_str() + "->" + repr(self.child.obj)

    def __repr__(self) -> str:
        """Print the class name and hash."""
        return self.__class__.__name__ + f"(hash={hash(self)})"


class Node:
    """Object node class that can form a graph with links to other related nodes."""

    __slots__ = "obj", "parent_link", "child_links", "interesting"

    def __init__(
        self,
        obj: Any,
        parent_node: Optional["Node"] = None,
        parent_accessor_type: Optional[Accessor] = None,
        parent_accessor_arg: Optional[Hashable] = None,
        child_links: Optional[list[Link]] = None,
        interesting: bool = True,
    ) -> None:
        self.obj = obj
        if child_links is None:
            child_links = []
        self.child_links = child_links
        self.interesting = interesting
        if parent_node is None:
            self.parent_link = None
        elif parent_accessor_type not in list(Accessor):
            raise TypeError(
                f"parent_accessor_type must be a member of {Accessor} if parent_node is not None."
            )
        else:
            self.parent_link = Link(parent_accessor_type, parent_accessor_arg, parent_node, self)

    def id(self) -> int:
        """Get the id of the node's object."""
        return id(self.obj)

    def __eq__(self, other: "Node") -> bool:
        """This checks"""
        child_nodes = [child_link.child for child_link in self.child_links]
        other_child_nodes = [child_link.child for child_link in other.child_links]
        return self.single_node_equal(other) and child_nodes == other_child_nodes

    def single_node_equal(self, other: "Node") -> bool:
        """
        Check if nodes equivalent without recursion below.

        This checks if the parent links and child links are equivalent. Note that
        checking the link equality ensures that the parent and child ids are the same
        so in total this method verifies:
        - self.parent_link == other.parent_link
          - same accessor enum member
          - same accessor arg
          - same parent node id
          - same self node id
          - same interesting bool
        - self.child_links == other.child_links
          - same accessor enum member
          - same accesor args
          - same self/other node id
          - same child node ids
          - same interesting bools
          - same insertion order for children
        """

        same_parent_link = self.parent_link == other.parent_link
        if not same_parent_link:
            return False
        return self.child_links == other.child_links

    def __repr__(self) -> str:
        return f"Node({repr(self.obj)}, len(child_links)={len(self.child_links)})"


def has_attrs(obj: Any) -> bool:
    """Determine if an object has the potential to contain attributes."""

    return hasattr(obj, "__dict__") or hasattr(obj, "__slots__")


def get_object_graph(
    root_obj: Any,
    obj_filter: Optional[Callable[[Any], bool]] = None,
    accessor_filter: Optional[Callable[[Hashable], bool]] = None,
    unravel_strings: bool = False,
) -> Node:
    """
    Get the graph that corresponds to an object's dependency relationsips.

    :param root_obj: The root object in the graph (starting point).
    :param obj_filter: A callable to test on the object of a node to determine if the node is
                       "interesting".
    :param accessor_filter: Test the key/index/attr name at the parent link to determine if an
                            object is interesting.
    """
    root_node = Node(root_obj)
    _get_obj_graph_helper(
        current_node=root_node,
        obj_filter=obj_filter,
        accessor_filter=accessor_filter,
        link_cache={},
        unravel_strings=unravel_strings,
    )
    return root_node


def _get_obj_graph_helper(
    current_node: Node,
    obj_filter: Optional[Callable[[Any], bool]],
    accessor_filter: Optional[Callable[[Hashable], bool]],
    link_cache: dict[int, bool],
    unravel_strings: bool = False,
) -> None:
    """Recursive function that searches for nested objects within an object."""

    # Determine if current node and accessor_type  accessor_arg pass filters
    obj_test = True
    accessor_test = True

    if obj_filter is not None:
        if not callable(obj_filter):
            raise TypeError("obj_filter must be None or a callable.")
        obj_test = obj_filter(current_node.obj)

    if accessor_filter is not None:
        if not callable(accessor_filter):
            raise TypeError("accessor_filter must be None or a callable.")
        if current_node.parent_link is None:
            accessor_test = True
        else:
            accessor_value = current_node.parent_link.accessor_arg
            accessor_test = accessor_filter(accessor_value)

    if not (obj_test and accessor_test):
        current_node.interesting = False

    accessor = _get_accessor(current_node)

    # current node has no attributes and is not a collection
    if accessor is None:
        return

    if not isinstance(current_node.obj, ObjectCollections):
        # prevent recursing into collections that are usually treated like atomic units
        if isinstance(current_node.obj, AtomicCollections) and not unravel_strings:
            return

        # prevent infinite loop when recursing through string of length 1 (during unravel)
        if isinstance(current_node.obj, str) and len(current_node.obj) == 1:
            return

    for link in _gen_child_links_object(current_node, accessor):
        # prevent recursion if we've seen the link before, this prevents getting
        # stuck on cycles with circularly referenced objects
        if link in link_cache and not (
            isinstance(link.parent.obj, AtomicCollections) and unravel_strings
        ):
            return
        link_cache[link] = None  # dummy accessor_arg
        current_node.child_links.append(link)
        _get_obj_graph_helper(
            link.child,
            obj_filter=obj_filter,
            accessor_filter=accessor_filter,
            link_cache=link_cache,
            unravel_strings=unravel_strings,
        )


def _get_accessor(node: Node) -> Optional[Accessor]:
    # Getting protocol attrs is very slow, so we first test to see if something is a member of
    # Collection, if not return. Then we prioritize testing for proper collections objects. Then
    # we fall back to test the protocols so that we avoid hitting these checks for the majority
    # of objects that will be proper collections.
    if isinstance(node.obj, Collection) and not isinstance(node.obj, ObjectCollections):
        if isinstance(node.obj, Sequence):
            if isinstance(node.obj, MutableSequence):
                return Accessor.MUTABLE_SEQUENCE
            return Accessor.SEQUENCE
        if isinstance(node.obj, Mapping):
            if isinstance(node.obj, MutableMapping):
                return Accessor.MUTABLE_MAPPING
            return Accessor.MAPPING
        if isinstance(node.obj, Set):
            if isinstance(node.obj, MutableSet):
                return Accessor.MUTABLE_SET
            return Accessor.SET
        if isinstance(node.obj, MappingLike):
            if isinstance(node.obj, MutableMappingLike):
                return Accessor.MUTABLE_MAPPING
            return Accessor.MAPPING
        if isinstance(node.obj, SequenceLike):
            if isinstance(node.obj, MutableSequenceLike):
                return Accessor.MUTABLE_SEQUENCE
            return Accessor.SEQUENCE
        return Accessor.COLLECTION
    # Prioritize object over collection. This only comes up with metaclasses like Enums which
    # can both have __dict__ as well as be instances of str.

    if has_attrs(node.obj):
        return Accessor.OBJECT

    return None


def _collect_all_attrs(obj: Any) -> list[str]:
    """Collect all entries of __dict__ from obj and of __slots__ from MRO."""
    attrs = []
    if hasattr(obj, "__dict__"):
        dict_attrs = getattr(obj, "__dict__")
        for a in dict_attrs:
            if a not in attrs:
                attrs.append(a)
    for cls in obj.__class__.__mro__:
        if hasattr(cls, "__slots__"):
            slots = getattr(cls, "__slots__")
            if isinstance(slots, str):
                if slots not in attrs:
                    attrs.append(slots)
            else:
                for a in slots:
                    if a not in attrs:
                        attrs.append(a)
    return attrs


def _gen_child_links_object(node: Node, accessor: Accessor) -> Generator[Link, None, None]:
    """Return a generator that yields the child links from a given node."""
    if accessor is Accessor.OBJECT:
        for key in accessor.iterable(node.obj):
            child_obj = accessor.getter(node.obj, key)
            child_node = Node(
                child_obj, parent_node=node, parent_accessor_type=accessor, parent_accessor_arg=key
            )
            yield child_node.parent_link
        return

    for idx, (key, fallback_iter) in enumerate(accessor.iterable(node.obj)):
        child_obj, no_fallback_flag = accessor.getter(node.obj, (key, fallback_iter))
        if not no_fallback_flag:
            accessor = accessor.COLLECTION
            key = IterAccessorValue(idx)
        child_node = Node(
            child_obj, parent_node=node, parent_accessor_type=accessor, parent_accessor_arg=key
        )
        yield child_node.parent_link
