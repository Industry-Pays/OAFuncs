from typing import Union, Literal

import numpy as np
import xarray as xr
from rich import print


__all__ = ["earth_distance", "mask_shapefile", "mask_land_ocean"]


def earth_distance(lon1, lat1, lon2, lat2):
    """
    计算两点间的距离（km）
    """
    from math import asin, cos, radians, sin, sqrt
    # 将经纬度转换为弧度
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球半径（公里）
    return c * r


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
    import salem
    try:
        shp_f = salem.read_shapefile(shapefile_path)
        data_da = xr.DataArray(data_array, coords=[("latitude", latitudes), ("longitude", longitudes)])
        masked_data = data_da.salem.roi(shape=shp_f)
        return masked_data
    except Exception as e:
        print(f"[red]An error occurred: {e}[/red]")
        return None



def _normalize_lon(lon: np.ndarray) -> np.ndarray:
    """将经度转换到 [-180, 180)。"""
    lon = np.asarray(lon, dtype=float)
    return np.where(lon >= 180, lon - 360, lon)


def _land_sea_mask(
    lon: np.ndarray,
    lat: np.ndarray,
    keep: Literal["land", "ocean"],
) -> np.ndarray:
    """
    根据 1-D 或 2-D 经纬度返回布尔掩膜。
    True 表示该位置 *保留*，False 表示该位置将被掩掉。
    """
    from global_land_mask import globe
    
    lon = _normalize_lon(lon)
    lat = np.asarray(lat, dtype=float)

    # 如果输入是 1-D，则网格化；2-D 则直接使用
    if lon.ndim == 1 and lat.ndim == 1:
        lon_2d, lat_2d = np.meshgrid(lon, lat)
    elif lon.ndim == 2 and lat.ndim == 2:
        lon_2d, lat_2d = lon, lat
    else:
        raise ValueError("经纬度必须是同维度的 1-D 或 2-D 数组")

    is_ocean = globe.is_ocean(lat_2d, lon_2d)

    if keep == "land":
        mask = ~is_ocean
    elif keep == "ocean":
        mask = is_ocean
    else:
        raise ValueError("keep 只能是 'land' 或 'ocean'")

    return mask


def mask_land_ocean(
    data: xr.DataArray | xr.Dataset,
    lon: np.ndarray,
    lat: np.ndarray,
    *,  # 强制关键字参数
    keep: Literal["land", "ocean"] = "land",
) -> xr.DataArray | xr.Dataset:
    """
    根据海陆分布掩膜 xarray 对象。

    Parameters
    ----------
    data : xr.DataArray 或 xr.Dataset
        至少包含 'lat' 和 'lon' 维度/坐标的数组。
    lon : array_like
        经度，可以是 1-D 或 2-D。
    lat : array_like
        纬度，可以是 1-D 或 2-D。
    keep : {'land', 'ocean'}, optional
        指定要保留的部分，默认为 'land'。

    Returns
    -------
    掩膜后的 xr.DataArray / xr.Dataset
    """
    mask = _land_sea_mask(lon, lat, keep)

    # 用 apply_ufunc 自动对齐并广播掩膜
    return xr.apply_ufunc(
        lambda x, m: x.where(m),
        data,
        xr.DataArray(mask, dims=("lat", "lon")),
        dask="parallelized",
        keep_attrs=True,
    )

if __name__ == "__main__":
    pass
