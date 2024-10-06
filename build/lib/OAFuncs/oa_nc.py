#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 14:58:50
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-10-06 19:11:30
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_nc.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''



import netCDF4 as nc
import os
import numpy as np
import xarray as xr

__all__ = ['get_var', 'extract5nc', 'write2nc']

def get_var(file, *vars):
    '''
    datas_ecm = get_var(file_ecm, 'h', 't', 'u', 'v')
    '''
    ds = xr.open_dataset(file)
    datas = []
    for var in vars:
        data = ds[var]
        datas.append(data)
    ds.close()
    return datas


def extract5nc(file, varname):
    '''
    提取nc文件中的变量，再将相应维度提取，建立字典
    返回变量及字典
    '''
    ds = xr.open_dataset(file)
    vardata = ds[varname]
    dims = vardata.dims
    dimdict = {}
    for dim in dims:
        dimdict[dim] = ds[dim].values
    ds.close()
    return np.array(vardata), dimdict


def _numpy_to_nc_type(numpy_type):
    """将NumPy数据类型映射到NetCDF数据类型"""
    numpy_to_nc = {
        'float32': 'f4',
        'float64': 'f8',
        'int8': 'i1',
        'int16': 'i2',
        'int32': 'i4',
        'int64': 'i8',
        'uint8': 'u1',
        'uint16': 'u2',
        'uint32': 'u4',
        'uint64': 'u8',
    }
    return numpy_to_nc.get(str(numpy_type), 'f4')  # 默认使用 'float32'


def write2nc(file, data, varname, coords, mode):
    '''
    file: 文件路径
    data: 数据
    varname: 变量名
    coords: 坐标，字典，键为维度名称，值为坐标数据
    mode: 写入模式，'w'为写入，'a'为追加
    '''
    # 判断mode是写入还是追加
    if mode == 'w':
        if os.path.exists(file):
            os.remove(file)
            print("Warning: File already exists. Deleting it.")
    elif mode == 'a':
        if not os.path.exists(file):
            print("Warning: File doesn't exist. Creating a new file.")
            mode = 'w'

    # 打开 NetCDF 文件
    with nc.Dataset(file, mode, format="NETCDF4") as ncfile:
        # 处理坐标
        for dim, coord_data in coords.items():
            add_coords = True
            # 判断坐标是否存在，若存在，则替换/报错
            if ncfile.dimensions:
                # 返回字典，字典、列表、元组若为空，都表示False
                if dim in ncfile.dimensions:
                    # del nc.dimensions[dim]
                    if len(coord_data) != len(ncfile.dimensions[dim]):
                        raise ValueError(
                            "Length of coordinate does not match the dimension length.")
                    else:
                        add_coords = False
                        print(
                            f"Warning: Coordinate '{dim}' already exists. Replacing it.")
                        ncfile.variables[dim][:] = np.array(coord_data)
            if add_coords:
                # 创建新坐标
                ncfile.createDimension(dim, len(coord_data))
                ncfile.createVariable(dim, _numpy_to_nc_type(
                    coord_data.dtype), (dim,))
                ncfile.variables[dim][:] = np.array(coord_data)

        # 判断变量是否存在，若存在，则删除原变量
        add_var = True
        if varname in ncfile.variables:
            print(f"Warning: Variable '{varname}' already exists.")
            if data.shape != ncfile.variables[varname].shape:
                raise ValueError(
                    "Shape of data does not match the variable shape.")
            else:
                # 写入数据
                ncfile.variables[varname][:] = data
                add_var = False
                print(
                    f"Warning: Variable '{varname}' already exists. Replacing it.")

        if add_var:
            # 创建变量及其维度
            dim_names = tuple(coords.keys())  # 使用coords传入的维度名称
            ncfile.createVariable(
                varname, _numpy_to_nc_type(data.dtype), dim_names)
            # ncfile.createVariable('data', 'f4', ('time','lev'))

            # 写入数据
            ncfile.variables[varname][:] = data

        # 判断维度是否匹配
        if len(data.shape) != len(coords):
            raise ValueError(
                "Number of dimensions does not match the data shape.")




if __name__ == '__main__':
    
    data = np.random.rand(100, 50)
    write2nc(r'test.nc', data,
         'data', {'time': np.linspace(0, 120, 100), 'lev': np.linspace(0, 120, 50)}, 'a')

