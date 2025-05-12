#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-03-27 16:51:26
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-04-05 14:17:07
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_python.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import os
from typing import List, Optional

from rich import print

__all__ = ["install_packages", "upgrade_packages"]


def install_packages(
    packages: Optional[List[str]] = None,
    python_executable: str = "python",
    package_manager: str = "pip",
) -> None:
    """
    Install the specified Python packages using the given package manager.

    Args:
        packages (Optional[List[str]]): A list of libraries to be installed. If None, no packages will be installed.
        python_executable (str): The Python executable to use (e.g., 'python312').
        package_manager (str): The package manager to use ('pip' or 'conda').

    Raises:
        ValueError: If 'packages' is not a list or None, or if 'package_manager' is not 'pip' or 'conda'.
    
    Example:
        >>> install_packages(packages=["numpy", "pandas"], python_executable="python", package_manager="pip")
    """
    if not isinstance(packages, (list, type(None))):
        raise ValueError("[red]The 'packages' parameter must be a list or None[/red]")

    if package_manager not in ["pip", "conda"]:
        raise ValueError("[red]The 'package_manager' parameter must be either 'pip' or 'conda'[/red]")

    if package_manager == "conda":
        if not packages:
            return
        try:
            package_count = len(packages)
            for i, package in enumerate(packages):
                os.system(f"conda install -c conda-forge {package} -y")
                print(f"[green]{'-' * 100}[/green]")
                print(f"[green]Successfully installed {package} ({i + 1}/{package_count})[/green]")
                print(f"[green]{'-' * 100}[/green]")
        except Exception as e:
            print(f"[red]Installation failed: {str(e)}[/red]")
        return

    os.system(f"{python_executable} -m ensurepip")
    os.system(f"{python_executable} -m pip install --upgrade pip")
    if not packages:
        return
    try:
        installed_packages = os.popen(f"{python_executable} -m pip list --format=freeze").read().splitlines()
        installed_packages = {pkg.split("==")[0].lower() for pkg in installed_packages}
        package_count = len(packages)
        for i, package in enumerate(packages):
            if package.lower() in installed_packages:
                print(f"[yellow]{package} is already installed[/yellow]")
                continue
            os.system(f"{python_executable} -m pip install {package}")
            print(f"[green]{'-' * 100}[/green]")
            print(f"[green]Successfully installed {package} ({i + 1}/{package_count})[/green]")
            print(f"[green]{'-' * 100}[/green]")
    except Exception as e:
        print(f"[red]Installation failed: {str(e)}[/red]")


def upgrade_packages(
    packages: Optional[List[str]] = None,
    python_executable: str = "python",
    package_manager: str = "pip",
) -> None:
    """
    Upgrade the specified Python packages using the given package manager.

    Args:
        packages (Optional[List[str]]): A list of libraries to be upgraded. If None, all installed packages will be upgraded.
        python_executable (str): The Python executable to use (e.g., 'python312').
        package_manager (str): The package manager to use ('pip' or 'conda').

    Raises:
        ValueError: If 'packages' is not a list or None, or if 'package_manager' is not 'pip' or 'conda'.
    
    Example:
        >>> upgrade_packages(packages=["numpy", "pandas"], python_executable="python", package_manager="pip")
    """
    if not isinstance(packages, (list, type(None))):
        raise ValueError("[red]The 'packages' parameter must be a list or None[/red]")

    if package_manager not in ["pip", "conda"]:
        raise ValueError("[red]The 'package_manager' parameter must be either 'pip' or 'conda'[/red]")

    try:
        if package_manager == "conda":
            if not packages:
                installed_packages = os.popen("conda list --export").read().splitlines()
                packages = [pkg.split("=")[0] for pkg in installed_packages if not pkg.startswith("#")]
            for package in packages:
                os.system(f"conda update -c conda-forge {package} -y")
            print("[green]Upgrade successful[/green]")
        else:
            if not packages:
                installed_packages = os.popen(f"{python_executable} -m pip list --format=freeze").read().splitlines()
                packages = [pkg.split("==")[0] for pkg in installed_packages]
            for package in packages:
                os.system(f"{python_executable} -m pip install --upgrade {package}")
            print("[green]Upgrade successful[/green]")
    except Exception as e:
        print(f"[red]Upgrade failed: {str(e)}[/red]")
