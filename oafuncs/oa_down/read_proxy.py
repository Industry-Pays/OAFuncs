#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-04-17 13:59:14
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-04-17 14:00:38
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_down\\read_proxy.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import threading
from queue import Queue
import random
import requests
import os


# 从文件中读取代理列表
def read_proxies_from_file(filename):
    try:
        with open(filename, "r") as file:
            proxies = [line.strip() for line in file if line.strip()]
        return proxies
    except FileNotFoundError:
        print(f"未找到文件: {filename}，请检查文件是否存在。")
        return []


# 测试单个代理的可用性
def test_single_proxy(proxy, test_url, working_proxies_queue):
    try:
        response = requests.get(test_url, proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            # print(f"代理 {proxy} 可用，返回 IP: {response.json()['origin']}")
            working_proxies_queue.put(proxy)
        else:
            # print(f"代理 {proxy} 不可用，状态码: {response.status_code}")
            pass
    except Exception as e: # noqa: F841
        # print(f"代理 {proxy} 不可用，错误: {e}")
        pass


# 测试代理的可用性（多线程）
def test_proxies(proxies, test_url):
    working_proxies_queue = Queue()
    threads = []

    # 为每个代理创建一个线程
    for proxy in proxies:
        thread = threading.Thread(target=test_single_proxy, args=(proxy, test_url, working_proxies_queue))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 从队列中取出所有可用代理
    working_proxies = []
    while not working_proxies_queue.empty():
        working_proxies.append(working_proxies_queue.get())

    return working_proxies




# 主函数
def read_test(input_filename=r"E:\Code\Python\Tools\Yccol\output\http.txt"):
    # 测试 URL
    test_url = "http://httpbin.org/ip"

    # 读取代理列表
    proxies = read_proxies_from_file(input_filename)
    if not proxies:
        print(f"文件 '{input_filename}' 中没有找到有效的代理。")
        return

    # print(f"从文件 '{input_filename}' 中读取到 {len(proxies)} 个代理，开始测试...")

    # 测试代理
    working_proxies = test_proxies(proxies, test_url)
    
    return working_proxies

def get_valid_proxy(input_filename=r"E:\Code\Python\Tools\Yccol\output\http.txt"):
    working_proxies = read_test(input_filename)
    if not working_proxies:
        print("没有找到可用的代理。")
        return None
    choose_proxy = random.choice(working_proxies)
    print(f"Randomly selected available proxy: {choose_proxy}")

    # proxies = {"http": choose_proxy, "https": choose_proxy}
    # return proxies
    
    return choose_proxy


if __name__ == "__main__":
    pwd = os.path.dirname(os.path.abspath(__file__))
    read_test()
