import warnings

import cartopy.crs as ccrs
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from rich import print

__all__ = ["fig_minus", "gif", "movie", "setup_map", "ticks_symmetric"]

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
        >>> fig_minus(x_axis=ax, decimal_places=2, add_spacing=True)
    """
    current_ticks = None
    target_object = None

    # Determine which object to use and get its ticks
    if x_axis is not None:
        current_ticks = x_axis.get_xticks()
        target_object = x_axis
    elif y_axis is not None:
        current_ticks = y_axis.get_yticks()
        target_object = y_axis
    elif colorbar is not None:
        current_ticks = colorbar.get_ticks()
        target_object = colorbar
    else:
        print("[yellow]Warning:[/yellow] No valid axis or colorbar provided.")
        return None

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
    elif y_axis is not None:
        y_axis.set_yticklabels(out_ticks)
    elif colorbar is not None:
        colorbar.set_ticklabels(out_ticks)

    # print("[green]Axis tick labels updated successfully.[/green]")
    return target_object


def gif(image_paths: list[str], output_gif_name: str, frame_duration: float = 0.2, resize_dimensions: tuple[int, int] = None) -> None:
    """Create a GIF from a list of images.

    Args:
        image_paths (list[str]): List of image file paths.
        output_gif_name (str): Name of the output GIF file.
        frame_duration (float): Duration of each frame in seconds. Defaults to 0.2.
        resize_dimensions (tuple[int, int], optional): Resize dimensions (width, height). Defaults to None.

    Returns:
        None

    Example:
        >>> gif(['image1.png', 'image2.png'], 'output.gif', frame_duration=0.5, resize_dimensions=(800, 600))
    """
    import imageio.v2 as imageio
    from PIL import Image

    if not image_paths:
        print("[red]Error:[/red] Image paths list is empty.")
        return

    frames = []

    # Get target dimensions
    if resize_dimensions is None and image_paths:
        with Image.open(image_paths[0]) as img:
            resize_dimensions = img.size

    # Read and resize all images
    for image_name in image_paths:
        try:
            with Image.open(image_name) as img:
                if resize_dimensions:
                    img = img.resize(resize_dimensions, Image.LANCZOS)
                frames.append(np.array(img))
        except Exception as e:
            print(f"[yellow]Warning:[/yellow] Failed to read image {image_name}: {e}")
            continue

    if not frames:
        print("[red]Error:[/red] No valid images found.")
        return

    # Create GIF
    try:
        imageio.mimsave(output_gif_name, frames, format="GIF", duration=frame_duration)
        print(f"[green]GIF created successfully![/green] Size: {resize_dimensions}, Frame duration: {frame_duration}s")
    except Exception as e:
        print(f"[red]Error:[/red] Failed to create GIF: {e}")


def movie(image_files: list[str], output_video_path: str, fps: int) -> None:
    """Create a video from a list of image files.

    Args:
        image_files (list[str]): List of image file paths in order.
        output_video_path (str): Output video file path (e.g., 'output.mp4').
        fps (int): Video frame rate.

    Returns:
        None

    Example:
        >>> movie(['img1.jpg', 'img2.jpg'], 'output.mp4', fps=30)
    """
    if not image_files:
        print("[red]Error:[/red] Image files list is empty.")
        return

    import cv2
    # Read first image to get frame dimensions
    try:
        frame = cv2.imread(image_files[0])
        if frame is None:
            print(f"[red]Error:[/red] Cannot read first image: {image_files[0]}")
            return
        height, width, layers = frame.shape
        size = (width, height)
        print(f"Video dimensions set to: {size}")
    except Exception as e:
        print(f"[red]Error:[/red] Error reading first image: {e}")
        return

    # Create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, size)

    if not out.isOpened():
        print(f"[red]Error:[/red] Cannot open video file for writing: {output_video_path}")
        print("Please check if the codec is supported and the path is valid.")
        return

    print(f"Starting to write images to video: {output_video_path}...")
    successful_frames = 0

    for i, filename in enumerate(image_files):
        try:
            frame = cv2.imread(filename)
            if frame is None:
                print(f"[yellow]Warning:[/yellow] Skipping unreadable image: {filename}")
                continue

            # Ensure frame dimensions match initialization
            current_height, current_width, _ = frame.shape
            if (current_width, current_height) != size:
                frame = cv2.resize(frame, size)

            out.write(frame)
            successful_frames += 1

            # Print progress
            if (i + 1) % 50 == 0 or (i + 1) == len(image_files):
                print(f"Processed {i + 1}/{len(image_files)} frames")

        except Exception as e:
            print(f"[yellow]Warning:[/yellow] Error processing image {filename}: {e}")
            continue

    # Release resources
    out.release()
    print(f"[green]Video created successfully:[/green] {output_video_path} ({successful_frames} frames)")


def setup_map(
    axes: plt.Axes,
    longitude_data: np.ndarray = None,
    latitude_data: np.ndarray = None,
    map_projection: ccrs.Projection = ccrs.PlateCarree(),
    # Map features
    show_land: bool = True,
    show_ocean: bool = True,
    show_coastline: bool = True,
    show_borders: bool = False,
    land_color: str = "lightgrey",
    ocean_color: str = "lightblue",
    coastline_linewidth: float = 0.5,
    # Gridlines and ticks
    show_gridlines: bool = False,
    longitude_ticks: list[float] = None,
    latitude_ticks: list[float] = None,
    tick_decimals: int = 0,
    # Gridline styling
    grid_color: str = "k",
    grid_alpha: float = 0.5,
    grid_style: str = "--",
    grid_width: float = 0.5,
    # Label options
    show_labels: bool = True,
    left_labels: bool = True,
    bottom_labels: bool = True,
    right_labels: bool = False,
    top_labels: bool = False,
) -> plt.Axes:
    """Setup a complete cartopy map with customizable features."""
    from matplotlib import ticker as mticker

    # Add map features
    import cartopy.feature as cfeature
    if show_land:
        axes.add_feature(cfeature.LAND, facecolor=land_color)
    if show_ocean:
        axes.add_feature(cfeature.OCEAN, facecolor=ocean_color)
    if show_coastline:
        axes.add_feature(cfeature.COASTLINE, linewidth=coastline_linewidth)
    if show_borders:
        axes.add_feature(cfeature.BORDERS, linewidth=coastline_linewidth, linestyle=":")

    # Setup coordinate formatting
    from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
    lon_formatter = LongitudeFormatter(zero_direction_label=False, number_format=f".{tick_decimals}f")
    lat_formatter = LatitudeFormatter(number_format=f".{tick_decimals}f")
    
        # 只要传入经纬度数据就自动设置范围
    # 范围必须在cartopy添加地图特征之后设置，因为添加特征可能会改变axes的范围
    if longitude_data is not None and latitude_data is not None:
        # 过滤掉NaN，避免极端值影响
        lon_data = np.asarray(longitude_data)
        lat_data = np.asarray(latitude_data)
        lon_valid = lon_data[~np.isnan(lon_data)]
        lat_valid = lat_data[~np.isnan(lat_data)]
        if lon_valid.size > 0 and lat_valid.size > 0:
            lon_min, lon_max = np.min(lon_valid), np.max(lon_valid)
            lat_min, lat_max = np.min(lat_valid), np.max(lat_valid)
            axes.set_extent([lon_min, lon_max, lat_min, lat_max], crs=map_projection)
        else:
            # 若全是NaN则不设置范围
            pass
    
    if show_labels:
        # Add tick labels without gridlines
        # Generate default tick positions based on current extent if not provided
        if longitude_ticks is None:
            current_extent = axes.get_extent(crs=map_projection)
            lon_range = current_extent[1] - current_extent[0]
            # Generate reasonable tick spacing
            tick_spacing = 1 if lon_range <= 10 else (5 if lon_range <= 30 else (15 if lon_range <= 90 else (30 if lon_range <= 180 else 60)))
            longitude_ticks = np.arange(np.ceil(current_extent[0] / tick_spacing) * tick_spacing, current_extent[1] + 0.1, tick_spacing)
            # print(f"[green]Longitude ticks set to:[/green] {longitude_ticks}")

        if latitude_ticks is None:
            current_extent = axes.get_extent(crs=map_projection)
            lat_range = current_extent[3] - current_extent[2]
            # Generate reasonable tick spacing
            tick_spacing = 1 if lat_range <= 10 else (5 if lat_range <= 30 else (15 if lat_range <= 90 else 30))
            latitude_ticks = np.arange(np.ceil(current_extent[2] / tick_spacing) * tick_spacing, current_extent[3] + 0.1, tick_spacing)
            # print(f"[green]Latitude ticks set to:[/green] {latitude_ticks}")

        # Set tick positions and formatters
        axes.set_xticks(longitude_ticks, crs=map_projection)
        axes.set_yticks(latitude_ticks, crs=map_projection)
        axes.xaxis.set_major_formatter(lon_formatter)
        axes.yaxis.set_major_formatter(lat_formatter)

        # Control label visibility based on input parameters
        axes.tick_params(axis="x", labelbottom=bottom_labels, labeltop=top_labels)
        axes.tick_params(axis="y", labelleft=left_labels, labelright=right_labels)

    # Handle gridlines and ticks
    if show_gridlines:
        # Add gridlines with labels
        gl = axes.gridlines(crs=map_projection, draw_labels=show_labels, linewidth=grid_width, color=grid_color, alpha=grid_alpha, linestyle=grid_style)

        # Configure label positions
        gl.left_labels = left_labels
        gl.bottom_labels = bottom_labels
        gl.right_labels = right_labels
        gl.top_labels = top_labels

        # Set formatters
        gl.xformatter = lon_formatter
        gl.yformatter = lat_formatter

        # Set custom tick positions if provided
        if longitude_ticks is not None:
            gl.xlocator = mticker.FixedLocator(np.array(longitude_ticks))
        if latitude_ticks is not None:
            gl.ylocator = mticker.FixedLocator(np.array(latitude_ticks))
            
    return axes


def ticks_symmetric(vmin: float, vcenter: float, vmax: float, num: int = 7) -> np.ndarray:
    """
    生成以指定中心点对称分布的刻度值
    
    参数:
        vmin (float): 最小值
        vcenter (float): 中心值
        vmax (float): 最大值
        num (int, optional): 期望的刻度数量（必须是奇数）。默认为7
    
    返回:
        np.ndarray: 对称分布的刻度值数组
    
    异常:
        ValueError: 如果输入值无效
    
    示例:
        >>> ticks_symmetric(vmin=-10, vcenter=0, vmax=10, num=5)
        array([-10.,  -5.,   0.,   5.,  10.])
    """
    # 验证输入参数
    if vmin >= vcenter:
        raise ValueError(f"vmin ({vmin}) must be less than vcenter ({vcenter})")
    if vcenter >= vmax:
        raise ValueError(f"vcenter ({vcenter}) must be less than vmax ({vmax})")
    
    # 确保刻度数量是奇数
    if num % 2 == 0:
        num += 1
    
    # 计算每侧的点数（包括中心点）
    side_points = (num - 1) // 2 + 1
    
    # 生成左侧刻度（从最小值到中心值）
    left_ticks = np.linspace(vmin, vcenter, side_points)[:-1]
    
    # 生成右侧刻度（从中心值到最大值）
    right_ticks = np.linspace(vcenter, vmax, side_points)[1:]
    
    # 组合所有刻度
    return np.concatenate([left_ticks, [vcenter], right_ticks])


if __name__ == "__main__":
    pass
