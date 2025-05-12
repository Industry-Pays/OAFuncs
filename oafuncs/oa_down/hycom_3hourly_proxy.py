#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-04-17 15:16:02
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-04-17 15:16:04
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_down\\hycom_3hourly copy.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""



import asyncio
import datetime
import logging
import os
import random
import re
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import httpx
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import pandas as pd
import xarray as xr
from rich import print
from rich.progress import Progress

from oafuncs.oa_down.idm import downloader as idm_downloader
from oafuncs.oa_down.user_agent import get_ua
from oafuncs.oa_file import file_size
from oafuncs.oa_nc import check as check_nc
from oafuncs.oa_nc import modify as modify_nc

logging.getLogger("httpx").setLevel(logging.WARNING)  # 关闭 httpx 的 INFO 日志，只显示 WARNING 及以上


warnings.filterwarnings("ignore", category=RuntimeWarning, message="Engine '.*' loading failed:.*")

__all__ = ["draw_time_range", "download"]


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


def _get_time_list(time_s, time_e, delta, interval_type="hour"):
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

    if have_data:
        if match_time is None:
            print(f"[bold red]Time {time_input_str} included in:")
            dv_num = 1
            for d, v, trange in zip(d_list, v_list, trange_list):
                print(f"{dv_num} -> [bold blue]{d} - {v} : {trange}")
                dv_num += 1
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
        print(f"[bold red]Time {time_input_str} has no data")
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
                dataset_name_out, version_name_out = dataset_name, version_name

    if dataset_name_out is not None and version_name_out is not None:
        if match_time is None:
            # print(f"[bold purple]dataset: {dataset_name_out}, version: {version_name_out} is chosen")
            print(f"[bold purple]Chosen dataset: {dataset_name_out} - {version_name_out}")

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
                return True
            else:
                # print(f"File size is abnormal and cannot be opened, {file_full_path}: {fsize:.2f} KB")
                return False
        else:
            return True
    else:
        return False


def _get_mean_size_move(same_file, current_file):
    with fsize_dict_lock:
        if same_file not in fsize_dict.keys():
            fsize_dict[same_file] = {"size_list": [], "mean_size": 1.0}

        tolerance_ratio = 0.025
        current_file_size = file_size(current_file)

        if fsize_dict[same_file]["size_list"]:
            fsize_dict[same_file]["mean_size"] = sum(fsize_dict[same_file]["size_list"]) / len(fsize_dict[same_file]["size_list"])
            fsize_dict[same_file]["mean_size"] = max(fsize_dict[same_file]["mean_size"], 1.0)
        else:
            fsize_dict[same_file]["mean_size"] = 1.0

        size_difference_ratio = (current_file_size - fsize_dict[same_file]["mean_size"]) / fsize_dict[same_file]["mean_size"]

        if abs(size_difference_ratio) > tolerance_ratio:
            if check_nc(current_file, print_messages=False):
                fsize_dict[same_file]["size_list"] = [current_file_size]
                fsize_dict[same_file]["mean_size"] = current_file_size
            else:
                _clear_existing_file(current_file)
                # print(f"File size is abnormal, may need to be downloaded again, file size: {current_file_size:.2f} KB")
        else:
            fsize_dict[same_file]["size_list"].append(current_file_size)

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
    dataset = nc.Dataset(nc_file)
    time_units = dataset.variables["time"].units
    dataset.close()
    origin_str = time_units.split("since")[1].strip()
    origin_datetime = datetime.datetime.strptime(origin_str, "%Y-%m-%d %H:%M:%S")
    given_date_str = re.findall(r"\d{10}", str(nc_file))[0]
    given_datetime = datetime.datetime.strptime(given_date_str, "%Y%m%d%H")
    time_difference = (given_datetime - origin_datetime).total_seconds()
    if "hours" in time_units:
        time_difference /= 3600
    elif "days" in time_units:
        time_difference /= 3600 * 24
    modify_nc(nc_file, "time", None, time_difference)


