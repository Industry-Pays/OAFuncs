#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-01-29 19:05:09
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-01-29 19:05:10
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_down\\hycom_3hourly_20250129 copy.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import datetime
import os
import random
import re
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd
import requests
import xarray as xr
from rich import print
from rich.progress import Progress

from oafuncs.oa_down.idm import downloader as idm_downloader
from oafuncs.oa_down.user_agent import get_ua
from oafuncs.oa_file import file_size, mean_size
from oafuncs.oa_nc import check as check_nc
from oafuncs.oa_nc import modify as modify_nc

warnings.filterwarnings("ignore", category=RuntimeWarning, message="Engine '.*' loading failed:.*")

__all__ = ["draw_time_range", "download", "how_to_use", "get_time_list"]


def _get_initial_data():
    global variable_info, data_info, var_group, single_var_group
    # ----------------------------------------------
    # variable
    variable_info = {
        "u": {"var_name": "water_u", "standard_name": "eastward_sea_water_velocity"},
        "v": {"var_name": "water_v", "standard_name": "northward_sea_water_velocity"},
        "temp": {"var_name": "water_temp", "standard_name": "sea_water_potential_temperature"},
        "salt": {"var_name": "salinity", "standard_name": "sea_water_salinity"},
        "ssh": {"var_name": "surf_el", "standard_name": "sea_surface_elevation"},
        "u_b": {"var_name": "water_u_bottom", "standard_name": "eastward_sea_water_velocity_at_sea_floor"},
        "v_b": {"var_name": "water_v_bottom", "standard_name": "northward_sea_water_velocity_at_sea_floor"},
        "temp_b": {"var_name": "water_temp_bottom", "standard_name": "sea_water_potential_temperature_at_sea_floor"},
        "salt_b": {"var_name": "salinity_bottom", "standard_name": "sea_water_salinity_at_sea_floor"},
    }
    # ----------------------------------------------
    # time resolution
    data_info = {"yearly": {}, "monthly": {}, "daily": {}, "hourly": {}}

    # hourly data
    # dataset: GLBv0.08, GLBu0.08, GLBy0.08
    data_info["hourly"]["dataset"] = {"GLBv0.08": {}, "GLBu0.08": {}, "GLBy0.08": {}, "ESPC_D": {}}

    # version
    # version of GLBv0.08: 53.X, 56.3, 57.2, 92.8, 57.7, 92.9, 93.0
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"] = {"53.X": {}, "56.3": {}, "57.2": {}, "92.8": {}, "57.7": {}, "92.9": {}, "93.0": {}}
    # version of GLBu0.08: 93.0
    data_info["hourly"]["dataset"]["GLBu0.08"]["version"] = {"93.0": {}}
    # version of GLBy0.08: 93.0
    data_info["hourly"]["dataset"]["GLBy0.08"]["version"] = {"93.0": {}}
    # version of ESPC_D: V02
    data_info["hourly"]["dataset"]["ESPC_D"]["version"] = {"V02": {}}

    # info details
    # time range
    # GLBv0.08
    # 在网页上提交超过范围的时间，会返回该数据集实际时间范围，从而纠正下面的时间范围
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["53.X"]["time_range"] = {"time_start": "1994010112", "time_end": "2015123109"}
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["56.3"]["time_range"] = {"time_start": "2014070112", "time_end": "2016093009"}
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["57.2"]["time_range"] = {"time_start": "2016050112", "time_end": "2017020109"}
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["92.8"]["time_range"] = {"time_start": "2017020112", "time_end": "2017060109"}
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["57.7"]["time_range"] = {"time_start": "2017060112", "time_end": "2017100109"}
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["92.9"]["time_range"] = {"time_start": "2017100112", "time_end": "2018032009"}
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["93.0"]["time_range"] = {"time_start": "2018010112", "time_end": "2020021909"}
    # GLBu0.08
    data_info["hourly"]["dataset"]["GLBu0.08"]["version"]["93.0"]["time_range"] = {"time_start": "2018091912", "time_end": "2018120909"}
    # GLBy0.08
    data_info["hourly"]["dataset"]["GLBy0.08"]["version"]["93.0"]["time_range"] = {"time_start": "2018120412", "time_end": "2024090509"}
    # ESPC-D
    data_info["hourly"]["dataset"]["ESPC_D"]["version"]["V02"]["time_range"] = {"time_start": "2024081012", "time_end": "2030010100"}

    # classification method
    # year_different: the data of different years is stored in different files
    # same_path: the data of different years is stored in the same file
    # var_different: the data of different variables is stored in different files
    # var_year_different: the data of different variables and years is stored in different files
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["53.X"]["classification"] = "year_different"
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["56.3"]["classification"] = "same_path"
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["57.2"]["classification"] = "same_path"
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["92.8"]["classification"] = "var_different"
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["57.7"]["classification"] = "same_path"
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["92.9"]["classification"] = "var_different"
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["93.0"]["classification"] = "var_different"
    data_info["hourly"]["dataset"]["GLBu0.08"]["version"]["93.0"]["classification"] = "var_different"
    data_info["hourly"]["dataset"]["GLBy0.08"]["version"]["93.0"]["classification"] = "var_year_different"
    data_info["hourly"]["dataset"]["ESPC_D"]["version"]["V02"]["classification"] = "single_var_year_different"

    # download info
    # base url
    # GLBv0.08 53.X
    url_53x = {}
    for y_53x in range(1994, 2016):
        # r'https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_53.X/data/2013?'
        url_53x[str(y_53x)] = rf"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_53.X/data/{y_53x}?"
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["53.X"]["url"] = url_53x
    # GLBv0.08 56.3
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["56.3"]["url"] = r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_56.3?"
    # GLBv0.08 57.2
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["57.2"]["url"] = r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_57.2?"
    # GLBv0.08 92.8
    url_928 = {
        "uv3z": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.8/uv3z?",
        "ts3z": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.8/ts3z?",
        "ssh": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.8/ssh?",
    }
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["92.8"]["url"] = url_928
    # GLBv0.08 57.7
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["57.7"]["url"] = r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_57.7?"
    # GLBv0.08 92.9
    url_929 = {
        "uv3z": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.9/uv3z?",
        "ts3z": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.9/ts3z?",
        "ssh": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_92.9/ssh?",
    }
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["92.9"]["url"] = url_929
    # GLBv0.08 93.0
    url_930_v = {
        "uv3z": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_93.0/uv3z?",
        "ts3z": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_93.0/ts3z?",
        "ssh": r"https://ncss.hycom.org/thredds/ncss/GLBv0.08/expt_93.0/ssh?",
    }
    data_info["hourly"]["dataset"]["GLBv0.08"]["version"]["93.0"]["url"] = url_930_v
    # GLBu0.08 93.0
    url_930_u = {
        "uv3z": r"https://ncss.hycom.org/thredds/ncss/GLBu0.08/expt_93.0/uv3z?",
        "ts3z": r"https://ncss.hycom.org/thredds/ncss/GLBu0.08/expt_93.0/ts3z?",
        "ssh": r"https://ncss.hycom.org/thredds/ncss/GLBu0.08/expt_93.0/ssh?",
    }
    data_info["hourly"]["dataset"]["GLBu0.08"]["version"]["93.0"]["url"] = url_930_u
    # GLBy0.08 93.0
    uv3z_930_y = {}
    ts3z_930_y = {}
    ssh_930_y = {}
    for y_930_y in range(2018, 2025):
        uv3z_930_y[str(y_930_y)] = rf"https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/uv3z/{y_930_y}?"
        ts3z_930_y[str(y_930_y)] = rf"https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/ts3z/{y_930_y}?"
        ssh_930_y[str(y_930_y)] = rf"https://ncss.hycom.org/thredds/ncss/GLBy0.08/expt_93.0/ssh/{y_930_y}?"
    # GLBy0.08 93.0 data time range in each year: year-01-01 12:00 to year+1-01-01 09:00
    url_930_y = {
        "uv3z": uv3z_930_y,
        "ts3z": ts3z_930_y,
        "ssh": ssh_930_y,
    }
    data_info["hourly"]["dataset"]["GLBy0.08"]["version"]["93.0"]["url"] = url_930_y
    # ESPC-D-V02
    u3z_espc_d_v02_y = {}
    v3z_espc_d_v02_y = {}
    t3z_espc_d_v02_y = {}
    s3z_espc_d_v02_y = {}
    ssh_espc_d_v02_y = {}
    for y_espc_d_v02 in range(2024, 2030):
        u3z_espc_d_v02_y[str(y_espc_d_v02)] = rf"https://ncss.hycom.org/thredds/ncss/ESPC-D-V02/u3z/{y_espc_d_v02}?"
        v3z_espc_d_v02_y[str(y_espc_d_v02)] = rf"https://ncss.hycom.org/thredds/ncss/ESPC-D-V02/v3z/{y_espc_d_v02}?"
        t3z_espc_d_v02_y[str(y_espc_d_v02)] = rf"https://ncss.hycom.org/thredds/ncss/ESPC-D-V02/t3z/{y_espc_d_v02}?"
        s3z_espc_d_v02_y[str(y_espc_d_v02)] = rf"https://ncss.hycom.org/thredds/ncss/ESPC-D-V02/s3z/{y_espc_d_v02}?"
        ssh_espc_d_v02_y[str(y_espc_d_v02)] = rf"https://ncss.hycom.org/thredds/ncss/ESPC-D-V02/ssh/{y_espc_d_v02}?"
    url_espc_d_v02_y = {
        "u3z": u3z_espc_d_v02_y,
        "v3z": v3z_espc_d_v02_y,
        "t3z": t3z_espc_d_v02_y,
        "s3z": s3z_espc_d_v02_y,
        "ssh": ssh_espc_d_v02_y,
    }
    data_info["hourly"]["dataset"]["ESPC_D"]["version"]["V02"]["url"] = url_espc_d_v02_y
    # ----------------------------------------------
    var_group = {
        "uv3z": ["u", "v", "u_b", "v_b"],
        "ts3z": ["temp", "salt", "temp_b", "salt_b"],
        "ssh": ["ssh"],
    }
    # ----------------------------------------------
    single_var_group = {
        "u3z": ["u"],
        "v3z": ["v"],
        "t3z": ["temp"],
        "s3z": ["salt"],
        "ssh": ["ssh"],
    }

    return variable_info, data_info, var_group, single_var_group


