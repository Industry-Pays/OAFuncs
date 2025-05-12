from typing import List, Optional, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

__all__ = ["show", "to_color", "create", "get"]


# ** 将cmap用填色图可视化（官网摘抄函数）
def show(
    colormaps: Union[str, mpl.colors.Colormap, List[Union[str, mpl.colors.Colormap]]],
) -> None:
    """Helper function to plot data with associated colormap.

    This function creates a visualization of one or more colormaps by applying them
    to randomly generated data in a pcolormesh plot.

    Parameters
    ----------
    colormaps : Union[str, mpl.colors.Colormap, List[Union[str, mpl.colors.Colormap]]]
        List of colormaps, or a single colormap; can be a string name or a colormap object.

    Returns
    -------
    None
        This function displays the plot but does not return any value.

    Examples
    --------
    >>> cmap = matplotlib.colors.ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
    >>> show([cmap])
    >>> show("viridis")
    >>> show(["viridis", "cividis"])
    """
    # Convert single colormap to list for uniform processing
    if not isinstance(colormaps, list):
        colormaps = [colormaps]

    # Create a formatted list of colormap names for display
    cmap_names = []
    for cmap in colormaps:
        if isinstance(cmap, str):
            cmap_names.append(cmap)
        elif hasattr(cmap, "name"):
            cmap_names.append(cmap.name)
        else:
            cmap_names.append("unnamed_colormap")

    print(f"Visualizing {len(colormaps)} colormap(s): {', '.join(cmap_names)}")

    # Generate random data with fixed seed for reproducibility
    np.random.seed(19680801)
    data = np.random.randn(30, 30)

    # Create subplots based on number of colormaps
    n = len(colormaps)
    fig, axs = plt.subplots(1, n, figsize=(n * 2 + 2, 3), constrained_layout=True, squeeze=False)

    # Plot each colormap
    for ax, cmap in zip(axs.flat, colormaps):
        psm = ax.pcolormesh(data, cmap=cmap, rasterized=True, vmin=-4, vmax=4)
        fig.colorbar(psm, ax=ax)

        # Set title if colormap has a name
        if isinstance(cmap, str):
            ax.set_title(cmap)
        elif hasattr(cmap, "name") and cmap.name:
            ax.set_title(cmap.name)

    print("Displaying colormap visualization...")
    plt.show()


# ** 将cmap转为list，即多个颜色的列表
def to_color(colormap_name: str, num_colors: int = 256) -> List[tuple]:
    """Convert a colormap to a list of colors.

    Args:
        colormap_name (str): The name of the colormap.
        num_colors (int, optional): The number of colors. Defaults to 256.

    Returns:
        List[tuple]: List of RGBA colors.

    Raises:
        ValueError: If the colormap name is not recognized.

    Examples:
        >>> out_colors = to_color('viridis', 256)
    """
    try:
        cmap = mpl.colormaps.get_cmap(colormap_name)
        return [cmap(i) for i in np.linspace(0, 1, num_colors)]
    except (ValueError, TypeError):
        error_msg = f"Invalid colormap name: {colormap_name}"
        print(error_msg)
        raise ValueError(error_msg)


