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

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from cartopy.mpl.ticker import LatitudeFormatter, LongitudeFormatter
from rich import print

__all__ = ["fig_minus", "gif", "add_cartopy", "add_gridlines", "MidpointNormalize", "add_lonlat_unit", "contour", "contourf", "quiver"]

warnings.filterwarnings("ignore")


def fig_minus(ax_x=None, ax_y=None, cbar=None, decimal=None, add_space=False):
    """
    Description: 将坐标轴刻度中的负号替换为减号

    param {*} ax_x : x轴
    param {*} ax_y : y轴
    param {*} cbar : colorbar
    param {*} decimal : 小数位数
    param {*} add_space : 是否在非负数前面加空格

    return {*} ax_x or ax_y or cbar
    """
    if ax_x is not None:
        current_ticks = ax_x.get_xticks()
    if ax_y is not None:
        current_ticks = ax_y.get_yticks()
    if cbar is not None:
        current_ticks = cbar.get_ticks()
    # 先判断是否需要加空格，如果要，先获取需要加的索引
    if add_space:
        index = 0
        for _, tick in enumerate(current_ticks):
            if tick >= 0:
                index = _
                break
    if decimal is not None:
        # my_ticks = [(round(float(iii), decimal)) for iii in my_ticks]
        current_ticks = [f"{val:.{decimal}f}" if val != 0 else "0" for val in current_ticks]

    out_ticks = [f"{val}".replace("-", "\u2212") for val in current_ticks]
    if add_space:
        # 在非负数前面加两个空格
        out_ticks[index:] = ["  " + m for m in out_ticks[index:]]

    if ax_x is not None:
        ax_x.set_xticklabels(out_ticks)
        return ax_x
    if ax_y is not None:
        ax_y.set_yticklabels(out_ticks)
        return ax_y
    if cbar is not None:
        cbar.set_ticklabels(out_ticks)
        return cbar


# ** 将生成图片/已有图片制作成动图
def gif(image_list: list, gif_name: str, duration=200, resize=None):  # 制作动图，默认间隔0.2
    """
    Description
        Make gif from images
    Parameters
        image_list : list, list of images
        gif_name : str, name of gif
        duration : float, duration of each frame, units: ms
        resize : tuple, (width, height) to resize images, if None, use first image size
    Returns
        None
    Example
        gif(["1.png", "2.png"], "test.gif", duration=0.2)
    """
    import imageio.v2 as imageio
    import numpy as np
    from PIL import Image

    frames = []

    # 获取目标尺寸
    if resize is None and image_list:
        # 使用第一张图片的尺寸作为标准
        with Image.open(image_list[0]) as img:
            resize = img.size

    # 读取并调整所有图片的尺寸
    for image_name in image_list:
        with Image.open(image_name) as img:
            if resize:
                img = img.resize(resize, Image.LANCZOS)
            frames.append(np.array(img))

    # 修改此处：明确使用 duration 值，并将其作为每帧的持续时间（以秒为单位）
    # 某些版本的 imageio 可能需要以毫秒为单位，或者使用 fps 参数
    try:
        # 先尝试直接使用 duration 参数（以秒为单位）
        imageio.mimsave(gif_name, frames, format="GIF", duration=duration)
    except Exception as e:
        print(f"尝试使用fps参数替代duration: {e}")
        # 如果失败，尝试使用 fps 参数（fps = 1/duration）
        fps = 1.0 / duration if duration > 0 else 5.0
        imageio.mimsave(gif_name, frames, format="GIF", fps=fps)

    print(f"Gif制作完成！尺寸: {resize}, 帧间隔: {duration}毫秒")
    return


