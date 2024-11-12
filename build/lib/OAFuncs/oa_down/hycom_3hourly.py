#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-11-01 10:31:09
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-11-12 16:22:33
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_down\\hycom_3hourly.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''
import datetime
import os
import random
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from rich import print
from rich.progress import Progress

warnings.filterwarnings("ignore", category=RuntimeWarning,
                        message="Engine '.*' loading failed:.*")

__all__ = ['draw_time_range', 'download', 'how_to_use', 'get_time_list']

# time resolution
data_info = {'yearly': {}, 'monthly': {}, 'daily': {}, 'hourly': {}}

# hourly data
# dataset: GLBv0.08, GLBu0.08, GLBy0.08
data_info['hourly']['dataset'] = {
    'GLBv0.08': {}, 'GLBu0.08': {}, 'GLBy0.08': {}}

# version
# version of GLBv0.08: 53.X, 56.3, 57.2, 92.8, 57.7, 92.9, 93.0
data_info['hourly']['dataset']['GLBv0.08']['version'] = {
    '53.X': {}, '56.3': {}, '57.2': {}, '92.8': {}, '57.7': {}, '92.9': {}, '93.0': {}}
# version of GLBu0.08: 93.0
data_info['hourly']['dataset']['GLBu0.08']['version'] = {'93.0': {}}
# version of GLBy0.08: 93.0
data_info['hourly']['dataset']['GLBy0.08']['version'] = {'93.0': {}}

# info details
# time range
# GLBv0.08
# 在网页上提交超过范围的时间，会返回该数据集实际时间范围，从而纠正下面的时间范围
# 目前只纠正了GLBv0.08 93.0的时间范围，具体到小时了
# 其他数据集的时刻暂时默认为00起，21止
data_info['hourly']['dataset']['GLBv0.08']['version']['53.X']['time_range'] = {
    'time_start': '19940101', 'time_end': '20151230'}
data_info['hourly']['dataset']['GLBv0.08']['version']['56.3']['time_range'] = {
    'time_start': '20140701', 'time_end': '20160430'}
data_info['hourly']['dataset']['GLBv0.08']['version']['57.2']['time_range'] = {
    'time_start': '20160501', 'time_end': '20170131'}
data_info['hourly']['dataset']['GLBv0.08']['version']['92.8']['time_range'] = {
    'time_start': '20170201', 'time_end': '20170531'}
data_info['hourly']['dataset']['GLBv0.08']['version']['57.7']['time_range'] = {
    'time_start': '20170601', 'time_end': '20170930'}
data_info['hourly']['dataset']['GLBv0.08']['version']['92.9']['time_range'] = {
    'time_start': '20171001', 'time_end': '20171231'}
data_info['hourly']['dataset']['GLBv0.08']['version']['93.0']['time_range'] = {
    'time_start': '2018010112', 'time_end': '2020021909'}
# GLBu0.08
data_info['hourly']['dataset']['GLBu0.08']['version']['93.0']['time_range'] = {
    'time_start': '20180919', 'time_end': '20181208'}
# GLBy0.08
data_info['hourly']['dataset']['GLBy0.08']['version']['93.0']['time_range'] = {
    'time_start': '20181204', 'time_end': '20300904'}

# variable
variable_info = {
    'u': {'var_name': 'water_u', 'standard_name': 'eastward_sea_water_velocity'},
    'v': {'var_name': 'water_v', 'standard_name': 'northward_sea_water_velocity'},
    'temp': {'var_name': 'water_temp', 'standard_name': 'sea_water_potential_temperature'},
    'salinity': {'var_name': 'salinity', 'standard_name': 'sea_water_salinity'},
    'ssh': {'var_name': 'surf_el', 'standard_name': 'sea_surface_elevation'},
    'u_b': {'var_name': 'water_u_bottom', 'standard_name': 'eastward_sea_water_velocity_at_sea_floor'},
    'v_b': {'var_name': 'water_v_bottom', 'standard_name': 'northward_sea_water_velocity_at_sea_floor'},
    'temp_b': {'var_name': 'water_temp_bottom', 'standard_name': 'sea_water_potential_temperature_at_sea_floor'},
    'salinity_b': {'var_name': 'salinity_bottom', 'standard_name': 'sea_water_salinity_at_sea_floor'},
}

