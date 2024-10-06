#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-10-06 19:25:29
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-10-06 19:55:04
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_help.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''

import OAFuncs


def query():
    funcs = [func for func in dir(OAFuncs) if callable(getattr(OAFuncs, func))]
    print('函数数量：')
    print(len(funcs))
    print('函数列表：')
    print(funcs)


def use(func='get_var'):
    print('模块全路径：')
    print(getattr(OAFuncs, func).__module__+'.'+func)
    print('函数提示：')
    print(getattr(OAFuncs, func).__doc__)
