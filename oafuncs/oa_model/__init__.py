#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-03-09 16:28:42
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-03-09 16:28:42
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_model\\__init__.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""


# 会导致OAFuncs直接导入所有函数，不符合模块化设计
from .roms import *
from .wrf import *
