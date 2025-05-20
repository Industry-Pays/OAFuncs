# OAFuncs 使用指南

OAFuncs是一个功能丰富的Python工具包，提供了多种数据处理、下载、可视化和文件操作的函数。本文档提供了各模块的详细使用说明。

## 目录

1. [oa_python - Python包管理](#oa_python)
2. [oa_down - 数据下载工具](#oa_down)
3. [oa_file - 文件操作工具](#oa_file)
4. [oa_nc - NetCDF文件操作](#oa_nc)
5. [oa_data - 数据处理工具](#oa_data)
6. [oa_tool - 通用工具函数](#oa_tool)
7. [oa_cmap - 颜色映射工具](#oa_cmap)
8. [oa_draw - 绘图工具](#oa_draw)
9. [oa_date - 日期处理工具](#oa_date)

---

<a id="oa_python"></a>

## 1. oa_python - Python包管理

### install_packages

安装指定的Python包。

**参数**:

- `packages` (可选，列表): 要安装的库列表。如果为None，不安装任何包。
- `python_executable` (字符串): 使用的Python可执行文件，如'python312'。默认为'python'。
- `package_manager` (字符串): 使用的包管理器，'pip'或'conda'。默认为'pip'。

**示例**:

```python
from oafuncs.oa_python import install_packages

# 安装numpy和pandas
install_packages(packages=["numpy", "pandas"])

# 使用conda安装包
install_packages(packages=["numpy", "pandas"], package_manager="conda")

# 使用指定的Python版本安装
install_packages(packages=["numpy"], python_executable="python312")
```

### upgrade_packages

升级指定的Python包。

**参数**:

- `packages` (可选，列表): 要升级的库列表。如果为None，升级所有已安装的包。
- `python_executable` (字符串): 使用的Python可执行文件。默认为'python'。
- `package_manager` (字符串): 使用的包管理器，'pip'或'conda'。默认为'pip'。

**示例**:

```python
from oafuncs.oa_python import upgrade_packages

# 升级numpy和pandas
upgrade_packages(packages=["numpy", "pandas"])

# 升级所有包
upgrade_packages()

# 使用conda升级
upgrade_packages(package_manager="conda")
```

---

<a id="oa_down"></a>

## 2. oa_down - 数据下载工具

### download5doi

通过DOI下载学术文献的PDF文件。

**参数**:

- `store_path` (可选): 存储PDF文件的路径。默认为当前工作目录。
- `doi_list` (可选): DOI列表或单个DOI字符串。
- `txt_file` (可选): 包含DOI的txt文件路径。
- `excel_file` (可选): 包含DOI的Excel文件路径。
- `col_name` (字符串): Excel文件中的列名。默认为'DOI'。

**示例**:

```python
from oafuncs.oa_down import download5doi

# 下载单个DOI
download5doi(doi_list='10.3389/feart.2021.698876')

# 下载多个DOI
download5doi(store_path='./pdf_files', doi_list=['10.3389/feart.2021.698876', '10.1029/2020JC016555'])

# 从文本文件下载
download5doi(store_path='./pdf_files', txt_file='./dois.txt')

# 从Excel文件下载
download5doi(store_path='./pdf_files', excel_file='./dois.xlsx', col_name='DOI')
```

### hycom_3hourly.draw_time_range

绘制HYCOM数据集不同版本的时间范围。

**参数**:

- `pic_save_folder` (可选): 图片保存路径。如果为None，保存在当前目录。

**示例**:

```python
from oafuncs.oa_down.hycom_3hourly import draw_time_range

# 在当前目录保存图片
draw_time_range()

# 保存到指定目录
draw_time_range(pic_save_folder='./hycom_plots')
```

### hycom_3hourly.download

下载HYCOM海洋数据。

**参数**:

- `variables` (字符串或列表): 要下载的变量名。如'u', 'v', 'temp', 'salt', 'ssh'等。
- `start_time` (字符串): 开始时间，格式为'YYYYMMDDHH'或'YYYYMMDD'。
- `end_time` (可选，字符串): 结束时间。如不提供，则只下载start_time的数据。
- `lon_min` (可选，浮点数): 最小经度。默认为0。
- `lon_max` (可选，浮点数): 最大经度。默认为359.92。
- `lat_min` (可选，浮点数): 最小纬度。默认为-80。
- `lat_max` (可选，浮点数): 最大纬度。默认为90。
- `depth` (可选，浮点数): 深度（米）。如指定，将下载单一深度的数据。
- `level` (可选，整数): 垂直层级。如指定，将下载单一层级的数据。
- `output_dir` (可选，字符串): 保存文件的目录。默认为当前工作目录。
- `dataset` (可选，字符串): 数据集名称。如'GLBv0.08', 'GLBu0.08'等。
- `version` (可选，字符串): 数据集版本。如'53.X', '56.3'等。
- `workers` (可选，整数): 并行工作进程数。默认为1，最大为10。
- `overwrite` (可选，布尔值): 是否覆盖现有文件。默认为False。
- `idm_path` (可选，字符串): Internet Download Manager可执行文件路径。
- `validate_time` (可选，布尔值): 时间验证模式。
- `interval_hours` (可选，整数): 下载数据的时间间隔（小时）。默认为3。

**示例**:

```python
from oafuncs.oa_down.hycom_3hourly import download

# 下载单个变量，单一时间点
download(
    variables='u',
    start_time='2024083100',
    lon_min=120,
    lon_max=130,
    lat_min=20,
    lat_max=30
)

# 下载多个变量，时间范围
download(
    variables=['u', 'v', 'temp'],
    start_time='2024083100',
    end_time='2024090100',
    lon_min=120,
    lon_max=130,
    lat_min=20,
    lat_max=30,
    output_dir='./hycom_data',
    workers=4
)

# 下载特定深度的数据
download(
    variables='temp',
    start_time='2024083100',
    depth=100,  # 100米深度
    lon_min=120,
    lon_max=130,
    lat_min=20,
    lat_max=30
)
```

---

<a id="oa_file"></a>

## 3. oa_file - 文件操作工具

### file_size

获取文件大小。

**参数**:

- `file_path` (字符串): 文件路径
- `unit` (字符串): 大小单位，可选'PB', 'TB', 'GB', 'MB', 'KB'。默认为'KB'。

**返回值**:

- 文件大小（指定单位）

**示例**:

```python
from oafuncs.oa_file import file_size

# 获取文件大小（KB）
size_kb = file_size('data.nc')
print(f"File size: {size_kb} KB")

# 获取文件大小（MB）
size_mb = file_size('data.nc', unit='MB')
print(f"File size: {size_mb} MB")
```

### remove

删除文件或目录。

**参数**:

- `path` (字符串或Path): 要删除的文件或目录路径

**示例**:

```python
from oafuncs.oa_file import remove

# 删除文件
remove('data.txt')

# 删除目录
remove('./temp_folder')
```

---

<a id="oa_nc"></a>

## 4. oa_nc - NetCDF文件操作

### check

检查NetCDF文件是否有效。

**参数**:

- `nc_file` (字符串或Path): NetCDF文件路径
- `delete_if_invalid` (布尔值): 如果文件无效是否删除。默认为False。
- `print_messages` (布尔值): 是否打印消息。默认为True。

**返回值**:

- 布尔值，文件是否有效

**示例**:

```python
from oafuncs.oa_nc import check

# 检查文件是否有效
if check('data.nc'):
    print("File is valid")
else:
    print("File is invalid")

# 检查并删除无效文件
check('data.nc', delete_if_invalid=True)
```

### modify

修改NetCDF文件中的变量。

**参数**:

- `nc_file` (字符串): NetCDF文件路径
- `var_name` (字符串): 变量名
- `value_type` (字符串或None): 值类型
- `value` (任意): 新值

**示例**:

```python
from oafuncs.oa_nc import modify

# 修改变量值
modify('data.nc', 'temperature', None, 25.5)
```

---

<a id="oa_data"></a>

## 5. oa_data - 数据处理工具

### ensure_list

确保输入是列表类型。

**参数**:

- `obj` (任意): 要转换的对象

**返回值**:

- 列表形式的对象

**示例**:

```python
from oafuncs.oa_data import ensure_list

# 将单个值转换为列表
values = ensure_list(5)  # 返回 [5]

# 保持列表不变
values = ensure_list([1, 2, 3])  # 返回 [1, 2, 3]
```

---

<a id="oa_tool"></a>

## 6. oa_tool - 通用工具函数

### pbar

显示进度条。

**参数**:

- `iterable` (可迭代对象): 要迭代的对象
- `description` (字符串): 进度条描述
- `total` (整数, 可选): 总项数
- `next_line` (布尔值, 可选): 是否显示在下一行。默认为False。

**返回值**:

- 可迭代对象的生成器

**示例**:

```python
from oafuncs.oa_tool import pbar

# 使用进度条遍历列表
for i in pbar(range(100), "Processing", total=100):
    # 处理逻辑
    pass

# 在新行显示进度条
for i in pbar(range(100), "Processing", next_line=True):
    # 处理逻辑
    pass
```

### PEx

并行执行类。

**示例**:

```python
from oafuncs.oa_tool import PEx

def process_data(data, param):
    # 处理数据
    return data * param

# 准备参数列表
params = [(1, 2), (3, 4), (5, 6)]

# 使用PEx并行执行
with PEx() as executor:
    results = executor.run(process_data, params)

# 处理结果
for result in results:
    print(result)
```

---

<a id="oa_cmap"></a>

## 7. oa_cmap - 颜色映射工具

提供自定义的颜色映射和颜色处理函数。

---

<a id="oa_draw"></a>

## 8. oa_draw - 绘图工具

提供用于绘制各种图表的绘图函数。

---

<a id="oa_date"></a>

## 9. oa_date - 日期处理工具

提供日期格式转换和处理的函数。

---

## 安装说明

安装OAFuncs包：

```bash
pip install oafuncs
```

或从源代码安装：

```bash
git clone https://github.com/yourusername/OAFuncs.git
cd OAFuncs
pip install -e .
```

## 贡献指南

如欲贡献代码，请遵循以下步骤：

1. Fork仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目在MIT许可证下发布。详情请查看LICENSE文件。
