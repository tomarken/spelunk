# Spelunk
Spelunk is a module containing tools for recursively exploring and manipulating python objects.


## Installation
To install spelunk, simply install with `pip install spelunk`. See below for details on how to install 
the project for development.


## Overview
This section will review the major utilities of spelunk.
### 1. Printing an object's tree
```python
from spelunk import print_obj_tree

class A:
   def __init__(self):
      self.val = 'val'
    
   def __repr__(self):
      return f'A(val={self.val})'
 
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}

print_obj_tree(root_obj=obj)
# ROOT -> {'key': [1, (2.0,), ...]}
# ROOT['key'] -> [1, (2.0,), ...]
# ROOT['key'][0] -> 1
# ROOT['key'][1] -> (2.0,)
# ROOT['key'][1][0] -> 2.0
# ROOT['key'][2] -> {3}
# ROOT['key'][2]{id=4315240816} -> 3
# ROOT['key'][3] -> frozenset({4})
# ROOT['key'][3]{id=4315240848} -> 4
# ROOT['key'][4] -> {'subkey': [(1,), A(val=val)]}
# ROOT['key'][4]['subkey'] -> [(1,), A(val=val)]
# ROOT['key'][4]['subkey'][0] -> (1,)
# ROOT['key'][4]['subkey'][0][0] -> 1
# ROOT['key'][4]['subkey'][1] -> A(val=val)
# ROOT['key'][4]['subkey'][1].val -> 'val'
```
* The root object is referred to as `ROOT`. 
* Attributes are denoted with `ROOT.attr`.
* Keys from mappings are denoted with `ROOT['key']`.
* Indices from sequences are denoted with `ROOT[idx]`.
* Elements of sets and frozensets are indicated by their id in memory with `ROOT{id=10012}`. 
* Elements of a `ValuesView` are indicated by their id in memory with `ROOT{ValuesView_id=10012}`. 

Note that `ValuesView` may seem odd here. This is included separately because this is a unique subclass
of `Collection` not captured by `Mapping`, `Sequence`, or `Set`. In contrast, both `KeysView` and 
`ItemsView` are subclasses of `Set`.

The previous notations will be recursively chained together. For example, the path 
`ROOT['key'][2]` indicates that in order to access the corresponding object `{3}`, we would 
use `root_obj['key'][2]`. For sets it is also possible by iterating and inspecting by id. To
access `4` via `ROOT['key'][3]{id=4315240848}` we would iterate through `root_obj['key'][3]` until 
we found a matching id:
  ```python
for elem in root_obj['key'][3]:
    if id(elem) == 4315240848:
      break
      
print(elem)
# 4
  ```

Fortunately, for accessing and manipulating elements of `root_obj`, there are additional 
tools that avoid needing to tediously address and iterate (see below).


Before moving on, it's worth pointing out you can also select by element and/or by "path name" by 
supplying callables `element_test` and `path_test` that determine whether an element or path is 
interesting (by default they always return `True`). `element_test` operates on the element itself and 
returns a bool. `path_test` operates on the most recent branch of the current path and returns a bool. For 
example, if you're at `root_obj['key']` with path `ROOT['key']`, it would pass `key` to the input of
`path_test` and `[1, (2,), ...]` to `element_test`.

  ```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}
print_obj_tree(root_obj=obj, element_test=lambda x: isinstance(x, float))

# ROOT['key'][1][0] -> 2.0
  ```
  ```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}
print_obj_tree(root_obj=obj, path_test=lambda x: x=='subkey')  

# ROOT['key'][4]['subkey'] -> [(1,), A(val=val)]
```

### 2. Getting the values and paths of objects
To get a dictionary of objects filtered by element/path and keyed by full path string, 
use `get_elements`:
```python
from spelunk import get_elements
  
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}
get_elements(root_obj=obj, element_test=lambda x: isinstance(x, frozenset))

# {"ROOT['key'][3]": frozenset({4})}

get_elements(root_obj=obj, element_test=lambda x: isinstance(x, dict))
# {
#   'ROOT': {'key': [1, (2.0,), {3}, frozenset({4}), {'subkey': [(1,), A(val=val)]}]},
#   "ROOT['key'][4]": {'subkey': [(1,), A(val=val)]}
# }
```

