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


from typing import Any, List, Union

import numpy as np
import salem
import xarray as xr
from rich import print
from scipy.interpolate import interp1d


__all__ = ["interp_along_dim", "interp_2d", "interp_2d_geo", "ensure_list", "mask_shapefile"]


def ensure_list(input_value: Any) -> List[str]:
    """
    Ensure the input is converted into a list.

    Args:
        input_value (Any): The input which can be a list, a string, or any other type.

    Returns:
        List[str]: A list containing the input or the string representation of the input.
    """
    if isinstance(input_value, list):
        return input_value
    elif isinstance(input_value, str):
        return [input_value]
    else:
        return [str(input_value)]


def interp_along_dim(
    target_coordinates: np.ndarray,
    source_coordinates: Union[np.ndarray, List[float]],
    source_data: np.ndarray,
    interpolation_axis: int = -1,
    interpolation_method: str = "linear",
    extrapolation_method: str = "linear",
) -> np.ndarray:
    """
    Perform interpolation and extrapolation along a specified dimension.

    Args:
        target_coordinates (np.ndarray): 1D array of target coordinate points.
        source_coordinates (Union[np.ndarray, List[float]]): Source coordinate points (1D or ND array).
        source_data (np.ndarray): Source data array to interpolate.
        interpolation_axis (int, optional): Axis to perform interpolation on. Defaults to -1.
        interpolation_method (str, optional): Interpolation method. Defaults to "linear".
        extrapolation_method (str, optional): Extrapolation method. Defaults to "linear".

    Returns:
        np.ndarray: Interpolated data array.

    Raises:
        ValueError: If input dimensions or shapes are invalid.

    Examples:
        >>> target_coordinates = np.array([1, 2, 3])
        >>> source_coordinates = np.array([0, 1, 2, 3])
        >>> source_data = np.array([10, 20, 30, 40])
        >>> result = interp_along_dim(target_coordinates, source_coordinates, source_data)
        >>> print(result)  # Expected output: [20.0, 30.0]
    """
    target_coordinates = np.asarray(target_coordinates)
    if target_coordinates.ndim != 1:
        raise ValueError("[red]target_coordinates must be a 1D array.[/red]")

    source_coordinates = np.asarray(source_coordinates)
    source_data = np.asarray(source_data)

    if source_data.ndim == 1 and source_coordinates.ndim == 1:
        if len(source_coordinates) != len(source_data):
            raise ValueError("[red]For 1D data, source_coordinates and source_data must have the same length.[/red]")

        interpolator = interp1d(source_coordinates, source_data, kind=interpolation_method, fill_value="extrapolate", bounds_error=False)
        return interpolator(target_coordinates)

    if source_coordinates.ndim == 1:
        shape = [1] * source_data.ndim
        shape[interpolation_axis] = source_coordinates.shape[0]
        source_coordinates = np.reshape(source_coordinates, shape)
        source_coordinates = np.broadcast_to(source_coordinates, source_data.shape)
    elif source_coordinates.shape != source_data.shape:
        raise ValueError("[red]source_coordinates and source_data must have the same shape.[/red]")

    def apply_interp_extrap(arr: np.ndarray) -> np.ndarray:
        xp = np.moveaxis(source_coordinates, interpolation_axis, 0)
        xp = xp[:, 0] if xp.ndim > 1 else xp
        arr = np.moveaxis(arr, interpolation_axis, 0)
        interpolator = interp1d(xp, arr, kind=interpolation_method, fill_value="extrapolate", bounds_error=False)
        interpolated = interpolator(target_coordinates)
        if extrapolation_method != interpolation_method:
            mask_extrap = (target_coordinates < xp.min()) | (target_coordinates > xp.max())
            if np.any(mask_extrap):
                extrap_interpolator = interp1d(xp, arr, kind=extrapolation_method, fill_value="extrapolate", bounds_error=False)
                interpolated[mask_extrap] = extrap_interpolator(target_coordinates[mask_extrap])
        return np.moveaxis(interpolated, 0, interpolation_axis)

    return np.apply_along_axis(apply_interp_extrap, interpolation_axis, source_data)


def interp_2d(
    target_x_coordinates: Union[np.ndarray, List[float]],
    target_y_coordinates: Union[np.ndarray, List[float]],
    source_x_coordinates: Union[np.ndarray, List[float]],
    source_y_coordinates: Union[np.ndarray, List[float]],
    source_data: np.ndarray,
    interpolation_method: str = "cubic",
) -> np.ndarray:
    """
    Perform 2D interpolation on the last two dimensions of a multi-dimensional array.

    Args:
        target_x_coordinates (Union[np.ndarray, List[float]]): Target grid's x-coordinates.
        target_y_coordinates (Union[np.ndarray, List[float]]): Target grid's y-coordinates.
        source_x_coordinates (Union[np.ndarray, List[float]]): Original grid's x-coordinates.
        source_y_coordinates (Union[np.ndarray, List[float]]): Original grid's y-coordinates.
        source_data (np.ndarray): Multi-dimensional array with the last two dimensions as spatial.
            >>> must be [y, x] or [*, y, x] or [*, *, y, x]
        interpolation_method (str, optional): Interpolation method. Defaults to "cubic".
            >>> optional: 'linear', 'nearest', 'cubic', 'quintic', etc.
        use_parallel (bool, optional): Enable parallel processing. Defaults to True.

    Returns:
        np.ndarray: Interpolated data array.

    Raises:
        ValueError: If input shapes are invalid.

    Examples:
        >>> target_x_coordinates = np.array([1, 2, 3])
        >>> target_y_coordinates = np.array([4, 5, 6])
        >>> source_x_coordinates = np.array([7, 8, 9])
        >>> source_y_coordinates = np.array([10, 11, 12])
        >>> source_data = np.random.rand(3, 3)
        >>> result = interp_2d(target_x_coordinates, target_y_coordinates, source_x_coordinates, source_y_coordinates, source_data)
        >>> print(result.shape)  # Expected output: (3, 3)
    """
    from ._script.data_interp import interp_2d_func
    
    return interp_2d_func(
        target_x_coordinates=target_x_coordinates,
        target_y_coordinates=target_y_coordinates,
        source_x_coordinates=source_x_coordinates,
        source_y_coordinates=source_y_coordinates,
        source_data=source_data,
        interpolation_method=interpolation_method,
    )