def draw_time_range(pic_save_folder=None):
    if pic_save_folder is not None:
        os.makedirs(pic_save_folder, exist_ok=True)
    # Converting the data into a format suitable for plotting
    data = []
    for dataset, versions in data_info["hourly"]["dataset"].items():
        for version, time_range in versions["version"].items():
            t_s = time_range["time_range"]["time_start"]
            t_e = time_range["time_range"]["time_end"]
            if len(t_s) == 8:
                t_s = t_s + "00"
            if len(t_e) == 8:
                t_e = t_e + "21"
            t_s, t_e = t_s + "0000", t_e + "0000"
            data.append(
                {
                    "dataset": dataset,
                    "version": version,
                    "start_date": pd.to_datetime(t_s),
                    "end_date": pd.to_datetime(t_e),
                }
            )

    # Creating a DataFrame
    df = pd.DataFrame(data)

    # Plotting with combined labels for datasets and versions on the y-axis
    plt.figure(figsize=(12, 6))

    # Combined labels for datasets and versions
    combined_labels = [f"{dataset}_{version}" for dataset, version in zip(df["dataset"], df["version"])]

    colors = plt.cm.viridis(np.linspace(0, 1, len(combined_labels)))

    # Assigning a color to each combined label
    label_colors = {label: colors[i] for i, label in enumerate(combined_labels)}

    # Plotting each time range
    k = 1
    for _, row in df.iterrows():
        plt.plot([row["start_date"], row["end_date"]], [k, k], color=label_colors[f"{row['dataset']}_{row['version']}"], linewidth=6)
        # plt.text(row['end_date'], k,
        #          f"{row['version']}", ha='right', color='black')
        ymdh_s = row["start_date"].strftime("%Y-%m-%d %H")
        ymdh_e = row["end_date"].strftime("%Y-%m-%d %H")
        # if k == 1 or k == len(combined_labels):
        if k == 1:
            plt.text(row["start_date"], k + 0.125, f"{ymdh_s}", ha="left", color="black")
            plt.text(row["end_date"], k + 0.125, f"{ymdh_e}", ha="right", color="black")
        else:
            plt.text(row["start_date"], k + 0.125, f"{ymdh_s}", ha="right", color="black")
            plt.text(row["end_date"], k + 0.125, f"{ymdh_e}", ha="left", color="black")
        k += 1

    # Setting the y-axis labels
    plt.yticks(range(1, len(combined_labels) + 1), combined_labels)
    plt.xlabel("Time")
    plt.ylabel("Dataset - Version")
    plt.title("Time Range of Different Versions of Datasets")
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    if pic_save_folder:
        plt.savefig(Path(pic_save_folder) / "HYCOM_time_range.png")
        print(f"[bold green]HYCOM_time_range.png has been saved in {pic_save_folder}")
    else:
        plt.savefig("HYCOM_time_range.png")
        print("[bold green]HYCOM_time_range.png has been saved in the current folder")
        print(f"Curren folder: {os.getcwd()}")
    # plt.show()
    plt.close()


def get_time_list(time_s, time_e, delta, interval_type="hour"):
    """
    Description: get a list of time strings from time_s to time_e with a specified interval
    Args:
        time_s: start time string, e.g. '2023080203' for hours or '20230802' for days
        time_e: end time string, e.g. '2023080303' for hours or '20230803' for days
        delta: interval of hours or days
        interval_type: 'hour' for hour interval, 'day' for day interval
    Returns:
        dt_list: a list of time strings
    """
    time_s, time_e = str(time_s), str(time_e)
    if interval_type == "hour":
        time_format = "%Y%m%d%H"
        delta_type = "hours"
    elif interval_type == "day":
        time_format = "%Y%m%d"
        delta_type = "days"
        # Ensure time strings are in the correct format for days
        time_s = time_s[:8]
        time_e = time_e[:8]
    else:
        raise ValueError("interval_type must be 'hour' or 'day'")

    dt = datetime.datetime.strptime(time_s, time_format)
    dt_list = []
    while dt.strftime(time_format) <= time_e:
        dt_list.append(dt.strftime(time_format))
        dt += datetime.timedelta(**{delta_type: delta})
    return dt_list


