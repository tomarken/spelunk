# Spelunk
Spelunk is a module containing tools for recursively exploring and manipulating python objects.


## Installation
To install spelunk, simply install with `pip install spelunk`. It requires no dependencies besides python. See below for detail on how to install the project for development.

## Quick start
Here is a quick, motivating example.
```python
from spelunk import print_object_graph, hot_swap
from datetime import datetime
import json

obj = {'key0': 0, 'key2': [0, 1, 2, 3], 'datetime': datetime(year=2023, month=1, day=1)}

print_object_graph(obj)
# ROOT -> {'datetime': datetime.datetime(2023, 1, 1, 0, 0), 'key0': 0, ...}
# ROOT['key0'] -> 0
# ROOT['key2'] -> [0, 1, ...]
# ROOT['key2'][0] -> 0
# ROOT['key2'][1] -> 1
# ROOT['key2'][2] -> 2
# ROOT['key2'][3] -> 3
# ROOT['datetime'] -> datetime.datetime(2023, 1, 1, 0, 0)

json_obj = json.dumps(obj)
# Traceback (most recent call last):
# ...
# TypeError: Object of type datetime is not JSON serializable

# cast datetime -> str but preserve the original object
# - we define a filter to flag which items to overwrite (datetime instances)
# - we define an overwrite callable to determine how to overwrite flagged entries
with hot_swap(obj, overwrite_callable=str, obj_filter=lambda x: isinstance(x, datetime)) as new_obj:
    json_obj = json.dumps(new_obj)

print(json_obj)
# {"key0": 0, "key2": [0, 1, 2, 3], "datetime": "2023-01-01 00:00:00"}

print_object_graph(obj)
# ROOT -> {'datetime': datetime.datetime(2023, 1, 1, 0, 0), 'key0': 0, ...}
# ROOT['key0'] -> 0
# ROOT['key2'] -> [0, 1, ...]
# ROOT['key2'][0] -> 0
# ROOT['key2'][1] -> 1
# ROOT['key2'][2] -> 2
# ROOT['key2'][3] -> 3
# ROOT['datetime'] -> datetime.datetime(2023, 1, 1, 0, 0)
```

## Overview
Spelunk contains a handful of public functions that support recursive object exploration and manipulation. These tools are motivated by the lack of a common framework for "crawling" through generic python objects. Spelunk divides all objects in python into three categories: (1) collections, (2) non-collections with attributes, and (3) primitive objects that cannot be recursed into.  
1. An object is a collection if it is an instance of `collections.abc.Collection`. For example, `list, tuple, dict, set, frozenset, numpy.ndarray`. Spelunk will recursively explore each element of the collection. 
    ```python
    from spelunk import print_object_graph
    import numpy as np
    
    collections = {
        'list': [0, 1, 2],
        'frozenset': frozenset({0, 1, 2}),
        'dict': {'0': 0, '1': 1, '2': 2},
        'numpy_array': np.array([0, 1, 2])
    }
    
    print_object_graph(collections)
    # ROOT -> {'dict': {'0': 0, '1': 1, ...}, 'frozenset': frozenset({0, 1, ...}), ...}
    # ROOT['list'] -> [0, 1, ...]
    # ROOT['list'][0] -> 0
    # ROOT['list'][1] -> 1
    # ROOT['list'][2] -> 2
    # ROOT['frozenset'] -> frozenset({0, 1, ...})
    # ROOT['frozenset']{==0} -> 0
    # ROOT['frozenset']{==1} -> 1
    # ROOT['frozenset']{==2} -> 2
    # ROOT['dict'] -> {'0': 0, '1': 1, ...}
    # ROOT['dict']['0'] -> 0
    # ROOT['dict']['1'] -> 1
    # ROOT['dict']['2'] -> 2
    # ROOT['numpy_array'] -> array([0, 1, 2])
    # ROOT['numpy_array'][0] -> 0
    # ROOT['numpy_array'][1] -> 1
    # ROOT['numpy_array'][2] -> 2
    ```
    Spelunk defines the following types of collections: mapping-like, sequence-like, sets, and "other". 

   * Mapping-like: An object is mapping-like if it defines `__getitem__` and `keys`. It is considered mutable if it also defines `__setitem__`. Mapping-like collections are displayed with square brackets and the key value. Note that mapping-like objects do not need to be proper subclasses of `collections.abc.Mapping`.  
   * Sequence-like: An object is sequence-like if it defines `__getitem__` and does not define `keys`. It is considered mutable if it also defines `__setitem__`. Sequence-like collections are displayed with square brackets and the integer index value. Note that sequence-like objects do not need to be proper subclasses of `collections.abc.Sequence` (such as numpy arrays).
   * Sets: An object is a set if it is a proper subclass of `collections.abc.Set`. We do not similarly define set-like interfaces for sets because sets do not define a `__getitem__` or other keying/indexing. We ad hoc use the value itself of the set elements via `__eq__` comparisons to tag each element. This is a very generic requirement that many non-set collections would pass, so we enforce that an object is only considered a set if it subclasses `collections.abc.Set`. There are also far fewer examples of set-like objects in external libraries that don't subclass `collections.abc.Set` than sequence-like objects which do not subclass `collections.abc.Sequence` such as numpy arrays. 
   * Other: An object that is neither mapping-like, sequence-like, nor a subclass of `collections.abc.Set` is considered a generic collection that defines `__iter__` but makes no promises about what the iteration will look like and offers no standard interface for mutability. We recurse into such collections using `__iter__`.
Spelunk displays elements of sequence-like and mapping-like relationships with square brackets and the integer index or the mapping key (e.g. for `[1]`, `ROOT[0] -> 1` and for `{'a': 1}`, `ROOT['a'] -> 1`). Set elements are displayed with curly brackets and "indexed" by `==` comparison (e.g. for `{1, 2}`, `ROOT{==1} -> 1, ROOT{==2} -> 2`). "Other" collections cannot be indexed because we can make no assumptions about the type of information returned in the `__iter__`. 

2. Objects which are not instances of `collections.abc.Collection` but contain attributes. Spelunk will recursively explore each attribute. For example:
    ```python
    class A:
        def __init__(self, val):
            self.val = val
   
    print_object_graph(A(1))
    # ROOT -> <__main__.A object at 0x10cbddc70>
    # ROOT.val -> 1
   ```
   Spelunk can also handle cyclic references. E.g.
    ```python
    class A:
        def __init__(self, val):
            self.val = val
   
    class B:
        pass
   
    b = B()
    a = A(b)
    b.a = a
   
    print_object_graph(a)
    # ROOT -> <__main__.A object at 0x10df70490>
    # ROOT.val -> <__main__.B object at 0x10df70340>
    # ROOT.val.a -> <__main__.A object at 0x10df70490>
   ```
   Spelunk searches for attributes in an object's `__dict__` as well as in `__slots__` of any class in the object's MRO.
3. Objects which are neither (1) nor (2) do not contain any nested structures and are not recursed into further.


### Tests
For contributors, kindly use the `Makefile` to perform formatting, linting, and unit testing 
locally.
1. Run `make style-check` to dry-run `black` formatting changes.
2. Run `make format` to format with `black`.
3. Run `make lint` to lint with `ruff`.
4. Run `make unit-test` to run `pytest` and check the coverage report. 
