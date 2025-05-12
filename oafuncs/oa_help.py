#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-10-06 19:25:29
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-01-01 21:09:58
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_help.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import oafuncs
import pkgutil
import importlib
from rich import print

__all__ = ["query", "use", "log"]


def query():
    """
    Description:
        Show the number of functions and the list of functions in the module.
    Example:
        query()
    """
    funcs = [func for func in dir(oafuncs) if callable(getattr(oafuncs, func))]
    print("函数数量：")
    print(len(funcs))
    print("函数列表：")
    print(funcs)
    
    # 判断同名函数个数
    func_dict = dict()
    for func in funcs:
        func_dict[func] = 0
    for module_info in pkgutil.iter_modules(oafuncs.__path__, oafuncs.__name__ + "."):
        module = importlib.import_module(module_info.name)
        for func in funcs:
            if hasattr(module, func):
                func_dict[func] += 1
    print("同名函数：")
    for func, count in func_dict.items():
        if count > 1:
            print(f"{func} : {count}")


def _use_single(func="get_var", module="oafuncs"):
    """
    description: 查看函数的模块全路径和函数提示
    param {func} : 函数名
    example: use('get_var')
    """
    module = importlib.import_module(module)
    print("模块全路径：")
    print(getattr(module, func).__module__ + "." + func)
    print("函数提示：")
    print(getattr(module, func).__doc__)


def use(func_name='log'):
    """
    Description:
        Show the full path and help of the function.
    Args:
        func_name: The name of the function.
    Example:
        use('log')
    """
    found = False
    # 假设oafuncs是一个包
    if hasattr(oafuncs, "__path__"):
        print("-" * 40)  # 分隔线
        # 遍历包内的所有模块
        for module_info in pkgutil.iter_modules(oafuncs.__path__, oafuncs.__name__ + "."):
            module_name = module_info.name
            module = importlib.import_module(module_name)
            if hasattr(module, func_name):
                found = True
                func_obj = getattr(module, func_name)
                print(f"[bold purple]模块全路径：\n[bold green]{func_obj.__module__}.{func_name}\n")
                help(func_obj)
                """ doc = func_obj.__doc__
                print("函数提示：")
                if doc:
                    print(doc)
                else:
                    print("无文档字符串") """
                print("-" * 40)  # 分隔线
    else:
        # 如果oafuncs只是一个模块，直接查找
        if hasattr(oafuncs, func_name):
            found = True
            func_obj = getattr(oafuncs, func_name)
            print(f"模块全路径：\n{func_obj.__module__}.{func_name}\n")
            help(func_obj)
            """ doc = func_obj.__doc__
            print("函数提示：")
            if doc:
                print(doc)
            else:
                print("无文档字符串") """
    if not found:
        print(f"在oafuncs中没有找到名为 '{func_name}' 的函数。")


def log():
    """
    Description:
        Show the update log.
    Example:
        log()
    """
    print("更新日志：")
    print(
        """
        2025-04-06
        1. 给所有函数使用Python标准的docstring格式(英文)添加/修改说明
        2. 同时给所有参数添加类型声明
        3. 逻辑检查,优化
        4. 使用rich库的print函数，增加颜色
        5. 所有输出,如果是中文,改成英文
        """
    )
    print(
        """
        2025-01-15
        1. 优化了doi下载文献函数，增加下载途径及优化异常处理
        """
    )
    print(
        """
        2025-01-07
        1. 测试Python版本最低为3.9
        2. 优化了部分函数说明
        3. 优化hycom_3hourly模块，滑动判断文件是否正常
        """
    )
    print(
        """
        2025-01-01
        1. 添加了log函数，可以查看更新日志。
        2. 修改部分函数名，尽可能简化函数名。
        """
    )


if __name__ == "__main__":
    # use("find_file")
    query()