def _transform_time(time_str):
    # old_time = '2023080203'
    # time_new = '2023-08-02T03%3A00%3A00Z'
    time_new = f"{time_str[:4]}-{time_str[4:6]}-{time_str[6:8]}T{time_str[8:10]}%3A00%3A00Z"
    return time_new


def _get_query_dict(var, lon_min, lon_max, lat_min, lat_max, time_str_ymdh, time_str_end=None, mode="single_depth", depth=None, level_num=None):
    query_dict = {
        "var": variable_info[var]["var_name"],
        "north": lat_max,
        "west": lon_min,
        "east": lon_max,
        "south": lat_min,
        "horizStride": 1,
        "time": None,
        "time_start": None,
        "time_end": None,
        "timeStride": None,
        "vertCoord": None,
        "vertStride": None,
        "addLatLon": "true",
        "accept": "netcdf4",
    }

    if time_str_end is not None:
        query_dict["time_start"] = _transform_time(time_str_ymdh)
        query_dict["time_end"] = _transform_time(time_str_end)
        query_dict["timeStride"] = 1
    else:
        query_dict["time"] = _transform_time(time_str_ymdh)

    def get_nearest_level_index(depth):
        level_depth = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 125.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0, 1250.0, 1500.0, 2000.0, 2500.0, 3000.0, 4000.0, 5000]
        return min(range(len(level_depth)), key=lambda i: abs(level_depth[i] - depth))

    if var not in ["ssh", "u_b", "v_b", "temp_b", "salt_b"] and var in ["u", "v", "temp", "salt"]:
        if mode == "depth":
            if depth < 0 or depth > 5000:
                print("Please ensure the depth is in the range of 0-5000 m")
            query_dict["vertCoord"] = get_nearest_level_index(depth) + 1
        elif mode == "level":
            if level_num < 1 or level_num > 40:
                print("Please ensure the level_num is in the range of 1-40")
            query_dict["vertCoord"] = max(1, min(level_num, 40))
        elif mode == "full":
            query_dict["vertStride"] = 1
        else:
            raise ValueError("Invalid mode. Choose from 'depth', 'level', or 'full'")

    query_dict = {k: v for k, v in query_dict.items() if v is not None}

    return query_dict


def _check_time_in_dataset_and_version(time_input, time_end=None):
    # 判断是处理单个时间点还是时间范围
    is_single_time = time_end is None

    # 如果是单个时间点，初始化时间范围
    if is_single_time:
        time_start = int(time_input)
        time_end = time_start
        time_input_str = str(time_input)
    else:
        time_start = int(time_input)
        time_end = int(time_end)
        time_input_str = f"{time_input}-{time_end}"

    # 根据时间长度补全时间格式
    if len(str(time_start)) == 8:
        time_start = str(time_start) + "00"
    if len(str(time_end)) == 8:
        time_end = str(time_end) + "21"
    time_start, time_end = int(time_start), int(time_end)

    d_list = []
    v_list = []
    trange_list = []
    have_data = False

    # 遍历数据集和版本
    for dataset_name in data_info["hourly"]["dataset"].keys():
        for version_name in data_info["hourly"]["dataset"][dataset_name]["version"].keys():
            time_s, time_e = list(data_info["hourly"]["dataset"][dataset_name]["version"][version_name]["time_range"].values())
            time_s, time_e = str(time_s), str(time_e)
            if len(time_s) == 8:
                time_s = time_s + "00"
            if len(time_e) == 8:
                time_e = time_e + "21"
            # 检查时间是否在数据集的时间范围内
            if is_single_time:
                if time_start >= int(time_s) and time_start <= int(time_e):
                    d_list.append(dataset_name)
                    v_list.append(version_name)
                    trange_list.append(f"{time_s}-{time_e}")
                    have_data = True
            else:
                if time_start >= int(time_s) and time_end <= int(time_e):
                    d_list.append(dataset_name)
                    v_list.append(version_name)
                    trange_list.append(f"{time_s}-{time_e}")
                    have_data = True

    # 输出结果
    print(f"[bold red]{time_input_str} is in the following dataset and version:")
    if have_data:
        for d, v, trange in zip(d_list, v_list, trange_list):
            print(f"[bold blue]{d} {v} {trange}")
        if is_single_time:
            return True
        else:
            base_url_s = _get_base_url(d_list[0], v_list[0], "u", str(time_start))
            base_url_e = _get_base_url(d_list[0], v_list[0], "u", str(time_end))
            if base_url_s == base_url_e:
                return True
            else:
                print(f"[bold red]{time_start} to {time_end} is in different datasets or versions, so you can't download them together")
                return False
    else:
        print(f"[bold red]{time_input_str} is not in any dataset and version")
        return False


def _ensure_time_in_specific_dataset_and_version(dataset_name, version_name, time_input, time_end=None):
    # 根据时间长度补全时间格式
    if len(str(time_input)) == 8:
        time_input = str(time_input) + "00"
    time_start = int(time_input)
    if time_end is not None:
        if len(str(time_end)) == 8:
            time_end = str(time_end) + "21"
        time_end = int(time_end)
    else:
        time_end = time_start

    # 检查指定的数据集和版本是否存在
    if dataset_name not in data_info["hourly"]["dataset"]:
        print(f"[bold red]Dataset {dataset_name} not found.")
        return False
    if version_name not in data_info["hourly"]["dataset"][dataset_name]["version"]:
        print(f"[bold red]Version {version_name} not found in dataset {dataset_name}.")
        return False

    # 获取指定数据集和版本的时间范围
    time_range = data_info["hourly"]["dataset"][dataset_name]["version"][version_name]["time_range"]
    time_s, time_e = list(time_range.values())
    time_s, time_e = str(time_s), str(time_e)
    if len(time_s) == 8:
        time_s = time_s + "00"
    if len(time_e) == 8:
        time_e = time_e + "21"
    time_s, time_e = int(time_s), int(time_e)

    # 检查时间是否在指定数据集和版本的时间范围内
    if time_start >= time_s and time_end <= time_e:
        print(f"[bold blue]Time {time_input} to {time_end} is within dataset {dataset_name} and version {version_name}.")
        return True
    else:
        print(f"[bold red]Time {time_input} to {time_end} is not within dataset {dataset_name} and version {version_name}.")
        return False


def _direct_choose_dataset_and_version(time_input, time_end=None):
    # 假设 data_info 是一个字典，包含了数据集和版本的信息
    # 示例结构：data_info['hourly']['dataset'][dataset_name]['version'][version_name]['time_range']

    if len(str(time_input)) == 8:
        time_input = str(time_input) + "00"

    # 如果 time_end 是 None，则将 time_input 的值赋给它
    if time_end is None:
        time_end = time_input

    # 处理开始和结束时间，确保它们是完整的 ymdh 格式
    time_start, time_end = int(str(time_input)[:10]), int(str(time_end)[:10])

    dataset_name_out, version_name_out = None, None

    for dataset_name in data_info["hourly"]["dataset"].keys():
        for version_name in data_info["hourly"]["dataset"][dataset_name]["version"].keys():
            [time_s, time_e] = list(data_info["hourly"]["dataset"][dataset_name]["version"][version_name]["time_range"].values())
            time_s, time_e = str(time_s), str(time_e)
            if len(time_s) == 8:
                time_s = time_s + "00"
            if len(time_e) == 8:
                time_e = time_e + "21"
            time_s, time_e = int(time_s), int(time_e)

            # 检查时间是否在数据集版本的时间范围内
            if time_start >= time_s and time_end <= time_e:
                # print(f'[bold purple]dataset: {dataset_name}, version: {version_name} is chosen')
                # return dataset_name, version_name
                dataset_name_out, version_name_out = dataset_name, version_name

    if dataset_name_out is not None and version_name_out is not None:
        print(f"[bold purple]dataset: {dataset_name_out}, version: {version_name_out} is chosen")

    # 如果没有找到匹配的数据集和版本，会返回 None
    return dataset_name_out, version_name_out


