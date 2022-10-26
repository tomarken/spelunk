# spelunk
`spelunk` is a module containing tools for recursively exploring python objects. Here are a few examples.

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
You can also sort by element and/or by path name.
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
To get a dictionary of objects of a particular type/path keyed by path string, use `get_elements`:
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
`raise_on_exception`.
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
values and then restore the original values, there is a context manager `hot_swap` that achieves this. 
As an example, say you had an object that contained a thread lock and you wanted to make a deepcopy in 
order to serialize the object. The deepcopy will fail on the original object due to the fact that thread locks 
are not serializable.
```python
from spelunk import hot_swap
from _thread import LockType
from threading import Lock
from copy import deepcopy

lock_0 = Lock()
lock_1 = Lock()
obj = {'key': [1, lock_0, {3}, frozenset((4,)), {'subkey': [(1,)]}], 'other_lock': lock_1}

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
#   'key': [1, <unlocked _thread.lock object at 0x104a7b870>, {3}, frozenset({4}), {'subkey': [(1,)]}], 
#  'other_lock': <unlocked _thread.lock object at 0x104a7b840>
# }
```
One caveat is that sets cannot be safely hot swapped. This is due to the following situation. Imagine 
swapping all `int` for `None` in `{1, 2, 3, None}` -> `{None}`. It is ambiguous to determine which 
elements of the new set should be restored. By default, hot swapping is not allowed with sets, however,
if you know it can be performed safely you can use the flag `allow_mutable_set_mutations`. For example,
the set `{1}` could be safely hot swapped to `{None}` and restored.

## Details
### `__slots__`
`spelunk` fully support objects that define `__slots__` (as well as `__dict__` simultaneously). For each
object that isn't an ignored type or a container, the object's MRO is looked up and each parent class is queried
for possible values of `__slots__` in order to capture those from inheritance. These attributes are collected 
together (along with the instance's `obj.__dict__`). Note that an object's class attributes are not included. 
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
we can see that both the `__slots__` and `__dict__` attributes are captured but the 
class attributes `important` is not. However, the class itself can be inspected:
```python
print_obj_tree(A)
# ROOT -> <class '__main__.A'>
# ROOT.__module__ -> '__main__'
# ROOT.important -> 'important'
# ROOT.__slots__ -> ('__dict__', ...)
# ROOT.__slots__[0] -> '__dict__'
# ROOT.__slots__[1] -> 'val'
```

## Installation
If you prefer using `pyenv` and `Poetry` (or have no preference), the `Makefile` provides installation support. Make sure `conda` is deactivated fully (not even `base` active) and `pyenv` is not running a shell. 
1. Run `make install-python` to install `pyenv` (if not present) and then use `pyenv` to install the specific version of `python`.
2. Run `make install-poetry` to install `Poetry` if not already present. 
3. Run `make install-repo` to create a virtual environment `spelunk` stored in `spelunk/.venv` and use `Poetry` to install all dependencies.
4. To use the environment simply run `source .venv/bin/activate`.
5. To deactivate simply run `deactivate`.

If you have a different package management system:
1. Create a virtual environment.
2. Either install using `Poetry` or use external tools to convert `poetry.lock` to a `requirements.txt` and `pip install`.


## Developing
For contributors, kindly use the `Makefile` to perform formatting, linting, and unit testing locally.
1. Run `make style-check` to dry-run `black` formatting changes.
2. Run `make format` to format with `black`.
3. Run `make lint` to lint with `flake8`.
4. Run `make unit-test` to run `pytest` and check the coverage report. 