# ** 转化经/纬度刻度
def add_lonlat_unit(lon=None, lat=None, decimal=2):
    """
    param        {*} lon : 经度列表
    param        {*} lat : 纬度列表
    param        {*} decimal : 小数位数
    return       {*} 转化后的经/纬度列表
    example     : add_lonlat_unit(lon=lon, lat=lat, decimal=2)
    """

    def _format_longitude(x_list):
        out_list = []
        for x in x_list:
            if x > 180:
                x -= 360
            # degrees = int(abs(x))
            degrees = round(abs(x), decimal)
            direction = "E" if x >= 0 else "W"
            out_list.append(f"{degrees:.{decimal}f}°{direction}" if x != 0 and x != 180 else f"{degrees}°")
        return out_list if len(out_list) > 1 else out_list[0]

    def _format_latitude(y_list):
        out_list = []
        for y in y_list:
            if y > 90:
                y -= 180
            # degrees = int(abs(y))
            degrees = round(abs(y), decimal)
            direction = "N" if y >= 0 else "S"
            out_list.append(f"{degrees:.{decimal}f}°{direction}" if y != 0 else f"{degrees}°")
        return out_list if len(out_list) > 1 else out_list[0]

    if lon and lat:
        return _format_longitude(lon), _format_latitude(lat)
    elif lon:
        return _format_longitude(lon)
    elif lat:
        return _format_latitude(lat)


# ** 添加网格线
def add_gridlines(ax, projection=ccrs.PlateCarree(), color="k", alpha=0.5, linestyle="--", linewidth=0.5):
    # add gridlines
    gl = ax.gridlines(crs=projection, draw_labels=True, linewidth=linewidth, color=color, alpha=alpha, linestyle=linestyle)
    gl.right_labels = False
    gl.top_labels = False
    gl.xformatter = LongitudeFormatter(zero_direction_label=False)
    gl.yformatter = LatitudeFormatter()

    return ax, gl


# ** 添加地图
def add_cartopy(ax, lon=None, lat=None, projection=ccrs.PlateCarree(), gridlines=True, landcolor="lightgrey", oceancolor="lightblue", cartopy_linewidth=0.5):
    # add coastlines
    ax.add_feature(cfeature.LAND, facecolor=landcolor)
    ax.add_feature(cfeature.OCEAN, facecolor=oceancolor)
    ax.add_feature(cfeature.COASTLINE, linewidth=cartopy_linewidth)
    # ax.add_feature(cfeature.BORDERS, linewidth=cartopy_linewidth, linestyle=":")

    # add gridlines
    if gridlines:
        ax, gl = add_gridlines(ax, projection)

    # set longitude and latitude format
    lon_formatter = LongitudeFormatter(zero_direction_label=False)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)

    # set extent
    if lon is not None and lat is not None:
        lon_min, lon_max = np.nanmin(lon), np.nanmax(lon)
        lat_min, lat_max = np.nanmin(lat), np.nanmax(lat)
        ax.set_extent([lon_min, lon_max, lat_min, lat_max], crs=projection)


# ** 自定义归一化类，使得0值处为中心点
class MidpointNormalize(mpl.colors.Normalize):
    """
    Description: 自定义归一化类，使得0值处为中心点

    param {*} mpl.colors.Normalize : 继承Normalize类
    return {*}

    Example:
    nrom = MidpointNormalize(vmin=-2, vmax=1, vcenter=0)
    """

    def __init__(self, vmin=None, vmax=None, vcenter=None, clip=False):
        self.vcenter = vcenter
        super().__init__(vmin, vmax, clip)

    def __call__(self, value, clip=None):
        x, y = [self.vmin, self.vcenter, self.vmax], [0, 0.5, 1.0]
        return np.ma.masked_array(np.interp(value, x, y, left=-np.inf, right=np.inf))

    def inverse(self, value):
        y, x = [self.vmin, self.vcenter, self.vmax], [0, 0.5, 1]
        return np.interp(value, x, y, left=-np.inf, right=np.inf)


# -----------------------------------------------------------------------------------------------------------------------------------------------------------------

# ** 绘制填色图
def contourf(data,x=None,y=None,cmap='coolwarm',show=True,store=None,cartopy=False):
    """
    Description: 绘制填色图

    param {*} data : 二维数据
    param {*} x : x轴坐标
    param {*} y : y轴坐标
    param {*} cmap : 颜色映射
    param {*} show : 是否显示
    param {*} store : 是否保存
    param {*} cartopy : 是否使用cartopy

    return {*}
    """
    data = np.array(data)
    if x is None or y is None:
        x = np.arange(data.shape[1])
        y = np.arange(data.shape[0])
    if cartopy:
        fig, ax = plt.subplots(subplot_kw={'projection': ccrs.PlateCarree()})
        add_cartopy(ax, lon=x, lat=y)
        ax.contourf(x, y, data, transform=ccrs.PlateCarree(), cmap=cmap)
    else:
        plt.contourf(x, y, data, cmap=cmap)
    plt.colorbar()
    plt.savefig(store, dpi=600, bbox_inches="tight") if store else plt.show()
    plt.close()


