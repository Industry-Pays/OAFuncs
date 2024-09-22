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

## 1 `oa_cmap`

### 1.1 description

针对cmap相关操作写了一些函数，可以生成cmap，简单可视化，以及将cmap拆分成颜色序列等等。

### 1.2 `show(colormaps: list)`

#### 描述

帮助函数，用于绘制与给定颜色映射（colormap）关联的数据。

#### 参数

- `colormaps` (list): 颜色映射列表。

#### 示例

```python
cmap = mpl.colors.ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
show([cmap])
```

### 1.3 `extract_colors(cmap, n=256)`

#### 描述

将颜色映射（cmap）转换为颜色列表。

#### 参数

- `cmap` (str): 颜色映射名称。

- `n` (int): 颜色分割的数量，默认为256。

#### 返回

- `out_cmap` (list): 颜色列表。

#### 示例

```python
out_cmap = extract_colors('viridis', 256)
```

### 1.4 `create_custom(colors: list, nodes=None)`

#### 描述

创建自定义颜色映射（cmap），可以自动确定颜色位置（等比例）。

#### 参数

- `colors` (list): 颜色列表，可以是颜色名称或十六进制颜色代码。

- `nodes` (list, optional): 颜色位置列表，默认为None，表示等间距。

#### 返回

- `c_map` (matplotlib.colors.LinearSegmentedColormap): 自定义颜色映射。

#### 示例

```python
c_map = create_custom(['#C2B7F3','#B3BBF2','#B0CBF1','#ACDCF0','#A8EEED'])
c_map = create_custom(['aliceblue','skyblue','deepskyblue'], [0.0, 0.5, 1.0])
```

### 1.5 `create_diverging(colors: list)`

#### 描述

创建双色diverging型颜色映射（cmap），默认中间为白色。

#### 参数

- `colors` (list): 颜色列表，可以是颜色名称或十六进制颜色代码。

#### 返回

- `cmap_color` (matplotlib.colors.LinearSegmentedColormap): 自定义diverging型颜色映射。

#### 示例

```python
diverging_cmap = create_diverging(
  ["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"])
```

### 1.6 `create_5rgb_txt(rgb_txt_filepath: str)`

#### 描述

根据RGB的txt文档制作色卡。

#### 参数

- `rgb_txt_filepath` (str): RGB txt文件的路径。

#### 返回

- `icmap` (matplotlib.colors.ListedColormap): 根据RGB值创建的颜色映射。

#### 示例

```python
cmap_color = create_5rgb_txt('E:/python/colorbar/test.txt')
```







#### 2 oa_data

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