def _get_base_url(dataset_name, version_name, var, ymdh_str):
    year_str = int(ymdh_str[:4])
    url_dict = data_info["hourly"]["dataset"][dataset_name]["version"][version_name]["url"]
    classification_method = data_info["hourly"]["dataset"][dataset_name]["version"][version_name]["classification"]
    if classification_method == "year_different":
        base_url = url_dict[str(year_str)]
    elif classification_method == "same_path":
        base_url = url_dict
    elif classification_method == "var_different":
        base_url = None
        for key, value in var_group.items():
            if var in value:
                base_url = url_dict[key]
                break
        if base_url is None:
            print("Please ensure the var is in [u,v,temp,salt,ssh,u_b,v_b,temp_b,salt_b]")
    elif classification_method == "var_year_different":
        if dataset_name == "GLBy0.08" and version_name == "93.0":
            mdh_str = ymdh_str[4:]
            # GLBy0.08 93.0
            # data time range in each year: year-01-01 12:00 to year+1-01-01 09:00
            if "010100" <= mdh_str <= "010109":
                year_str = int(ymdh_str[:4]) - 1
            else:
                year_str = int(ymdh_str[:4])
        base_url = None
        for key, value in var_group.items():
            if var in value:
                base_url = url_dict[key][str(year_str)]
                break
        if base_url is None:
            print("Please ensure the var is in [u,v,temp,salt,ssh,u_b,v_b,temp_b,salt_b]")
    elif classification_method == "single_var_year_different":
        base_url = None
        if dataset_name == "ESPC_D" and version_name == "V02":
            mdh_str = ymdh_str[4:]
            # ESPC-D-V02
            if "010100" <= mdh_str <= "010109":
                year_str = int(ymdh_str[:4]) - 1
            else:
                year_str = int(ymdh_str[:4])
        for key, value in single_var_group.items():
            if var in value:
                base_url = url_dict[key][str(year_str)]
                break
        if base_url is None:
            print("Please ensure the var is in [u,v,temp,salt,ssh]")
    return base_url


def _get_submit_url(dataset_name, version_name, var, ymdh_str, query_dict):
    base_url = _get_base_url(dataset_name, version_name, var, ymdh_str)
    if isinstance(query_dict["var"], str):
        query_dict["var"] = [query_dict["var"]]
    target_url = base_url + "&".join(f"var={var}" for var in query_dict["var"]) + "&" + "&".join(f"{key}={value}" for key, value in query_dict.items() if key != "var")
    return target_url


def _clear_existing_file(file_full_path):
    if os.path.exists(file_full_path):
        os.remove(file_full_path)
        print(f"{file_full_path} has been removed")


def _check_existing_file(file_full_path, avg_size):
    if os.path.exists(file_full_path):
        print(f"[bold #FFA54F]{file_full_path} exists")
        fsize = file_size(file_full_path)
        delta_size_ratio = (fsize - avg_size) / avg_size
        if abs(delta_size_ratio) > 0.025:
            if check_nc(file_full_path):
                # print(f"File size is abnormal but can be opened normally, file size: {fsize:.2f} KB")
                return True
            else:
                print(f"File size is abnormal and cannot be opened, {file_full_path}: {fsize:.2f} KB")
                return False
        else:
            return True
    else:
        return False


def _get_mean_size30(store_path, same_file):
    if same_file not in fsize_dict.keys():
        # print(f'Same file name: {same_file}')
        fsize_dict[same_file] = {"size": 0, "count": 0}

    if fsize_dict[same_file]["count"] < 30 or fsize_dict[same_file]["size"] == 0:
        # 更新30次文件最小值，后续认为可以代表所有文件，不再更新占用时间
        fsize_mean = mean_size(store_path, same_file, max_num=30)
        set_min_size = fsize_mean * 0.95
        fsize_dict[same_file]["size"] = set_min_size
        fsize_dict[same_file]["count"] += 1
    else:
        set_min_size = fsize_dict[same_file]["size"]
    return set_min_size


def _get_mean_size_move(same_file, current_file):
    # 获取锁
    with fsize_dict_lock:  # 全局锁，确保同一时间只能有一个线程访问
        # 初始化字典中的值，如果文件不在字典中
        if same_file not in fsize_dict.keys():
            fsize_dict[same_file] = {"size_list": [], "mean_size": 1.0}

        tolerance_ratio = 0.025  # 容忍的阈值比例
        current_file_size = file_size(current_file)

        # 如果列表不为空，则计算平均值，否则保持为1
        if fsize_dict[same_file]["size_list"]:
            fsize_dict[same_file]["mean_size"] = sum(fsize_dict[same_file]["size_list"]) / len(fsize_dict[same_file]["size_list"])
            fsize_dict[same_file]["mean_size"] = max(fsize_dict[same_file]["mean_size"], 1.0)
        else:
            fsize_dict[same_file]["mean_size"] = 1.0

        size_difference_ratio = (current_file_size - fsize_dict[same_file]["mean_size"]) / fsize_dict[same_file]["mean_size"]

        if abs(size_difference_ratio) > tolerance_ratio:
            if check_nc(current_file):
                # print(f"File size is abnormal but can be opened normally, file size: {current_file_size:.2f} KB")
                # 文件可以正常打开，但大小异常，保留当前文件大小
                fsize_dict[same_file]["size_list"] = [current_file_size]
                fsize_dict[same_file]["mean_size"] = current_file_size
            else:
                _clear_existing_file(current_file)
                print(f"File size is abnormal, may need to be downloaded again, file size: {current_file_size:.2f} KB")
        else:
            # 添加当前文件大小到列表中，并更新计数
            fsize_dict[same_file]["size_list"].append(current_file_size)

    # 返回调整后的平均值，这里根据您的需求，返回的是添加新值之前的平均值
    return fsize_dict[same_file]["mean_size"]


def _check_ftime(nc_file, tname="time", if_print=False):
    if not os.path.exists(nc_file):
        return False
    nc_file = str(nc_file)
    try:
        ds = xr.open_dataset(nc_file)
        real_time = ds[tname].values[0]
        ds.close()
        real_time = str(real_time)[:13]
        real_time = real_time.replace("-", "").replace("T", "")
        # -----------------------------------------------------
        f_time = re.findall(r"\d{10}", nc_file)[0]
        if real_time == f_time:
            return True
        else:
            if if_print:
                print(f"[bold #daff5c]File time error, file/real time: [bold blue]{f_time}/{real_time}")
            return False
    except Exception as e:
        if if_print:
            print(f"[bold #daff5c]File time check failed, {nc_file}: {e}")
        return False