def interp_2d_geo(target_x_coordinates: Union[np.ndarray, List[float]], target_y_coordinates: Union[np.ndarray, List[float]], source_x_coordinates: Union[np.ndarray, List[float]], source_y_coordinates: Union[np.ndarray, List[float]], source_data: np.ndarray, interpolation_method: str = "cubic") -> np.ndarray:
    """
    Perform 2D interpolation on the last two dimensions of a multi-dimensional array (spherical coordinates).
    使用球面坐标系进行插值，适用于全球尺度的地理数据，能正确处理经度跨越日期线的情况。

    Args:
        target_x_coordinates (Union[np.ndarray, List[float]]): Target grid's longitude (-180 to 180 or 0 to 360).
        target_y_coordinates (Union[np.ndarray, List[float]]): Target grid's latitude (-90 to 90).
        source_x_coordinates (Union[np.ndarray, List[float]]): Original grid's longitude (-180 to 180 or 0 to 360).
        source_y_coordinates (Union[np.ndarray, List[float]]): Original grid's latitude (-90 to 90).
        source_data (np.ndarray): Multi-dimensional array with the last two dimensions as spatial.
        interpolation_method (str, optional): Interpolation method. Defaults to "cubic".
            >>> optional: 'linear', 'nearest', 'cubic', 'quintic', etc.

    Returns:
        np.ndarray: Interpolated data array.

    Raises:
        ValueError: If input shapes are invalid.

    Examples:
        >>> # 创建一个全球网格示例
        >>> target_lon = np.arange(-180, 181, 1)  # 1度分辨率目标网格
        >>> target_lat = np.arange(-90, 91, 1)
        >>> source_lon = np.arange(-180, 181, 5)  # 5度分辨率源网格
        >>> source_lat = np.arange(-90, 91, 5)
        >>> # 创建一个简单的数据场 (例如温度场)
        >>> source_data = np.cos(np.deg2rad(source_lat.reshape(-1, 1))) * np.cos(np.deg2rad(source_lon))
        >>> # 插值到高分辨率网格
        >>> result = interp_2d_geo(target_lon, target_lat, source_lon, source_lat, source_data)
        >>> print(result.shape)  # Expected output: (181, 361)
    """
    from ._script.data_interp_geo import interp_2d_func_geo
    interp_2d_func_geo(
        target_x_coordinates=target_x_coordinates,
        target_y_coordinates=target_y_coordinates,
        source_x_coordinates=source_x_coordinates,
        source_y_coordinates=source_y_coordinates,
        source_data=source_data,
        interpolation_method=interpolation_method,
    )

def mask_shapefile(
    data_array: np.ndarray,
    longitudes: np.ndarray,
    latitudes: np.ndarray,
    shapefile_path: str,
) -> Union[xr.DataArray, None]:
    """
    Mask a 2D data array using a shapefile.

    Args:
        data_array (np.ndarray): 2D array of data to be masked.
        longitudes (np.ndarray): 1D array of longitudes.
        latitudes (np.ndarray): 1D array of latitudes.
        shapefile_path (str): Path to the shapefile used for masking.

    Returns:
        Union[xr.DataArray, None]: Masked xarray DataArray or None if an error occurs.

    Raises:
        FileNotFoundError: If the shapefile does not exist.
        ValueError: If the data dimensions do not match the coordinates.

    Examples:
        >>> data_array = np.random.rand(10, 10)
        >>> longitudes = np.linspace(-180, 180, 10)
        >>> latitudes = np.linspace(-90, 90, 10)
        >>> shapefile_path = "path/to/shapefile.shp"
        >>> masked_data = mask_shapefile(data_array, longitudes, latitudes, shapefile_path)
        >>> print(masked_data)  # Expected output: Masked DataArray

    """
    try:
        shp_f = salem.read_shapefile(shapefile_path)
        data_da = xr.DataArray(data_array, coords=[("latitude", latitudes), ("longitude", longitudes)])
        masked_data = data_da.salem.roi(shape=shp_f)
        return masked_data
    except Exception as e:
        print(f"[red]An error occurred: {e}[/red]")
        return None


if __name__ == "__main__":
    pass
