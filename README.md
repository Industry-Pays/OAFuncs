# oafuncs

## Description

**Python Function**

```text
In the field of geoscience, some commonly used and universal operations!

Just for the convenience of daily use, some complex operations are integrated into general functions.

The code will be optimized and updated from time to time, with additions, deletions, or modifications…

Existing functions will not be completely removed, they might just have a different function name, or the parameter passing might have been optimized…

Note: If there are any requirements, you can email to liukun0312@stu.ouc.edu.cn. Within my capabilities, I can consider implementing them.
```

## PyPI

```html
https://pypi.org/project/oafuncs
```

## Github

```html
https://github.com/Industry-Pays/OAFuncs
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
# 此小板块于2024/12/26更新，仅为示例，不代表最新情况
函数数量：
49
函数列表：
['MidpointNormalize', 'add_cartopy', 'add_gridlines', 'add_lonlat_unit', 'check_ncfile', 'choose_cmap', 'clear_folder', 'cmap2colors', 'convert_longitude', 'copy_file', 'create_cmap', 'create_cmap_rgbtxt', 'create_gif', 'download', 'download5doi', 'draw_time_range', 'extract5nc', 'fig_minus', 'file_size', 'find_file', 'get_time_list', 'get_ua', 'get_var', 'how_to_use', 'install_lib', 'interp_2d', 'link_file', 'make_folder', 'merge5nc', 'modify_var_attr', 'modify_var_value', 'nc_isel', 'plot_contourf', 'plot_contourf_cartopy', 'plot_contourf_lonlat', 'plot_quiver', 'query', 'remove', 'remove_empty_folder', 'rename_file', 'rename_var_or_dim', 'send', 'show', 'sign_in_love_ocean', 'sign_in_meteorological_home', 'sign_in_scientific_research', 'upgrade_lib', 'use', 'write2nc']
模块全路径：
oafuncs.oa_help.query
函数提示：

    description: 查看oafuncs模块的函数列表
    example: query()
```

## Structure

<img title="" src="./oafuncs/data_store/OAFuncs.png" alt="">

<img title="OAFuncs" src="https://raw.githubusercontent.com/Industry-Pays/OAFuncs/main/oafuncs/data_store/OAFuncs.png" alt="OAFuncs">
