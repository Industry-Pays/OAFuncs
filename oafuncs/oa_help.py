#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-10-06 19:25:29
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-12-26 10:43:40
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_help.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import oafuncs

__all__ = ["query", "use"]


def query():
    """
    description: 查看oafuncs模块的函数列表
    example: query()
    """
    funcs = [func for func in dir(oafuncs) if callable(getattr(oafuncs, func))]
    print("函数数量：")
    print(len(funcs))
    print("函数列表：")
    print(funcs)


def use(func="get_var"):
    """
    description: 查看函数的模块全路径和函数提示
    param {func} : 函数名
    example: use('get_var')
    """
    print("模块全路径：")
    print(getattr(oafuncs, func).__module__ + "." + func)
    print("函数提示：")
    print(getattr(oafuncs, func).__doc__)
