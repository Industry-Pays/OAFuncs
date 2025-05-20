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
from rich import print
from typing import Dict, List, Union

__all__ = ["get_var", "extract", "save", "merge", "modify", "rename", "check", "convert_longitude", "isel", "draw"]


def get_var(file, *vars):
    """
    Description:
        Read variables from nc file
    Parameters:
        file: str, file path
        *vars: str, variable name or variable names; should be in same size
    Example:
        datas = get_var(file_ecm, 'h', 't', 'u', 'v')
    Return:
        datas: list, variable data
    """
    ds = xr.open_dataset(file)
    datas = []
    for var in vars:
        data = ds[var]
        datas.append(data)
    ds.close()
    return datas


def extract(file, varname, only_value=True):
    """
    Description:
        Extract variables from nc file
        Return the variable and coordinate dictionary
    Parameters:
        file: str, file path
        varname: str, variable name
        only_value: bool, whether to keep only the value of the variable and dimension
    Example:
        data, dimdict = extract('test.nc', 'h')
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


def save(file, data, varname=None, coords=None, mode="w", scale_offset_switch=True, compile_switch=True):
    """
    Description:
        Write data to NetCDF file
    Parameters:
        file: str, file path
        data: data
        varname: str, variable name
        coords: dict, coordinates, key is the dimension name, value is the coordinate data
        mode: str, write mode, 'w' for write, 'a' for append
        scale_offset_switch: bool, whether to use scale_factor and add_offset, default is True
        compile_switch: bool, whether to use compression parameters, default is True
    Example:
        save(r'test.nc', data, 'u', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'a')
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


def merge(file_list: Union[str, List[str]], var_name: Union[str, List[str], None] = None, dim_name: str = "time", target_filename: str = "merged.nc", chunk_config: Dict = {"time": 1000}, compression: Union[bool, Dict] = True, sanity_check: bool = True, overwrite: bool = True, parallel: bool = True) -> None:
    """
    NetCDF合并函数

    Parameters:
        file_list: 文件路径列表或单个文件路径
        var_name: 需要合并的变量（单个变量名/变量列表/None表示全部）
        dim_name: 合并维度，默认为'time'
        target_filename: 输出文件路径
        chunk_config: Dask分块配置，如{"time": 1000}
        compression: 压缩配置（True启用默认压缩，或自定义编码字典）
        sanity_check: 是否执行数据完整性校验
        overwrite: 是否覆盖已存在文件
        parallel: 是否启用并行处理

    Example:
        merge(["data1.nc", "data2.nc"],
             var_name=["temp", "salt"],
             target_filename="result.nc",
             chunk_config={"time": 500})
    """
    from ._script.netcdf_merge import merge as nc_merge
    nc_merge(file_list, var_name, dim_name, target_filename, chunk_config, compression, sanity_check, overwrite, parallel)


def _modify_var(nc_file_path, variable_name, new_value):
    """
    Description:
        Modify the value of a variable in a NetCDF file using the netCDF4 library.

    Parameters:
        nc_file_path (str): The path to the NetCDF file.
        variable_name (str): The name of the variable to be modified.
        new_value (numpy.ndarray): The new value of the variable.

    Example:
        modify_var('test.nc', 'u', np.random.rand(100, 50))
    """
    try:
        # Open the NetCDF file
        with nc.Dataset(nc_file_path, "r+") as dataset:
            # Check if the variable exists
            if variable_name not in dataset.variables:
                raise ValueError(f"Variable '{variable_name}' not found in the NetCDF file.")
            # Get the variable to be modified
            variable = dataset.variables[variable_name]
            # Check if the shape of the new value matches the variable's shape
            if variable.shape != new_value.shape:
                raise ValueError(f"Shape mismatch: Variable '{variable_name}' has shape {variable.shape}, "
                                 f"but new value has shape {new_value.shape}.")
            # Modify the value of the variable
            variable[:] = new_value
        print(f"Successfully modified variable '{variable_name}' in '{nc_file_path}'.")
    except Exception as e:
        print(f"An error occurred while modifying variable '{variable_name}' in '{nc_file_path}': {e}")


