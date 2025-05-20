#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-01-11 16:19:12
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-01-11 16:25:47
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_down\\idm.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import datetime
import os
from subprocess import call

from rich import print

__all__ = ["downloader"]


def downloader(task_url, folder_path, file_name, idm_engine=r"D:\Programs\Internet Download Manager\IDMan.exe"):
    """
    Description:
        Use IDM to download files.
    Parameter:
        task_url: str
            The download link of the file.
        folder_path: str
            The path of the folder where the file is saved.
        file_name: str
            The name of the file to be saved.
        idm_engine: str
            The path of the IDM engine. Note: "IDMan.exe"
    Return:
        None
    Example:
        downloader("https://www.test.com/data.nc", "E:\\Data", "test.nc", "D:\\Programs\\Internet Download Manager\\IDMan.exe")
    """
    os.makedirs(folder_path, exist_ok=True)
    # 将任务添加至队列
    call([idm_engine, "/d", task_url, "/p", folder_path, "/f", file_name, "/a"])
    # 开始任务队列
    call([idm_engine, "/s"])
    # print(f"IDM下载器：{file_name}下载任务已添加至队列...")
    print("[purple]-" * 50 + f"\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n" + "[purple]-" * 50)
    print(f"[green]IDM Downloader: {file_name} download task has been added to the queue...[/green]")
