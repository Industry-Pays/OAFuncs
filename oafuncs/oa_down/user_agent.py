#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-12-26 08:06:34
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-12-26 08:06:34
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_down\\user_agent.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""
import os
import random


__all__ = ["get_ua"]


def get_ua():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ua_file_txt = os.path.join(current_dir, "User_Agent-list.txt")

    with open(ua_file_txt, "r") as f:
        ua_list = f.readlines()
        # 去掉换行符和空行
        ua_list = [line.strip() for line in ua_list if line.strip()]

    return random.choice(ua_list)