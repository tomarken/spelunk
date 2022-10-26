# spelunk
`spelunk` is a module containing tools for recursively exploring python objects. Here are a few examples.

### 1. Printing an object's tree
#### Ex:
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
#### You can also sort by element and/or by path name.
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



