# oafuncs

## Description

**Python Function**

```text
In the field of geoscience, some commonly used and universal operations!

Just for the convenience of daily use, some complex operations are integrated into general functions.

The code will be optimized and updated from time to time, with additions, deletions, or modifications…

Existing functions will not be completely removed, they might just have a different function name, or the parameter passing might have been optimized…
```

## PyPI

```html
https://pypi.org/project/oafuncs
```

## Github

```html
https://github.com/Industry-Pays/OAFuncs
```

## Download information
```html
https://pypistats.org/packages/oafuncs
```

## Example

```python
import oafuncs

# 查询当前所有可用函数
oafuncs.oa_help.query()
# 根据函数名获取使用方法
oafuncs.oa_help.use('query')
```

```shell
# 此小板块于2025/03/16更新，仅为示例，不代表最新情况
函数数量：
62
函数列表：
[
    'MidpointNormalize',
    'ParallelExecutor',
    'add_cartopy',
    'add_gridlines',
    'add_lonlat_unit',
    'check',
    'clear_folder',
    'contour',
    'contourf',
    'convert_longitude',
    'copy_file',
    'create',
    'create_rgbtxt',
    'data_record',
    'download',
    'download5doi',
    'downloader',
    'draw',
    'draw_time_range',
    'ending_record',
    'ensure_list',
    'extract',
    'fig_minus',
    'file_size',
    'find_file',
    'get',
    'get_days',
    'get_time_list',
    'get_ua',
    'get_var',
    'gif',
    'header_record',
    'how_to_use',
    'install_lib',
    'interp_2d',
    'interp_along_dim',
    'isel',
    'link_file',
    'log',
    'make_dir',
    'make_folder',
    'mask_shapefile',
    'mean_size',
    'merge',
    'modify',
    'query',
    'quiver',
    'remove',
    'remove_empty_folder',
    'rename',
    'rename_file',
    'save',
    'send',
    'show',
    'sign_in_love_ocean',
    'sign_in_meteorological_home',
    'sign_in_scientific_research',
    'tail_record',
    'test',
    'to_color',
    'upgrade_lib',
    'use'
]
同名函数：
----------------------------------------
模块全路径：
oafuncs.oa_help.query

Help on function query in module oafuncs.oa_help:

query()
    Description:
        Show the number of functions and the list of functions in the module.
    Example:
        query()

----------------------------------------
```

## Structure

<img title="" src="./oafuncs/data_store/OAFuncs.png" alt="">

<img title="OAFuncs" src="https://raw.githubusercontent.com/Industry-Pays/OAFuncs/main/oafuncs/_data/oafuncs.png" alt="OAFuncs">

## Wiki
更多内容，查看[wiki](https://opendeep.wiki/Industry-Pays/OAFuncs/introduction)