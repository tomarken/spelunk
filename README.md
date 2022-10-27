# spelunk
`spelunk` is a module containing tools for recursively exploring python objects.

## Installation
`spelunk` can be installed with `pip install spelunk`. See below for details on how to install 
the project for development.

## Quick Use Guide
### 1. Printing an object's tree


Ex:
  ```python
from spelunk import print_obj_tree
  
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,)]}]}
print_obj_tree(root_obj=obj)

# ROOT -> {'key': [1, ...]}
# ROOT['key'] -> [1, ...]
# ROOT['key'][0] -> 1
# ROOT['key'][1] -> (2.0,)
# ROOT['key'][1][0] -> 2.0
# ROOT['key'][2] -> {3}
# ROOT['key'][2]{id=4431022448} -> 3
# ROOT['key'][3] -> frozenset({4})
# ROOT['key'][3]{id=4431022480} -> 4
# ROOT['key'][4] -> {'subkey': [(1,)]}
# ROOT['key'][4]['subkey'] -> [(1,)]
# ROOT['key'][4]['subkey'][0] -> (1,)
# ROOT['key'][4]['subkey'][0][0] -> 1
  ```
* The root object is referred to as `ROOT`. 
* Attributes are denoted with `ROOT.attr`.
* Keys from mappings are denoted with `ROOT['key']`.
* Indices from sequences are denoted with `ROOT[idx]`.
* Elements of sets and frozensets are indicated by their id in memory with `ROOT{id=10012}`. 
* Elements of a `ValuesView` are indicated by their id in memory with `ROOT{ValuesView_id=10012}`.
(These are not common.)

The previous notations will be recursively chained together. For example, the path 
`ROOT['key'][2]` indicates that in order to access the corresponding object `{3}`, we would 
use `root_obj['key'][2]`. For sets it is a bit more difficult due to the need to inspect by id. To
access `4` via `ROOT['key'][3]{id=4431022480}` we would iterate through `root_obj['key'][3]` until 
we found a matching id:
  ```python
for elem in root_obj['key'][3]:
    if id(elem) == 4431022480:
      break
      
print(elem)
# 4
  ```

Fortunately, for getting references and manipulating elements of `root_obj`, there are additional 
tools that avoid needing to tediously address and iterate (see below). 


Before moving on, it's worth pointing out you can also sort by element and/or by path name by 
supplying callables `element_test` and `path_test` that determine whether an element or path is 
interesting (by default they always return True). `element_test` operates on the element itself and 
returns a bool. `path_test` operates on the most recent path value  of the current path (either 
string for attributes/mapping keys or integers for sequences and sets) and returns a bool. For 
example, if you're at `root_obj['key']` with path `ROOT['key']`, it would pass `key` to the input of
`path_test` and `[1, (2,), ...]` to `element_test`.

  ```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,)]}]}
print_obj_tree(root_obj=obj, element_test=lambda x: isinstance(x, float))

# ROOT['key'][1][0] -> 2.0
  ```
  ```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,)]}]}
print_obj_tree(root_obj=obj, path_test=lambda x: x=='subkey')  

# ROOT['key'][4]['subkey'] -> [(1,)]
  ```

### 2. Getting the values and paths of objects
To get a dictionary of objects filtered by element/path and keyed by full path string, 
use `get_elements`:
```python
from spelunk import get_elements
  
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,)]}]}
get_elements(root_obj=obj, element_test=lambda x: isinstance(x, frozenset))

# {"ROOT['key'][3]": frozenset({4})}

get_elements(root_obj=obj, element_test=lambda x: isinstance(x, dict))
# {
#   'ROOT':           {'key': [1, (2.0,), {3}, frozenset({4}), {'subkey': [(1,)]}]}, 
#   "ROOT['key'][4]": {'subkey': [(1,)]}
# }
```