### 3. Overwriting elements 
To overwrite elements use `overwrite_elements`:
```python
from spelunk import overwrite_elements

obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}
overwrite_elements(
    root_obj=obj, 
    overwrite_value=None, 
    element_test=lambda x: isinstance(x, tuple)
)
print(obj)

# {'key': [1, None, {3}, frozenset({4}), {'subkey': [None, A(val=val)]}]}
```
Objects can also be overwritten using a callable `overwrite_func`. If `overwrite_func` is not `None` and 
callable, `overwrite_value` will be ignored.
```python
from spelunk import overwrite_elements

obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}
overwrite_elements(
    root_obj=obj, 
    overwrite_func=str, 
    element_test=lambda x: isinstance(x, tuple)
)
print(obj)

# {'key': [1, '(2.0,)', {3}, frozenset({4}), {'subkey': ['(1,)', A(val=val)]}]}
```
Overwriting will fail if attempting to overwrite an immutable container.
```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}
overwrite_elements(
    root_obj=obj, 
    overwrite_value=None, 
    element_test=lambda x: isinstance(x, int)
)
print(obj)

# Failed to overwrite 4 at ROOT['key'][3]{id=4315240848}.
# Traceback (most recent call last):
# ...
# TypeError: Cannot overwrite immutable collections.
```
Error messages can be silenced with `silent=True` and exceptions can be dismissed with 
`raise_on_exception=False` kwargs. Be aware that it may be difficult to determine which objects 
failed with these options.
```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,), A()]}]}
overwrite_elements(
    root_obj=obj, 
    overwrite_value=None, 
    element_test=lambda x: isinstance(x, int),
    silent=True,
    raise_on_exception=False
)
print(obj)

# {'key': [None, (2.0,), {None}, frozenset({4}), {'subkey': [(1,), A(val=val)]}]}
```

### 4. Hot swapping
One helpful utility is the ability to safely and reversibly "hot swap" certain elements of an object.
One use-case is writing a non-serializable object to JSON. Say we have some root object `root_obj`
that needs to be serialized to JSON but some of its constituent elements are not
serializable. It may be tedious to go through and null/convert the
non-serializable content. Furthermore, we may not want to permanently overwrite the non-serializable
content. One tool in spelunk is a context manager `hot_swap` that can find elements to arbitrary 
specification and at any depth in the root object, overwrite their values, and then restore the originals.

```python
from spelunk import hot_swap
import json
from datetime import datetime
from threading import Lock
from _thread import LockType
from typing import Any, Optional, Union


root_obj = {
    'date': datetime.now(), 
    'thread_lock': Lock(), 
    'data': [1, 2, 3, 4], 
    'other_locks': [Lock(), Lock()]
}

print(root_obj)
# {
#   'date': datetime.datetime(2022, 11, 9, 13, 48, 19, 969856), 
#   'thread_lock': <unlocked _thread.lock object at 0x105ff4600>, 
#   'data': [1, 2, 3, 4], 
#   'other_locks': [
#       <unlocked _thread.lock object at 0x105ff4630>, 
#       <unlocked _thread.lock object at 0x105ff4690>
#   ]
# }
```
Neither `datetime` nor `_thread.lock` objects are serializable.
```python
json.dumps(root_obj)
# Traceback (most recent call last):
# ...
# TypeError: Object of type datetime is not JSON serializable
```
We can define callables to both capture the bad elements (`get_datetime_and_locks`) as well as 
overwrite intelligently (`overwrite_func`).
```python
def get_datetime_and_locks(obj: Any) -> bool:
    """Get the non-serializable content"""
    return isinstance(obj, (datetime, LockType))

def overwrite_func(obj: Union[datetime, LockType]) -> Optional[str]:
    """Overwrite the non-serializable content"""
    if isinstance(obj, datetime):
        return str(obj)
    else:
        return None
```
Note that `overwrite_func` will only get called on objects for which `get_datetime_and_locks` returns
`True`. Now, we can use our context manager `hot_swap` to temporarily overwrite the non-serializable
content and then restore on exit.

```python
with hot_swap(root_obj, element_test=get_datetime_and_locks, overwrite_func=overwrite_func):
    serialized_obj = json.dumps(root_obj)

print(serialized_obj)
# {
#   "date": "2022-11-09 13:48:19.969856", 
#   "thread_lock": null, 
#   "data": [1, 2, 3, 4], 
#   "other_locks": [null, null]
# }
```
`root_obj` is restored to its original form, allowing the datetime and thread lock objects to
continue to provide utility with further use.

```python
print(root_obj)
# {
#   'date': datetime.datetime(2022, 11, 9, 13, 48, 19, 969856), 
#   'thread_lock': <unlocked _thread.lock object at 0x105ff4600>, 
#   'data': [1, 2, 3, 4], 
#   'other_locks': [
#       <unlocked _thread.lock object at 0x105ff4630>, 
#       <unlocked _thread.lock object at 0x105ff4690>
#   ]
# }
```
If performing a `hot_swap` on a `root_obj` throws an exception, an attempt to restore`root_obj` to 
its original form is made. Additionally, by default, it will throw an exception before any attempt 
to hot swap an element of a mutable set because this cannot be performed reliably. Imagine swapping 
all `int` for `None` in `{1, 2, 3, None}` -> `{None}`. It is then ambiguous to determine which 
elements of the new set should be restored. It would be possible to copy the set `{1, 2, 3, None}` 
and restore this to the parent object, however, this copy would not share the same location in 
memory as the original and it may break internal references as a result. By default, hot swapping is
not allowed with mutable sets, however, if you know it can be performed safely you can use the kwarg 
`allow_mutable_set_mutations=True`. For example, the set `{1}` could be safely hot swapped to 
`{None}` and restored due to the fact that the cardinality is unchanged.