class _HycomDownloader:
    def __init__(self, tasks, delay_range=(3, 6), timeout_factor=120, max_var_count=5, max_retries=3):
        """
        :param tasks: List of (url, save_path)
        """
        self.tasks = tasks
        self.delay_range = delay_range
        self.timeout_factor = timeout_factor
        self.max_var_count = max_var_count
        self.max_retries = max_retries
        self.count = {"success": 0, "fail": 0}

    def user_agent(self):
        return get_ua()

    async def _download_one(self, url, save_path):
        file_name = os.path.basename(save_path)
        headers = {"User-Agent": self.user_agent()}
        var_count = min(max(url.count("var="), 1), self.max_var_count)
        timeout_max = self.timeout_factor * var_count
        timeout = random.randint(timeout_max // 2, timeout_max)

        retry = 0
        while retry <= self.max_retries:
            if proxy_txt_path:
                from .read_proxy import get_valid_proxy

                proxy_one = get_valid_proxy(proxy_txt_path)
                if proxy_one:
                    if proxy_one.startswith("http://"):
                        proxy_one = proxy_one[7:]
                    elif proxy_one.startswith("https://"):
                        proxy_one = proxy_one[8:]
            else:
                proxy_one = None
            if proxy_one:
                proxy = f"http://{proxy_one}"
                mounts = {
                    "http://": httpx.AsyncHTTPTransport(proxy=proxy),
                    "https://": httpx.AsyncHTTPTransport(proxy=proxy),
                }
            else:
                proxy = None
                mounts = None
            try:
                await asyncio.sleep(random.uniform(*self.delay_range))
                start = datetime.datetime.now()

                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(timeout),
                    limits=httpx.Limits(max_connections=2, max_keepalive_connections=2),
                    transport=httpx.AsyncHTTPTransport(retries=2),
                    # proxy=proxy,
                    mounts=mounts,
                ) as client:
                    print(f"[bold #f0f6d0]Requesting {file_name} (Attempt {retry + 1}) ...")
                    response = await client.get(url, headers=headers, follow_redirects=True)
                    response.raise_for_status()
                    if not response.content:
                        raise ValueError("Empty response received")

                    print(f"[bold #96cbd7]Downloading {file_name} ...")
                    with open(save_path, "wb") as f:
                        async for chunk in response.aiter_bytes(32 * 1024):
                            f.write(chunk)

                    elapsed = datetime.datetime.now() - start
                    print(f"[#3dfc40]File [bold #dfff73]{file_name} [#3dfc40]downloaded, Time: [#39cbdd]{elapsed}")
                    self.count["success"] += 1
                    count_dict["success"] += 1
                    return

            except Exception as e:
                print(f"[bold red]Failed ({type(e).__name__}): {e}")
                if retry < self.max_retries:
                    backoff = 2**retry
                    print(f"[yellow]Retrying in {backoff:.1f}s ...")
                    await asyncio.sleep(backoff)
                    retry += 1
                else:
                    print(f"[red]Giving up on {file_name}")
                    self.count["fail"] += 1
                    count_dict["fail"] += 1
                    return

    async def run(self):
        print(f"📥 Starting download of {len(self.tasks)} files ...")
        for url, save_path in self.tasks:
            await self._download_one(url, save_path)

        print("\n✅ All tasks completed.")
        print(f"✔️  Success: {self.count['success']} | ❌ Fail: {self.count['fail']}")


def _download_file(target_url, store_path, file_name, cover=False):
    save_path = Path(store_path) / file_name
    file_name_split = file_name.split("_")
    file_name_split = file_name_split[:-1]
    same_file = "_".join(file_name_split) + "*nc"

    if match_time is not None:
        if check_nc(save_path, print_messages=False):
            if not _check_ftime(save_path, if_print=True):
                if match_time:
                    _correct_time(save_path)
                    count_dict["skip"] += 1
                else:
                    _clear_existing_file(save_path)
                    count_dict["no_data"] += 1
            else:
                count_dict["skip"] += 1
                print(f"[bold green]{file_name} is correct")
        return

    if not cover and os.path.exists(save_path):
        print(f"[bold #FFA54F]{save_path} exists, skipping ...")
        count_dict["skip"] += 1
        return

    if same_file not in fsize_dict.keys():
        check_nc(save_path, delete_if_invalid=True, print_messages=False)

    get_mean_size = _get_mean_size_move(same_file, save_path)

    if _check_existing_file(save_path, get_mean_size):
        count_dict["skip"] += 1
        return

    _clear_existing_file(save_path)

    if not use_idm:
        python_downloader = _HycomDownloader([(target_url, save_path)])
        asyncio.run(python_downloader.run())
        time.sleep(3 + random.uniform(0, 10))
    else:
        idm_downloader(target_url, store_path, file_name, given_idm_engine)
        idm_download_list.append(save_path)
        # print(f"[bold #3dfc40]File [bold #dfff73]{save_path} [#3dfc40]has been submit to IDM for downloading")
        time.sleep(3 + random.uniform(0, 10))