# ** 自制cmap，多色，可带位置
def create(
    color_list: Optional[List[Union[str, tuple]]] = None,
    rgb_file: Optional[str] = None,
    color_positions: Optional[List[float]] = None,
    below_range_color: Optional[Union[str, tuple]] = None,
    above_range_color: Optional[Union[str, tuple]] = None,
    value_delimiter: str = ",",
) -> mpl.colors.Colormap:
    """Create a custom colormap from a list of colors or an RGB txt document.

    Args:
        color_list (Optional[List[Union[str, tuple]]]): List of colors. Required if rgb_file is None.
        rgb_file (Optional[str]): The path of txt file. Required if color_list is None.
        color_positions (Optional[List[float]]): List of positions for color_list. Must have same length as color_list.
        below_range_color (Optional[Union[str, tuple]]): Color for values below the colormap range.
        above_range_color (Optional[Union[str, tuple]]): Color for values above the colormap range.
        value_delimiter (str, optional): The delimiter of RGB values in txt file. Defaults to ",".

    Returns:
        mpl.colors.Colormap: Created colormap.

    Raises:
        ValueError: If neither color_list nor rgb_file is provided.
        ValueError: If color_positions is provided but has different length than color_list.
        FileNotFoundError: If rgb_file does not exist.
        ValueError: If the RGB file format is invalid.

    Examples:
        >>> cmap = create(color_list=['#C2B7F3','#B3BBF2','#B0CBF1','#ACDCF0','#A8EEED'])
        >>> cmap = create(color_list=['aliceblue','skyblue','deepskyblue'], color_positions=[0.0,0.5,1.0])
        >>> cmap = create(rgb_file='path/to/file.txt', value_delimiter=',')
    """
    # Input validation
    if rgb_file is None and color_list is None:
        error_msg = "Either 'color_list' or 'rgb_file' must be provided."
        print(error_msg)
        raise ValueError(error_msg)

    if color_positions is not None and color_list is not None:
        if len(color_positions) != len(color_list):
            error_msg = f"'color_positions' must have the same length as 'color_list' (positions: {len(color_positions)}, colors: {len(color_list)})"
            print(error_msg)
            raise ValueError(error_msg)
        if not all(0 <= pos <= 1 for pos in color_positions):
            error_msg = "All position values must be between 0 and 1"
            print(error_msg)
            raise ValueError(error_msg)
        if color_positions != sorted(color_positions):
            error_msg = f"Position values must be in ascending order: {color_positions}"
            print(error_msg)
            raise ValueError(error_msg)

    if rgb_file:
        try:
            # print(f"Reading RGB data from {rgb_file}...")

            with open(rgb_file) as fid:
                data = [line.strip() for line in fid if line.strip() and not line.strip().startswith("#")]

            if not data:
                error_msg = f"RGB file is empty or contains only comments: {rgb_file}"
                print(error_msg)
                raise ValueError(error_msg)

            n = len(data)
            rgb = np.zeros((n, 3))

            for i in np.arange(n):
                try:
                    parts = data[i].split(value_delimiter)
                    if len(parts) < 3:
                        error_msg = f"Line {i + 1}: Expected at least 3 values, got {len(parts)}"
                        print(error_msg)
                        raise ValueError(error_msg)

                    rgb[i][0] = float(parts[0])
                    rgb[i][1] = float(parts[1])
                    rgb[i][2] = float(parts[2])
                except (ValueError, IndexError) as e:
                    error_msg = f"Error parsing RGB values at line {i + 1}: {e}"
                    print(error_msg)
                    raise ValueError(error_msg)

            max_rgb = np.max(rgb)
            # Normalize RGB values if they are in 0-255 range
            if max_rgb > 2:
                rgb = rgb / 255.0
            cmap_color = mpl.colors.ListedColormap(rgb, name="my_color")
            # print(f"Successfully created colormap from {rgb_file}")
        except FileNotFoundError:
            error_msg = f"RGB file not found: {rgb_file}"
            print(error_msg)
            raise FileNotFoundError(error_msg)
    else:
        # Create colormap from color list
        if color_positions is None:
            cmap_color = mpl.colors.LinearSegmentedColormap.from_list("mycmap", color_list)
        else:
            cmap_color = mpl.colors.LinearSegmentedColormap.from_list("mycmap", list(zip(color_positions, color_list)))
        # print(f"Successfully created colormap from {len(color_list)} colors")

    # Set below/above range colors if provided
    if below_range_color is not None:
        cmap_color.set_under(below_range_color)
        # print(f"Set below-range color to {below_range_color}")
    if above_range_color is not None:
        cmap_color.set_over(above_range_color)
        # print(f"Set above-range color to {above_range_color}")

    return cmap_color


# ** 选择cmap
def get(colormap_name: Optional[str] = None, show_available: bool = False) -> Optional[mpl.colors.Colormap]:
    """Choose a colormap from the list of available colormaps or a custom colormap.

    Args:
        colormap_name (Optional[str], optional): The name of the colormap. Defaults to None.
        show_available (bool, optional): Whether to query the available colormap names. Defaults to False.

    Returns:
        Optional[mpl.colors.Colormap]: Selected colormap or None if show_available is True or colormap_name is None.

    Examples:
        >>> cmap = get('viridis')
        >>> cmap = get('diverging_1')
        >>> cmap = get('cool_1')
        >>> cmap = get('warm_1')
        >>> cmap = get('colorful_1')
    """
    my_cmap_dict = {
        "diverging_1": ["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"],
        "cool_1": ["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC"],
        "warm_1": ["#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"],
        "colorful_1": ["#6d00db", "#9800cb", "#F2003C", "#ff4500", "#ff7f00", "#FE28A2", "#FFC0CB", "#DDA0DD", "#40E0D0", "#1a66f2", "#00f7fb", "#8fff88", "#E3FF00"],
    }

    if show_available:
        print("Available cmap names:")
        print("-" * 20)
        print("Defined by myself:")
        for name in my_cmap_dict.keys():
            print(f"  • {name}")
        print("-" * 20)
        print("Matplotlib built-in:")
        # 将Matplotlib内置cmap分批次打印，每行5个
        built_in_cmaps = list(mpl.colormaps.keys())
        for i in range(0, len(built_in_cmaps), 5):
            print("  • " + ", ".join(built_in_cmaps[i : i + 5]))
        print("-" * 20)
        return None

    if colormap_name is None:
        return None

    if colormap_name in my_cmap_dict:
        # print(f"Using custom colormap: {colormap_name}")
        return create(my_cmap_dict[colormap_name])
    else:
        try:
            cmap = mpl.colormaps.get_cmap(colormap_name)
            # print(f"Using matplotlib colormap: {colormap_name}")
            return cmap
        except ValueError:
            print(f"Warning: Unknown cmap name: {colormap_name}")
            print("Using rainbow as default.")
            return mpl.colormaps.get_cmap("rainbow")  # 默认返回 'rainbow'


if __name__ == "__main__":
    # ** 测试自制cmap
    colors = ["#C2B7F3", "#B3BBF2", "#B0CBF1", "#ACDCF0", "#A8EEED"]
    color_nodes = [0.0, 0.2, 0.4, 0.6, 1.0]
    custom_cmap = create(colors, color_nodes)
    show([custom_cmap])

    # ** 测试自制diverging型cmap
    diverging_cmap = create(["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"])
    show([diverging_cmap])

    # ** 测试根据RGB的txt文档制作色卡
    rgb_file_path = "E:/python/colorbar/test.txt"
    cmap_from_rgb = create(rgb_file=rgb_file_path)

    # ** 测试将cmap转为list
    viridis_colors = to_color("viridis", 256)
