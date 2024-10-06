#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-09-17 17:12:47
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-10-06 19:05:38
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_data.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''



import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy.interpolate import griddata

__all__ = ['interp_2d', 'interp_2d_parallel']

# ** 高维插值函数，插值最后两个维度
def interp_2d(target_x, target_y, origin_x, origin_y, data, method='linear'):
    """
    高维插值函数，默认插值最后两个维度，传输数据前请确保数据的维度正确
    参数:
    target_y (array-like): 目标经度网格 1D 或 2D
    target_x (array-like): 目标纬度网格 1D 或 2D
    origin_y (array-like): 初始经度网格 1D 或 2D
    origin_x (array-like): 初始纬度网格 1D 或 2D
    data (array-like): 数据 (*, lat, lon) 2D, 3D, 4D
    method (str, optional): 插值方法，可选 'linear', 'nearest', 'cubic' 等，默认为 'linear'
    返回:
    array-like: 插值结果
    """

    # 确保目标网格和初始网格都是二维的
    if len(target_y.shape) == 1:
        target_x, target_y = np.meshgrid(target_x, target_y)
    if len(origin_y.shape) == 1:
        origin_x, origin_y = np.meshgrid(origin_x, origin_y)

    dims = data.shape
    len_dims = len(dims)
    # print(dims[-2:])
    # 根据经纬度网格判断输入数据的形状是否匹配

    if origin_x.shape != dims[-2:] or origin_y.shape != dims[-2:]:
        print(origin_x.shape, dims[-2:])
        raise ValueError(
            'Shape of data does not match shape of origin_x or origin_y.')

    # 将目标网格展平成一维数组
    target_points = np.column_stack((np.ravel(target_y), np.ravel(target_x)))

    # 将初始网格展平成一维数组
    origin_points = np.column_stack((np.ravel(origin_y), np.ravel(origin_x)))

    # 进行插值
    if len_dims == 2:
        interpolated_data = griddata(origin_points, np.ravel(
            data), target_points, method=method)
        interpolated_data = np.reshape(interpolated_data, target_y.shape)
    elif len_dims == 3:
        interpolated_data = []
        for i in range(dims[0]):
            dt = griddata(origin_points, np.ravel(
                data[i, :, :]), target_points, method=method)
            interpolated_data.append(np.reshape(dt, target_y.shape))
            print(f'Interpolating {i+1}/{dims[0]}...')
        interpolated_data = np.array(interpolated_data)
    elif len_dims == 4:
        interpolated_data = []
        for i in range(dims[0]):
            interpolated_data.append([])
            for j in range(dims[1]):
                dt = griddata(origin_points, np.ravel(
                    data[i, j, :, :]), target_points, method=method)
                interpolated_data[i].append(np.reshape(dt, target_y.shape))
                print(
                    f'\rInterpolating {i*dims[1]+j+1}/{dims[0]*dims[1]}...', end='')
        print('\n')
        interpolated_data = np.array(interpolated_data)

    return interpolated_data


# ** 高维插值函数，插值最后两个维度，使用多线程进行插值
# 在本地电脑上可以提速三倍左右，超算上暂时无法加速
def interp_2d_parallel(target_x, target_y, origin_x, origin_y, data, method='linear'):
    def interp_single2d(target_y, target_x, origin_y, origin_x, data, method='linear'):
        target_points = np.column_stack(
            (np.ravel(target_y), np.ravel(target_x)))
        origin_points = np.column_stack(
            (np.ravel(origin_y), np.ravel(origin_x)))

        dt = griddata(origin_points, np.ravel(
            data[:, :]), target_points, method=method)
        return np.reshape(dt, target_y.shape)

    def interp_single3d(i, target_y, target_x, origin_y, origin_x, data, method='linear'):
        target_points = np.column_stack(
            (np.ravel(target_y), np.ravel(target_x)))
        origin_points = np.column_stack(
            (np.ravel(origin_y), np.ravel(origin_x)))

        dt = griddata(origin_points, np.ravel(
            data[i, :, :]), target_points, method=method)
        return np.reshape(dt, target_y.shape)

    def interp_single4d(i, j, target_y, target_x, origin_y, origin_x, data, method='linear'):
        target_points = np.column_stack(
            (np.ravel(target_y), np.ravel(target_x)))
        origin_points = np.column_stack(
            (np.ravel(origin_y), np.ravel(origin_x)))

        dt = griddata(origin_points, np.ravel(
            data[i, j, :, :]), target_points, method=method)
        return np.reshape(dt, target_y.shape)

    if len(target_y.shape) == 1:
        target_x, target_y = np.meshgrid(target_x, target_y)
    if len(origin_y.shape) == 1:
        origin_x, origin_y = np.meshgrid(origin_x, origin_y)

    dims = data.shape
    len_dims = len(dims)

    if origin_x.shape != dims[-2:] or origin_y.shape != dims[-2:]:
        raise ValueError('数据形状与 origin_x 或 origin_y 的形状不匹配.')

    interpolated_data = []

    # 使用多线程进行插值
    with ThreadPoolExecutor(max_workers=mp.cpu_count()-2) as executor:
        print(f'Using {mp.cpu_count()-2} threads...')
        if len_dims == 2:
            interpolated_data = list(executor.map(interp_single2d, [target_y], [
                                     target_x], [origin_y], [origin_x], [data], [method]))
        elif len_dims == 3:
            interpolated_data = list(executor.map(interp_single3d, [i for i in range(dims[0])], [
                                     target_y]*dims[0], [target_x]*dims[0], [origin_y]*dims[0], [origin_x]*dims[0], [data]*dims[0], [method]*dims[0]))
        elif len_dims == 4:
            interpolated_data = list(executor.map(interp_single4d, [i for i in range(dims[0]) for j in range(dims[1])], [j for i in range(dims[0]) for j in range(dims[1])], [
                                     target_y]*dims[0]*dims[1], [target_x]*dims[0]*dims[1], [origin_y]*dims[0]*dims[1], [origin_x]*dims[0]*dims[1], [data]*dims[0]*dims[1], [method]*dims[0]*dims[1]))
            interpolated_data = np.array(interpolated_data).reshape(
                dims[0], dims[1], target_y.shape[0], target_x.shape[1])

    interpolated_data = np.array(interpolated_data)

    return interpolated_data


if __name__ == '__main__':
    import time

    import matplotlib.pyplot as plt

    # 测试数据
    origin_x = np.linspace(0, 10, 11)
    origin_y = np.linspace(0, 10, 11)
    target_x = np.linspace(0, 10, 101)
    target_y = np.linspace(0, 10, 101)
    data = np.random.rand(11, 11)

    # 高维插值
    origin_x = np.linspace(0, 10, 11)
    origin_y = np.linspace(0, 10, 11)
    target_x = np.linspace(0, 10, 101)
    target_y = np.linspace(0, 10, 101)
    data = np.random.rand(10, 10, 11, 11)

    start = time.time()
    interpolated_data = interp_2d(target_x, target_y, origin_x, origin_y, data)
    print(f'Interpolation time: {time.time()-start:.2f}s')

    print(interpolated_data.shape)

    # 高维插值多线程
    start = time.time()
    interpolated_data = interp_2d_parallel(
        target_x, target_y, origin_x, origin_y, data)
    print(f'Interpolation time: {time.time()-start:.2f}s')

    print(interpolated_data.shape)
    print(interpolated_data[0, 0, :, :].shape)
    plt.figure()
    plt.contourf(target_x, target_y, interpolated_data[0, 0, :, :])
    plt.colorbar()
    plt.show()
