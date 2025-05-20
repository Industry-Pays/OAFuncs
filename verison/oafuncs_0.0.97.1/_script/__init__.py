#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-03-13 15:26:15
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-03-13 15:26:18
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_script\\__init__.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""



# 会导致OAFuncs直接导入所有函数，不符合模块化设计
# from oafuncs.oa_s.oa_cmap import *
# from oafuncs.oa_s.oa_data import *
# from oafuncs.oa_s.oa_draw import *
# from oafuncs.oa_s.oa_file import *
# from oafuncs.oa_s.oa_help import *
# from oafuncs.oa_s.oa_nc import *
# from oafuncs.oa_s.oa_python import *

from .plot_dataset import func_plot_dataset