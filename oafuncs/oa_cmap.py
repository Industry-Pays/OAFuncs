#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 16:55:11
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-11-21 13:14:24
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_cmap.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from rich import print

__all__ = ["show", "to_color", "create", "create_rgbtxt", "get"]

# ** 将cmap用填色图可视化（官网摘抄函数）
def show(colormaps):
    """
    Description:
        Helper function to plot data with associated colormap.
    Parameters:
        colormaps : list of colormaps, or a single colormap; can be a string or a colormap object.
    Example:
        cmap = ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
        show([cmap]); show("viridis"); show(["viridis", "cividis"])
    """
    if isinstance(colormaps, str) or isinstance(colormaps, mpl.colors.Colormap):
        colormaps = [colormaps]
    np.random.seed(19680801)
    data = np.random.randn(30, 30)
    n = len(colormaps)
    fig, axs = plt.subplots(1, n, figsize=(n * 2 + 2, 3), constrained_layout=True, squeeze=False)
    for [ax, cmap] in zip(axs.flat, colormaps):
        psm = ax.pcolormesh(data, cmap=cmap, rasterized=True, vmin=-4, vmax=4)
        fig.colorbar(psm, ax=ax)
    plt.show()


# ** 将cmap转为list，即多个颜色的列表
def to_color(cmap, n=256):
    """
    Description:
        Convert a colormap to a list of colors
    Parameters:
        cmap : str; the name of the colormap
        n    : int, optional; the number of colors
    Return:
        out_colors : list of colors
    Example:
        out_colors = to_color('viridis', 256)
    """
    c_map = mpl.colormaps.get_cmap(cmap)
    out_colors = [c_map(i) for i in np.linspace(0, 1, n)]
    return out_colors


# ** 自制cmap，多色，可带位置
def create(colors: list, nodes=None, under=None, over=None):  # 利用颜色快速配色
    """
    Description:
        Create a custom colormap
    Parameters:
        colors : list of colors
        nodes  : list of positions
        under  : color
        over   : color
    Return:
        cmap : colormap
    Example:
        cmap = create(['#C2B7F3','#B3BBF2','#B0CBF1','#ACDCF0','#A8EEED'])
        cmap = create(['aliceblue','skyblue','deepskyblue'],[0.0,0.5,1.0])
    """

    if nodes is None:  # 采取自动分配比例
        cmap_color = mpl.colors.LinearSegmentedColormap.from_list("mycmap", colors)
    else:  # 按照提供比例分配
        cmap_color = mpl.colors.LinearSegmentedColormap.from_list("mycmap", list(zip(nodes, colors)))
    if under is not None:
        cmap_color.set_under(under)
    if over is not None:
        cmap_color.set_over(over)
    return cmap_color


# ** 根据RGB的txt文档制作色卡（利用Grads调色盘）
def create_rgbtxt(rgbtxt_file,split_mark=','):  # 根据RGB的txt文档制作色卡/根据rgb值制作
    """
    Description
    -----------
    Make a color card according to the RGB txt document, each line in the txt file is an RGB value, separated by commas, such as: 251,251,253
    
    Parameters
    ----------
    rgbtxt_file : str, the path of txt file
    split_mark  : str, optional, default is ','; the split mark of rgb value

    Returns
    -------
    cmap : colormap

    Example
    -------
    cmap=create_rgbtxt(path,split_mark=',')
    
    txt example
    -----------
    251,251,253
    225,125,25
    250,205,255
    """
    with open(rgbtxt_file) as fid:
        data = fid.readlines()
    n = len(data)
    rgb = np.zeros((n, 3))
    for i in np.arange(n):
        rgb[i][0] = data[i].split(split_mark)[0]
        rgb[i][1] = data[i].split(split_mark)[1]
        rgb[i][2] = data[i].split(split_mark)[2]
    max_rgb = np.max(rgb)
    if max_rgb > 2:  # if the value is greater than 2, it is normalized to 0-1
        rgb = rgb / 255.0
    my_cmap = mpl.colors.ListedColormap(rgb, name="my_color")
    return my_cmap


# ** 选择cmap
def get(cmap_name=None, query=False):
    """
    Description:
        Choosing a colormap from the list of available colormaps or a custom colormap
    Parameters:
        cmap_name : str, optional; the name of the colormap
        query     : bool, optional; whether to query the available colormap names
    Return:
        cmap : colormap
    Example:
        cmap = get('viridis')
        cmap = get('diverging_1')
        cmap = get('cold_1')
        cmap = get('warm_1')
        cmap = get('colorful_1')
    """

    my_cmap_dict = {
        "diverging_1": create(["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"]),
        "cold_1": create(["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC"]),
        "warm_1": create(["#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"]),
        # "land_1": create_custom(["#3E6436", "#678A59", "#91A176", "#B8A87D", "#D9CBB2"], under="#A6CEE3", over="#FFFFFF"),
        # "ocean_1": create_custom(["#126697", "#2D88B3", "#4EA1C9", "#78B9D8", "#A6CEE3"], under="#8470FF", over="#3E6436"), 
        # "ocean_land_1": create_custom(
        #     [
        #         "#126697",  # 深蓝（深海）
        #         "#2D88B3",  # 蓝
        #         "#4EA1C9",  # 蓝绿
        #         "#78B9D8",  # 浅蓝（浅海）
        #         "#A6CEE3",  # 浅蓝（近岸）
        #         "#AAAAAA",  # 灰色（0值，海平面）
        #         "#D9CBB2",  # 沙质土壤色（陆地开始）
        #         "#B8A87D",  # 浅棕
        #         "#91A176",  # 浅绿
        #         "#678A59",  # 中绿
        #         "#3E6436",  # 深绿（高山）
        #     ]
        # ),
        "colorful_1": create(["#6d00db", "#9800cb", "#F2003C", "#ff4500", "#ff7f00", "#FE28A2", "#FFC0CB", "#DDA0DD", "#40E0D0", "#1a66f2", "#00f7fb", "#8fff88", "#E3FF00"]),
    }
    if query:
        print("Available cmap names:")
        print('-' * 20)
        print('Defined by myself:')
        for key, _ in my_cmap_dict.items():
            print(key)
        print('-' * 20)
        print('Matplotlib built-in:')
        print(mpl.colormaps())
        print("-" * 20)
    
    if cmap_name is None:
        return

    if cmap_name in my_cmap_dict:
        return my_cmap_dict[cmap_name]
    else:
        try:
            return mpl.colormaps.get_cmap(cmap_name)
        except ValueError:
            raise ValueError(f"Unknown cmap name: {cmap_name}")


if __name__ == "__main__":
    # ** 测试自制cmap
    colors = ["#C2B7F3", "#B3BBF2", "#B0CBF1", "#ACDCF0", "#A8EEED"]
    nodes = [0.0, 0.2, 0.4, 0.6, 1.0]
    c_map = create(colors, nodes)
    show([c_map])

    # ** 测试自制diverging型cmap
    diverging_cmap = create(["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"])
    show([diverging_cmap])

    # ** 测试根据RGB的txt文档制作色卡
    file_path = "E:/python/colorbar/test.txt"
    cmap_rgb = create_rgbtxt(file_path)

    # ** 测试将cmap转为list
    out_colors = to_color("viridis", 256)