# classification method
# year_different: the data of different years is stored in different files
# same_path: the data of different years is stored in the same file
# var_different: the data of different variables is stored in different files
# var_year_different: the data of different variables and years is stored in different files
data_info['hourly']['dataset']['GLBv0.08']['version']['53.X']['classification'] = 'year_different'
data_info['hourly']['dataset']['GLBv0.08']['version']['56.3']['classification'] = 'same_path'
data_info['hourly']['dataset']['GLBv0.08']['version']['57.2']['classification'] = 'same_path'
data_info['hourly']['dataset']['GLBv0.08']['version']['92.8']['classification'] = 'var_different'
data_info['hourly']['dataset']['GLBv0.08']['version']['57.7']['classification'] = 'same_path'
data_info['hourly']['dataset']['GLBv0.08']['version']['92.9']['classification'] = 'var_different'
data_info['hourly']['dataset']['GLBv0.08']['version']['93.0']['classification'] = 'var_different'
data_info['hourly']['dataset']['GLBu0.08']['version']['93.0']['classification'] = 'var_different'
data_info['hourly']['dataset']['GLBy0.08']['version']['93.0']['classification'] = 'var_year_different'

# download info
# base url
# GLBv0.08 53.X
url_53x = {}
for y_53x in range(1994, 2016):
    # r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_53.X/data/2013?'
    url_53x[str(
        y_53x)] = rf'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_53.X/data/{y_53x}?'
data_info['hourly']['dataset']['GLBv0.08']['version']['53.X']['url'] = url_53x
# GLBv0.08 56.3
data_info['hourly']['dataset']['GLBv0.08']['version']['56.3']['url'] = r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_56.3?'
# GLBv0.08 57.2
data_info['hourly']['dataset']['GLBv0.08']['version']['57.2']['url'] = r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_57.2?'
# GLBv0.08 92.8
url_928 = {
    'uv3z': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.8/uv3z?',
    'ts3z': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.8/ts3z?',
    'ssh': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.8/ssh?',
}
data_info['hourly']['dataset']['GLBv0.08']['version']['92.8']['url'] = url_928
# GLBv0.08 57.7
data_info['hourly']['dataset']['GLBv0.08']['version']['57.7']['url'] = r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_57.7?'
# GLBv0.08 92.9
url_929 = {
    'uv3z': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.9/uv3z?',
    'ts3z': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.9/ts3z?',
    'ssh': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.9/ssh?',
}
data_info['hourly']['dataset']['GLBv0.08']['version']['92.9']['url'] = url_929
# GLBv0.08 93.0
url_930_v = {
    'uv3z': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_93.0/uv3z?',
    'ts3z': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_93.0/ts3z?',
    'ssh': r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_93.0/ssh?',
}
data_info['hourly']['dataset']['GLBv0.08']['version']['93.0']['url'] = url_930_v
# GLBu0.08 93.0
url_930_u = {
    'uv3z': r'https://ncss.hycom.org/thredds/ncss/GLBu0.08/expt_93.0/uv3z?',
    'ts3z': r'https://ncss.hycom.org/thredds/ncss/GLBu0.08/expt_93.0/ts3z?',
    'ssh': r'https://ncss.hycom.org/thredds/ncss/GLBu0.08/expt_93.0/ssh?',
}
data_info['hourly']['dataset']['GLBu0.08']['version']['93.0']['url'] = url_930_u
# GLBy0.08 93.0
uv3z_930_y = {}
ts3z_930_y = {}
ssh_930_y = {}
for y_930_y in range(2018, 2025):
    uv3z_930_y[str(
        y_930_y)] = rf'https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/uv3z/{y_930_y}?'
    ts3z_930_y[str(
        y_930_y)] = rf'https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/ts3z/{y_930_y}?'
    ssh_930_y[str(
        y_930_y)] = rf'https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/ssh/{y_930_y}?'
url_930_y = {
    'uv3z': uv3z_930_y,
    'ts3z': ts3z_930_y,
    'ssh': ssh_930_y,
}
data_info['hourly']['dataset']['GLBy0.08']['version']['93.0']['url'] = url_930_y


