# OAFuncs

## Description

Python Function

地学领域，一些常用操作！

只是方便日常使用，将一些复杂的操作集成到通用函数

代码会不定期优化更新，或增或删或改...

已有功能不会完全删除，可能是换了个函数名，或者优化了参数传递等...

<mark>注</mark>：若有需求，可邮件至`16031215@qq.com`，能力范围内可考虑实现

## PyPI

```html
https://pypi.org/project/OAFuncs
```

## Github

```html
https://github.com/Industry-Pays/OAFuncs
```

## Example

```python
import OAFuncs

# OAFuncs.oa_cmap.*
# OAFuncs.oa_data.*
# OAFuncs.oa_draw.*
# OAFuncs.oa_file.*
# OAFuncs.oa_nc.*
# OAFuncs.oa_help.*

# 查询当前所有可用函数
OAFuncs.oa_help.query()
# 根据函数名获取使用方法
OAFuncs.oa_help.use('get_var')
```

```shell
# 2024/10/06更新
函数数量：
25
函数列表：
['clear_folder', 'copy_file', 'create_5rgb_txt', 'create_custom', 'create_diverging', 'create_gif', 'extract5nc', 'extract_colors', 'get_var', 'interp_2d', 'interp_2d_parallel', 'link_file', 'make_folder', 'plot_contourf', 'plot_contourf_cartopy', 'plot_contourf_lonlat', 'plot_quiver', 'query', 'remove', 'remove_empty_folders', 'rename_files', 'show', 'use', 'write2nc', 'xy2lonlat']
模块全路径：
OAFuncs.oa_nc.get_var
函数提示：
datas_ecm = get_var(file_ecm, 'h', 't', 'u', 'v')

# 实际全路径：
datas_ecm = OAFuncs.oa_nc.get_var(file_ecm, 'h', 't', 'u', 'v')
```

```python
import numpy as np
from OAFuncs import oa_nc
# or
import OAFuncs

data = np.random.rand(100, 50)
oa_nc.write2nc(r'I:\test.nc', data,
         'data', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'a')

# or
OAFuncs.oa_nc.write2nc(r'I:\test.nc', data,
         'data', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'a')
```

## 结构

- **OAFuncs**
  - oa_cmap
    - show
      
      展示cmap效果
    - extract_colors
      
      将cmap拆分成颜色列表
    - create_custom
      
      自定义cmap，可提供颜色位置
    - create_diverging
      
      等比例两端型cmap
    - create_5rgb_txt
      
      基于RGB文件制作cmap
  - oa_data
    - interp_2d
      
      二维插值
    - interp_2d_parallel
      
      二维插值，并行加速
  - oa_draw
    - create_gif
      
      制作动图
    - xy2lonlat
      
      将数字转化为经/纬度字符串
    - plot_contourf
      
      粗略绘制填色图
    - plot_contourf_lonlat
      
      填色图叠加经纬度
    - plot_contourf_cartopy
      
      填色图加海陆线
    - plot_quiver
      
      矢量图
  - oa_file
    - link_file
      
      链接文件
    - copy_file
      
      复制文件
    - rename_files
      
      按一定规则重命名文件（可多个）
    - make_folder
      
      在指定路径下创建文件夹
    - clear_folder
      
      清空文件夹
    - remove_empty_folders
      
      删除路径下所有空的文件夹
    - remove
      
      删除文件/文件夹
  - oa_help
    - query
      
      查询本库所有可用函数
    - use
      
      获取函数路径、函数说明
  - oa_nc
    - get_var
      
      批量提取nc文件变量
    - extract5nc
      
      从nc文件中提取变量，包含所有坐标值
    - write2nc
      
      便捷将数据写入nc文件
      - 



## 依赖库

```shell
"matplotlib"
"numpy"
"scipy"
"xarray"
"Cartopy"
"netCDF4"
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

创建双色diverging型颜色映射（cmap），当传入颜色为偶数时，默认中间为白色。

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
cmap_color = create_5rgb_txt('./test.txt')
```

