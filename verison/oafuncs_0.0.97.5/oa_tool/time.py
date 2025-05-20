#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-03-09 13:55:46
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-03-09 13:55:46
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_tool\\time.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""


import calendar

__all__ = ["get_days"]

def get_days(year, month):
    return calendar.monthrange(year, month)[1]