def draw_time_range(pic_save_folder=None):
    if pic_save_folder is not None:
        os.makedirs(pic_save_folder, exist_ok=True)
    # Converting the data into a format suitable for plotting
    data = []
    for dataset, versions in data_info['hourly']['dataset'].items():
        for version, time_range in versions['version'].items():
            t_s = time_range['time_range']['time_start']
            t_e = time_range['time_range']['time_end']
            if len(t_s) == 8:
                t_s = t_s + '00'
            if len(t_e) == 8:
                t_e = t_e + '21'
            t_s, t_e = t_s + '0000', t_e + '0000'
            data.append({
                'dataset': dataset,
                'version': version,
                'start_date': pd.to_datetime(t_s),
                'end_date': pd.to_datetime(t_e)
            })

    # Creating a DataFrame
    df = pd.DataFrame(data)

    # Plotting with combined labels for datasets and versions on the y-axis
    plt.figure(figsize=(12, 6))

    # Combined labels for datasets and versions
    combined_labels = [f"{dataset}_{version}" for dataset,
                       version in zip(df['dataset'], df['version'])]

    colors = plt.cm.viridis(np.linspace(0, 1, len(combined_labels)))

    # Assigning a color to each combined label
    label_colors = {label: colors[i]
                    for i, label in enumerate(combined_labels)}

    # Plotting each time range
    k = 1
    for _, row in df.iterrows():
        plt.plot([row['start_date'], row['end_date']], [k, k],
                 color=label_colors[f"{row['dataset']}_{row['version']}"], linewidth=6)
        # plt.text(row['end_date'], k,
        #          f"{row['version']}", ha='right', color='black')
        ymdh_s = row['start_date'].strftime('%Y-%m-%d %H')
        ymdh_e = row['end_date'].strftime('%Y-%m-%d %H')
        if k == 1 or k == len(combined_labels):
            plt.text(row['start_date'], k+0.125,
                     f"{ymdh_s}", ha='left', color='black')
            plt.text(row['end_date'], k+0.125,
                     f"{ymdh_e}", ha='right', color='black')
        else:
            plt.text(row['start_date'], k+0.125,
                     f"{ymdh_s}", ha='right', color='black')
            plt.text(row['end_date'], k+0.125,
                     f"{ymdh_e}", ha='left', color='black')
        k += 1

    # Setting the y-axis labels
    plt.yticks(range(1, len(combined_labels)+1), combined_labels)
    plt.xlabel('Time')
    plt.ylabel('Dataset - Version')
    plt.title('Time Range of Different Versions of Datasets')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    if pic_save_folder:
        plt.savefig(Path(pic_save_folder) / 'HYCOM_time_range.png')
        print(f'[bold green]HYCOM_time_range.png has been saved in {
              pic_save_folder}')
    else:
        plt.savefig('HYCOM_time_range.png')
        print('[bold green]HYCOM_time_range.png has been saved in the current folder')
        print(f'Curren folder: {os.getcwd()}')
    # plt.show()
    plt.close()


def transform_time(time_str):
    # old_time = '2023080203'
    # time_new = '2023-08-02T03%3A00%3A00Z'
    time_new = f'{time_str[:4]}-{time_str[4:6]
                                 }-{time_str[6:8]}T{time_str[8:10]}%3A00%3A00Z'
    return time_new


def get_time_list(time_s, time_e, delta_hour):
    '''
    Description: get a list of time strings from time_s to time_e with delta_hour
    Args:
        time_s: start time string, e.g. '2023080203'
        time_e: end time string, e.g. '2023080303'
        delta_hour: interval of hours
    Returns:
        dt_list: a list of time strings
    '''
    dt = datetime.datetime.strptime(time_s, '%Y%m%d%H')
    dt_list = []
    while dt.strftime('%Y%m%d%H') <= time_e:
        dt_list.append(dt.strftime('%Y%m%d%H'))
        dt = dt + datetime.timedelta(hours=delta_hour)
    return dt_list


def get_nearest_level_index(depth):
    level_depth = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 125.0,
                   150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1250.0, 1500.0, 2000.0, 2500.0, 3000.0, 4000.0, 5000]
    return min(range(len(level_depth)), key=lambda i: abs(level_depth[i]-depth))


def set_query_dict_no_vertical(var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh):
    query_dict = {
        'var': variable_info[var]['var_name'],
        'north': lat_max,
        'west': lon_min,
        'east': lon_max,
        'south': lat_min,
        'horizStride': 1,
        'time': transform_time(time_str_ymdh),
        'addLatLon': 'true',
        'accept': 'netcdf4'
    }
    return query_dict


def set_query_dict_depth_or_level(var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh):
    query_dict = {
        'var': variable_info[var]['var_name'],
        'north': lat_max,
        'west': lon_min,
        'east': lon_max,
        'south': lat_min,
        'horizStride': 1,
        'time': transform_time(time_str_ymdh),
        'vertCoord': 0,
        'addLatLon': 'true',
        'accept': 'netcdf4'
    }
    return query_dict


def set_query_dict_full(var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh):
    query_dict = {
        'var': variable_info[var]['var_name'],
        'north': lat_max,
        'west': lon_min,
        'east': lon_max,
        'south': lat_min,
        'horizStride': 1,
        'time': transform_time(time_str_ymdh),
        'vertStride': 1,
        'addLatLon': 'true',
        'accept': 'netcdf4'
    }
    return query_dict


