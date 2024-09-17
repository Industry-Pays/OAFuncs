# OAFuncs

## Description

Python Function

## Example

```python
import numpy as np
from OAFuncs import oa_nc

data = np.random.rand(100, 50)
oa_nc.write2nc(r'I:\test.nc', data,
         'data', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'a')
```