def _correct_time(nc_file):
    # 打开NC文件
    dataset = nc.Dataset(nc_file)

    # 读取时间单位
    time_units = dataset.variables["time"].units

    # 关闭文件
    dataset.close()

    # 解析时间单位字符串以获取时间原点
    origin_str = time_units.split("since")[1].strip()
    origin_datetime = datetime.datetime.strptime(origin_str, "%Y-%m-%d %H:%M:%S")

    # 从文件名中提取日期字符串
    given_date_str = re.findall(r"\d{10}", str(nc_file))[0]

    # 将提取的日期字符串转换为datetime对象
    given_datetime = datetime.datetime.strptime(given_date_str, "%Y%m%d%H")

    # 计算给定日期与时间原点之间的差值（以小时为单位）
    time_difference = (given_datetime - origin_datetime).total_seconds()
    if "hours" in time_units:
        time_difference /= 3600
    elif "days" in time_units:
        time_difference /= 3600 * 24

    # 修改NC文件中的时间变量
    modify_nc(nc_file, "time", None, time_difference)


def _download_file(target_url, store_path, file_name, check=False):
    # Check if the file exists
    fname = Path(store_path) / file_name
    file_name_split = file_name.split("_")
    file_name_split = file_name_split[:-1]
    # same_file = f"{file_name_split[0]}_{file_name_split[1]}*nc"
    same_file = "_".join(file_name_split) + "*nc"

    if match_time is not None:
        if check_nc(fname):
            if not _check_ftime(fname, if_print=True):
                if match_time:
                    _correct_time(fname)
                    count_dict["skip"] += 1
                else:
                    _clear_existing_file(fname)
                    # print(f"[bold #ffe5c0]File time error, {fname}")
                    count_dict["no_data"] += 1
            else:
                count_dict["skip"] += 1
                print(f"[bold green]{file_name} is correct")
        return

    if check:
        if same_file not in fsize_dict.keys():  # 对第一个文件单独进行检查，因为没有大小可以对比
            check_nc(fname, delete_switch=True)

        # set_min_size = _get_mean_size30(store_path, same_file) # 原方案，只30次取平均值；若遇变化，无法判断
        get_mean_size = _get_mean_size_move(same_file, fname)

        if _check_existing_file(fname, get_mean_size):
            count_dict["skip"] += 1
            return
    _clear_existing_file(fname)

    if not use_idm:
        # -----------------------------------------------
        print(f"[bold #f0f6d0]Requesting {file_name} ...")
        # 创建会话
        s = requests.Session()
        download_success = False
        request_times = 0

        def calculate_wait_time(time_str, target_url):
            # 定义正则表达式，匹配YYYYMMDDHH格式的时间
            time_pattern = r"\d{10}"

            # 定义两个字符串
            # str1 = 'HYCOM_water_u_2018010100-2018010112.nc'
            # str2 = 'HYCOM_water_u_2018010100.nc'

            # 使用正则表达式查找时间
            times_in_str = re.findall(time_pattern, time_str)

            # 计算每个字符串中的时间数量
            num_times_str = len(times_in_str)

            if num_times_str > 1:
                delta_t = datetime.datetime.strptime(times_in_str[1], "%Y%m%d%H") - datetime.datetime.strptime(times_in_str[0], "%Y%m%d%H")
                delta_t = delta_t.total_seconds() / 3600
                delta_t = delta_t / 3 + 1
            else:
                delta_t = 1
            # 单个要素最多等待5分钟，不宜太短，太短可能请求失败；也不宜太长，太长可能会浪费时间
            num_var = int(target_url.count("var="))
            if num_var <= 0:
                num_var = 1
            return int(delta_t * 5 * 60 * num_var)

        max_timeout = calculate_wait_time(file_name, target_url)
        print(f"[bold #912dbc]Max timeout: {max_timeout} seconds")

        # print(f'Download_start_time: {datetime.datetime.now()}')
        download_time_s = datetime.datetime.now()
        order_list = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th"]
        while not download_success:
            if request_times >= 10:
                # print(f'下载失败，已重试 {request_times} 次\n可先跳过，后续再试')
                print(f"[bold #ffe5c0]Download failed after {request_times} times\nYou can skip it and try again later")
                count_dict["fail"] += 1
                break
            if request_times > 0:
                # print(f'\r正在重试第 {request_times} 次', end="")
                print(f"[bold #ffe5c0]Retrying the {order_list[request_times - 1]} time...")
            # 尝试下载文件
            try:
                headers = {"User-Agent": get_ua()}
                """ response = s.get(target_url, headers=headers, timeout=random.randint(5, max_timeout))
                response.raise_for_status()  # 如果请求返回的不是200，将抛出HTTPError异常

                # 保存文件
                with open(filename, 'wb') as f:
                    f.write(response.content) """

                response = s.get(target_url, headers=headers, stream=True, timeout=random.randint(5, max_timeout))  # 启用流式传输
                response.raise_for_status()  # 如果请求返回的不是200，将抛出HTTPError异常
                # 保存文件
                with open(fname, "wb") as f:
                    print(f"[bold #96cbd7]Downloading {file_name} ...")
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)

                f.close()

                # print(f'\r文件 {fname} 下载成功', end="")
                if os.path.exists(fname):
                    download_success = True
                    download_time_e = datetime.datetime.now()
                    download_delta = download_time_e - download_time_s
                    print(f"[#3dfc40]File [bold #dfff73]{fname} [#3dfc40]has been downloaded successfully, Time: [#39cbdd]{download_delta}")
                    count_dict["success"] += 1
                    # print(f'Download_end_time: {datetime.datetime.now()}')

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
    else:
        idm_downloader(target_url, store_path, file_name, given_idm_engine)
        idm_download_list.append(fname)
        print(f"[bold #3dfc40]File [bold #dfff73]{fname} [#3dfc40]has been submit to IDM for downloading")


def _check_hour_is_valid(ymdh_str):
    # hour should be 00, 03, 06, 09, 12, 15, 18, 21
    hh = int(str(ymdh_str[-2:]))
    if hh in [0, 3, 6, 9, 12, 15, 18, 21]:
        return True
    else:
        return False


def _check_dataset_version(dataset_name, version_name, download_time, download_time_end=None):
    if dataset_name is not None and version_name is not None:
        just_ensure = _ensure_time_in_specific_dataset_and_version(dataset_name, version_name, download_time, download_time_end)
        if just_ensure:
            return dataset_name, version_name
        else:
            return None, None

    # 确保下载时间是一个字符串
    download_time_str = str(download_time)

    if len(download_time_str) == 8:
        download_time_str = download_time_str + "00"

    # 检查小时是否有效（如果需要的话）
    if download_time_end is None and not _check_hour_is_valid(download_time_str):
        print("Please ensure the hour is 00, 03, 06, 09, 12, 15, 18, 21")
        raise ValueError("The hour is invalid")

    # 根据是否检查整个天来设置时间范围
    if download_time_end is not None:
        if len(str(download_time_end)) == 8:
            download_time_end = str(download_time_end) + "21"
        have_data = _check_time_in_dataset_and_version(download_time_str, download_time_end)
        if have_data:
            return _direct_choose_dataset_and_version(download_time_str, download_time_end)
    else:
        have_data = _check_time_in_dataset_and_version(download_time_str)
        if have_data:
            return _direct_choose_dataset_and_version(download_time_str)

    return None, None


