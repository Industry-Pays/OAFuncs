#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-04-05 14:00:50
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-04-05 14:00:50
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\_script\\netcdf_modify.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import os

import netCDF4 as nc
import numpy as np
from rich import print


def _is_valid_netcdf_file(file_path):
    """
    Check if the file is a valid NetCDF file.
    """
    try:
        with nc.Dataset(file_path, "r") as _:
            pass
        return True
    except Exception:
        return False


def _modify_var(nc_file_path, variable_name, new_value):
    """
    Modify the value of a variable in a NetCDF file.
    """
    if not os.path.exists(nc_file_path):
        raise FileNotFoundError(f"NetCDF file '{nc_file_path}' does not exist.")
    if not _is_valid_netcdf_file(nc_file_path):
        raise ValueError(f"File '{nc_file_path}' is not a valid NetCDF file.")
    if not variable_name:
        raise ValueError("Variable name cannot be empty or None.")

    # 自动尝试将 new_value 转换为 numpy.ndarray
    if not isinstance(new_value, np.ndarray):
        try:
            new_value = np.array(new_value)
        except Exception:
            raise TypeError("New value must be a numpy.ndarray or convertible to numpy.ndarray.")

    try:
        with nc.Dataset(nc_file_path, "r+") as dataset:
            if variable_name not in dataset.variables:
                raise ValueError(f"Variable '{variable_name}' not found in the NetCDF file.")
            variable = dataset.variables[variable_name]
            if variable.shape != new_value.shape:
                try:
                    new_value = new_value.reshape(variable.shape)
                except ValueError:
                    raise ValueError(f"Shape mismatch: Variable '{variable_name}' has shape {variable.shape}, but new value has shape {new_value.shape}. Reshaping failed.")
            variable[:] = new_value
        print(f"[green]Successfully modified variable '{variable_name}' in '{nc_file_path}'.[/green]")
        return True
    except (FileNotFoundError, ValueError, TypeError) as e:
        print(f"[red]Error:[/red] {e}")
        return False
    except Exception as e:
        print(f"[red]Unexpected Error:[/red] Failed to modify variable '{variable_name}' in '{nc_file_path}'. [bold]Details:[/bold] {e}")
        return False


def _modify_attr(nc_file_path, variable_name, attribute_name, attribute_value):
    """
    Add or modify an attribute of a variable in a NetCDF file.
    """
    if not os.path.exists(nc_file_path):
        raise FileNotFoundError(f"NetCDF file '{nc_file_path}' does not exist.")
    if not _is_valid_netcdf_file(nc_file_path):
        raise ValueError(f"File '{nc_file_path}' is not a valid NetCDF file.")
    if not variable_name:
        raise ValueError("Variable name cannot be empty or None.")
    if not attribute_name:
        raise ValueError("Attribute name cannot be empty or None.")

    try:
        with nc.Dataset(nc_file_path, "r+") as ds:
            if variable_name not in ds.variables:
                raise ValueError(f"Variable '{variable_name}' not found in the NetCDF file.")
            variable = ds.variables[variable_name]
            variable.setncattr(attribute_name, attribute_value)
        print(f"[green]Successfully modified attribute '{attribute_name}' of variable '{variable_name}' in '{nc_file_path}'.[/green]")
        return True
    except (FileNotFoundError, ValueError) as e:
        print(f"[red]Error:[/red] {e}")
        return False
    except Exception as e:
        print(f"[red]Unexpected Error:[/red] Failed to modify attribute '{attribute_name}' of variable '{variable_name}' in file '{nc_file_path}'. [bold]Details:[/bold] {e}")
        return False


def modify_nc(nc_file, var_name, attr_name=None, new_value=None):
    """
    Modify the value of a variable or the value of an attribute in a NetCDF file.
    """
    try:
        if attr_name is None:
            return _modify_var(nc_file, var_name, new_value)
        else:
            return _modify_attr(nc_file, var_name, attr_name, new_value)
    except Exception as e:
        print(f"[red]Error:[/red] An error occurred while modifying '{var_name}' in '{nc_file}'. [bold]Details:[/bold] {e}")
        return False
