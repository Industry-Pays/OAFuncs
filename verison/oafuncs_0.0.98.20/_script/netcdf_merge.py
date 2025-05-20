import logging
import os
from typing import List, Optional, Union

import xarray as xr

from oafuncs import pbar


def merge_nc(file_list: Union[str, List[str]], var_name: Optional[Union[str, List[str]]] = None, dim_name: Optional[str] = None, target_filename: Optional[str] = None) -> None:
    """
    Description:
        Merge variables from multiple NetCDF files along a specified dimension and write to a new file.
        If var_name is a string, it is considered a single variable; if it is a list and has only one element, it is also a single variable;
        If the list has more than one element, it is a multi-variable; if var_name is None, all variables are merged.

    Parameters:
        file_list: List of NetCDF file paths or a single file path as a string
        var_name: Name of the variable to be extracted or a list of variable names, default is None, which means all variables are extracted
        dim_name: Dimension name used for merging
        target_filename: Target file name after merging

    Example:
        merge(file_list, var_name='u', dim_name='time', target_filename='merged.nc')
        merge(file_list, var_name=['u', 'v'], dim_name='time', target_filename='merged.nc')
        merge(file_list, var_name=None, dim_name='time', target_filename='merged.nc')
    """

    if target_filename is None:
        target_filename = "merged.nc"

    # 确保目标路径存在
    target_dir = os.path.dirname(target_filename)
    if target_dir and not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if isinstance(file_list, str):
        file_list = [file_list]

    # 初始化变量名列表
    if var_name is None:
        with xr.open_dataset(file_list[0]) as ds:
            var_names = list(ds.variables.keys())
    elif isinstance(var_name, str):
        var_names = [var_name]
    elif isinstance(var_name, list):
        var_names = var_name
    else:
        raise ValueError("var_name must be a string, a list of strings, or None")

    # 初始化合并数据字典
    merged_data = {}

    for i, file in pbar(enumerate(file_list), "Reading files", total=len(file_list)):
        with xr.open_dataset(file) as ds:
            for var in var_names:
                data_var = ds[var]
                if dim_name in data_var.dims:
                    merged_data.setdefault(var, []).append(data_var)
                elif var not in merged_data:
                    # 只负责合并，不做NaN填充，统一交由 netcdf_write.py 处理
                    merged_data[var] = data_var

    # 记录变量的填充值和缺失值信息，确保不会丢失
    fill_values = {}
    missing_values = {}
    for var_name, var_data in merged_data.items():
        if isinstance(var_data, list) and var_data:
            # 如果是要合并的变量，检查第一个元素的属性
            attrs = var_data[0].attrs
            if "_FillValue" in attrs:
                fill_values[var_name] = attrs["_FillValue"]
            if "missing_value" in attrs:
                missing_values[var_name] = attrs["missing_value"]
        else:
            # 如果是单个变量，直接检查属性
            attrs = var_data.attrs if hasattr(var_data, "attrs") else {}
            if "_FillValue" in attrs:
                fill_values[var_name] = attrs["_FillValue"]
            if "missing_value" in attrs:
                missing_values[var_name] = attrs["missing_value"]

    for var in pbar(merged_data, "Merging variables"):
        if isinstance(merged_data[var], list):
            # 使用compat='override'确保合并时属性不会冲突
            merged_data[var] = xr.concat(merged_data[var], dim=dim_name, compat="override")
            # 恢复原始填充值和缺失值属性
            if var in fill_values:
                merged_data[var].attrs["_FillValue"] = fill_values[var]
            if var in missing_values:
                merged_data[var].attrs["missing_value"] = missing_values[var]

    # 合并后构建 Dataset，此时 merged_data 只包含数据变量，不包含坐标变量
    merged_ds = xr.Dataset(merged_data)

    # 自动补充坐标变量（如 time、lat、lon 等），以第一个文件为准
    with xr.open_dataset(file_list[0]) as ds0:
        for coord in ds0.coords:
            # 保证坐标变量不会被覆盖，且数据类型和属性保持一致
            if coord not in merged_ds.coords:
                merged_ds = merged_ds.assign_coords({coord: ds0[coord]})

    # 如果合并维度是坐标，检查所有文件的该坐标是否一致
    if dim_name in merged_ds.coords and len(file_list) > 1:
        logging.info(f"验证合并维度 {dim_name} 的一致性...")
        for file in file_list[1:]:
            with xr.open_dataset(file) as ds:
                if dim_name in ds.coords and not ds[dim_name].equals(merged_ds[dim_name]):
                    logging.warning(f"文件 {file} 的 {dim_name} 坐标与合并后的数据不一致，可能导致数据失真")

    if os.path.exists(target_filename):
        logging.warning("The target file already exists. Removing it ...")
        os.remove(target_filename)

    merged_ds.to_netcdf(target_filename,mode='w')


# Example usage
if __name__ == "__main__":
    files_to_merge = ["file1.nc", "file2.nc", "file3.nc"]
    output_path = "merged_output.nc"
    merge_nc(files_to_merge, var_name=None, dim_name="time", target_filename=output_path)
