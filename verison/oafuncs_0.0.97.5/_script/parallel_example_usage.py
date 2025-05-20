#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-03-18 19:14:19
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-03-18 19:18:38
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\_script\\parallel_example_usage.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import logging
import time
from auto_optimized_parallel_executor import ParallelExecutor

# 设置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# 示例函数
def compute_intensive_task(n):
    """计算密集型任务示例"""
    result = 0
    for i in range(n):
        result += i**0.5
    return result


def io_intensive_task(seconds, value):
    """IO密集型任务示例"""
    time.sleep(seconds)  # 模拟IO操作
    return f"Processed {value}"


def main():
    # 创建自动优化的执行器
    executor = ParallelExecutor()

    # 打印选择的模式和工作线程/进程数量
    print(f"自动选择的执行模式: {executor.mode}")
    print(f"自动选择的工作线程/进程数: {executor.max_workers}")
    print(f"运行平台: {executor.platform}")

    # 示例1: 计算密集型任务
    print("\n运行计算密集型任务...")
    params = [(1000000,) for _ in range(20)]
    results = executor.run(compute_intensive_task, params)
    print(f"完成计算密集型任务，结果数量: {len(results)}")

    # 示例2: IO密集型任务
    print("\n运行IO密集型任务...")
    io_params = [(0.1, f"item-{i}") for i in range(30)]
    io_results = executor.run(io_intensive_task, io_params)
    print(f"完成IO密集型任务，结果示例: {io_results[:3]}")

    # 示例3: 使用map接口
    print("\n使用map接口...")
    numbers = list(range(1, 11))
    squared = list(executor.map(lambda x: x * x, numbers))
    print(f"Map结果: {squared}")

    # 示例4: 使用imap_unordered接口（乱序返回结果）
    print("\n使用imap_unordered接口...")
    for i, result in enumerate(executor.imap_unordered(lambda x: x * x * x, range(1, 11))):
        print(f"收到结果 #{i}: {result}")

    # 示例5: 使用gather执行不同函数
    print("\n使用gather接口执行不同函数...")
    tasks = [(compute_intensive_task, (500000,)), (io_intensive_task, (0.2, "task1")), (io_intensive_task, (0.1, "task2")), (compute_intensive_task, (300000,))]
    gather_results = executor.gather(tasks)
    print(f"Gather结果: {gather_results}")

    # 关闭执行器
    executor.shutdown()
    print("\n执行器已关闭")


if __name__ == "__main__":
    main()