def _check_hour_is_valid(ymdh_str):
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

    download_time_str = str(download_time)

    if len(download_time_str) == 8:
        download_time_str = download_time_str + "00"

    if download_time_end is None and not _check_hour_is_valid(download_time_str):
        print("Please ensure the hour is 00, 03, 06, 09, 12, 15, 18, 21")
        raise ValueError("The hour is invalid")

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
        which_mode = "full"
    query_dict = _get_query_dict(var, lon_min, lon_max, lat_min, lat_max, download_time, download_time_end, which_mode, depth, level_num)
    submit_url = _get_submit_url(dataset_name, version_name, var, ymdh_str, query_dict)
    return submit_url


def _prepare_url_to_download(var, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90, download_time="2024083100", download_time_end=None, depth=None, level_num=None, store_path=None, dataset_name=None, version_name=None, cover=False):
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
                file_name = f"HYCOM_{variable_info[var]['var_name']}_{download_time}-{download_time_end}.nc"
            _download_file(submit_url, store_path, file_name, cover)
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
                        file_name = f"HYCOM_{key}_{download_time}.nc"
                        if download_time_end is not None:
                            file_name = f"HYCOM_{key}_{download_time}-{download_time_end}.nc"
                    _download_file(submit_url, store_path, file_name, cover)
            else:
                for v in var:
                    submit_url = _get_submit_url_var(v, depth, level_num, lon_min, lon_max, lat_min, lat_max, dataset_name, version_name, download_time, download_time_end)
                    file_name = f"HYCOM_{variable_info[v]['var_name']}_{download_time}.nc"
                    if download_time_end is not None:
                        file_name = f"HYCOM_{variable_info[v]['var_name']}_{download_time}-{download_time_end}.nc"
                    _download_file(submit_url, store_path, file_name, cover)


def _convert_full_name_to_short_name(full_name):
    for var, info in variable_info.items():
        if full_name == info["var_name"] or full_name == info["standard_name"] or full_name == var:
            return var
    print("[bold #FFE4E1]Please ensure the var is in:\n[bold blue]u,v,temp,salt,ssh,u_b,v_b,temp_b,salt_b")
    print("or")
    print("[bold blue]water_u, water_v, water_temp, salinity, surf_el, water_u_bottom, water_v_bottom, water_temp_bottom, salinity_bottom")
    return False


def _download_task(var, time_str, time_str_end, lon_min, lon_max, lat_min, lat_max, depth, level, store_path, dataset_name, version_name, cover):
    _prepare_url_to_download(var, lon_min, lon_max, lat_min, lat_max, time_str, time_str_end, depth, level, store_path, dataset_name, version_name, cover)


def _done_callback(future, progress, task, total, counter_lock):
    global parallel_counter
    with counter_lock:
        parallel_counter += 1
        progress.update(task, advance=1, description=f"[cyan]{bar_desc} {parallel_counter}/{total}")


def _download_hourly_func(var, time_s, time_e, lon_min=0, lon_max=359.92, lat_min=-80, lat_max=90, depth=None, level=None, store_path=None, dataset_name=None, version_name=None, num_workers=None, cover=False, interval_hour=3):
    ymdh_time_s, ymdh_time_e = str(time_s), str(time_e)
    if num_workers is not None and num_workers > 1:
        global parallel_counter
        parallel_counter = 0
        counter_lock = Lock()
    if ymdh_time_s == ymdh_time_e:
        _prepare_url_to_download(var, lon_min, lon_max, lat_min, lat_max, ymdh_time_s, None, depth, level, store_path, dataset_name, version_name, cover)
    elif int(ymdh_time_s) < int(ymdh_time_e):
        if match_time is None:
            print("*" * mark_len)
            print("Downloading a series of files...")
        time_list = _get_time_list(ymdh_time_s, ymdh_time_e, interval_hour, "hour")
        with Progress() as progress:
            task = progress.add_task(f"[cyan]{bar_desc}", total=len(time_list))
            if num_workers is None or num_workers <= 1:
                for i, time_str in enumerate(time_list):
                    _prepare_url_to_download(var, lon_min, lon_max, lat_min, lat_max, time_str, None, depth, level, store_path, dataset_name, version_name, cover)
                    progress.update(task, advance=1, description=f"[cyan]{bar_desc} {i + 1}/{len(time_list)}")
            else:
                with ThreadPoolExecutor(max_workers=num_workers) as executor:
                    futures = [executor.submit(_download_task, var, time_str, None, lon_min, lon_max, lat_min, lat_max, depth, level, store_path, dataset_name, version_name, cover) for time_str in time_list]
                    for feature in as_completed(futures):
                        _done_callback(feature, progress, task, len(time_list), counter_lock)
    else:
        print("[bold red]Please ensure the time_s is no more than time_e")