def _modify_attr(nc_file_path, variable_name, attribute_name, attribute_value):
    """
    Description:
        Add or modify an attribute of a variable in a NetCDF file using the netCDF4 library.

    Parameters:
        nc_file_path (str): The path to the NetCDF file.
        variable_name (str): The name of the variable to be modified.
        attribute_name (str): The name of the attribute to be added or modified.
        attribute_value (any): The value of the attribute.

    Example:
        modify_attr('test.nc', 'temperature', 'long_name', 'Temperature in Celsius')
    """
    try:
        with nc.Dataset(nc_file_path, "r+") as ds:
            # Check if the variable exists
            if variable_name not in ds.variables:
                raise ValueError(f"Variable '{variable_name}' not found in the NetCDF file.")
            # Get the variable
            variable = ds.variables[variable_name]
            # Add or modify the attribute
            variable.setncattr(attribute_name, attribute_value)
        print(f"Successfully modified attribute '{attribute_name}' of variable '{variable_name}' in '{nc_file_path}'.")
    except Exception as e:
        print(f"[red]Error:[/red] Failed to modify attribute '{attribute_name}' of variable '{variable_name}' "
              f"in file '{nc_file_path}'. [bold]Details:[/bold] {e}")


def modify(nc_file, var_name, attr_name=None, new_value=None):
    """
    Description:
        Modify the value of a variable or the value of an attribute in a NetCDF file.

    Parameters:
        nc_file (str): The path to the NetCDF file.
        var_name (str): The name of the variable to be modified.
        attr_name (str): The name of the attribute to be modified. If None, the variable value will be modified.
        new_value (any): The new value of the variable or attribute.

    Example:
        modify('test.nc', 'temperature', 'long_name', 'Temperature in Celsius')
        modify('test.nc', 'temperature', None, np.random.rand(100, 50))
    """
    try:
        if attr_name is None:
            _modify_var(nc_file, var_name, new_value)
        else:
            _modify_attr(nc_file, var_name, attr_name, new_value)
    except Exception as e:
        print(f"An error occurred while modifying '{var_name}' in '{nc_file}': {e}")