RGB.txt格式：

```textile
50,54,156
...
255,255,255
```

## 2 oa_data

### 2.1 description

对数据进行处理，目前主要提供二维及以上数据的水平二维插值。（2D~4D）

### 2.2 `interp_2d(target_x, target_y, origin_x, origin_y, data, method='linear')`

#### 描述

高维插值函数，默认对数据的最后两个维度进行插值。该函数适用于二维~四维空间数据的插值，不使用并行计算。

#### 参数

- `target_x` (array-like): 目标纬度网格，可以是1D或2D数组。
- `target_y` (array-like): 目标经度网格，可以是1D或2D数组。
- `origin_x` (array-like): 初始纬度网格，与原始数据形状匹配的1D或2D数组。
- `origin_y` (array-like): 初始经度网格，与原始数据形状匹配的1D或2D数组。
- `data` (array-like): 待插值的数据，形状为(*, lat, lon)，其中`*`可以是任意1~2D。
- `method` (str, optional): 插值方法，默认为'linear'。可选值还包括'nearest', 'cubic'等。

#### 返回

- `array-like`: 插值结果，形状与`target_x`和`target_y`构成的网格形状一致，并且保持原始数据除了最后两个维度之外的其他维度结构。

#### 示例

```python
import numpy as np
import matplotlib.pyplot as plt

# 创建初始网格和数据
origin_x = np.linspace(0, 10, 11)
origin_y = np.linspace(0, 10, 11)
data = np.random.rand(10, 10, 11, 11)

# 创建目标网格
target_x = np.linspace(0, 10, 101)
target_y = np.linspace(0, 10, 101)

# 执行插值
interpolated_data = interp_2d(target_x, target_y, origin_x, origin_y, data)

# 打印插值结果形状
print(interpolated_data.shape)

# 可视化插值结果
plt.figure()
plt.contourf(target_x, target_y, interpolated_data[0, 0, :, :])
plt.colorbar()
plt.show()
```

### 2.3 `interp_2d_parallel(target_x, target_y, origin_x, origin_y, data, method='linear')`

#### 描述

高维插值函数，使用多线程加速插值过程。该函数默认对数据的最后两个维度进行插值，适用于二维到四维空间数据的插值。通过`ThreadPoolExecutor`来并行处理数据的不同切片，以提升计算效率。

#### 参数

- `target_x` (array-like): 目标纬度网格，可以是1D或2D数组。
- `target_y` (array-like): 目标经度网格，可以是1D或2D数组。
- `origin_x` (array-like): 初始纬度网格，与原始数据形状匹配的1D或2D数组。
- `origin_y` (array-like): 初始经度网格，与原始数据形状匹配的1D或2D数组。
- `data` (array-like): 待插值的数据，形状为(*, lat, lon)，其中`*`可以是任意维度。
- `method` (str, optional): 插值方法，默认为'linear'。可选值还包括'nearest', 'cubic'等。

#### 返回

- `array-like`: 插值结果，形状与`target_x`和`target_y`构成的网格形状一致，并且保持原始数据除了最后两个维度之外的其他维度结构。

#### 示例

```python
import numpy as np
import matplotlib.pyplot as plt

# 创建初始网格和数据
origin_x = np.linspace(0, 10, 11)
origin_y = np.linspace(0, 10, 11)
data = np.random.rand(10, 10, 11, 11)

# 创建目标网格
target_x = np.linspace(0, 10, 101)
target_y = np.linspace(0, 10, 101)

# 执行插值
interpolated_data = interp_2d_parallel(target_x, target_y, origin_x, origin_y, data)

# 打印插值结果形状
print(interpolated_data.shape)

# 可视化插值结果
plt.figure()
plt.contourf(target_x, target_y, interpolated_data[0, 0, :, :])
plt.colorbar()
plt.show()
```

## 3 oa_draw

### 3.1 description

一些简单的绘图函数，由于绘图需要高度自定义，所以这部分仅作为速览。

