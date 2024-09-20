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

## 1 oa_cmap

### 1.1 description

针对cmap相关操作写了一些函数，可以生成cmap，简单可视化，以及将cmap拆分成颜色序列等等。

## 2 oa_data

### 2.1 description

对数据进行处理，目前主要提供二维及以上数据的水平二维插值。

## 3 oa_draw

### 3.1 description

一些简单的绘图函数，由于绘图需要高度自定义，所以这部分仅作为速览。

## 4 oa_file

### 4.1 description

对文件进行一些处理，包含文件夹、文件等处理。

## 5 oa_nc

### 5.1 description

对nc数据进行处理，便捷提取变量、维度，以及将数据写入nc文件。