### 3. Overwriting elements 
To overwrite elements use `overwrite_elements`:
```python
from spelunk import overwrite_elements

obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,)]}]}
overwrite_elements(
    root_obj=obj, 
    overwrite_value=None, 
    element_test=lambda x: isinstance(x, tuple)
)
print(obj)

# {'key': [1, None, {3}, frozenset({4}), {'subkey': [None]}]}
```
Overwriting will fail if attempting to overwrite an immutable container. 


Ex: 
```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,)]}]}
overwrite_elements(
    root_obj=obj, 
    overwrite_value=None, 
    element_test=lambda x: isinstance(x, int)
)
print(obj)

# Failed to overwrite [(<Address.MUTABLE_MAPPING_KEY: 'MutableMappingKey'>, ...
# Exception: Cannot overwrite immutable collections.
# Traceback (most recent call last):
# ...
# TypeError: Cannot overwrite immutable collections.
```
Error messages can be silenced with `silent=True` and exceptions can be dismissed with 
`raise_on_exception=False` kwargs. Be aware that it may be difficult to determine which objects 
failed with these options.
```python
obj = {'key': [1, (2.0,), {3}, frozenset((4,)), {'subkey': [(1,)]}]}
overwrite_elements(
    root_obj=obj, 
    overwrite_value=None, 
    element_test=lambda x: isinstance(x, int),
    silent=True,
    raise_on_exception=False
)
print(obj)

# {'key': [None, (2.0,), {None}, frozenset({4}), {'subkey': [(1,)]}]}
```

### 4. Hot swapping
If you need to temporarily overwrite an object's contents with replacement 
values and then restore the original values, there is a context manager `hot_swap` that achieves 
this. As an example, say you had an object that contained threading locks, and you wanted to make a 
deepcopy in order to manipulate the copy but preserve the original. The deepcopy will fail on the 
original object due to the fact that threading locks are not serializable. With `hot_swap`, you can 
safely overwrite the non-serializable elements with something safe, perform the deepcopy, and then 
restore the original elements.

```python
from spelunk import hot_swap
from _thread import LockType
from threading import Lock
from copy import deepcopy

lock_0 = Lock()
lock_1 = Lock()
obj = {'key': [1, lock_0, {3}, frozenset((4,)), {'subkey': [(1,)]}], 'other_lock': lock_1}

print(obj)
# {
#  'key': [1, <unlocked _thread.lock... 0x104a7b870>, {3}, frozenset({4}), {'subkey': [(1,)]}], 
#  'other_lock': <unlocked _thread.lock... 0x104a7b840>
# }

obj_deepcopy = deepcopy(obj)
# Traceback (most recent call last):
# ...
# TypeError: cannot pickle '_thread.lock' object

with hot_swap(root_obj=obj, overwrite_value='lock', element_test=lambda x: isinstance(x, LockType)):
    obj_deepcopy = deepcopy(obj)

print(obj_deepcopy)
# {'key': [1, 'lock', {3}, frozenset({4}), {'subkey': [(1,)]}], 'other_lock': 'lock'}

print(obj)
# {
#  'key': [1, <unlocked _thread.lock... 0x104a7b870>, {3}, frozenset({4}), {'subkey': [(1,)]}], 
#  'other_lock': <unlocked _thread.lock... 0x104a7b840>
# }
```
If performing a `hot_swap` on a `root_obj` would involve attempting to mutate an immutable 
collection, an exception will be thrown before any modifications occur (even legal mutations) to 
leave `root_obj` unchanged. Additionally, by default, it will throw an exception before any attempt 
to hot swap an element of a mutable set because this cannot be performed reliably. Imagine swapping 
all `int` for `None` in `{1, 2, 3, None}` -> `{None}`. It is then ambiguous to determine which 
elements of the new set should be restored. By default, hot swapping is not allowed with sets, 
however, if you know it can be performed safely you can use the kwarg 
`allow_mutable_set_mutations=True`. For example, the set `{1}` could be safely hot swapped to 
`{None}` and restored due to the fact that the cardinality is unchanged.

