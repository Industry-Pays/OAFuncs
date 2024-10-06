#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 16:55:11
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-10-06 19:34:57
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_cmap.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''



import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

__all__ = ['show', 'extract_colors', 'create_custom',
           'create_diverging', 'create_5rgb_txt']

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
    fig, axs = plt.subplots(1, n, figsize=(n * 2 + 2, 3),
                            constrained_layout=True, squeeze=False)
    for [ax, cmap] in zip(axs.flat, colormaps):
        psm = ax.pcolormesh(data, cmap=cmap, rasterized=True, vmin=-4, vmax=4)
        fig.colorbar(psm, ax=ax)
    plt.show()


# ** 将cmap转为list，即多个颜色的列表
def extract_colors(cmap, n=256):
    '''
    cmap        : cmap名称
    n           : 提取颜色数量
    return      : 提取的颜色列表
    example     : out_cmap = extract_colors('viridis', 256)
    '''
    c_map = mpl.colormaps.get_cmap(cmap)
    out_cmap = [c_map(i) for i in np.linspace(0, 1, n)]
    return out_cmap


# ** 自制cmap，多色，可带位置
def create_custom(colors: list, nodes=None):  # 利用颜色快速配色
    '''
    func        : 自制cmap，自动确定颜色位置（等比例）
    description : colors可以是颜色名称，也可以是十六进制颜色代码
    param        {*} colors 颜色
    param        {*} nodes 颜色位置，默认不提供，等间距
    return       {*} c_map
    example     : c_map = mk_cmap(['#C2B7F3','#B3BBF2','#B0CBF1','#ACDCF0','#A8EEED'])
                c_map = mk_cmap(['aliceblue','skyblue','deepskyblue'],[0.0,0.5,1.0])
    '''
    if nodes is None:  # 采取自动分配比例
        cmap_color = mpl.colors.LinearSegmentedColormap.from_list(
            'mycmap', colors)
    else:  # 按照提供比例分配
        cmap_color = mpl.colors.LinearSegmentedColormap.from_list(
            "mycmap", list(zip(nodes, colors)))
    return cmap_color

# ** 自制diverging型cmap，默认中间为白色


def create_diverging(colors: list):
    '''
    func        : 自制cmap，双色，中间默认为白色；如果输入偶数个颜色，则中间为白，如果奇数个颜色，则中间色为中间色
    description : colors可以是颜色名称，也可以是十六进制颜色代码
    param        {*} colors
    return       {*}
    example     : diverging_cmap = mk_cmap_diverging(
    ["#4e00b3", "#0000FF", "#00c0ff", "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"])
    '''
    # 自定义颜色位置
    n = len(colors)
    nodes = np.linspace(0.0, 1.0, n + 1 if n % 2 == 0 else n)
    newcolors = colors
    if n % 2 == 0:
        newcolors.insert(int(n / 2), '#ffffff')  # 偶数个颜色，中间为白色
    cmap_color = mpl.colors.LinearSegmentedColormap.from_list(
        "mycmap", list(zip(nodes, newcolors)))
    return cmap_color

# ** 根据RGB的txt文档制作色卡（利用Grads调色盘）


def create_5rgb_txt(rgb_txt_filepath: str):  # 根据RGB的txt文档制作色卡/根据rgb值制作
    '''
    func        : 根据RGB的txt文档制作色卡
    description : rgb_txt_filepath='E:/python/colorbar/test.txt'
    param        {*} rgb_txt_filepath txt文件路径
    return       {*} camp
    example     : cmap_color=dcmap(path)
    '''
    with open(rgb_txt_filepath) as fid:
        data = fid.readlines()
    n = len(data)
    rgb = np.zeros((n, 3))
    for i in np.arange(n):
        rgb[i][0] = data[i].split(',')[0]
        rgb[i][1] = data[i].split(',')[1]
        rgb[i][2] = data[i].split(',')[2]
    max_rgb = np.max(rgb)
    if max_rgb > 2:  # 如果rgb值大于2，则认为是0-255的值，需要归一化
        rgb = rgb / 255.0
    icmap = mpl.colors.ListedColormap(rgb, name='my_color')
    return icmap




if __name__ == '__main__':
    # ** 测试自制cmap
    colors = ['#C2B7F3', '#B3BBF2', '#B0CBF1', '#ACDCF0', '#A8EEED']
    nodes = [0.0, 0.2, 0.4, 0.6, 1.0]
    c_map = create_custom(colors, nodes)
    show([c_map])

    # ** 测试自制diverging型cmap
    diverging_cmap = create_diverging(["#4e00b3", "#0000FF", "#00c0ff",
                                       "#a1d3ff", "#DCDCDC", "#FFD39B", "#FF8247", "#FF0000", "#FF5F9E"])
    show([diverging_cmap])

    # ** 测试根据RGB的txt文档制作色卡
    file_path = 'E:/python/colorbar/test.txt'
    cmap_color = create_5rgb_txt(file_path)

    # ** 测试将cmap转为list
    out_cmap = extract_colors('viridis', 256)
