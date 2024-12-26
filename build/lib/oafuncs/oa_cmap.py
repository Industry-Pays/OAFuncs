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

__all__ = ["show", "cmap2colors", "create_cmap", "create_cmap_rgbtxt", "choose_cmap"]

# ** 将cmap用填色图可视化（官网摘抄函数）
def show(colormaps: list):
    """
    Helper function to plot data with associated colormap.
    example:
    cmap = ListedColormap(["darkorange", "gold", "lawngreen", "lightseagreen"])
    show([cmap])
    """
    np.random.seed(19680801)
    data = np.random.randn(30, 30)
    n = len(colormaps)
    fig, axs = plt.subplots(1, n, figsize=(n * 2 + 2, 3), constrained_layout=True, squeeze=False)
    for [ax, cmap] in zip(axs.flat, colormaps):
        psm = ax.pcolormesh(data, cmap=cmap, rasterized=True, vmin=-4, vmax=4)
        fig.colorbar(psm, ax=ax)
    plt.show()


# ** 将cmap转为list，即多个颜色的列表
def cmap2colors(cmap, n=256):
    """
    cmap        : cmap名称
    n           : 提取颜色数量
    return      : 提取的颜色列表
    example     : out_colors = cmap2colors('viridis', 256)
    """
    c_map = mpl.colormaps.get_cmap(cmap)
    out_colors = [c_map(i) for i in np.linspace(0, 1, n)]
    return out_colors


# ** 自制cmap，多色，可带位置
def create_cmap(colors: list, nodes=None, under=None, over=None):  # 利用颜色快速配色
    """
    func        : 自制cmap，自动确定颜色位置（等比例）
    description : colors可以是颜色名称，也可以是十六进制颜色代码
    param        {*} colors 颜色
    param        {*} nodes 颜色位置，默认不提供，等间距
    return       {*} cmap
    example     : cmap = create_cmap(['#C2B7F3','#B3BBF2','#B0CBF1','#ACDCF0','#A8EEED'])
                cmap = create_cmap(['aliceblue','skyblue','deepskyblue'],[0.0,0.5,1.0])
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
def create_cmap_rgbtxt(rgbtxt_file,split_mark=','):  # 根据RGB的txt文档制作色卡/根据rgb值制作
    """
    func        : 根据RGB的txt文档制作色卡
    description : rgbtxt_file='E:/python/colorbar/test.txt'
    param        {*} rgbtxt_file txt文件路径
    return       {*} camp
    example     : cmap=create_cmap_rgbtxt(path,split_mark=',') #

    txt example : 251,251,253
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
    if max_rgb > 2:  # 如果rgb值大于2，则认为是0-255的值，需要归一化
        rgb = rgb / 255.0
    icmap = mpl.colors.ListedColormap(rgb, name="my_color")
    return icmap


def choose_cmap(cmap_name=None, query=False):
    """
    description: Choosing a colormap from the list of available colormaps or a custom colormap
    param {*} cmap_name:
    param {*} query:
    return {*}
    """

    my_cmap_dict = {
        "diverging_1": create_cmap(["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"]),
        "cold_1": create_cmap(["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC"]),
        "warm_1": create_cmap(["#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"]),
        # "land_1": create_custom(["#3E6436", "#678A59", "#91A176", "#B8A87D", "#D9CBB2"], under="#A6CEE3", over="#FFFFFF"), # 陆地颜色从深绿到浅棕，表示从植被到沙地的递减
        # "ocean_1": create_custom(["#126697", "#2D88B3", "#4EA1C9", "#78B9D8", "#A6CEE3"], under="#8470FF", over="#3E6436"), # 海洋颜色从深蓝到浅蓝，表示从深海到浅海的递减
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
        "colorful_1": create_cmap(["#6d00db", "#9800cb", "#F2003C", "#ff4500", "#ff7f00", "#FE28A2", "#FFC0CB", "#DDA0DD", "#40E0D0", "#1a66f2", "#00f7fb", "#8fff88", "#E3FF00"]),
    }
    if query:
        for key, _ in my_cmap_dict.items():
            print(key)

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
    c_map = create_cmap(colors, nodes)
    show([c_map])

    # ** 测试自制diverging型cmap
    diverging_cmap = create_cmap(["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"])
    show([diverging_cmap])

    # ** 测试根据RGB的txt文档制作色卡
    file_path = "E:/python/colorbar/test.txt"
    cmap_rgb = create_cmap_rgbtxt(file_path)

    # ** 测试将cmap转为list
    out_colors = cmap2colors("viridis", 256)
