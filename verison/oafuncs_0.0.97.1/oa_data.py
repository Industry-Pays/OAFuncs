#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 17:12:47
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-12-13 19:11:08
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_data.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
"""

import itertools
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import salem
import xarray as xr
from scipy.interpolate import griddata
from scipy.interpolate import interp1d

__all__ = ["interp_along_dim", "interp_2d", "ensure_list", "mask_shapefile"]


def ensure_list(input_data):
    """
    Ensures that the input is converted into a list.

    If the input is already a list, it returns it directly.
    If the input is a string, it wraps it in a list and returns.
    For other types of input, it converts them to a string and then wraps in a list.

    :param input_data: The input which can be a list, a string, or any other type.
    :return: A list containing the input or the string representation of the input.
    """
    if isinstance(input_data, list):
        return input_data
    elif isinstance(input_data, str):
        return [input_data]
    else:
        # For non-list and non-string inputs, convert to string and wrap in a list
        return [str(input_data)]


def interp_along_dim(tgt_coords, src_coords, src_data, axis=-1, interp_method="linear", extrap_method="linear"):
    """
    在指定维度上执行插值和外插操作。

    Parameters:
    -----------
    tgt_coords: 1d array
        目标坐标点数组，必须是一维数组。

    src_coords: 1d or nd array
        源坐标点数组。可以是一维数组（将被广播到与src_data匹配的形状）或与src_data相同形状的多维数组。

    src_data: nd array
        源数据数组，包含要从src_coords插值到tgt_coords的现象值。

    axis: int (default -1)
        要在src_data上执行插值的轴。默认为最后一个轴。

    interp_method: str (default "linear")
        核心插值方法。
        可选值包括:
        - "linear": 线性插值（默认）
        - "nearest": 最近邻插值
        - "zero": 零阶插值
        - "slinear": 样条一阶插值
        - "quadratic": 二阶插值
        - "cubic": 三阶插值
        - "previous": 使用前一个点的值
        - "next": 使用后一个点的值
        更多选项参考scipy.interpolate.interp1d的kind参数。

    extrap_method: str (default "linear")
        核心外插方法，用于处理超出源坐标范围的目标坐标点。
        支持与interp_method相同的选项:
        - "linear": 线性外插（默认）
        - "nearest": 最近邻外插
        - "zero": 零阶外插
        - "slinear": 样条一阶外插
        - "quadratic": 二阶外插
        - "cubic": 三阶外插
        - "previous": 使用最近的前一个点的值
        - "next": 使用最近的后一个点的值

    Returns:
    --------
    array
        插值后的数据数组，形状将与src_data相同，但在axis轴上长度为len(tgt_coords)。

    Examples:
    ---------
    1D插值示例:
    >>> tgt_coords = np.array([1, 2, 3, 4])
    >>> src_coords = np.array([0, 1, 2, 3, 4, 5])
    >>> src_data = np.array([0, 1, 4, 9, 16, 25])
    >>> interp_along_dim(tgt_coords, src_coords, src_data)
    array([ 1.,  4.,  9., 16.])

    多维插值示例:
    >>> src_data = np.array([[0, 1, 4], [10, 20, 30]])
    >>> interp_along_dim(np.array([0.5, 1.5]), np.array([0, 1, 2]), src_data, axis=1)
    array([[ 0.5,  2.5],
           [15. , 25. ]])
    """
    tgt_coords = np.asarray(tgt_coords)
    if tgt_coords.ndim != 1:
        raise ValueError("tgt_coords must be a 1d array.")

    src_coords = np.asarray(src_coords)
    src_data = np.asarray(src_data)

    # 处理1维的简单情况
    if src_data.ndim == 1 and src_coords.ndim == 1:
        if len(src_coords) != len(src_data):
            raise ValueError("For 1D data, src_coords and src_data must have the same length")

        interpolator = interp1d(src_coords, src_data, kind=interp_method, fill_value="extrapolate", bounds_error=False)
        return interpolator(tgt_coords)

    # 多维情况的处理
    if src_coords.ndim == 1:
        # Expand src_coords to match src_data dimensions along the specified axis
        shape = [1] * src_data.ndim
        shape[axis] = src_coords.shape[0]
        src_coords = np.reshape(src_coords, shape)
        src_coords = np.broadcast_to(src_coords, src_data.shape)
    elif src_coords.shape != src_data.shape:
        raise ValueError("src_coords and src_data must have the same shape.")

    def apply_interp_extrap(arr):
        xp = np.moveaxis(src_coords, axis, 0)
        # 根据维度正确获取坐标
        if xp.ndim > 1:
            xp = xp[:, 0]  # 多维情况
        else:
            xp = xp  # 1维情况

        arr = np.moveaxis(arr, axis, 0)
        interpolator = interp1d(xp, arr, kind=interp_method, fill_value="extrapolate", bounds_error=False)
        interpolated = interpolator(tgt_coords)
        if extrap_method != interp_method:
            mask_extrap = (tgt_coords < xp.min()) | (tgt_coords > xp.max())
            if np.any(mask_extrap):
                extrap_interpolator = interp1d(xp, arr, kind=extrap_method, fill_value="extrapolate", bounds_error=False)
                interpolated[mask_extrap] = extrap_interpolator(tgt_coords[mask_extrap])
        return np.moveaxis(interpolated, 0, axis)

    result = np.apply_along_axis(apply_interp_extrap, axis, src_data)

    return result


def interp_2d(target_x, target_y, origin_x, origin_y, data, method="linear", parallel=True):
    """
    Perform 2D interpolation on the last two dimensions of a multi-dimensional array.

    Parameters:
    - target_x (array-like): 1D or 2D array of target grid's x-coordinates.
    - target_y (array-like): 1D or 2D array of target grid's y-coordinates.
    - origin_x (array-like): 1D or 2D array of original grid's x-coordinates.
    - origin_y (array-like): 1D or 2D array of original grid's y-coordinates.
    - data (numpy.ndarray): Multi-dimensional array where the last two dimensions correspond to the original grid.
    - method (str, optional): Interpolation method, default is 'linear'. Other options include 'nearest', 'cubic', etc.
    - parallel (bool, optional): Flag to enable parallel processing. Default is True.

    Returns:
    - interpolated_data (numpy.ndarray): Interpolated data with the same leading dimensions as the input data, but with the last two dimensions corresponding to the target grid.

    Raises:
    - ValueError: If the shape of the data does not match the shape of the origin_x or origin_y grids.

    Usage:
    - Interpolate a 2D array:
        result = interp_2d(target_x, target_y, origin_x, origin_y, data_2d)
    - Interpolate a 3D array (where the last two dimensions are spatial):
        result = interp_2d(target_x, target_y, origin_x, origin_y, data_3d)
    - Interpolate a 4D array (where the last two dimensions are spatial):
        result = interp_2d(target_x, target_y, origin_x, origin_y, data_4d)
    """

    def interp_single(data_slice, target_points, origin_points, method):
        return griddata(origin_points, data_slice.ravel(), target_points, method=method).reshape(target_y.shape)

    # 确保目标网格和初始网格都是二维的
    if len(target_y.shape) == 1:
        target_x, target_y = np.meshgrid(target_x, target_y)
    if len(origin_y.shape) == 1:
        origin_x, origin_y = np.meshgrid(origin_x, origin_y)

    # 根据经纬度网格判断输入数据的形状是否匹配
    if origin_x.shape != data.shape[-2:] or origin_y.shape != data.shape[-2:]:
        raise ValueError("Shape of data does not match shape of origin_x or origin_y.")

    # 创建网格和展平数据
    target_x, target_y = np.array(target_x), np.array(target_y)
    origin_x, origin_y = np.array(origin_x), np.array(origin_y)
    target_points = np.column_stack((target_y.ravel(), target_x.ravel()))
    origin_points = np.column_stack((origin_y.ravel(), origin_x.ravel()))

    # 根据是否并行选择不同的执行方式
    if parallel:
        with ThreadPoolExecutor(max_workers=mp.cpu_count() - 2) as executor:
            if len(data.shape) == 2:
                interpolated_data = list(executor.map(interp_single, [data], [target_points], [origin_points], [method]))
            elif len(data.shape) == 3:
                interpolated_data = list(executor.map(interp_single, [data[i] for i in range(data.shape[0])], [target_points] * data.shape[0], [origin_points] * data.shape[0], [method] * data.shape[0]))
            elif len(data.shape) == 4:
                index_combinations = list(itertools.product(range(data.shape[0]), range(data.shape[1])))
                interpolated_data = list(executor.map(interp_single, [data[i, j] for i, j in index_combinations], [target_points] * len(index_combinations), [origin_points] * len(index_combinations), [method] * len(index_combinations)))
                interpolated_data = np.array(interpolated_data).reshape(data.shape[0], data.shape[1], *target_y.shape)
    else:
        if len(data.shape) == 2:
            interpolated_data = interp_single(data, target_points, origin_points, method)
        elif len(data.shape) == 3:
            interpolated_data = np.stack([interp_single(data[i], target_points, origin_points, method) for i in range(data.shape[0])])
        elif len(data.shape) == 4:
            interpolated_data = np.stack([np.stack([interp_single(data[i, j], target_points, origin_points, method) for j in range(data.shape[1])]) for i in range(data.shape[0])])

    return np.squeeze(np.array(interpolated_data))


def mask_shapefile(data: np.ndarray, lons: np.ndarray, lats: np.ndarray, shapefile_path: str) -> xr.DataArray:
    """
    Masks a 2D data array using a shapefile.

    Parameters:
    - data: 2D numpy array of data to be masked.
    - lons: 1D numpy array of longitudes.
    - lats: 1D numpy array of latitudes.
    - shapefile_path: Path to the shapefile used for masking.

    Returns:
    - Masked xarray DataArray.
    """
    """
    https://cloud.tencent.com/developer/article/1701896
    """
    try:
        # import geopandas as gpd
        # shp_f = gpd.read_file(shapefile_path)
        shp_f = salem.read_shapefile(shapefile_path)
        data_da = xr.DataArray(data, coords=[("latitude", lats), ("longitude", lons)])
        masked_data = data_da.salem.roi(shape=shp_f)
        return masked_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    pass
    """ import time

    import matplotlib.pyplot as plt

    # 测试数据
    origin_x = np.linspace(0, 10, 11)
    origin_y = np.linspace(0, 10, 11)
    target_x = np.linspace(0, 10, 101)
    target_y = np.linspace(0, 10, 101)
    data = np.random.rand(11, 11)

    # 高维插值
    origin_x = np.linspace(0, 10, 11)
    origin_y = np.linspace(0, 10, 11)
    target_x = np.linspace(0, 10, 101)
    target_y = np.linspace(0, 10, 101)
    data = np.random.rand(10, 10, 11, 11)

    start = time.time()
    interpolated_data = interp_2d(target_x, target_y, origin_x, origin_y, data, parallel=False)
    print(f"Interpolation time: {time.time()-start:.2f}s")

    print(interpolated_data.shape)

    # 高维插值多线程
    start = time.time()
    interpolated_data = interp_2d(target_x, target_y, origin_x, origin_y, data)
    print(f"Interpolation time: {time.time()-start:.2f}s")

    print(interpolated_data.shape)
    print(interpolated_data[0, 0, :, :].shape)
    plt.figure()
    plt.contourf(target_x, target_y, interpolated_data[0, 0, :, :])
    plt.colorbar()
    plt.show() """