## More Details
### `__slots__` and other class attributes
`spelunk` fully support objects that define `__slots__` (as well as `__dict__` simultaneously). In 
order to deal with slot attributes that may be inherited from parent classes, the object's MRO is 
queried. For each parent class, the contents of `__slots__` is collected (along with the object's 
`__dict__` contents if `__dict__` is defined). Note that although we are accessing the class 
attribute `__slots__`, we don't collect the object `__slots__` itself since this belongs to the 
class and not the instance. Additionally, the attribute `__dict__` itself and any attributes stored 
outside `obj.__dict__` are not collected. To be clear, the contents of `obj.__dict__` are collected, 
just not `__dict__` itself. The one exception is when `__dict__` is defined as a member of 
`__slots__` to support both slot attributes and dynamically assigned attributes. 

If one wants to inspect a class attribute, the class itself can be passed in as the `root_obj`. 
Here, `__slots__` as well as all methods and other attributes of the class will be collected and 
explored since these are direct attributes of the root object.


Ex:
```python
from spelunk import print_obj_tree

class A:
    important = "important"
    __slots__ = '__dict__', 'val'
    def __init__(self, val):
        self.val = val
        self.other = 'other'

print_obj_tree(A(1))
# ROOT -> <__main__.A object at 0x10a3dcdc0>
# ROOT.other -> 'other'
# ROOT.__dict__ -> {'other': 'other'}
# ROOT.__dict__['other'] -> 'other'
# ROOT.val -> 1
# ...
```
We can see that both the contents of `__slots__` (which contains `__dict__`) and `__dict__` 
are captured but the class attribute `important` is not. However, the class itself can be 
inspected:
```python
print_obj_tree(A)
# ROOT -> <class '__main__.A'>
# ROOT.__module__ -> '__main__'
# ROOT.important -> 'important'
# ROOT.__slots__ -> ('__dict__', ...)
# ROOT.__slots__[0] -> '__dict__'
# ROOT.__slots__[1] -> 'val'
# ...
```

### Memoization
`spelunk` optionally utilizes memoization to increase performance and to prevent reporting multiple 
paths which point to the same object in memory. By default, memoization is not used in order to 
retrieve and output the full hierarchy of the object. Memoization can be turned on and off with the 
kwarg `memoization=True`. Note that some objects cannot be memoized regardless of whether 
memoization is turned on. Namely, any subclass of `Number`, `str`, or `ByteString`  (along with 
`None`) will not be memoized due to the fact that members of these classes may be interned and 
all instances will always refer to the same item in memory in CPython.

### String unraveling
`spelunk` by default assumes that all subclasses of `str` or `ByteString` refer to an atomic 
collection that should not be recursed into character by character. If you do want to recurse 
into a `str` or `ByteString` instance, use the kwarg `unravel_strings=True`.

## Developing
### Project Installation
If you prefer using `pyenv` and `Poetry` (or have no preference), the `Makefile` provides 
installation support. Make sure `conda` is deactivated fully (not even `base` active) and `pyenv` is
not running a shell. 
1. Run `make install-python` to install `pyenv` (if not present) and then use `pyenv` to install the 
specific version of `python`.
2. Run `make install-poetry` to install `Poetry` if not already present. 
3. Run `make install-repo` to create a virtual environment `spelunk` stored in `spelunk/.venv` and 
use `Poetry` to install all dependencies.
4. To use the environment simply run `source .venv/bin/activate`.
5. To deactivate simply run `deactivate`.

If you have a different package management system:
1. Create a virtual environment.
2. Either install using `Poetry` or use external tools to convert `poetry.lock` to a 
`requirements.txt` and `pip install`.

### Tests
For contributors, kindly use the `Makefile` to perform formatting, linting, and unit testing 
locally.
1. Run `make style-check` to dry-run `black` formatting changes.
2. Run `make format` to format with `black`.
3. Run `make lint` to lint with `flake8`.
4. Run `make unit-test` to run `pytest` and check the coverage report. 
