#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-11-21 09:48:00
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-11-21 10:18:33
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_tool\\__init__.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
'''


# 会导致OAFuncs直接导入所有函数，不符合模块化设计
from .email import *
