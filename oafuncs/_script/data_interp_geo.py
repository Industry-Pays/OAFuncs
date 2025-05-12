from typing import List, Union

import numpy as np
from scipy.interpolate import NearestNDInterpolator, griddata

from oafuncs.oa_tool import PEx


def _normalize_lon(lon, ref_lon):
    """
    将经度数组 lon 归一化到与 ref_lon 相同的区间（[-180,180] 或 [0,360]）
    并在经度分界（如180/-180, 0/360）附近自动拓宽，避免插值断裂。
    """
    lon = np.asarray(lon)
    ref_lon = np.asarray(ref_lon)
    if np.nanmax(ref_lon) > 180:
        lon = np.where(lon < 0, lon + 360, lon)
    else:
        lon = np.where(lon > 180, lon - 360, lon)
    return lon


def _expand_lonlat_for_dateline(points, values):
    """
    对经度分界（如180/-180, 0/360）附近的数据进行拓宽，避免插值断裂。
    points: (N,2) [lon,lat]
    values: (N,)
    返回拓宽后的 points, values
    """
    lon = points[:, 0]
    lat = points[:, 1]
    expanded_points = [points]
    expanded_values = [values]
    if (np.nanmax(lon) > 170) and (np.nanmin(lon) < -170):
        expanded_points.append(np.column_stack((lon + 360, lat)))
        expanded_points.append(np.column_stack((lon - 360, lat)))
        expanded_values.append(values)
        expanded_values.append(values)
    if (np.nanmax(lon) > 350) and (np.nanmin(lon) < 10):
        expanded_points.append(np.column_stack((lon - 360, lat)))
        expanded_points.append(np.column_stack((lon + 360, lat)))
        expanded_values.append(values)
        expanded_values.append(values)
    points_new = np.vstack(expanded_points)
    values_new = np.concatenate(expanded_values)
    return points_new, values_new


def _interp_single_worker(*args):
    """
    用于PEx并行的单slice插值worker。
    参数: data_slice, origin_points, target_points, interpolation_method, target_shape
    球面插值：经纬度转球面坐标后插值
    """
    data_slice, origin_points, target_points, interpolation_method, target_shape = args

    # 经纬度归一化
    origin_points = origin_points.copy()
    target_points = target_points.copy()
    origin_points[:, 0] = _normalize_lon(origin_points[:, 0], target_points[:, 0])
    target_points[:, 0] = _normalize_lon(target_points[:, 0], origin_points[:, 0])

    def lonlat2xyz(lon, lat):
        lon_rad = np.deg2rad(lon)
        lat_rad = np.deg2rad(lat)
        x = np.cos(lat_rad) * np.cos(lon_rad)
        y = np.cos(lat_rad) * np.sin(lon_rad)
        z = np.sin(lat_rad)
        return np.stack([x, y, z], axis=-1)

    # 过滤掉包含 NaN 的点
    valid_mask = ~np.isnan(data_slice.ravel())
    valid_data = data_slice.ravel()[valid_mask]
    valid_points = origin_points[valid_mask]

    if len(valid_data) < 10:
        return np.full(target_shape, np.nanmean(data_slice))

    # 拓宽经度分界，避免如179/-181插值断裂
    valid_points_exp, valid_data_exp = _expand_lonlat_for_dateline(valid_points, valid_data)

    valid_xyz = lonlat2xyz(valid_points_exp[:, 0], valid_points_exp[:, 1])
    target_xyz = lonlat2xyz(target_points[:, 0], target_points[:, 1])

    # 使用 griddata 的 cubic 插值以获得更好平滑效果
    result = griddata(valid_xyz, valid_data_exp, target_xyz, method=interpolation_method).reshape(target_shape)

    # 用最近邻处理残余 NaN
    if np.isnan(result).any():
        nn_interp = NearestNDInterpolator(valid_xyz, valid_data_exp)
        nn = nn_interp(target_xyz).reshape(target_shape)
        result[np.isnan(result)] = nn[np.isnan(result)]

    return result


def interp_2d_func_geo(target_x_coordinates: Union[np.ndarray, List[float]], target_y_coordinates: Union[np.ndarray, List[float]], source_x_coordinates: Union[np.ndarray, List[float]], source_y_coordinates: Union[np.ndarray, List[float]], source_data: np.ndarray, interpolation_method: str = "cubic") -> np.ndarray:
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
    # 验证输入数据范围
    if np.nanmin(target_y_coordinates) < -90 or np.nanmax(target_y_coordinates) > 90:
        raise ValueError("[red]Target latitude must be in range [-90, 90].[/red]")
    if np.nanmin(source_y_coordinates) < -90 or np.nanmax(source_y_coordinates) > 90:
        raise ValueError("[red]Source latitude must be in range [-90, 90].[/red]")

    if len(target_y_coordinates.shape) == 1:
        target_x_coordinates, target_y_coordinates = np.meshgrid(target_x_coordinates, target_y_coordinates)
    if len(source_y_coordinates.shape) == 1:
        source_x_coordinates, source_y_coordinates = np.meshgrid(source_x_coordinates, source_y_coordinates)

    if source_x_coordinates.shape != source_data.shape[-2:] or source_y_coordinates.shape != source_data.shape[-2:]:
        raise ValueError("[red]Shape of source_data does not match shape of source_x_coordinates or source_y_coordinates.[/red]")

    target_points = np.column_stack((np.array(target_x_coordinates).ravel(), np.array(target_y_coordinates).ravel()))
    origin_points = np.column_stack((np.array(source_x_coordinates).ravel(), np.array(source_y_coordinates).ravel()))

    data_dims = len(source_data.shape)
    if data_dims < 2:
        raise ValueError(f"[red]Source data must have at least 2 dimensions, but got {data_dims}.[/red]")
    elif data_dims > 4:
        raise ValueError(f"Source data has {data_dims} dimensions, but this function currently supports only up to 4.")

    num_dims_to_add = 4 - data_dims
    new_shape = (1,) * num_dims_to_add + source_data.shape
    new_src_data = source_data.reshape(new_shape)

    t, z, y, x = new_src_data.shape

    params = []
    target_shape = target_y_coordinates.shape
    for t_index in range(t):
        for z_index in range(z):
            params.append((new_src_data[t_index, z_index], origin_points, target_points, interpolation_method, target_shape))

    with PEx() as excutor:
        result = excutor.run(_interp_single_worker, params)

    return np.squeeze(np.array(result).reshape(t, z, *target_shape))