def get_query_dict_single_depth(var, lon_min, lon_max, lat_min, lat_max, depth, time_str_ymdh):
    if var in ['ssh']:
        query_dict = set_query_dict_no_vertical(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    else:
        query_dict = set_query_dict_depth_or_level(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    if var in ['u', 'v', 'temp', 'salinity']:
        print('Please ensure the depth is in the range of 0-5000 m')
        query_dict['vertCoord'] = get_nearest_level_index(depth)+1
    return query_dict


def get_query_dict_single_level(var, lon_min, lon_max, lat_min, lat_max, level_num, time_str_ymdh):
    if var in ['ssh']:
        query_dict = set_query_dict_no_vertical(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    else:
        # level_num: 1-40
        query_dict = set_query_dict_depth_or_level(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    if var in ['u', 'v', 'temp', 'salinity']:
        print('Please ensure the level_num is in the range of 1-40')
        if level_num == 0:
            level_num = 1
            print('The level_num is set to 1')
        if level_num > 40:
            level_num = 40
            print('The level_num is set to 40')
        query_dict['vertCoord'] = level_num
    return query_dict


def get_query_dict_full_level(var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh):
    if var in ['ssh']:
        query_dict = set_query_dict_no_vertical(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    else:
        query_dict = set_query_dict_full(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    return query_dict


def get_query_dict_full_depth(var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh):
    if var in ['ssh']:
        query_dict = set_query_dict_no_vertical(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    else:
        query_dict = set_query_dict_full(
            var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh)
    return query_dict


def ymd_in_which_dataset_and_version(time_ymdh):
    time_ymdh = int(time_ymdh)
    d_list = []
    v_list = []
    trange_list = []
    have_data = False
    for dataset_name in data_info['hourly']['dataset'].keys():
        for version_name in data_info['hourly']['dataset'][dataset_name]['version'].keys():
            # print(data_info['hourly']['dataset'][dataset_name]
            #       ['version'][version_name]['time_range'].values())
            time_s, time_e = list(
                data_info['hourly']['dataset'][dataset_name]['version'][version_name]['time_range'].values())
            time_s, time_e = str(time_s), str(time_e)
            if len(time_s) == 8:
                time_s = time_s + '00'
            if len(time_e) == 8:
                time_e = time_e + '21'
            if time_ymdh >= int(time_s) and time_ymdh <= int(time_e):
                d_list.append(dataset_name)
                v_list.append(version_name)
                trange_list.append(f'{time_s}-{time_e}')
                have_data = True
    print(f'[bold red]{time_ymdh} is in the following dataset and version:')
    if have_data:
        for d, v, trange in zip(d_list, v_list, trange_list):
            # print(f'{time_ymd} is in {d} {v} {trange}')
            print(f'[bold blue]{d} {v} {trange}')
    else:
        raise ValueError(
            f'[bold red]{time_ymdh} is not in any dataset and version')


def direct_choose_dataset_and_version(time_ymdh):
    time_ymdh = int(time_ymdh)
    for dataset_name in data_info['hourly']['dataset'].keys():
        for version_name in data_info['hourly']['dataset'][dataset_name]['version'].keys():
            [time_s, time_e] = list(data_info['hourly']['dataset'][dataset_name]['version'][version_name]['time_range'].values(
            ))
            # print(time_s, time_e, time_ymd)
            time_s, time_e = str(time_s), str(time_e)
            if len(time_s) == 8:
                time_s = time_s + '00'
            if len(time_e) == 8:
                time_e = time_e + '21'
            if time_ymdh >= int(time_s) and time_ymdh <= int(time_e):
                print(
                    f'[bold purple]dataset: {dataset_name}, version: {version_name} is chosen')
                # print(f'{time_ymdh} is in {dataset_name} {version_name}')
                return dataset_name, version_name


def get_base_url(dataset_name, version_name, var, year_str):
    url_dict = data_info['hourly']['dataset'][dataset_name]['version'][version_name]['url']
    classification_method = data_info['hourly']['dataset'][dataset_name]['version'][version_name]['classification']
    if classification_method == 'year_different':
        base_url = url_dict[str(year_str)]
    elif classification_method == 'same_path':
        base_url = url_dict
    elif classification_method == 'var_different':
        if var in ['u', 'v', 'u_b', 'v_b']:
            base_url = url_dict['uv3z']
        elif var in ['temp', 'salinity', 'temp_b', 'salinity_b']:
            base_url = url_dict['ts3z']
        elif var in ['ssh']:
            base_url = url_dict['ssh']
        else:
            print(
                'Please ensure the var is in [u,v,temp,salinity,ssh,u_b,v_b,temp_b,salinity_b]')
    elif classification_method == 'var_year_different':
        if var in ['u', 'v', 'u_b', 'v_b']:
            base_url = url_dict['uv3z'][str(year_str)]
        elif var in ['temp', 'salinity', 'temp_b', 'salinity_b']:
            base_url = url_dict['ts3z'][str(year_str)]
        elif var in ['ssh']:
            base_url = url_dict['ssh'][str(year_str)]
        else:
            print(
                'Please ensure the var is in [u,v,temp,salinity,ssh,u_b,v_b,temp_b,salinity_b]')
    return base_url


def get_submit_url(dataset_name, version_name, var, year_str, query_dict):
    base_url = get_base_url(dataset_name, version_name, var, year_str)
    query_dict['var'] = [query_dict['var']]
    target_url = base_url + '&'.join(f"var={var}" for var in query_dict['var']) + '&' + '&'.join(
        f"{key}={value}" for key, value in query_dict.items() if key != 'var')
    return target_url


def clear_existing_file(file_full_path):
    if os.path.exists(file_full_path):
        os.remove(file_full_path)
        print(f'{file_full_path} has been removed')


def check_existing_file(file_full_path):
    if os.path.exists(file_full_path):
        print(f'{file_full_path} exists')
        return True
    else:
        print(f'{file_full_path} does not exist')
        return False


def get_ua():
    ua_list = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60",
        "Opera/8.0 (Windows NT 5.1; U; en)",
        "Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
        "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11",
        "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
        "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
        "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv,2.0.1) Gecko/20100101 Firefox/4.0.1",
        "Mozilla/5.0 (Windows NT 6.1; rv,2.0.1) Gecko/20100101 Firefox/4.0.1",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
        "MAC：Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36",
        "Windows：Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
        "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
        "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
        "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)"
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 UBrowser/4.0.3214.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.4094.1 Safari/537.36",
        "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
        "Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
        "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
        "Mozilla/5.0 (iPad; U; CPU OS 4_3_3 like Mac OS X; en-us) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8J2 Safari/6533.18.5",
        "Mozilla/5.0 (Linux; U; Android 2.2.1; zh-cn; HTC_Wildfire_A3333 Build/FRG83D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
        "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
        "MQQBrowser/26 Mozilla/5.0 (Linux; U; Android 2.3.7; zh-cn; MB200 Build/GRJ22; CyanogenMod-7) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
        "Opera/9.80 (Android 2.3.4; Linux; Opera Mobi/build-1107180945; U; en-GB) Presto/2.8.149 Version/11.10",
        "Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13",
        "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.337 Mobile Safari/534.1+",
        "Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.0; U; en-US) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/233.70 Safari/534.6 TouchPad/1.0",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0)",
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)",
        "Mozilla/5.0 (Linux; U; Android 2.3.7; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
        "Mozilla/5.0 (SymbianOS/9.4; Series60/5.0 NokiaN97-1/20.0.019; Profile/MIDP-2.1 Configuration/CLDC-1.1) AppleWebKit/525 (KHTML, like Gecko) BrowserNG/7.1.18124",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0; HTC; Titan)",
        "UCWEB7.0.2.37/28/999",
        "NOKIA5700/UCWEB7.0.2.37/28/999",
        "Openwave/UCWEB7.0.2.37/28/999",
        "Openwave/UCWEB7.0.2.37/28/999",
    ]
    ua_index = random.randint(0, len(ua_list)-1)
    ua = ua_list[ua_index]
    # print(f'Using User-Agent: {ua}')
    return ua


def get_proxy():
    # 获取当前脚本的绝对路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建ip.txt的绝对路径
    ip_file_txt = os.path.join(script_dir, 'ip.txt')
    with open(ip_file_txt, 'r') as f:
        ips = f.readlines()
    ip_list = []
    for ip in ips:
        ip_list.append(ip.strip())
    choose_ip = random.choice(ip_list)
    proxies = {
        'http': 'http://' + choose_ip,
        'https': 'https://' + choose_ip
    }
    # print(f'Using proxy: {proxies}')
    return proxies


def dlownload_file(target_url, store_path, file_name, check=False):
    print(f'[bold red]Downloading {file_name}...')
    # 创建会话
    s = requests.Session()
    download_success = False
    request_times = 0
    filename = Path(store_path) / file_name
    if check:
        if check_existing_file(filename):
            return
    clear_existing_file(filename)
    print(f'Download_start_time: {datetime.datetime.now()}')
    while not download_success:
        if request_times > 0:
            print(f'\r正在重试第 {request_times} 次', end="")
        # 尝试下载文件
        try:
            headers = {
                'User-Agent': get_ua()}
            # response = s.get(target_url, headers=headers, stream=True)
            # response = s.get(target_url, headers=headers,
            #                  proxies=get_proxy(), timeout=5)
            response = s.get(target_url, headers=headers,
                             timeout=5)
            # response = s.get(target_url, headers=headers)
            # print(target_url)
            response.raise_for_status()  # 如果请求返回的不是200，将抛出HTTPError异常

            # 保存文件
            with open(filename, 'wb') as f:
                f.write(response.content)
            # print(f'\r文件 {filename} 下载成功', end="")
            print(f'[bold green]文件 {filename} 下载成功')
            # query_ncfile_time(filename) # 这个函数在linux上目前会出问题
            download_success = True

        except requests.exceptions.HTTPError as errh:
            print(f"Http Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            print(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            print(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            print(f"OOps: Something Else: {err}")

        time.sleep(3)
        request_times += 1
    print(f'Download_end_time: {datetime.datetime.now()}')


def check_hour_is_valid(ymdh_str):
    # hour should be 00, 03, 06, 09, 12, 15, 18, 21
    hh = int(str(ymdh_str[-2:]))
    if hh in [0, 3, 6, 9, 12, 15, 18, 21]:
        return True
    else:
        return False


def direct_download(var, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90, download_time='2024083100', depth=None, level_num=None, store_path=None, dataset_name=None, version_name=None, check=False):
    download_time = str(download_time)
    if not check_hour_is_valid(download_time):
        print('Please ensure the hour is 00, 03, 06, 09, 12, 15, 18, 21')
        raise ValueError('The hour is invalid')
    if dataset_name is None and version_name is None:
        print('The dataset_name and version_name are None, so the dataset and version will be chosen according to the download_time.\nIf there is more than one dataset and version in the time range, the first one will be chosen.')
        print('If you wanna choose the dataset and version by yourself, please set the dataset_name and version_name together.')
        ymd_in_which_dataset_and_version(download_time)
        dataset_name, version_name = direct_choose_dataset_and_version(
            download_time)
    elif dataset_name is None and version_name is not None:
        print('Please ensure the dataset_name is not None')
        print('If you do not add the dataset_name, both the dataset and version will be chosen according to the download_time.')
        ymd_in_which_dataset_and_version(download_time)
        dataset_name, version_name = direct_choose_dataset_and_version(
            download_time)
    elif dataset_name is not None and version_name is None:
        print('Please ensure the version_name is not None')
        print('If you do not add the version_name, both the dataset and version will be chosen according to the download_time.')
        ymd_in_which_dataset_and_version(download_time)
        dataset_name, version_name = direct_choose_dataset_and_version(
            download_time)
    else:
        print('The dataset_name and version_name are both set by yourself.')

    year_str = str(download_time)[:4]
    if depth is not None and level_num is not None:
        print('Please ensure the depth or level_num is None')
    elif depth is not None:
        print(f'Data of single depth ({depth}m) will be downloaded...')
        query_dict = get_query_dict_single_depth(
            var, lon_min, lon_max, lat_min, lat_max, depth, download_time)
    elif level_num is not None:
        print(f'Data of single level ({level_num}) will be downloaded...')
        query_dict = get_query_dict_single_level(
            var, lon_min, lon_max, lat_min, lat_max, level_num, download_time)
    else:
        print('Full depth or full level data will be downloaded...')
        query_dict = get_query_dict_full_level(
            var, lon_min, lon_max, lat_min, lat_max, download_time)
    submit_url = get_submit_url(
        dataset_name, version_name, var, year_str, query_dict)
    file_name = f"HYCOM_{variable_info[var]['var_name']}_{download_time}.nc"
    if store_path is None:
        store_path = str(Path.cwd())
    else:
        os.makedirs(str(store_path), exist_ok=True)
    dlownload_file(submit_url, store_path, file_name, check)


def convert_full_name_to_short_name(full_name):
    for var, info in variable_info.items():
        if full_name == info['var_name'] or full_name == info['standard_name'] or full_name == var:
            return var
    print('[bold #FFE4E1]Please ensure the var is in:\n[bold blue]u,v,temp,salinity,ssh,u_b,v_b,temp_b,salinity_b')
    print('or')
    print('[bold blue]water_u, water_v, water_temp, salinity, surf_el, water_u_bottom, water_v_bottom, water_temp_bottom, salinity_bottom')
    return False


def download_task(var, time_str, lon_min, lon_max, lat_min, lat_max, depth, level, store_path, dataset_name, version_name, check):
    '''
    # 并行下载任务
    # 这个函数是为了并行下载而设置的，是必须的，直接调用direct_download并行下载会出问题

    任务封装：将每个任务需要的数据和操作封装在一个函数中，这样每个任务都是独立的，不会相互干扰。
    本情况下，download_task函数的作用是将每个下载任务封装起来，包括它所需的所有参数。
    这样，每个任务都是独立的，有自己的参数和数据，不会与其他任务共享或修改任何数据。
    因此，即使多个任务同时执行，也不会出现数据交互错乱的问题。
    '''
    direct_download(var, lon_min, lon_max, lat_min, lat_max, time_str,
                    depth, level, store_path, dataset_name, version_name, check)


def download(var, time_s, time_e, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90,  depth=None, level=None, store_path=None, dataset_name=None, version_name=None, num_workers=None, check=False):
    '''
    Description:
    Download the data of single time or a series of time

    Parameters:
    var: str, the variable name, such as 'u', 'v', 'temp', 'salinity', 'ssh', 'u_b', 'v_b', 'temp_b', 'salinity_b' or 'water_u', 'water_v', 'water_temp', 'salinity', 'surf_el', 'water_u_bottom', 'water_v_bottom', 'water_temp_bottom', 'salinity_bottom'
    time_s: str, the start time, such as '2024110100' or '20241101', if add hour, the hour should be 00, 03, 06, 09, 12, 15, 18, 21
    time_e: str, the end time, such as '2024110221' or '20241102', if add hour, the hour should be 00, 03, 06, 09, 12, 15, 18, 21
    lon_min: float, the minimum longitude, default is 0
    lon_max: float, the maximum longitude, default is 359.92
    lat_min: float, the minimum latitude, default is -80
    lat_max: float, the maximum latitude, default is 90
    depth: float, the depth, default is None
    level: int, the level number, default is None
    store_path: str, the path to store the data, default is None
    dataset_name: str, the dataset name, default is None, example: 'GLBv0.08', 'GLBu0.08', 'GLBy0.08'
    version_name: str, the version name, default is None, example: '53.X', '56.3'
    num_workers: int, the number of workers, default is None

    Returns:
    None
    '''
    var = convert_full_name_to_short_name(var)
    if var is False:
        raise ValueError('The var is invalid')
    if lon_min < 0 or lon_min > 359.92 or lon_max < 0 or lon_max > 359.92 or lat_min < -80 or lat_min > 90 or lat_max < -80 or lat_max > 90:
        print('Please ensure the lon_min, lon_max, lat_min, lat_max are in the range')
        print('The range of lon_min, lon_max is 0~359.92')
        print('The range of lat_min, lat_max is -80~90')
        raise ValueError('The lon or lat is invalid')
    ymdh_time_s = str(time_s)
    if len(ymdh_time_s) == 8:
        ymdh_time_s += '00'
    ymdh_time_e = str(time_e)
    if len(ymdh_time_e) == 8:
        ymdh_time_e += '21'
    if ymdh_time_s == ymdh_time_e:
        direct_download(var, lon_min, lon_max, lat_min, lat_max,
                        ymdh_time_s, depth, level, store_path, dataset_name, version_name)
    elif int(ymdh_time_s) < int(ymdh_time_e):
        print('Downloading a series of files...')
        time_list = get_time_list(ymdh_time_s, ymdh_time_e, 3)
        with Progress() as progress:
            task = progress.add_task(
                "[cyan]Downloading...", total=len(time_list))
            if num_workers is None or num_workers <= 1:
                # 串行方式
                for time_str in time_list:
                    direct_download(var, lon_min, lon_max, lat_min, lat_max,
                                    time_str, depth, level, store_path, dataset_name, version_name, check)
                    progress.update(task, advance=1)
            else:
                # 并行方式
                if num_workers > 10:
                    print('The number of workers is too large!')
                    print(
                        'In order to avoid the server being blocked, the number of workers is set to 10')
                    num_workers = 10
                with ThreadPoolExecutor(max_workers=num_workers) as executor:
                    futures = [executor.submit(download_task, var, time_str, lon_min, lon_max, lat_min, lat_max,
                                               depth, level, store_path, dataset_name, version_name, check) for time_str in time_list]
                    for future in futures:
                        future.add_done_callback(
                            lambda _: progress.update(task, advance=1))
    else:
        print('Please ensure the ymdh_time_s is less than the ymdh_time_e')


def how_to_use():
    print('''
    # 1. Choose the dataset and version according to the time:
    # 1.1 Use function to query
    You can use the function ymd_in_which_dataset_and_version(time_ymd=20241101) to find the dataset and version  according to the time.
    Then, you can see the dataset and version in the output.
    # 1.2 Draw a picture to see
    You can draw a picture to see the time range of each dataset and version.
    Using the function draw_time_range(pic_save_folder=None) to draw the picture.

    # 2. Get the base url according to the dataset, version, var and year:
    # 2.1 Dataset and version were found in step 1
    # 2.2 Var: u, v, temp, salinity, ssh, u_b, v_b, temp_b, salinity_b
    # 2.3 Year: 1994-2024(current year)

    # 3. Get the query_dict according to the var, lon_min, lon_max, lat_min, lat_max, depth, level_num, time_str_ymdh:
    # 3.1 Var: u, v, temp, salinity, ssh, u_b, v_b, temp_b, salinity_b
    # 3.2 Lon_min, lon_max, lat_min, lat_max: float
    # 3.3 Depth: 0-5000m, if you wanna get single depth data, you can set the depth
    # 3.4 Level_num: 1-40, if you wanna get single level data, you can set the level_num
    # 3.5 Time_str_ymdh: '2024110112', the hour normally is 00, 03, 06, 09, 12, 15, 18, 21, besides 1 hourly data
    # 3.6 Use the function to get the query_dict
    # 3.7 Note: If you wanna get the full depth or full level data, you can needn't set the depth or level_num

    # 4. Get the submit url according to the dataset, version, var, year, query_dict:
    # 4.1 Use the function to get the submit url
    # 4.2 You can use the submit url to download the data

    # 5. Download the data according to the submit url:
    # 5.1 Use the function to download the data
    # 5.2 You can download the data of single time or a series of time
    # 5.3 Note: If you wanna download a series of data, you can set the ymdh_time_s and ymdh_time_e different
    # 5.4 Note: The time resolution is 3 hours

    # 6. Direct download the data:
    # 6.1 Use the function to direct download the data
    # 6.2 You can set the dataset_name and version_name by yourself
    # 6.3 Note: If you do not set the dataset_name and version_name, the dataset and version will be chosen according to the download_time
    # 6.4 Note: If you set the dataset_name and version_name, please ensure the dataset_name and version_name are correct
    # 6.5 Note: If you just set one of the dataset_name and version_name, both the dataset and version will be chosen according to the download_time

    # 7. Simple use:
    # 7.1 You can use the function: download(var, ymdh_time_s, ymdh_time_e, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90,  depth=None, level_num=None, store_path=None, dataset_name=None, version_name=None)
    # 7.2 You can download the data of single time or a series of time
    # 7.3 The parameters you must set are var, ymdh_time_s, ymdh_time_e
    # 7.4 Example: download('u', '2024110112', '2024110212', lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90,  depth=None, level_num=None, store_path=None, dataset_name=None, version_name=None)
    ''')


if __name__ == '__main__':
    time_s, time_e = '2018010112', '2018010300'
    merge_name = '201801'
    root_path = r'I:\hycom_data_2018'
    location_dict = {'west': 115, 'east': 130, 'south': 33, 'north': 45}
    download_dict = {
        'water_u': {'simple_name': 'u', 'download': 1},
        'water_v': {'simple_name': 'v', 'download': 0},
        'surf_el': {'simple_name': 'ssh', 'download': 0},
        'water_temp': {'simple_name': 'temp', 'download': 0},
        'salinity': {'simple_name': 'salinity', 'download': 1},
    }

    # set depth or level, only one can be True
    # if you wanna download all depth or level, set both False
    set_depth, depth = False, 0  # 0-4000 meters
    set_level, level = False, 1  # 1-40 levels
    num_workers = 5
    check = True

    download_switch = True
    combine_switch = False

    def download_var(var_name):
        var = download_dict[var_name]['simple_name']
        if_download = download_dict[var_name]['download']
        if if_download == 0:
            return
        if set_depth:
            download(var=var, time_s=time_s, time_e=time_e, store_path=Path(root_path)/var, lon_min=location_dict[
                'west'], lon_max=location_dict['east'], lat_min=location_dict['south'], lat_max=location_dict['north'], depth=depth, num_workers=num_workers, check=check)
        elif set_level:
            download(var=var, time_s=time_s, time_e=time_e, store_path=Path(root_path)/var, lon_min=location_dict[
                'west'], lon_max=location_dict['east'], lat_min=location_dict['south'], lat_max=location_dict['north'], level=level, num_workers=num_workers, check=check)
        else:
            download(var=var, time_s=time_s, time_e=time_e, store_path=Path(root_path)/var, lon_min=location_dict[
                'west'], lon_max=location_dict['east'], lat_min=location_dict['south'], lat_max=location_dict['north'], num_workers=num_workers, check=check)

    if download_switch:
        for var_name in download_dict.keys():
            download_var(var_name)

    # draw_time_range(r'I:\Delete')

    """ if combine_switch:
        time_list = get_time_list(time_s, time_e, 3)
        for var_name in download_dict.keys():
            var = download_dict[var_name]['simple_name']
            if_download = download_dict[var_name]['download']
            if if_download == 0:
                continue
            file_list = []
            for time_str in time_list:
                file_list.append(
                    Path(root_path)/var/f'HYCOM_{var_name}_{time_str}.nc')
            merge5nc(file_list, var_name, 'time',
                     Path(root_path)/var/f'HYCOM_{var_name}_{merge_name}.nc') """