### 3.2 等待优化再写

目前已有部分函数，可自行尝试

```python
create_gif(image_list: list, gif_name: str, duration=0.2)


xy2lonlat(xy, lonlat='lon', decimal=2)


plot_contourf(pic_data, picname=None, c_map='rainbow', minmax=None, labels=None, ticks_space=None, ticks=None, figsize=(12, 9))


plot_contourf_lonlat(data, lon, lat, interval=5, picname=None, c_map='rainbow')


plot_quiver(u, v, lon, lat, picname=None, cmap='coolwarm', scale=0.25, width=0.002, x_space=5, y_space=5)


plot_contourf_cartopy(data, lon, lat, picname=None, cmap='rainbow', cn_fill_num=20, fig_size=(12, 9), title='Cartopy', land_color='green', ocean_color='lightgrey')
```

## 4 oa_file

### 4.1 description

对文件进行一些处理，包含文件夹、文件等处理。

### 4.2 `link_file(src_pattern, dst)`

#### 描述

创建符号链接，支持通配符匹配源文件。

#### 参数

- `src_pattern`: 源文件路径，支持通配符。
- `dst`: 目标路径或文件名。

#### 返回

无返回值

#### 示例

```python
link_file(r'/data/hejx/liukun/era5/*', r'/data/hejx/liukun/Test/')
link_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test/py.o')
link_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test')
```

### 4.3 `copy_file(src_pattern, dst)`

#### 描述

复制文件或目录，支持使用通配符匹配源文件。

#### 参数

- `src_pattern`: 源文件或目录的路径，可以包含通配符来匹配多个文件。
- `dst`: 目标路径或文件名。如果指定的是目录路径，则保持源文件的文件名；如果指定的是文件名，则会覆盖同名文件。

#### 返回

无返回值

#### 示例

复制单个文件到指定目录，保持原文件名：

```python
copy_file(r'/path/to/source/file.txt', r'/path/to/destination/')
```

### 4.4 `rename_files(directory, old_str, new_str)`

#### 描述

在指定目录下批量重命名文件，将文件名中的指定字符串替换为新的字符串。

#### 参数

- `directory`：需要操作的目录路径，字符串类型。
- `old_str`：需要被替换的旧字符串，字符串类型。
- `new_str`：用于替换旧字符串的新字符串，字符串类型。

#### 返回

该函数没有返回值，但会直接修改指定目录下的文件名。

#### 示例

```python
# 调用函数
directory_path = "E:\\Code\\Matlab\\Master\\Ocean\\ROMS\\CROCO-1.3.1\\My_Models\\windfarm\\CROCO_FILES"
old_str = "croco"
new_str = "roms"
rename_files(directory_path, old_str, new_str)
```

### 4.5 `make_folder(rootpath: str, folder_name: str, clear=0)`

#### 描述

创建一个新文件夹在指定的根路径下，如果文件夹已存在，可以选择是否清除其内容。函数返回创建的文件夹路径。

#### 参数

- `rootpath`：新文件夹的根路径，字符串类型。
- `folder_name`：要创建的文件夹名称，字符串类型。
- `clear`：可选参数，默认为0。如果设置为1，且文件夹已存在，则将其内容清除。

#### 返回

函数返回创建或清理后的文件夹路径，字符串类型。

#### 示例

```python
# 调用函数
root_path = "/path/to/root"
folder_name = "new_folder"
created_folder_path = make_folder(root_path, folder_name, clear=1)
print(f"Folder created at: {created_folder_path}")
```

### 4.6 `clear_folder(folder_path)`

#### 描述

清空指定文件夹中的所有内容，包括文件、子文件夹以及符号链接。如果文件夹不存在，则不会有任何操作。

#### 参数

- `folder_path`：需要清空的文件夹路径，字符串类型。

#### 返回

该函数没有返回值

#### 示例

```python
# 调用函数
folder_to_clear = "/path/to/folder"
clear_folder(folder_to_clear)
```

### 4.7 `remove_empty_folders(path, print_info=1)`