def download(
    variables,
    start_time,
    end_time=None,
    lon_min=0,
    lon_max=359.92,
    lat_min=-80,
    lat_max=90,
    depth=None,
    level=None,
    output_dir=None,
    dataset=None,
    version=None,
    workers=None,
    overwrite=False,
    idm_path=None,
    validate_time=None,
    interval_hours=3,
    proxy_txt=None,
):
    """
    Download data for a single time or a series of times.

    Parameters:
        variables (str or list): Variable names to download. Examples include:
            'u', 'v', 'temp', 'salt', 'ssh', 'u_b', 'v_b', 'temp_b', 'salt_b'
            or their full names like 'water_u', 'water_v', etc.
        start_time (str): Start time in the format 'YYYYMMDDHH' or 'YYYYMMDD'.
            If hour is included, it must be one of [00, 03, 06, 09, 12, 15, 18, 21].
        end_time (str, optional): End time in the format 'YYYYMMDDHH' or 'YYYYMMDD'.
            If not provided, only data for the start_time will be downloaded.
        lon_min (float, optional): Minimum longitude. Default is 0.
        lon_max (float, optional): Maximum longitude. Default is 359.92.
        lat_min (float, optional): Minimum latitude. Default is -80.
        lat_max (float, optional): Maximum latitude. Default is 90.
        depth (float, optional): Depth in meters. If specified, data for a single depth
            will be downloaded. Suggested range: [0, 5000].
        level (int, optional): Vertical level number. If specified, data for a single
            level will be downloaded. Suggested range: [1, 40].
        output_dir (str, optional): Directory to save downloaded files. If not provided,
            files will be saved in the current working directory.
        dataset (str, optional): Dataset name. Examples: 'GLBv0.08', 'GLBu0.08', etc.
            If not provided, the dataset will be chosen based on the time range.
        version (str, optional): Dataset version. Examples: '53.X', '56.3', etc.
            If not provided, the version will be chosen based on the time range.
        workers (int, optional): Number of parallel workers. Default is 1. Maximum is 10.
        overwrite (bool, optional): Whether to overwrite existing files. Default is False.
        idm_path (str, optional): Path to the Internet Download Manager (IDM) executable.
            If provided, IDM will be used for downloading.
        validate_time (bool, optional): Time validation mode. Default is None.
            - None: Only download data.
            - True: Modify the real time in the data to match the file name.
            - False: Check if the real time matches the file name. If not, delete the file.
        interval_hours (int, optional): Time interval in hours for downloading data.
            Default is 3. Examples: 3, 6, etc.

    Returns:
        None

    Example:
        >>> download(
        variables='u',
        start_time='2024083100',
        end_time='2024090100',
        lon_min=0,
        lon_max=359.92,
        lat_min=-80,
        lat_max=90,
        depth=None,
        level=None,
        output_dir=None,
        dataset=None,
        version=None,
        workers=4,
        overwrite=False,
        idm_path=None,
        validate_time=None,
        interval_hours=3,
        )
    """
    from oafuncs.oa_tool import pbar

    _get_initial_data()

    if dataset is None and version is None:
        if validate_time is None:
            print("Dataset and version will be chosen based on the time range.")
            print("If multiple datasets or versions exist, the latest one will be used.")
    elif dataset is None:
        print("Please provide a dataset name if specifying a version.")
    elif version is None:
        print("Please provide a version if specifying a dataset name.")
    else:
        print("Using the specified dataset and version.")

    if isinstance(variables, list):
        if len(variables) == 1:
            variables = _convert_full_name_to_short_name(variables[0])
        else:
            variables = [_convert_full_name_to_short_name(v) for v in variables]
    elif isinstance(variables, str):
        variables = _convert_full_name_to_short_name(variables)
    else:
        raise ValueError("Invalid variable(s) provided.")
    if variables is False:
        raise ValueError("Invalid variable(s) provided.")
    if not (0 <= lon_min <= 359.92 and 0 <= lon_max <= 359.92 and -80 <= lat_min <= 90 and -80 <= lat_max <= 90):
        raise ValueError("Longitude or latitude values are out of range.")

    if output_dir is None:
        output_dir = str(Path.cwd())
    else:
        os.makedirs(output_dir, exist_ok=True)

    if workers is not None:
        workers = max(min(workers, 10), 1)
    start_time = str(start_time)
    if len(start_time) == 8:
        start_time += "00"
    if end_time is None:
        end_time = start_time[:]
    else:
        end_time = str(end_time)
        if len(end_time) == 8:
            end_time += "21"

    global count_dict
    count_dict = {"success": 0, "fail": 0, "skip": 0, "no_data": 0, "total": 0, "no_data_list": []}

    global fsize_dict
    fsize_dict = {}

    global fsize_dict_lock
    fsize_dict_lock = Lock()

    global use_idm, given_idm_engine, idm_download_list, bar_desc
    if idm_path is not None:
        use_idm = True
        workers = 1
        given_idm_engine = idm_path
        idm_download_list = []
        bar_desc = "Submitting to IDM ..."
    else:
        use_idm = False
        bar_desc = "Downloading ..."

    global match_time
    match_time = validate_time

    global mark_len
    mark_len = 100

    global proxy_txt_path
    proxy_txt_path = proxy_txt

    if validate_time is not None:
        workers = 1
        print("*" * mark_len)
        print("[bold red]Only checking the time of existing files.")
        bar_desc = "Checking time ..."

    _download_hourly_func(
        variables,
        start_time,
        end_time,
        lon_min,
        lon_max,
        lat_min,
        lat_max,
        depth,
        level,
        output_dir,
        dataset,
        version,
        workers,
        overwrite,
        int(interval_hours),
    )

    if idm_path is not None:
        print("[bold #ecdbfe]*" * mark_len)
        print(f"[bold #3dfc40]{'All files have been submitted to IDM for downloading'.center(mark_len, '*')}")
        print("[bold #ecdbfe]*" * mark_len)
        if idm_download_list:
            remain_list = idm_download_list.copy()
            for _ in pbar(range(len(idm_download_list)), cmap="diverging_1", description="Downloading: "):
                success = False
                while not success:
                    for f in remain_list:
                        if check_nc(f, print_messages=False):
                            count_dict["success"] += 1
                            success = True
                            remain_list.remove(f)
                            break

    count_dict["total"] = count_dict["success"] + count_dict["fail"] + count_dict["skip"] + count_dict["no_data"]
    print("[bold #ecdbfe]=" * mark_len)
    print(f"[bold #ff80ab]Total: {count_dict['total']}\nSuccess: {count_dict['success']}\nFail: {count_dict['fail']}\nSkip: {count_dict['skip']}\nNo data: {count_dict['no_data']}")
    print("[bold #ecdbfe]=" * mark_len)
    if count_dict["fail"] > 0:
        print("[bold #be5528]Please try again to download the failed data later.")
    if count_dict["no_data"] > 0:
        print(f"[bold #f90000]{count_dict['no_data']} data entries do not exist in any dataset or version.")
        for no_data in count_dict["no_data_list"]:
            print(f"[bold #d81b60]{no_data}")
    print("[bold #ecdbfe]=" * mark_len)


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

    options = {
        "variables": var_list,
        "start_time": "2018010100",
        "end_time": "2019063000",
        "output_dir": r"G:\Data\HYCOM\china_sea\hourly_24",
        "lon_min": 105,
        "lon_max": 135,
        "lat_min": 10,
        "lat_max": 45,
        "workers": 1,
        "overwrite": False,
        "depth": None,
        "level": None,
        "validate_time": None,
        # "idm_path": r"D:\Programs\Internet Download Manager\IDMan.exe",
        "interval_hours": 24,
        "proxy_txt": None,
    }

    if single_var:
        for var_name in var_list:
            options["variables"] = var_name
            download(**options)
    else:
        download(**options)
