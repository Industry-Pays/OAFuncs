#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 14:58:50
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-12-06 14:16:56
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_nc.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
"""

import os

import netCDF4 as nc
import numpy as np
import xarray as xr

__all__ = ["get_var", "extract5nc", "write2nc", "merge5nc", "modify_var_value", "modify_var_attr", "rename_var_or_dim", "check_ncfile", "convert_longitude", "nc_isel"]


def get_var(file, *vars):
    """
    description: 读取nc文件中的变量
    param {file: 文件路径, *vars: 变量名}
    example: datas = get_var(file_ecm, 'h', 't', 'u', 'v')
    return {datas: 变量数据}
    """
    ds = xr.open_dataset(file)
    datas = []
    for var in vars:
        data = ds[var]
        datas.append(data)
    ds.close()
    return datas


def extract5nc(file, varname, only_value=True):
    """
    描述：
    1、提取nc文件中的变量
    2、将相应维度提取，建立字典
    return：返回变量及坐标字典
    参数：
    file: 文件路径
    varname: 变量名
    only_value: 变量和维度是否只保留数值
    example: data, dimdict = extract5nc(file_ecm, 'h')
    """
    ds = xr.open_dataset(file)
    vardata = ds[varname]
    ds.close()
    dims = vardata.dims
    dimdict = {}
    for dim in dims:
        if only_value:
            dimdict[dim] = vardata[dim].values
        else:
            dimdict[dim] = ds[dim]
    if only_value:
        vardata = np.array(vardata)
    return vardata, dimdict


def _numpy_to_nc_type(numpy_type):
    """将NumPy数据类型映射到NetCDF数据类型"""
    numpy_to_nc = {
        "float32": "f4",
        "float64": "f8",
        "int8": "i1",
        "int16": "i2",
        "int32": "i4",
        "int64": "i8",
        "uint8": "u1",
        "uint16": "u2",
        "uint32": "u4",
        "uint64": "u8",
    }
    # 确保传入的是字符串类型，如果不是，则转换为字符串
    numpy_type_str = str(numpy_type) if not isinstance(numpy_type, str) else numpy_type
    return numpy_to_nc.get(numpy_type_str, "f4")  # 默认使用 'float32'


def _calculate_scale_and_offset(data, n=16):
    if not isinstance(data, np.ndarray):
        raise ValueError("Input data must be a NumPy array.")

    # 使用 nan_to_num 来避免 NaN 值对 min 和 max 的影响
    data_min = np.nanmin(data)
    data_max = np.nanmax(data)

    if np.isnan(data_min) or np.isnan(data_max):
        raise ValueError("Input data contains NaN values, which are not allowed.")

    scale_factor = (data_max - data_min) / (2**n - 1)
    add_offset = data_min + 2 ** (n - 1) * scale_factor

    return scale_factor, add_offset


def write2nc(file, data, varname=None, coords=None, mode="w", scale_offset_switch=True, compile_switch=True):
    """
    description: 写入数据到nc文件

    参数：
    file: 文件路径
    data: 数据
    varname: 变量名
    coords: 坐标，字典，键为维度名称，值为坐标数据
    mode: 写入模式，'w'为写入，'a'为追加
    scale_offset_switch: 是否使用scale_factor和add_offset，默认为True
    compile_switch: 是否使用压缩参数，默认为True

    example: write2nc(r'test.nc', data, 'data', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'a')
    """
    # 设置压缩参数
    kwargs = {"zlib": True, "complevel": 4} if compile_switch else {}

    # 检查文件存在性并根据模式决定操作
    if mode == "w" and os.path.exists(file):
        os.remove(file)
    elif mode == "a" and not os.path.exists(file):
        mode = "w"

    # 打开 NetCDF 文件
    with nc.Dataset(file, mode, format="NETCDF4") as ncfile:
        # 如果 data 是 DataArray 并且没有提供 varname 和 coords
        if varname is None and coords is None and isinstance(data, xr.DataArray):
            data.to_netcdf(file, mode=mode)
            return

        # 添加坐标
        for dim, coord_data in coords.items():
            if dim in ncfile.dimensions:
                if len(coord_data) != len(ncfile.dimensions[dim]):
                    raise ValueError(f"Length of coordinate '{dim}' does not match the dimension length.")
                else:
                    ncfile.variables[dim][:] = np.array(coord_data)
            else:
                ncfile.createDimension(dim, len(coord_data))
                var = ncfile.createVariable(dim, _numpy_to_nc_type(coord_data.dtype), (dim,), **kwargs)
                var[:] = np.array(coord_data)

                # 如果坐标数据有属性，则添加到 NetCDF 变量
                if isinstance(coord_data, xr.DataArray) and coord_data.attrs:
                    for attr_name, attr_value in coord_data.attrs.items():
                        var.setncattr(attr_name, attr_value)

        # 添加或更新变量
        if varname in ncfile.variables:
            if data.shape != ncfile.variables[varname].shape:
                raise ValueError(f"Shape of data does not match the variable shape for '{varname}'.")
            ncfile.variables[varname][:] = np.array(data)
        else:
            # 创建变量
            dim_names = tuple(coords.keys())
            if scale_offset_switch:
                scale_factor, add_offset = _calculate_scale_and_offset(np.array(data))
                dtype = "i2"
                var = ncfile.createVariable(varname, dtype, dim_names, fill_value=-32767, **kwargs)
                var.setncattr("scale_factor", scale_factor)
                var.setncattr("add_offset", add_offset)
            else:
                dtype = _numpy_to_nc_type(data.dtype)
                var = ncfile.createVariable(varname, dtype, dim_names, **kwargs)
            var[:] = np.array(data)

        # 添加属性
        if isinstance(data, xr.DataArray) and data.attrs:
            for key, value in data.attrs.items():
                if key not in ["scale_factor", "add_offset", "_FillValue", "missing_value"] or not scale_offset_switch:
                    var.setncattr(key, value)


def merge5nc(file_list, var_name=None, dim_name=None, target_filename=None):
    """
    批量提取 nc 文件中的变量，按照某一维度合并后写入新的 nc 文件。
    如果 var_name 是字符串，则认为是单变量；如果是列表，且只有一个元素，也是单变量；
    如果列表元素大于1，则是多变量；如果 var_name 是 None，则合并所有变量。

    参数：
    file_list：nc 文件路径列表
    var_name：要提取的变量名或变量名列表，默认为 None，表示提取所有变量
    dim_name：用于合并的维度名
    target_filename：合并后的目标文件名
    
    example: 
    merge5nc(file_list, var_name='data', dim_name='time', target_filename='merged.nc')
    merge5nc(file_list, var_name=['data1', 'data2'], dim_name='time', target_filename='merged.nc')
    merge5nc(file_list, var_name=None, dim_name='time', target_filename='merged.nc')
    """
    if isinstance(file_list, str):
        file_list = [file_list]
    
    # 初始化变量名列表
    var_names = None

    # 判断 var_name 是单变量、多变量还是合并所有变量
    if var_name is None:
        # 获取第一个文件中的所有变量名
        ds = xr.open_dataset(file_list[0])
        var_names = list(ds.variables.keys())
        ds.close()
    elif isinstance(var_name, str):
        var_names = [var_name]
    elif isinstance(var_name, list):
        var_names = var_name
    else:
        raise ValueError("var_name must be a string, a list of strings, or None")

    # 初始化合并数据字典
    merged_data = {}

    # 遍历文件列表
    for i, file in enumerate(file_list):
        print(f"\rReading file {i + 1}/{len(file_list)}...", end="")
        ds = xr.open_dataset(file)
        for var_name in var_names:
            var = ds[var_name]
            # 如果变量包含合并维度，则合并它们
            if dim_name in var.dims:
                if var_name not in merged_data:
                    merged_data[var_name] = [var]
                else:
                    merged_data[var_name].append(var)
            # 如果变量不包含合并维度，则仅保留第一个文件中的值
            else:
                if var_name not in merged_data:
                    merged_data[var_name] = var
        ds.close()

    print("\nMerging data...")
    for var_name in merged_data:
        if isinstance(merged_data[var_name], list):
            merged_data[var_name] = xr.concat(merged_data[var_name], dim=dim_name)

    merged_data = xr.Dataset(merged_data)

    print("Writing data to file...")
    if os.path.exists(target_filename):
        print("Warning: The target file already exists.")
        print("Removing existing file...")
        os.remove(target_filename)
    merged_data.to_netcdf(target_filename)
    print(f'File "{target_filename}" has been created.')


def modify_var_value(nc_file_path, variable_name, new_value):
    """
    使用 netCDF4 库修改 NetCDF 文件中特定变量的值

    参数：
    nc_file_path (str): NetCDF 文件路径
    variable_name (str): 要修改的变量名
    new_value (numpy.ndarray): 新的变量值

    example: modify_var_value('test.nc', 'data', np.random.rand(100, 50))
    """
    try:
        # Open the NetCDF file
        dataset = nc.Dataset(nc_file_path, "r+")
        # Get the variable to be modified
        variable = dataset.variables[variable_name]
        # Modify the value of the variable
        variable[:] = new_value
        dataset.close()
        print(f"Successfully modified variable {variable_name} in {nc_file_path}.")
    except Exception as e:
        print(f"An error occurred while modifying variable {variable_name} in {nc_file_path}: {e}")


def modify_var_attr(nc_file_path, variable_name, attribute_name, attribute_value):
    """
    使用 netCDF4 库添加或修改 NetCDF 文件中特定变量的属性。

    参数：
    nc_file_path (str): NetCDF 文件路径
    variable_name (str): 要操作的变量名
    attribute_name (str): 属性名
    attribute_value (任意类型): 属性值
    example: modify_var_attr('test.nc', 'data', 'long_name', 'This is a test variable.')
    """
    try:
        ds = nc.Dataset(nc_file_path, "r+")
        if variable_name not in ds.variables:
            raise ValueError(f"Variable '{variable_name}' not found in the NetCDF file.")

        variable = ds.variables[variable_name]
        if attribute_name in variable.ncattrs():
            print(f"Warning: Attribute '{attribute_name}' already exists. Replacing it.")
            variable.setncattr(attribute_name, attribute_value)
        else:
            print(f"Adding attribute '{attribute_name}'...")
            variable.setncattr(attribute_name, attribute_value)

        ds.close()
    except Exception as e:
        raise RuntimeError(f"An error occurred: {e}")


def rename_var_or_dim(ncfile_path, old_name, new_name):
    """
    Rename a variable and/or dimension in a NetCDF file.

    Parameters:
    ncfile_path (str): The path to the NetCDF file.
    old_name (str): The name of the variable or dimension to be renamed.
    new_name (str): The new name for the variable or dimension.

    example: rename_var_or_dim('test.nc', 'time', 'ocean_time')
    """
    try:
        with nc.Dataset(ncfile_path, "r+") as dataset:
            # If the old name is not found as a variable or dimension, print a message
            if old_name not in dataset.variables and old_name not in dataset.dimensions:
                print(f"Variable or dimension {old_name} not found in the file.")

            # Attempt to rename the variable
            if old_name in dataset.variables:
                dataset.renameVariable(old_name, new_name)
                print(f"Successfully renamed variable {old_name} to {new_name}.")

            # Attempt to rename the dimension
            if old_name in dataset.dimensions:
                # Check if the new dimension name already exists
                if new_name in dataset.dimensions:
                    raise ValueError(f"Dimension name {new_name} already exists in the file.")
                dataset.renameDimension(old_name, new_name)
                print(f"Successfully renamed dimension {old_name} to {new_name}.")

    except Exception as e:
        print(f"An error occurred: {e}")


def check_ncfile(ncfile, if_delete=False):
    if not os.path.exists(ncfile):
        return False

    try:
        with nc.Dataset(ncfile, "r") as f:
            # 确保f被使用，这里我们检查文件中变量的数量
            if len(f.variables) > 0:
                return True
            else:
                # 如果没有变量，我们可以认为文件是损坏的
                raise ValueError("File is empty or corrupted.")
    except OSError as e:
        # 捕获文件打开时可能发生的OSError
        print(f"An error occurred while opening the file: {e}")
        if if_delete:
            os.remove(ncfile)
            print(f"File {ncfile} has been deleted.")
        return False
    except Exception as e:
        # 捕获其他可能的异常
        print(f"An unexpected error occurred: {e}")
        if if_delete:
            os.remove(ncfile)
            print(f"File {ncfile} has been deleted.")
        return False


def convert_longitude(ds, lon_name="longitude", convert=180):
    """
    将经度数组转换为指定的范围。

    参数：
    ds (xarray.Dataset): 包含经度数据的xarray数据集。
    lon_name (str): 经度变量的名称，默认为"longitude"。
    convert (int): 转换目标范围，可以是180或360，默认为180。

    返回值：
    xarray.Dataset: 经度转换后的xarray数据集。
    """
    to_which = int(convert)
    if to_which not in [180, 360]:
        raise ValueError("to_which must be '180' or '360'")

    if to_which == 180:
        ds = ds.assign_coords({lon_name: (ds[lon_name] + 180) % 360 - 180})
    elif to_which == 360:
        ds = ds.assign_coords({lon_name: (ds[lon_name] + 360) % 360})

    return ds.sortby(lon_name)


def nc_isel(ncfile, dim_name, slice_list):
    """
    Description: Choose the data by the index of the dimension

    Parameters:
        ncfile: str, the path of the netCDF file
        dim_name: str, the name of the dimension
        slice_list: list, the index of the dimension

    slice_list example: slice_list = [[y*12+m for m in range(11,14)] for y in range(84)]
                    or
                        slice_list = [y * 12 + m for y in range(84) for m in range(11, 14)]
    """
    ds = xr.open_dataset(ncfile)
    slice_list = np.array(slice_list).flatten()
    slice_list = [int(i) for i in slice_list]
    ds_new = ds.isel(**{dim_name: slice_list})
    ds.close()
    return ds_new


if __name__ == "__main__":
    data = np.random.rand(100, 50)
    write2nc(r"test.nc", data, "data", {"time": np.linspace(0, 120, 100), "lev": np.linspace(0, 120, 50)}, "a")
