#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 15:07:13
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-09-17 15:10:22
FilePath: \\Python\\My_Funcs\\OAFuncs\\file.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''

import os
import glob


# ** 创建文件夹/清空已有文件夹（可选）
def mk_path(pictpath: str, vars_name: str, clear=1) -> list:
    import shutil
    pictpaths = []
    for i in range(len(vars_name)):
        pictpaths.append(os.path.join(pictpath, vars_name[i]))
        if clear:
            shutil.rmtree(pictpaths[i], ignore_errors=True)
        os.makedirs(pictpaths[i], exist_ok=True)
    return pictpaths


def remove_empty_folders(path, print_info=0):
    # 遍历当前目录下的所有文件夹和文件
    for root, dirs, files in os.walk(path, topdown=False):
        # 遍历文件夹列表
        for folder in dirs:
            folder_path = os.path.join(root, folder)
            # 判断文件是否有权限访问
            try:
                os.listdir(folder_path)
            except OSError:
                continue
            # 判断文件夹是否为空
            if not os.listdir(folder_path):
                # 删除空文件夹
                try:
                    os.rmdir(folder_path)
                    print(f"Deleted empty folder: {folder_path}")
                except OSError:
                    if print_info:
                        print(f"Skipping protected folder: {folder_path}")
                    pass


def remove_file(pattern):
    '''
    remove_file(r'E:\Code\Python\Model\WRF\Radar2\bzip2-radar-0*')
    # or
    os.chdir(r'E:\Code\Python\Model\WRF\Radar2')
    remove_file('bzip2-radar-0*')
    '''
    # 使用glob.glob来获取所有匹配的文件
    # 可以使用通配符*来匹配所有文件
    file_list = glob.glob(pattern)
    for file_path in file_list:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f'成功删除文件: {file_path}')
            except Exception as e:
                print(f'删除文件失败: {file_path}')
                print(e)


if __name__ == '__main__':
    pictpath = 'D:/Data/2024/09/17/'
    vars_name = ['var1', 'var2']
    pictpaths = mk_path(pictpath, vars_name, clear=1)
    print(pictpaths)