def _get_submit_url_var(var, depth, level_num, lon_min, lon_max, lat_min, lat_max, dataset_name, version_name, download_time, download_time_end=None):
    # year_str = str(download_time)[:4]
    ymdh_str = str(download_time)
    if depth is not None and level_num is not None:
        print("Please ensure the depth or level_num is None")
        print("Progress will use the depth")
        which_mode = "depth"
    elif depth is not None and level_num is None:
        print(f"Data of single depth (~{depth} m) will be downloaded...")
        which_mode = "depth"
    elif level_num is not None and depth is None:
        print(f"Data of single level ({level_num}) will be downloaded...")
        which_mode = "level"
    else:
        # print("Full depth or full level data will be downloaded...")
        which_mode = "full"
    query_dict = _get_query_dict(var, lon_min, lon_max, lat_min, lat_max, download_time, download_time_end, which_mode, depth, level_num)
    submit_url = _get_submit_url(dataset_name, version_name, var, ymdh_str, query_dict)
    return submit_url


def _prepare_url_to_download(var, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90, download_time="2024083100", download_time_end=None, depth=None, level_num=None, store_path=None, dataset_name=None, version_name=None, check=False):
    print("[bold #ecdbfe]-" * mark_len)
    download_time = str(download_time)
    if download_time_end is not None:
        download_time_end = str(download_time_end)
        dataset_name, version_name = _check_dataset_version(dataset_name, version_name, download_time, download_time_end)
    else:
        dataset_name, version_name = _check_dataset_version(dataset_name, version_name, download_time)
    if dataset_name is None and version_name is None:
        count_dict["no_data"] += 1
        if download_time_end is not None:
            count_dict["no_data_list"].append(f"{download_time}-{download_time_end}")
        else:
            count_dict["no_data_list"].append(download_time)
        return

    if isinstance(var, str):
        var = [var]

    if isinstance(var, list):
        if len(var) == 1:
            var = var[0]
            submit_url = _get_submit_url_var(var, depth, level_num, lon_min, lon_max, lat_min, lat_max, dataset_name, version_name, download_time, download_time_end)
            file_name = f"HYCOM_{variable_info[var]['var_name']}_{download_time}.nc"
            if download_time_end is not None:
                file_name = f"HYCOM_{variable_info[var]['var_name']}_{download_time}-{download_time_end}.nc"  # 这里时间不能用下划线，不然后续处理查找同一变量文件会出问题
            _download_file(submit_url, store_path, file_name, check)
        else:
            if download_time < "2024081012":
                varlist = [_ for _ in var]
                for key, value in var_group.items():
                    current_group = []
                    for v in varlist:
                        if v in value:
                            current_group.append(v)
                    if len(current_group) == 0:
                        continue

                    var = current_group[0]
                    submit_url = _get_submit_url_var(var, depth, level_num, lon_min, lon_max, lat_min, lat_max, dataset_name, version_name, download_time, download_time_end)
                    file_name = f"HYCOM_{variable_info[var]['var_name']}_{download_time}.nc"
                    old_str = f"var={variable_info[var]['var_name']}"
                    new_str = f"var={variable_info[var]['var_name']}"
                    if len(current_group) > 1:
                        for v in current_group[1:]:
                            new_str = f"{new_str}&var={variable_info[v]['var_name']}"
                        submit_url = submit_url.replace(old_str, new_str)
                        # file_name = f'HYCOM_{'-'.join([variable_info[v]["var_name"] for v in current_group])}_{download_time}.nc'
                        file_name = f"HYCOM_{key}_{download_time}.nc"
                        if download_time_end is not None:
                            file_name = f"HYCOM_{key}_{download_time}-{download_time_end}.nc"  # 这里时间不能用下划线，不然后续处理查找同一变量文件会出问题
                    _download_file(submit_url, store_path, file_name, check)
            else:
                for v in var:
                    submit_url = _get_submit_url_var(v, depth, level_num, lon_min, lon_max, lat_min, lat_max, dataset_name, version_name, download_time, download_time_end)
                    file_name = f"HYCOM_{variable_info[v]['var_name']}_{download_time}.nc"
                    if download_time_end is not None:
                        file_name = f"HYCOM_{variable_info[v]['var_name']}_{download_time}-{download_time_end}.nc"
                    _download_file(submit_url, store_path, file_name, check)


def _convert_full_name_to_short_name(full_name):
    for var, info in variable_info.items():
        if full_name == info["var_name"] or full_name == info["standard_name"] or full_name == var:
            return var
    print("[bold #FFE4E1]Please ensure the var is in:\n[bold blue]u,v,temp,salt,ssh,u_b,v_b,temp_b,salt_b")
    print("or")
    print("[bold blue]water_u, water_v, water_temp, salinity, surf_el, water_u_bottom, water_v_bottom, water_temp_bottom, salinity_bottom")
    return False


def _download_task(var, time_str, time_str_end, lon_min, lon_max, lat_min, lat_max, depth, level, store_path, dataset_name, version_name, check):
    """
    # 并行下载任务
    # 这个函数是为了并行下载而设置的，是必须的，直接调用direct_download并行下载会出问题

    任务封装：将每个任务需要的数据和操作封装在一个函数中，这样每个任务都是独立的，不会相互干扰。
    本情况下，download_task函数的作用是将每个下载任务封装起来，包括它所需的所有参数。
    这样，每个任务都是独立的，有自己的参数和数据，不会与其他任务共享或修改任何数据。
    因此，即使多个任务同时执行，也不会出现数据交互错乱的问题。
    """

    _prepare_url_to_download(var, lon_min, lon_max, lat_min, lat_max, time_str, time_str_end, depth, level, store_path, dataset_name, version_name, check)


def _done_callback(future, progress, task, total, counter_lock):
    """
    # 并行下载任务的回调函数
    # 这个函数是为了并行下载而设置的，是必须的，直接调用direct_download并行下载会出问题

    回调函数：当一个任务完成后，会调用这个函数，这样可以及时更新进度条，显示任务的完成情况。
    本情况下，done_callback函数的作用是当一个任务完成后，更新进度条的进度，显示任务的完成情况。
    这样，即使多个任务同时执行，也可以及时看到每个任务的完成情况，不会等到所有任务都完成才显示。
    """

    global parallel_counter
    with counter_lock:
        parallel_counter += 1
        progress.update(task, advance=1, description=f"[cyan]{bar_desc} {parallel_counter}/{total}")