# ** 绘制等值线图
def contour(data, x=None, y=None, cmap="coolwarm", show=True, store=None, cartopy=False):
    """
    Description: 绘制等值线图

    param {*} data : 二维数据
    param {*} x : x轴坐标
    param {*} y : y轴坐标
    param {*} cmap : 颜色映射
    param {*} show : 是否显示
    param {*} store : 是否保存
    param {*} cartopy : 是否使用cartopy

    return {*}
    """
    data = np.array(data)
    if x is None or y is None:
        x = np.arange(data.shape[1])
        y = np.arange(data.shape[0])
    if cartopy:
        fig, ax = plt.subplots(subplot_kw={"projection": ccrs.PlateCarree()})
        add_cartopy(ax, lon=x, lat=y)
        cr = ax.contour(x, y, data, transform=ccrs.PlateCarree(), cmap=cmap)
    else:
        cr = plt.contour(x, y, data, cmap=cmap)
    plt.clabel(cr, inline=True, fontsize=10)
    plt.savefig(store, dpi=600, bbox_inches="tight") if store else plt.show()
    plt.close()


# ** 绘制矢量场
def quiver(u, v, lon, lat, picname=None, cmap="coolwarm", scale=0.25, width=0.002, x_space=5, y_space=5):
    """
    param        {*} u : 二维数据
    param        {*} v : 二维数据
    param        {*} lon : 经度, 1D or 2D
    param        {*} lat : 纬度, 1D or 2D
    param        {*} picname : 图片保存的文件名(含路径)
    param        {*} cmap : 颜色映射，默认coolwarm
    param        {*} scale : 箭头的大小 / 缩小程度
    param        {*} width : 箭头的宽度
    param        {*} x_space : x轴间隔
    param        {*} y_space : y轴间隔
    return       {*} 无返回值
    """
    # 创建新的网格位置变量(lat_c, lon_c)
    if len(lon.shape) == 1 and len(lat.shape) == 1:
        lon_c, lat_c = np.meshgrid(lon, lat)
    else:
        lon_c, lat_c = lon, lat

    # 设置箭头的比例、颜色、宽度等参数
    # scale = 0.25  # 箭头的大小 / 缩小程度
    # color = '#E5D1FA'
    # width = 0.002  # 箭头的宽度
    # x_space = 1
    # y_space = 1

    # 计算矢量的大小
    S = xr.DataArray(np.hypot(np.array(u), np.array(v)))

    mean_S = S.nanmean()

    # 使用 plt.quiver 函数绘制矢量图
    # 通过设置 quiver 函数的 pivot 参数来指定箭头的位置
    quiver_plot = plt.quiver(
        lon_c[::y_space, ::x_space],
        lat_c[::y_space, ::x_space],
        u[::y_space, ::x_space],
        v[::y_space, ::x_space],
        S[::y_space, ::x_space],  # 矢量的大小，可以不要
        pivot="middle",
        scale=scale,
        #  color=color, # 矢量的颜色，单色
        cmap=cmap,  # 矢量的颜色，多色
        width=width,
    )
    # plt.quiverkey(quiver_plot, X=0.90, Y=0.975, U=1, label='1 m/s', labelpos='E', fontproperties={'size': 10})
    plt.quiverkey(quiver_plot, X=0.87, Y=0.975, U=mean_S, label=f"{mean_S:.2f} m/s", labelpos="E", fontproperties={"size": 10})
    plt.colorbar(quiver_plot)
    plt.xlabel("X")
    plt.ylabel("Y")

    plt.savefig(picname, bbox_inches="tight") if picname is not None else plt.show()
    plt.clf()
    plt.close()



if __name__ == "__main__":
    pass
