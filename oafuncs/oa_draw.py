#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 17:26:11
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-11-21 13:10:47
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_draw.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
"""

import warnings

import cv2
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
from rich import print

__all__ = ["fig_minus", "gif", "add_cartopy", "add_gridlines", "MidpointNormalize", "add_lonlat_unit"]

warnings.filterwarnings("ignore")


def fig_minus(x_axis: plt.Axes = None, y_axis: plt.Axes = None, colorbar: mpl.colorbar.Colorbar = None, decimal_places: int = None, add_spacing: bool = False) -> plt.Axes | mpl.colorbar.Colorbar | None:
    """Replace negative signs with minus signs in axis tick labels.

    Args:
        x_axis (plt.Axes, optional): Matplotlib x-axis object to modify.
        y_axis (plt.Axes, optional): Matplotlib y-axis object to modify.
        colorbar (mpl.colorbar.Colorbar, optional): Matplotlib colorbar object to modify.
        decimal_places (int, optional): Number of decimal places to display.
        add_spacing (bool, optional): Whether to add spaces before non-negative numbers.

    Returns:
        plt.Axes | mpl.colorbar.Colorbar | None: The modified axis or colorbar object.

    Example:
        >>> fig_minus(x_axis=ax, y_axis=None, colorbar=colorbar, decimal_places=2, add_spacing=True)
    """
    # Determine which object to use and get its ticks
    if x_axis is not None:
        current_ticks = x_axis.get_xticks()
    if y_axis is not None:
        current_ticks = y_axis.get_yticks()
    if colorbar is not None:
        current_ticks = colorbar.get_ticks()

    # Find index for adding space to non-negative values if needed
    if add_spacing:
        index = 0
        for i, tick in enumerate(current_ticks):
            if tick >= 0:
                index = i
                break

    # Format according to decimal places if specified
    if decimal_places is not None:
        current_ticks = [f"{val:.{decimal_places}f}" if val != 0 else "0" for val in current_ticks]

    # Replace negative signs with minus signs
    out_ticks = [f"{val}".replace("-", "\u2212") for val in current_ticks]

    # Add spaces before non-negative values if specified
    if add_spacing:
        out_ticks[index:] = ["  " + m for m in out_ticks[index:]]

    # Apply formatted ticks to the appropriate object
    if x_axis is not None:
        x_axis.set_xticklabels(out_ticks)
    if y_axis is not None:
        y_axis.set_yticklabels(out_ticks)
    if colorbar is not None:
        colorbar.set_ticklabels(out_ticks)

    print("[green]Axis tick labels updated successfully.[/green]")
    return x_axis or y_axis or colorbar


def gif(image_paths: list[str], output_gif_name: str, frame_duration: float = 200, resize_dimensions: tuple[int, int] = None) -> None:
    """Create a GIF from a list of images.

    Args:
        image_paths (list[str]): List of image file paths.
        output_gif_name (str): Name of the output GIF file.
        frame_duration (float): Duration of each frame in milliseconds.
        resize_dimensions (tuple[int, int], optional): Resize dimensions (width, height). Defaults to None.

    Returns:
        None

    Example:
        >>> gif(['image1.png', 'image2.png'], 'output.gif', frame_duration=200, resize_dimensions=(800, 600))
    """
    import imageio.v2 as imageio
    import numpy as np
    from PIL import Image

    frames = []

    # 获取目标尺寸
    if resize_dimensions is None and image_paths:
        # 使用第一张图片的尺寸作为标准
        with Image.open(image_paths[0]) as img:
            resize_dimensions = img.size

    # 读取并调整所有图片的尺寸
    for image_name in image_paths:
        with Image.open(image_name) as img:
            if resize_dimensions:
                img = img.resize(resize_dimensions, Image.LANCZOS)
            frames.append(np.array(img))

    # 修改此处：明确使用 frame_duration 值，并将其作为每帧的持续时间（以秒为单位）
    # 某些版本的 imageio 可能需要以毫秒为单位，或者使用 fps 参数
    try:
        # 先尝试直接使用 frame_duration 参数（以秒为单位）
        imageio.mimsave(output_gif_name, frames, format="GIF", duration=frame_duration)
    except Exception as e:
        print(f"[yellow]Warning:[/yellow] Attempting to use fps parameter instead of duration: {e}")
        # 如果失败，尝试使用 fps 参数（fps = 1/frame_duration）
        fps = 1.0 / frame_duration if frame_duration > 0 else 5.0
        imageio.mimsave(output_gif_name, frames, format="GIF", fps=fps)

    print(f"[green]GIF created successfully![/green] Size: {resize_dimensions}, Frame interval: {frame_duration} ms")
    return


def movie(image_files, output_video_path, fps):
    """
    从图像文件列表创建视频。

    Args:
        image_files (list): 按顺序排列的图像文件路径列表。
        output_video_path (str): 输出视频文件的路径 (例如 'output.mp4')。
        fps (int): 视频的帧率。
    """
    if not image_files:
        print("错误：图像文件列表为空。")
        return

    # 读取第一张图片以获取帧尺寸
    try:
        frame = cv2.imread(image_files[0])
        if frame is None:
            print(f"错误：无法读取第一张图片：{image_files[0]}")
            return
        height, width, layers = frame.shape
        size = (width, height)
        print(f"视频尺寸设置为：{size}")
    except Exception as e:
        print(f"读取第一张图片时出错：{e}")
        return

    # 选择编解码器并创建VideoWriter对象
    # 对于 .mp4 文件，常用 'mp4v' 或 'avc1'
    # 对于 .avi 文件，常用 'XVID' 或 'MJPG'
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # 或者尝试 'avc1', 'XVID' 等
    out = cv2.VideoWriter(output_video_path, fourcc, fps, size)

    if not out.isOpened():
        print(f"错误：无法打开视频文件进行写入：{output_video_path}")
        print("请检查编解码器 ('fourcc') 是否受支持以及路径是否有效。")
        return

    print(f"开始将图像写入视频：{output_video_path}...")
    for i, filename in enumerate(image_files):
        try:
            frame = cv2.imread(filename)
            if frame is None:
                print(f"警告：跳过无法读取的图像：{filename}")
                continue
            # 确保帧尺寸与初始化时相同，如果需要可以调整大小
            current_height, current_width, _ = frame.shape
            if (current_width, current_height) != size:
                print(f"警告：图像 {filename} 的尺寸 ({current_width}, {current_height}) 与初始尺寸 {size} 不同。将调整大小。")
                frame = cv2.resize(frame, size)

            out.write(frame)
            # 打印进度（可选）
            if (i + 1) % 50 == 0 or (i + 1) == len(image_files):
                print(f"已处理 {i + 1}/{len(image_files)} 帧")

        except Exception as e:
            print(f"处理图像 {filename} 时出错：{e}")
            continue  # 跳过有问题的帧

    # 释放资源
    out.release()
    print(f"视频创建成功：{output_video_path}")


def add_lonlat_unit(longitudes: list[float] = None, latitudes: list[float] = None, decimal_places: int = 2) -> tuple[list[str], list[str]] | list[str]:
    """Convert longitude and latitude values to formatted string labels.

    Args:
        longitudes (list[float], optional): List of longitude values to format.
        latitudes (list[float], optional): List of latitude values to format.
        decimal_places (int, optional): Number of decimal places to display. Defaults to 2.

    Returns:
        tuple[list[str], list[str]] | list[str]: Formatted longitude and/or latitude labels.
            Returns a tuple of two lists if both longitudes and latitudes are provided,
            otherwise returns a single list of formatted values.

    Examples:
        >>> add_lonlat_unit(longitudes=[120, 180], latitudes=[30, 60], decimal_places=1)
        (['120.0°E', '180.0°'], ['30.0°N', '60.0°N'])
        >>> add_lonlat_unit(longitudes=[120, -60])
        ['120.00°E', '60.00°W']
    """

    def _format_longitude(longitude_values: list[float]) -> list[str] | str:
        """Format longitude values to string labels with directional indicators.

        Converts numerical longitude values to formatted strings with degree symbols
        and East/West indicators. Values outside the -180 to 180 range are normalized.

        Args:
            longitude_values: List of longitude values to format.

        Returns:
            List of formatted strings if input contains multiple values,
            or a single string if input contains just one value.
        """
        out_list = []
        for x in longitude_values:
            if x > 180 or x < -180:
                print(f"[yellow]Warning:[/yellow] Longitude value {x} outside normal range (-180 to 180)")
                x = ((x + 180) % 360) - 180  # Normalize to -180 to 180 range

            degrees = round(abs(x), decimal_places)
            direction = "E" if x >= 0 else "W"
            out_list.append(f"{degrees:.{decimal_places}f}°{direction}" if x != 0 and x != 180 else f"{degrees}°")
        return out_list if len(out_list) > 1 else out_list[0]

    def _format_latitude(latitude_values: list[float]) -> list[str] | str:
        """Format latitude values to string labels with directional indicators.

        Converts numerical latitude values to formatted strings with degree symbols
        and North/South indicators. Values outside the -90 to 90 range are normalized.

        Args:
            latitude_values (list[float]): List of latitude values to format

        Returns:
            list[str] | str: List of formatted strings if input contains multiple values,
                             or a single string if input contains just one value
        """
        out_list = []
        for y in latitude_values:
            if y > 90 or y < -90:
                print(f"[yellow]Warning:[/yellow] Latitude value {y} outside valid range (-90 to 90)")
                y = min(max(y % 180 - 90, -90), 90)  # Normalize to -90 to 90 range

            degrees = round(abs(y), decimal_places)
            direction = "N" if y >= 0 else "S"
            out_list.append(f"{degrees:.{decimal_places}f}°{direction}" if y != 0 else f"{degrees}°")
        return out_list if len(out_list) > 1 else out_list[0]

    # Input validation
    if longitudes is not None and not isinstance(longitudes, list):
        longitudes = [longitudes]  # Convert single value to list
    if latitudes is not None and not isinstance(latitudes, list):
        latitudes = [latitudes]  # Convert single value to list

    if longitudes and latitudes:
        result = _format_longitude(longitudes), _format_latitude(latitudes)
    elif longitudes:
        result = _format_longitude(longitudes)
    elif latitudes:
        result = _format_latitude(latitudes)
    else:
        result = []

    print("[green]Longitude and latitude values formatted successfully.[/green]")
    return result


def add_gridlines(axes: plt.Axes, longitude_lines: list[float] = None, latitude_lines: list[float] = None, map_projection: ccrs.Projection = ccrs.PlateCarree(), line_color: str = "k", line_alpha: float = 0.5, line_style: str = "--", line_width: float = 0.5) -> tuple[plt.Axes, mpl.ticker.Locator]:
    """Add gridlines to a map.

    Args:
        axes (plt.Axes): The axes to add gridlines to.
        longitude_lines (list[float], optional): List of longitude positions for gridlines.
        latitude_lines (list[float], optional): List of latitude positions for gridlines.
        map_projection (ccrs.Projection, optional): Coordinate reference system. Defaults to PlateCarree.
        line_color (str, optional): Line color. Defaults to "k".
        line_alpha (float, optional): Line transparency. Defaults to 0.5.
        line_style (str, optional): Line style. Defaults to "--".
        line_width (float, optional): Line width. Defaults to 0.5.

    Returns:
        tuple[plt.Axes, mpl.ticker.Locator]: The axes and gridlines objects.

    Example:
        >>> add_gridlines(axes, longitude_lines=[0, 30], latitude_lines=[-90, 90], map_projection=ccrs.PlateCarree())
        >>> axes, gl = add_gridlines(axes, longitude_lines=[0, 30], latitude_lines=[-90, 90])
    """
    from matplotlib import ticker as mticker

    # add gridlines
    gl = axes.gridlines(crs=map_projection, draw_labels=True, linewidth=line_width, color=line_color, alpha=line_alpha, linestyle=line_style)
    gl.right_labels = False
    gl.top_labels = False
    gl.xformatter = LongitudeFormatter(zero_direction_label=False)
    gl.yformatter = LatitudeFormatter()

    if longitude_lines is not None:
        gl.xlocator = mticker.FixedLocator(np.array(longitude_lines))
    if latitude_lines is not None:
        gl.ylocator = mticker.FixedLocator(np.array(latitude_lines))

    # print("[green]Gridlines added successfully.[/green]")
    return axes, gl


def add_cartopy(axes: plt.Axes, longitude_data: np.ndarray = None, latitude_data: np.ndarray = None, map_projection: ccrs.Projection = ccrs.PlateCarree(), show_gridlines: bool = True, land_color: str = "lightgrey", ocean_color: str = "lightblue", coastline_linewidth: float = 0.5) -> None:
    """Add cartopy features to a map.

    Args:
        axes (plt.Axes): The axes to add map features to.
        longitude_data (np.ndarray, optional): Array of longitudes to set map extent.
        latitude_data (np.ndarray, optional): Array of latitudes to set map extent.
        map_projection (ccrs.Projection, optional): Coordinate reference system. Defaults to PlateCarree.
        show_gridlines (bool, optional): Whether to add gridlines. Defaults to True.
        land_color (str, optional): Color of land. Defaults to "lightgrey".
        ocean_color (str, optional): Color of oceans. Defaults to "lightblue".
        coastline_linewidth (float, optional): Line width for coastlines. Defaults to 0.5.

    Returns:
        None

    Example:
        >>> add_cartopy(axes, longitude_data=lon_data, latitude_data=lat_data, map_projection=ccrs.PlateCarree(), show_gridlines=True)
        >>> axes = add_cartopy(axes, longitude_data=None, latitude_data=None, map_projection=ccrs.PlateCarree(), show_gridlines=False)

    """
    # add coastlines
    axes.add_feature(cfeature.LAND, facecolor=land_color)
    axes.add_feature(cfeature.OCEAN, facecolor=ocean_color)
    axes.add_feature(cfeature.COASTLINE, linewidth=coastline_linewidth)
    # axes.add_feature(cfeature.BORDERS, linewidth=coastline_linewidth, linestyle=":")

    # add gridlines
    if show_gridlines:
        axes, gl = add_gridlines(axes, map_projection=map_projection)

    # set longitude and latitude format
    lon_formatter = LongitudeFormatter(zero_direction_label=False)
    lat_formatter = LatitudeFormatter()
    axes.xaxis.set_major_formatter(lon_formatter)
    axes.yaxis.set_major_formatter(lat_formatter)

    # set extent
    if longitude_data is not None and latitude_data is not None:
        lon_min, lon_max = np.nanmin(longitude_data), np.nanmax(longitude_data)
        lat_min, lat_max = np.nanmin(latitude_data), np.nanmax(latitude_data)
        axes.set_extent([lon_min, lon_max, lat_min, lat_max], crs=map_projection)

    # print("[green]Cartopy features added successfully.[/green]")
    return axes


class MidpointNormalize(mpl.colors.Normalize):
    """Custom normalization class to center 0 value.

    Args:
        min_value (float, optional): Minimum data value. Defaults to None.
        max_value (float, optional): Maximum data value. Defaults to None.
        center_value (float, optional): Center value for normalization. Defaults to None.
        clip_values (bool, optional): Whether to clip data outside the range. Defaults to False.

    Example:
        >>> norm = MidpointNormalize(min_value=-2, max_value=1, center_value=0)
    """

    def __init__(self, min_value: float = None, max_value: float = None, center_value: float = None, clip_values: bool = False) -> None:
        self.vcenter = center_value
        super().__init__(min_value, max_value, clip_values)

    def __call__(self, input_values: np.ndarray, clip_values: bool = None) -> np.ma.MaskedArray:
        x, y = [self.vmin, self.vcenter, self.vmax], [0, 0.5, 1.0]
        return np.ma.masked_array(np.interp(input_values, x, y, left=-np.inf, right=np.inf))

    def inverse(self, normalized_values: np.ndarray) -> np.ndarray:
        y, x = [self.vmin, self.vcenter, self.vmax], [0, 0.5, 1]
        return np.interp(normalized_values, x, y, left=-np.inf, right=np.inf)

    # print("[green]Midpoint normalization applied successfully.[/green]")


if __name__ == "__main__":
    pass
