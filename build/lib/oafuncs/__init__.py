#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 16:09:20
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-12-13 12:31:06
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_s\\__init__.py
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

# ------------------- 2024-12-13 12:31:06 -------------------
# path: My_Funcs/OAFuncs/oafuncs/
from .oa_cmap import *
from .oa_data import *
from .oa_draw import *
from .oa_file import *
from .oa_help import *
from .oa_nc import *
from .oa_python import *
# ------------------- 2024-12-13 12:31:06 -------------------
# path: My_Funcs/OAFuncs/oafuncs/oa_down/
from .oa_down import *
# ------------------- 2024-12-13 12:31:06 -------------------
# path: My_Funcs/OAFuncs/oafuncs/oa_sign/
from .oa_sign import *
# ------------------- 2024-12-13 12:31:06 -------------------
# path: My_Funcs/OAFuncs/oafuncs/oa_tool/
from .oa_tool import *
# ------------------- 2024-12-13 12:31:06 -------------------