## More Details
### `__slots__` and other class attributes
Spelunk fully support objects that define `__slots__`, `__dict__`, as well as `__slots__` and `__dict__`
simultaneously). In order to deal with instance attributes derived from `__slots__` defined on the 
class itself (or which may be inherited from parent classes), the MRO is used. For each class 
in the object's MRO, the contents of `cls.__slots__` is collected (along with the contents of `obj.__dict__` if 
`__dict__` is defined). For a given object, its attributes are collected as follows:
- `attrs = []`
- If `obj.__dict__` exists, add all elements to `attrs`. 
- For `cls` in `obj.__class__.__mro__`:
  - If `cls.__slots__` exists, add all elements to `attrs`.

Note in the special case that both `__slots__` and `__dict__` are defined (such that `__dict__` is 
a member of `__slots__`), `__dict__` itself will be independently added as an attribute to `attrs`
in addition to the contents of `__dict__`.

Note that any attributes accessible to `obj` outside of `__dict__` (such as attributes of the class), 
are not included by spelunk. However, if one wants to inspect class attribute, the class itself can be 
passed in as the `root_obj`. Here, `__slots__` as well as all methods and other attributes of the class 
will be collected and explored since these are direct attributes of the root object.


Ex:
```python
from spelunk import print_obj_tree

class A:
    important = "important"
    __slots__ = '__dict__', 'val'
    def __init__(self, val):
        self.val = val
        self.other = 'other'
    
    def __repr__(self):
       return f"A(val={self.val})"

print_obj_tree(A(1))
# ROOT -> A(val=1)
# ROOT.other -> 'other'
# ROOT.__dict__ -> {'other': 'other'}
# ROOT.__dict__['other'] -> 'other'
# ROOT.val -> 1
```
We can see that both the contents of `__slots__` (which contains `__dict__`) and `__dict__` 
are captured but the class attribute `important` is not. However, the class itself can be 
inspected:
```python
print_obj_tree(A)
# ROOT -> <class '__main__.A'>
# ROOT.__module__ -> '__main__'
# ROOT.important -> 'important'
# ROOT.__slots__ -> ('__dict__', 'val')
# ROOT.__slots__[0] -> '__dict__'
# ROOT.__slots__[1] -> 'val'
# ...
```

### Memoization
Spelunk optionally utilizes memoization to increase performance and to prevent reporting multiple 
paths which point to the same object in memory. By default, memoization is not used in order to 
retrieve and output the full hierarchy of the object. Memoization can be turned on and off with the 
kwarg `memoization=True`. Note that some objects cannot be memoized regardless of whether 
memoization is turned on. Namely, any subclass of `Number`, `str`, or `ByteString`  (along with 
`None`) will not be memoized due to the fact that members of these classes may be interned and 
all instances will always refer to the same singleton in memory in CPython.

### String unraveling
Spelunk by default assumes that all subclasses of `str` or `ByteString` refer to an atomic 
collection that should not be recursed into character by character. If you do want to recurse 
into a `str` or `ByteString` instance, use the kwarg `unravel_strings=True`.

## Developing
### Project Installation
1. Install an appropriate version of python and create a virtual environment. [Pyenv](https://github.com/pyenv/pyenv) is recommended.
   1. Set the shell variable `VENV_LOC` according to the location of the virtural environment. For example, if
   the virtual environment is inside the repo home directory in a directory named `.venv` you would run `export VENV_LOC=.venv` (this is used by default
   and isn't needed unless the virtual environment is located elsewhere).
2. Install [Poetry](https://python-poetry.org/).
3. Run `make install-repo` to activate the virtual environment and install the dependencies with Poetry.

If you have a different package management system (e.g. `conda`):
1. Create and source/activate a virtual environment.
2. Either install using `Poetry` or use external tools to convert the `poetry.lock` file to a 
`requirements.txt` and install with `pip install -r requirements.txt`.

### Tests
For contributors, kindly use the `Makefile` to perform formatting, linting, and unit testing 
locally.
1. Run `make style-check` to dry-run `black` formatting changes.
2. Run `make reformat` to format with `black`.
3. Run `make lint` to lint with `flake8`.
4. Run `make unit-test` to run `pytest` and check the coverage report. 