def rename(ncfile_path, old_name, new_name):
    """
    Description:
        Rename a variable and/or dimension in a NetCDF file.

    Parameters:
        ncfile_path (str): The path to the NetCDF file.
        old_name (str): The current name of the variable or dimension.
        new_name (str): The new name to assign to the variable or dimension.

    example:
        rename('test.nc', 'temperature', 'temp')
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


def check(ncfile: str, delete_switch: bool = False, print_switch: bool = True) -> bool:
    """
    Check if a NetCDF file is corrupted with enhanced error handling.

    Handles HDF5 library errors gracefully without terminating program.
    """
    is_valid = False

    if not os.path.exists(ncfile):
        if print_switch:
            print(f"[#ffeac5]Local file missing: [#009d88]{ncfile}")
            # 提示：提示文件缺失也许是正常的，这只是检查文件是否存在于本地
            print("[#d6d9fd]Note: File missing may be normal, this is just to check if the file exists locally.")
        return False

    try:
        # # 深度验证文件结构
        # with nc.Dataset(ncfile, "r") as ds:
        #     # 显式检查文件结构完整性
        #     ds.sync()  # 强制刷新缓冲区
        #     ds.close()  # 显式关闭后重新打开验证

        # 二次验证确保变量可访问
        with nc.Dataset(ncfile, "r") as ds_verify:
            if not ds_verify.variables:
                if print_switch:
                    print(f"[red]Empty variables: {ncfile}[/red]")
            else:
                # 尝试访问元数据
                _ = ds_verify.__dict__
                # 抽样检查第一个变量
                for var in ds_verify.variables.values():
                    _ = var.shape  # 触发实际数据访问
                    break
                is_valid = True

    except Exception as e:  # 捕获所有异常类型
        if print_switch:
            print(f"[red]HDF5 validation failed for {ncfile}: {str(e)}[/red]")
        error_type = type(e).__name__
        if "HDF5" in error_type or "h5" in error_type.lower():
            if print_switch:
                print(f"[red]Critical HDF5 structure error detected in {ncfile}[/red]")

    # 安全删除流程
    if not is_valid:
        if delete_switch:
            try:
                os.remove(ncfile)
                if print_switch:
                    print(f"[red]Removed corrupted file: {ncfile}[/red]")
            except Exception as del_error:
                if print_switch:
                    print(f"[red]Failed to delete corrupted file: {ncfile} - {str(del_error)}[/red]")
        return False

    return True


def convert_longitude(ds, lon_name="longitude", convert=180):
    """
    Description:
        Convert the longitude array to a specified range.

    Parameters:
        ds (xarray.Dataset): The xarray dataset containing the longitude data.
        lon_name (str): The name of the longitude variable, default is "longitude".
        convert (int): The target range to convert to, can be 180 or 360, default is 180.

    Returns:
        xarray.Dataset: The xarray dataset with the converted longitude.
    """
    to_which = int(convert)
    if to_which not in [180, 360]:
        raise ValueError("convert value must be '180' or '360'")

    if to_which == 180:
        ds = ds.assign_coords({lon_name: (ds[lon_name] + 180) % 360 - 180})
    elif to_which == 360:
        ds = ds.assign_coords({lon_name: (ds[lon_name] + 360) % 360})

    return ds.sortby(lon_name)


def isel(ncfile, dim_name, slice_list):
    """
    Description:
        Choose the data by the index of the dimension

    Parameters:
        ncfile: str, the path of the netCDF file
        dim_name: str, the name of the dimension
        slice_list: list, the index of the dimension

    Example:
        slice_list = [[y*12+m for m in range(11,14)] for y in range(84)]
        slice_list = [y * 12 + m for y in range(84) for m in range(11, 14)]
        isel(ncfile, 'time', slice_list)
    """
    ds = xr.open_dataset(ncfile)
    slice_list = np.array(slice_list).flatten()
    slice_list = [int(i) for i in slice_list]
    ds_new = ds.isel(**{dim_name: slice_list})
    ds.close()
    return ds_new


def draw(output_dir=None, dataset=None, ncfile=None, xyzt_dims=("longitude", "latitude", "level", "time"), plot_type="contourf",fixed_colorscale=False):
    """
    Description:
        Draw the data in the netCDF file

    Parameters:
        ncfile: str, the path of the netCDF file
        output_dir: str, the path of the output directory
        x_dim: str, the name of the x dimension
        y_dim: str, the name of the y dimension
        z_dim: str, the name of the z dimension
        t_dim: str, the name of the t dimension
        plot_type: str, the type of the plot, default is "contourf" (contourf, contour)
        fixed_colorscale: bool, whether to use fixed colorscale, default is False

    Example:
        draw(ncfile, output_dir, x_dim="longitude", y_dim="latitude", z_dim="level", t_dim="time", fixed_colorscale=False)
    """
    from ._script.plot_dataset import func_plot_dataset
    if output_dir is None:
        output_dir = str(os.getcwd())
    if isinstance(xyzt_dims, (list, tuple)):
        xyzt_dims = tuple(xyzt_dims)
    else:
        raise ValueError("xyzt_dims must be a list or tuple")
    if dataset is not None:
        func_plot_dataset(dataset, output_dir, xyzt_dims, plot_type, fixed_colorscale)
    else:
        if ncfile is not None:
            if check(ncfile):
                ds = xr.open_dataset(ncfile)
                func_plot_dataset(ds, output_dir, xyzt_dims, plot_type, fixed_colorscale)
            else:
                print(f"Invalid file: {ncfile}")
        else:
            print("No dataset or file provided.")


if __name__ == "__main__":
    data = np.random.rand(100, 50)
    save(r"test.nc", data, "data", {"time": np.linspace(0, 120, 100), "lev": np.linspace(0, 120, 50)}, "a")
