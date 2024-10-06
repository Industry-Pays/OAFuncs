#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 15:07:13
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-10-06 19:00:51
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_file.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''



import glob
import os
import re
import shutil

__all__ = ['link_file', 'copy_file', 'rename_files', 'make_folder',
           'clear_folder', 'remove_empty_folders', 'remove']

def link_file(src_pattern, dst):
    '''
    # 使用示例
    # link_file(r'/data/hejx/liukun/era5/*', r'/data/hejx/liukun/Test/')
    # link_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test/py.o')
    # link_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test')
    '''
    src_pattern = str(src_pattern)
    # 使用glob.glob来处理可能包含通配符的src
    src_files = glob.glob(src_pattern)
    if not src_files:
        raise FileNotFoundError('文件不存在: {}'.format(src_pattern))

    # 判断dst是路径还是包含文件名的路径
    if os.path.isdir(dst):
        # 如果dst是路径，则保持源文件的文件名
        dst_dir = dst
        for src_file in src_files:
            src_file_basename = os.path.basename(src_file)
            dst_file = os.path.join(dst_dir, src_file_basename)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            os.symlink(src_file, dst_file)
            print(f'创建符号链接: {src_file} -> {dst_file}')
    else:
        # 如果dst包含文件名，则创建链接后重命名
        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, exist_ok=True)
        # 只处理第一个匹配的文件
        src_file = src_files[0]
        dst_file = dst
        if os.path.exists(dst_file):
            os.remove(dst_file)
        os.symlink(src_file, dst_file)
        print(f'创建符号链接并重命名: {src_file} -> {dst_file}')


def copy_file(src_pattern, dst):
    '''
    # 使用示例
    # copy_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test/py.o')
    # link_file(r'/data/hejx/liukun/era5/*', r'/data/hejx/liukun/Test/')
    # link_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test/py.o')
    # copy_file(r'/data/hejx/liukun/era5/py.o*', r'/data/hejx/liukun/Test')
    '''
    src_pattern = str(src_pattern)
    # 使用glob.glob来处理可能包含通配符的src
    src_files = glob.glob(src_pattern)
    if not src_files:
        raise FileNotFoundError('文件不存在: {}'.format(src_pattern))

    # 判断dst是路径还是包含文件名的路径
    if os.path.isdir(dst):
        # 如果dst是路径，则保持源文件的文件名
        dst_dir = dst
        for src_file in src_files:
            src_file_basename = os.path.basename(src_file)
            dst_file = os.path.join(dst_dir, src_file_basename)
            if os.path.exists(dst_file):
                if os.path.isdir(dst_file):
                    shutil.rmtree(dst_file)
                else:
                    os.remove(dst_file)
            if os.path.isdir(src_file):
                shutil.copytree(src_file, dst_file, symlinks=True)
            else:
                shutil.copy2(src_file, dst_file)
            print(f'复制文件或目录: {src_file} -> {dst_file}')
    else:
        # 如果dst包含文件名，则复制后重命名
        dst_dir = os.path.dirname(dst)
        os.makedirs(dst_dir, exist_ok=True)
        # 只处理第一个匹配的文件
        src_file = src_files[0]
        dst_file = dst
        if os.path.exists(dst_file):
            if os.path.isdir(dst_file):
                shutil.rmtree(dst_file)
            else:
                os.remove(dst_file)
        if os.path.isdir(src_file):
            shutil.copytree(src_file, dst_file, symlinks=True)
        else:
            shutil.copy2(src_file, dst_file)
        print(f'复制文件或目录并重命名: {src_file} -> {dst_file}')


def rename_files(directory, old_str, new_str):
    '''
    # 使用示例
    directory_path = r"E:\Code\Matlab\Master\Ocean\ROMS\CROCO-1.3.1\My_Models\windfarm\CROCO_FILES"
    old_str = "croco"
    new_str = "roms"
    rename_files(directory_path, old_str, new_str)
    '''
    # 获取目录下的所有文件
    files = os.listdir(directory)

    # 构建正则表达式以匹配要替换的字符串
    pattern = re.compile(re.escape(old_str))

    # 遍历目录下的文件
    for filename in files:
        # 检查文件名中是否包含要替换的字符串
        if pattern.search(filename):
            # 构建新的文件名
            new_filename = pattern.sub(new_str, filename)

            # 构建旧文件的完整路径
            old_path = os.path.join(directory, filename)

            # 构建新文件的完整路径
            new_path = os.path.join(directory, new_filename)

            # 重命名文件
            os.rename(old_path, new_path)
            print(f"重命名文件: {old_path} -> {new_path}")


# ** 创建子文件夹（可选清空）
def make_folder(rootpath: str, folder_name: str, clear=0) -> str:
    folder_path = os.path.join(str(rootpath), str(folder_name))
    if clear:
        shutil.rmtree(folder_path, ignore_errors=True)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path

# ** 清空文件夹
def clear_folder(folder_path):
    folder_path = str(folder_path)
    if os.path.exists(folder_path):
        try:
            # 遍历文件夹中的所有文件和子文件夹
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                # 判断是文件还是文件夹
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # 删除文件或链接
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # 删除子文件夹
            print(f'成功清空文件夹: {folder_path}')
        except Exception as e:
            print(f'清空文件夹失败: {folder_path}')
            print(e)


# ** 清理空文件夹
def remove_empty_folders(path, print_info=1):
    path = str(path)
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


# ** 删除相关文件，可使用通配符
def remove(pattern):
    '''
    remove(r'E:\Code\Python\Model\WRF\Radar2\bzip2-radar-0*')
    # or
    os.chdir(r'E:\Code\Python\Model\WRF\Radar2')
    remove('bzip2-radar-0*')
    '''
    # 使用glob.glob来获取所有匹配的文件
    # 可以使用通配符*来匹配所有文件
    pattern = str(pattern)
    file_list = glob.glob(pattern)
    for file_path in file_list:
        if os.path.exists(file_path):
            try:
                shutil.rmtree(file_path)
                print(f'成功删除文件: {file_path}')
            except Exception as e:
                print(f'删除文件失败: {file_path}')
                print(e)
        else:
            print(f'文件不存在: {file_path}')


if __name__ == '__main__':
    # newpath = make_folder('D:/Data/2024/09/17/', 'var1', clear=1)
    # print(newpath)
    pass

    remove(r'I:\Delete\test\*')