#### 描述

遍历指定路径下的所有文件夹，并删除空的文件夹。该函数会递归地检查每个子文件夹，如果文件夹为空，则将其删除。

#### 参数

- `path`：需要检查和删除空文件夹的路径，字符串类型。
- `print_info`：可选参数，默认为1。如果设置为1，则在删除空文件夹或跳过受保护的文件夹时打印信息。

#### 返回

该函数没有返回值

#### 示例

```python
# 调用函数
path_to_check = "/path/to/directory"
remove_empty_folders(path_to_check)
```

### 4.8 `remove(pattern)`

#### 描述

删除与给定模式匹配的所有文件。该函数使用 `glob` 模块来匹配文件路径模式，并删除找到的所有文件。

#### 参数

- `pattern`：文件匹配模式，可以是相对路径或绝对路径，并可以使用通配符 `*` 来匹配多个文件。

#### 返回

该函数没有返回值

#### 示例

```python
# 调用函数
# 使用绝对路径
remove(r'E:\Code\Python\Model\WRF\Radar2\bzip2-radar-0*')

# 或者先切换到目标目录，再使用相对路径
os.chdir(r'E:\Code\Python\Model\WRF\Radar2')
remove('bzip2-radar-0*')
```

## 5 oa_nc

### 5.1 description

对nc数据进行处理，便捷提取变量、维度，以及将数据写入nc文件。

### 5.2 `get_var(file, *vars)`

#### 描述

从给定的 NetCDF 文件中提取并返回指定的变量数据。该函数使用 `xarray` 库来处理 NetCDF 文件。

#### 参数

- `file`：NetCDF 文件的路径，字符串类型。
- `*vars`：一个或多个变量名，这些是要从 NetCDF 文件中提取的变量。

#### 返回

- `datas`：一个列表，包含从 NetCDF 文件中提取的变量数据。

#### 示例

```python
# 调用函数
file_path = 'path_to_your.nc'
variables = ['temperature', 'pressure']
data_list = get_var(file_path, *variables)

# 现在 data_list 包含了 'temperature' 和 'pressure' 变量的数据
```

### 5.3 `extract5nc(file, varname)`

#### 描述

从 NetCDF 文件中提取指定变量的数据，并创建一个包含变量维度和对应值的字典。函数返回变量的数据数组以及维度字典。

#### 参数

- `file`：NetCDF 文件的路径，字符串类型。
- `varname`：要提取的变量名称，字符串类型。

#### 返回

- `np.array(vardata)`：提取的变量数据，转换为 NumPy 数组。
- `dimdict`：一个字典，键是变量维度名称，值是对应的维度数据。

#### 示例

```python
# 调用函数
file_path = 'path_to_your.nc'
variable_name = 'temperature'
data_array, dimensions_dict = extract5nc(file_path, variable_name)

# 现在 data_array 包含了 'temperature' 变量的数据，dimensions_dict 包含了维度信息
```

### 5.4 `write2nc(file, data, varname, coords, mode)`

#### 描述

将数据写入 NetCDF 文件。根据提供的模式（写入或追加），函数可以创建新的 NetCDF 文件，或者在现有文件中添加或替换变量和坐标。

#### 参数

- `file`：NetCDF 文件的路径，字符串类型。
- `data`：要写入的数据，NumPy 数组。
- `varname`：要创建或更新的变量名称，字符串类型。
- `coords`：坐标字典，键为维度名称，值为对应的坐标数据。
- `mode`：写入模式，'w' 表示写入（如果文件存在则删除），'a' 表示追加（如果文件不存在则创建）。

#### 返回

该函数没有返回值

#### 示例

```python
# 使用示例
file_path = 'output.nc'
data_to_write = np.random.rand(10, 5)  # 示例数据
variable_name = 'example_data'
coordinates = {'time': np.arange(10), 'level': np.arange(5)}
write_mode = 'w'  # 写入模式

write2nc(file_path, data_to_write, variable_name, coordinates, write_mode)
```
