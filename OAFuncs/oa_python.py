#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-10-11 21:02:07
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-10-11 21:47:19
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_python.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''

import os

__all__ = ['install_lib', 'upgrade_lib']

def install_lib(libs=None,python_exe='python'):
    '''
    libs: list, 需要安装的库
    python_exe: str, python版本；如在windows下，将python.exe复制为python312.exe，然后python_exe='python312'
    '''
    os.system(python_exe + " -m ensurepip")
    os.system(python_exe + " -m pip install --upgrade pip")
    if libs is None:
        libs = [
            # "OAFuncs",  # 自己的库，在这个函数不宜操作，避免报错
            "requests",  # 网页
            "xlwt",  # excel文件
            "xlrd",  # excel文件
            "openpyxl",  # excel文件
            "netCDF4",  # nc文件
            "numpy",  # 数组
            "pandas",  # 数据
            "xarray",  # 数组
            "scipy",  # 科学计算
            # "scikit-learn", # 机器学习
            "matplotlib",  # 绘图
            # "seaborn",
            "imageio",  # 图像
            # "pylustrator",  # 绘图
            "Cartopy",  # 绘图 #cartopy已经支持python3.11并且可以直接pip安装
            "seawater",  # 海洋计算
            "cmaps",  # 颜色
            "colorcet",   # 颜色
            "cmasher",     # 颜色
            "tqdm",  # 进度条
            # "taichi",      # 加速
            "icecream",  # 打印调试
            # "pyperclip",  # 系统剪切板
            "rich",  # 精美文本终端
            # "stratify",  # 大气海洋数据垂直插值
            "dask",  # 并行计算
            "bs4",  # 网页
            "pathlib",  # 路径
            "opencv-contrib-python",  # 图像处理
            # "pydap",  # 网络数据xarray下载
            "gsw",  # 海洋计算
            "global_land_mask",  # 陆地海洋掩码
            # "cfgrib", # grib文件
            # "ecmwflibs", # grib文件， 两个库都需要安装
            "geopandas",  # 矢量数据，shp文件
            # "geopy",  # 地理位置
            # "flask",  # 网页
            "cdsapi",  # 网络数据下载(era5)
            # 以下不太重要
            "lxml",  # 网页
            "keyboard",  # 键盘
            "zhdate",  # 中国农历
            "python-pptx",  # ppt
            "python-docx",  # word
            "ipywidgets",  # jupyter显示进度条插件
            "salem",  # 地图投影，可部分替代wrf-python
            "meteva",  # 气象数据处理，中国气象局开发
            "wget",  # 下载
            "pyautogui",  # 鼠标键盘，自动连点脚本需要
        ]
    try:
        installed_libs = os.popen(python_exe + ' -m pip list').read()
        lib_num = len(libs)
        for i, lib in enumerate(libs):
            # 判断库是否已经安装，已安装跳过
            if lib in installed_libs:
                print(lib, "早已安装")
                continue
            else:
                os.system(python_exe + " -m " + "pip install " + lib)
                print('-'*100)
                print("安装成功", lib, "({}/{})".format(i+1, lib_num))
                print('-'*100)
    except Exception as e:
        print("安装失败:", str(e))


def upgrade_lib(libs=None,python_exe='python'):
    if libs is None:
        installed_libs = os.popen(python_exe + ' -m pip list').read()
        libs = installed_libs
    try:
        for lib in libs:
            os.system(python_exe + " -m " + "pip install --upgrade " + lib)
        print("升级成功")
    except Exception as e:
        print("升级失败:", str(e))