def _download_hourly_func(var, time_s, time_e, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90, depth=None, level=None, store_path=None, dataset_name=None, version_name=None, num_workers=None, check=False, ftimes=1, interval_hour=3):
    """
    Description:
    Download the data of single time or a series of time

    Parameters:
    var: str, the variable name, such as 'u', 'v', 'temp', 'salt', 'ssh', 'u_b', 'v_b', 'temp_b', 'salt_b' or 'water_u', 'water_v', 'water_temp', 'salinity', 'surf_el', 'water_u_bottom', 'water_v_bottom', 'water_temp_bottom', 'salinity_bottom'
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
    """
    ymdh_time_s, ymdh_time_e = str(time_s), str(time_e)
    if num_workers is not None and num_workers > 1:  # 如果使用多线程下载，用于进度条显示
        global parallel_counter
        parallel_counter = 0
        counter_lock = Lock()  # 创建一个锁，线程安全的计数器
    if ymdh_time_s == ymdh_time_e:
        _prepare_url_to_download(var, lon_min, lon_max, lat_min, lat_max, ymdh_time_s, None, depth, level, store_path, dataset_name, version_name, check)
    elif int(ymdh_time_s) < int(ymdh_time_e):
        print("Downloading a series of files...")
        time_list = get_time_list(ymdh_time_s, ymdh_time_e, interval_hour, "hour")
        with Progress() as progress:
            task = progress.add_task(f"[cyan]{bar_desc}", total=len(time_list))
            if ftimes == 1:
                if num_workers is None or num_workers <= 1:
                    # 串行方式
                    for i, time_str in enumerate(time_list):
                        _prepare_url_to_download(var, lon_min, lon_max, lat_min, lat_max, time_str, None, depth, level, store_path, dataset_name, version_name, check)
                        progress.update(task, advance=1, description=f"[cyan]{bar_desc} {i + 1}/{len(time_list)}")
                else:
                    # 并行方式
                    with ThreadPoolExecutor(max_workers=num_workers) as executor:
                        futures = [executor.submit(_download_task, var, time_str, None, lon_min, lon_max, lat_min, lat_max, depth, level, store_path, dataset_name, version_name, check) for time_str in time_list]
                        """ for i, future in enumerate(futures):
                            future.add_done_callback(lambda _: progress.update(task, advance=1, description=f"[cyan]{bar_desc} {i+1}/{len(time_list)}")) """
                        for feature in as_completed(futures):
                            _done_callback(feature, progress, task, len(time_list), counter_lock)
            else:
                # new_time_list = get_time_list(ymdh_time_s, ymdh_time_e, 3 * ftimes, "hour")
                new_time_list = get_time_list(ymdh_time_s, ymdh_time_e, interval_hour * ftimes, "hour")
                total_num = len(new_time_list)
                if num_workers is None or num_workers <= 1:
                    # 串行方式
                    for i, time_str in enumerate(new_time_list):
                        time_str_end_index = int(min(len(time_list) - 1, int(i * ftimes + ftimes - 1)))
                        time_str_end = time_list[time_str_end_index]
                        _prepare_url_to_download(var, lon_min, lon_max, lat_min, lat_max, time_str, time_str_end, depth, level, store_path, dataset_name, version_name, check)
                        progress.update(task, advance=1, description=f"[cyan]{bar_desc} {i + 1}/{total_num}")
                else:
                    # 并行方式
                    with ThreadPoolExecutor(max_workers=num_workers) as executor:
                        futures = [executor.submit(_download_task, var, new_time_list[i], time_list[int(min(len(time_list) - 1, int(i * ftimes + ftimes - 1)))], lon_min, lon_max, lat_min, lat_max, depth, level, store_path, dataset_name, version_name, check) for i in range(total_num)]
                        """ for i, future in enumerate(futures):
                            future.add_done_callback(lambda _: progress.update(task, advance=1, description=f"[cyan]{bar_desc} {i+1}/{total_num}")) """
                        for feature in as_completed(futures):
                            _done_callback(feature, progress, task, len(time_list), counter_lock)
    else:
        print("[bold red]Please ensure the time_s is no more than time_e")


