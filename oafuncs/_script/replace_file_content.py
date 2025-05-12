#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-03-21 10:02:32
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-03-21 10:02:33
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\_script\\replace_file_concent.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import datetime
import os
import re
from pathlib import Path

from rich import print


def _prepare_file_operation(source_file, target_dir, new_name=None):
    """
    准备文件操作的公共逻辑

    参数:
    source_file: 源文件路径
    target_dir: 目标目录路径
    new_name: 新文件名，如果为None则使用原文件名

    返回:
    target_file: 目标文件路径
    """
    os.makedirs(target_dir, exist_ok=True)
    if new_name is None:
        return os.path.join(target_dir, os.path.basename(source_file))
    else:
        return os.path.join(target_dir, new_name)


def replace_config_values(source_file, target_dir, param_dict, new_name=None):
    """
    批量修改配置参数并保存到新路径（适用于等号赋值格式的参数）

    参数：
    source_file: 源文件路径
    target_dir: 目标目录路径
    param_dict: 要修改的参数字典 {参数名: 新值}
    new_name: 新文件名，如果为None则使用原文件名

    返回:
    set: 成功修改的参数集合
    """
    try:
        target_file = _prepare_file_operation(source_file, target_dir, new_name)

        with open(source_file, "r") as f:
            lines = f.readlines()

        modified = set()
        for i in range(len(lines)):
            line = lines[i]
            stripped = line.lstrip()

            # 跳过注释行和空行
            if stripped.startswith(("!", "#", ";", "%")) or not stripped.strip():
                continue

            # 匹配所有参数
            for param, new_val in param_dict.items():
                # 构造动态正则表达式
                pattern = re.compile(r'^(\s*{})(\s*=\s*)([\'"]?)(.*?)(\3)(\s*(!.*)?)$'.format(re.escape(param)), flags=re.IGNORECASE)

                match = pattern.match(line.rstrip("\n"))
                if match and param not in modified:
                    # 构造新行（保留原始格式）
                    new_line = f"{match.group(1)}{match.group(2)}{match.group(3)}{new_val}{match.group(5)}{match.group(6) or ''}\n"
                    lines[i] = new_line
                    modified.add(param)
                    break  # 每行最多处理一个参数

        with open(target_file, "w") as f:
            f.writelines(lines)

        print(f"[green]已将参数替换到新文件：{target_file}[/green]")
        return modified
    except Exception as e:
        print(f"[red]替换参数时出错：{str(e)}[/red]")
        return set()


def replace_direct_content(source_file, target_dir, content_dict, key_value=False, new_name=None):
    """
    直接替换文件中的指定内容并保存到新路径

    参数：
    source_file: 源文件路径
    target_dir: 目标目录路径
    content_dict: 要替换的内容字典 {旧内容: 新内容}
    key_value: 是否按键值对方式替换参数
    new_name: 新文件名，如果为None则使用原文件名

    返回:
    bool: 替换是否成功
    """
    try:
        if key_value:
            return len(replace_config_values(source_file, target_dir, content_dict, new_name)) > 0

        target_file = _prepare_file_operation(source_file, target_dir, new_name)

        with open(source_file, "r") as f:
            content = f.read()

        # 直接替换指定内容
        for old_content, new_content in content_dict.items():
            content = content.replace(old_content, new_content)

        with open(target_file, "w") as f:
            f.write(content)

        print(f"[green]已将内容替换到新文件：{target_file}[/green]")
        return True
    except Exception as e:
        print(f"[red]替换内容时出错：{str(e)}[/red]")
        return False


if __name__ == "__main__":
    control_file = Path(r"/data/hejx/liukun/Work/Model/cas_esm/data/control_file")
    target_dir = r"/data/hejx/liukun/Work/Model/cas_esm/run"

    force_time = 2023072900
    ini_time = datetime.datetime.strptime(str(force_time), "%Y%m%d%H")
    oisst_time = ini_time - datetime.timedelta(days=1)  # 需要在前一天

    replace_config_values(source_file=Path(r"/data/hejx/liukun/Work/Model/cas_esm/data/control_file") / "atm_in", target_dir=target_dir, param_dict={"ncdata": f"/data/hejx/liukun/Work/Model/cas_esm/data/IAP_ncep2_181x360_{ini_time.strftime('%Y%m%d')}_00_00_L35.nc"})

    replace_direct_content(source_file=Path(r"/data/hejx/liukun/Work/Model/cas_esm/data/control_file") / "docn.stream.txt", target_dir=target_dir, content_dict={"oisst.forecast.20230727.nc": f"oisst.forecast.{oisst_time.strftime('%Y%m%d')}.nc"})

    replace_config_values(source_file=Path(r"/data/hejx/liukun/Work/Model/cas_esm/data/control_file") / "drv_in", target_dir=target_dir, param_dict={"start_ymd": f"{ini_time.strftime('%Y%m%d')}"})

    replace_config_values(source_file=Path(r"/data/hejx/liukun/Work/Model/cas_esm/data/control_file") / "ice_in", target_dir=target_dir, param_dict={"stream_fldfilename": f"/data/hejx/liukun/Work/Model/cas_esm/data/oisst.forecast.{ini_time.strftime('%Y%m%d')}.nc"})

    replace_config_values(
        source_file=Path(r"/data/hejx/liukun/Work/Model/cas_esm/data/control_file") / "lnd_in",
        target_dir=target_dir,
        param_dict={"fini": f"/data/hejx/liukun/Work/Model/cas_esm/run_p1x1/colm-spinup-colm-restart-{ini_time.strftime('%Y-%m-%d')}-00000", "fsbc": f"/data/hejx/liukun/Work/Model/cas_esm/run_p1x1/colm-spinup-colm-restart-{ini_time.strftime('%Y-%m-%d')}-00000-sbc"},
    )