def download(var, time_s, time_e=None, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90, depth=None, level=None, store_path=None, dataset_name=None, version_name=None, num_workers=None, check=False, ftimes=1, idm_engine=None, fill_time=None, interval_hour=3):
    """
    Description:
        Download the data of single time or a series of time

    Parameters:
        var: str or list, the variable name, such as 'u', 'v', 'temp', 'salt', 'ssh', 'u_b', 'v_b', 'temp_b', 'salt_b' or 'water_u', 'water_v', 'water_temp', 'salinity', 'surf_el', 'water_u_bottom', 'water_v_bottom', 'water_temp_bottom', 'salinity_bottom'
        time_s: str, the start time, such as '2024110100' or '20241101', if add hour, the hour should be 00, 03, 06, 09, 12, 15, 18, 21
        time_e: str, the end time, such as '2024110221' or '20241102', if add hour, the hour should be 00, 03, 06, 09, 12, 15, 18, 21; default is None, if not set, the data of single time will be downloaded; or same as time_s, the data of single time will be downloaded
        lon_min: float, the minimum longitude, default is 0
        lon_max: float, the maximum longitude, default is 359.92
        lat_min: float, the minimum latitude, default is -80
        lat_max: float, the maximum latitude, default is 90
        depth: float, the depth, default is None, if you wanna get the data of single depth, you can set the depth, suggest to set the depth in [0, 5000]
        level: int, the level number, default is None, if you wanna get the data of single level, you can set the level, suggest to set the level in [1, 40]
        store_path: str, the path to store the data, default is None, if not set, the data will be stored in the current working directory
        dataset_name: str, the dataset name, default is None, example: 'GLBv0.08', 'GLBu0.08', 'GLBy0.08', if not set, the dataset will be chosen according to the download_time
        version_name: str, the version name, default is None, example: '53.X', '56.3', if not set, the version will be chosen according to the download_time
        num_workers: int, the number of workers, default is None, if not set, the number of workers will be 1; suggest not to set the number of workers too large
        check: bool, whether to check the existing file, default is False, if set to True, the existing file will be checked and not downloaded again; else, the existing file will be covered
        ftimes: int, the number of time in one file, default is 1, if set to 1, the data of single time will be downloaded; the maximum is 8, if set to 8, the data of 8 times will be downloaded in one file
        idm_engine: str, the IDM engine, default is None, if set, the IDM will be used to download the data; example: "D:\\Programs\\Internet Download Manager\\IDMan.exe"
        fill_time: bool or None, the mode to fill the time, default is None. None: only download the data; True: modify the real time of data to the time in the file name; False: check the time in the file name and the real time of data, if not match, delete the file
        interval_hour: int, the interval time to download the data, default is 3, if set, the interval time will be used to download the data; example: 3, 6, ...

    Returns:
        None
    """
    from oafuncs.oa_data import pbar
    from oafuncs.oa_cmap import get as get_cmap
    
    _get_initial_data()

    # 打印信息并处理数据集和版本名称
    if dataset_name is None and version_name is None:
        print("The dataset_name and version_name are None, so the dataset and version will be chosen according to the download_time.\nIf there is more than one dataset and version in the time range, the first one will be chosen.")
        print("If you wanna choose the dataset and version by yourself, please set the dataset_name and version_name together.")
    elif dataset_name is None and version_name is not None:
        print("Please ensure the dataset_name is not None")
        print("If you do not add the dataset_name, both the dataset and version will be chosen according to the download_time.")
    elif dataset_name is not None and version_name is None:
        print("Please ensure the version_name is not None")
        print("If you do not add the version_name, both the dataset and version will be chosen according to the download_time.")
    else:
        print("The dataset_name and version_name are both set by yourself.")
        print("Please ensure the dataset_name and version_name are correct.")

    if isinstance(var, list):
        if len(var) == 1:
            var = _convert_full_name_to_short_name(var[0])
        else:
            var = [_convert_full_name_to_short_name(v) for v in var]
    elif isinstance(var, str):
        var = _convert_full_name_to_short_name(var)
    else:
        raise ValueError("The var is invalid")
    if var is False:
        raise ValueError("The var is invalid")
    if lon_min < 0 or lon_min > 359.92 or lon_max < 0 or lon_max > 359.92 or lat_min < -80 or lat_min > 90 or lat_max < -80 or lat_max > 90:
        print("Please ensure the lon_min, lon_max, lat_min, lat_max are in the range")
        print("The range of lon_min, lon_max is 0~359.92")
        print("The range of lat_min, lat_max is -80~90")
        raise ValueError("The lon or lat is invalid")

    if ftimes != 1:
        print("Please ensure the ftimes is in [1, 8]")
        ftimes = max(min(ftimes, 8), 1)

    if store_path is None:
        store_path = str(Path.cwd())
    else:
        os.makedirs(str(store_path), exist_ok=True)

    if num_workers is not None:
        num_workers = max(min(num_workers, 10), 1)  # 暂时不限制最大值，再检查的时候可以多开一些线程
        # num_workers = int(max(num_workers, 1))
    time_s = str(time_s)
    if len(time_s) == 8:
        time_s += "00"
    if time_e is None:
        time_e = time_s[:]
    else:
        time_e = str(time_e)
        if len(time_e) == 8:
            time_e += "21"

    global count_dict
    count_dict = {"success": 0, "fail": 0, "skip": 0, "no_data": 0, "total": 0, "no_data_list": []}

    """ global current_platform
    current_platform = platform.system() """

    global fsize_dict
    fsize_dict = {}

    global fsize_dict_lock
    fsize_dict_lock = Lock()

    if fill_time is not None:
        num_workers = 1

    global use_idm, given_idm_engine, idm_download_list, bar_desc
    if idm_engine is not None:
        use_idm = True
        num_workers = 1
        given_idm_engine = idm_engine
        idm_download_list = []
        bar_desc = "Submitting to IDM ..."
    else:
        use_idm = False
        bar_desc = "Downloading ..."

    global match_time
    match_time = fill_time

    global mark_len
    mark_len = 100

    _download_hourly_func(var, time_s, time_e, lon_min, lon_max, lat_min, lat_max, depth, level, store_path, dataset_name, version_name, num_workers, check, ftimes, int(interval_hour))

    if idm_engine is not None:
        print("[bold #ecdbfe]*" * mark_len)
        str_info = "All files have been submitted to IDM for downloading"
        str_info = str_info.center(mark_len, "*")
        print(f"[bold #3dfc40]{str_info}")
        print("[bold #ecdbfe]*" * mark_len)
        if idm_download_list:
            """ file_download_time = 60  # 预设下载时间为1分钟
            for f in pbar(idm_download_list,cmap='bwr',prefix='HYCOM: '):
                file_download_start_time = time.time()
                wait_success = 0
                success = False
                while not success:
                    if check_nc(f,print_switch=False):
                        count_dict["success"] += 1
                        success = True
                        # print(f"[bold #3dfc40]File [bold #dfff73]{f} [#3dfc40]has been downloaded successfully")
                        file_download_end_time = time.time()
                        file_download_time = file_download_end_time - file_download_start_time
                        file_download_time = int(file_download_time)
                        # print(f"[bold #3dfc40]Time: {file_download_time} seconds")
                        file_download_time = max(60, file_download_time)  # 预设下载时间为1分钟起步
                    else:
                        wait_success += 1
                        # print(f"[bold #ffe5c0]Waiting {file_download_time} seconds to check the file {f}...")
                        time.sleep(file_download_time)
                        if wait_success >= 10:
                            success = True
                            # print(f'{f} download failed')
                            print(f"[bold #ffe5c0]Waiting for more than 10 times, skipping the file {f}...")
                            count_dict["fail"] += 1
                # print("[bold #ecdbfe]-" * mark_len) """
            remain_list = idm_download_list.copy()
            for f_count in pbar(range(len(idm_download_list)), cmap=get_cmap('diverging_1'), prefix="HYCOM: "):
                success = False
                while not success:
                    for f in remain_list:
                        if check_nc(f, print_switch=False):
                            count_dict["success"] += 1
                            success = True
                            remain_list.remove(f)
                            break

    count_dict["total"] = count_dict["success"] + count_dict["fail"] + count_dict["skip"] + count_dict["no_data"]
    print("[bold #ecdbfe]=" * mark_len)
    print(f"[bold #ff80ab]Total: {count_dict['total']}\nSuccess: {count_dict['success']}\nFail: {count_dict['fail']}\nSkip: {count_dict['skip']}\nNo data: {count_dict['no_data']}")
    print("[bold #ecdbfe]=" * mark_len)
    if count_dict["fail"] > 0:
        print("[bold #be5528]Please try again to download the failed data later")
    if count_dict["no_data"] > 0:
        if count_dict["no_data"] == 1:
            print(f"[bold #f90000]There is {count_dict['no_data']} data that does not exist in any dataset and version")
        else:
            print(f"[bold #f90000]These are {count_dict['no_data']} data that do not exist in any dataset and version")
        for no_data in count_dict["no_data_list"]:
            print(f"[bold #d81b60]{no_data}")
    print("[bold #ecdbfe]=" * mark_len)


def how_to_use():
    print("""
    # 1. Choose the dataset and version according to the time:
    # 1.1 Use function to query
    You can use the function check_time_in_dataset_and_version(time_input=20241101) to find the dataset and version  according to the time.
    Then, you can see the dataset and version in the output.
    # 1.2 Draw a picture to see
    You can draw a picture to see the time range of each dataset and version.
    Using the function draw_time_range(pic_save_folder=None) to draw the picture.

    # 2. Get the base url according to the dataset, version, var and year:
    # 2.1 Dataset and version were found in step 1
    # 2.2 Var: u, v, temp, salt, ssh, u_b, v_b, temp_b, salt_b
    # 2.3 Year: 1994-2024(current year)

    # 3. Get the query_dict according to the var, lon_min, lon_max, lat_min, lat_max, depth, level_num, time_str_ymdh:
    # 3.1 Var: u, v, temp, salt, ssh, u_b, v_b, temp_b, salt_b
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
    """)


if __name__ == "__main__":
    download_dict = {
        "water_u": {"simple_name": "u", "download": 1},
        "water_v": {"simple_name": "v", "download": 1},
        "surf_el": {"simple_name": "ssh", "download": 1},
        "water_temp": {"simple_name": "temp", "download": 1},
        "salinity": {"simple_name": "salt", "download": 1},
        "water_u_bottom": {"simple_name": "u_b", "download": 0},
        "water_v_bottom": {"simple_name": "v_b", "download": 0},
        "water_temp_bottom": {"simple_name": "temp_b", "download": 0},
        "salinity_bottom": {"simple_name": "salt_b", "download": 0},
    }

    var_list = [var_name for var_name in download_dict.keys() if download_dict[var_name]["download"]]

    single_var = False

    # draw_time_range(pic_save_folder=r'I:\Delete')

    options = {
        "var": var_list,
        "time_s": "2025010300",
        "time_e": "2025010321",
        "store_path": r"I:\Data\HYCOM\3hourly",
        "lon_min": 105,
        "lon_max": 130,
        "lat_min": 15,
        "lat_max": 45,
        "num_workers": 3,
        "check": True,
        "depth": None,  # or 0-5000 meters
        "level": None,  # or 1-40 levels
        "ftimes": 1,
        # "idm_engine": r"D:\Programs\Internet Download Manager\IDMan.exe",  # 查漏补缺不建议开启
        "fill_time": None,
    }

    if single_var:
        for var_name in var_list:
            options["var"] = var_name
            download(**options)
    else:
        download(**options)
