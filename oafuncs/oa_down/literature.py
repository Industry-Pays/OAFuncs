#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2024-11-28 10:42:56
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-01-05 10:51:42
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_down\\literature.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
from rich import print
from rich.progress import track
from oafuncs.oa_down.user_agent import get_ua
from oafuncs.oa_file import remove
from oafuncs.oa_data import ensure_list

__all__ = ["download5doi"]


def _get_file_size(file_path, unit="KB"):
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "文件不存在"

    # 获取文件大小（字节）
    file_size = os.path.getsize(file_path)

    # 单位转换字典
    unit_dict = {
        "PB": 1024**5,
        "TB": 1024**4,
        "GB": 1024**3,
        "MB": 1024**2,
        "KB": 1024,
    }

    # 检查传入的单位是否合法
    if unit not in unit_dict:
        return "单位不合法，请选择PB、TB、GB、MB、KB中的一个"

    # 转换文件大小到指定单位
    converted_size = file_size / unit_dict[unit]

    return converted_size


class _Downloader:
    """
    根据doi下载文献pdf
    """

    def __init__(self, doi, store_path):
        self.url_list = [
            r"https://sci-hub.se",
            r"https://sci-hub.ren",
            r"https://sci-hub.st",
            r"https://sci-hub.ru", # 最好用的一个网站
            # ------------------------------------- 以下网站没验证
            r"https://sci-hub.wf",
            r"https://sci-hub.yt",
            r"https://sci-hub.ee",
            r"https://sci-hub.cat",
            r"https://sci-hub.in",
            r"https://www.pismin.com",
            r"https://sci-hub.vkif.top",
            r"https://www.bothonce.com",
            r"https://sci-hub.et-fine.com",
            r"https://sci-hub.hkvisa.net",
            # r"https://sci-hub.3800808.com", # 这个只能手动保存
            r"https://sci-hub.zidianzhan.net",
            r"https://sci-hub.usualwant.com",
        ]
        self.base_url = None
        self.url = None
        self.doi = doi
        self.pdf_url = None
        self.pdf_path = None
        self.headers = {"User-Agent": get_ua().encode("utf-8")}
        # 10.1175/1520-0493(1997)125<0742:IODAOO>2.0.CO;2.pdf
        # self.fname = doi.replace(r'/', '_') + '.pdf'
        self.fname = re.sub(r'[/<>:"?*|]', "_", doi) + ".pdf"
        self.store_path = Path(store_path)
        self.fpath = self.store_path / self.fname
        self.wrong_record_file = self.store_path / "wrong_record.txt"
        self.sleep = 5
        self.cookies = None
        self.check_size = 50
        self.url_index = 0
        self.try_times_each_url_max = 3
        self.try_times = 0

    def get_pdf_url(self):
        print("[bold #E6E6FA]-" * 120)
        print(f"DOI: {self.doi}")
        print(f"Requesting: {self.url}...")
        try:
            response = requests.get(self.url, headers=self.headers)
            if response.status_code == 200:
                self.cookies = response.cookies
                text = response.text.replace("\\", "")
                # text = text.replace(' ', '')  # It is important to remove the space
                # print(text)
                pattern = re.compile(r'onclick = "location.href=\'(.*?\.pdf\?download=true)\'"')
                match = pattern.search(text)
                if match:
                    got_url = match.group(1)
                    if r"http" not in got_url:
                        if got_url[:2] == "//":
                            self.pdf_url = "https:" + got_url
                        else:
                            self.pdf_url = self.base_url + got_url
                    else:
                        self.pdf_url = got_url
                    print(f"URL: {self.pdf_url}")
                else:
                    print(f"[bold #AFEEEE]The website {self.url_list[self.url_index]} do not inlcude the PDF file.")
                    self.try_times = self.try_times_each_url_max + 1
            else:
                print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
                print(f"[bold #AFEEEE]The website {self.url_list[self.url_index]} do not inlcude the PDF file.")
                self.try_times = self.try_times_each_url_max + 1
        except Exception as e:
            print(f"Failed to retrieve the webpage. Error: {e}")
            self.try_times = self.try_times_each_url_max + 1

    def url_iterate(self):
        if self.url_index >= len(self.url_list):
            return
        url = self.url_list[self.url_index]
        self.base_url = url
        self.url = url + "/" + self.doi
        self.get_pdf_url()
        # for url in self.url_list:
        #     self.url = url + self.doi
        #     self.get_pdf_url()
        #     if self.pdf_url:
        #         break

    def write_wrong_record(self):
        # 先读取txt中的内容，如果已经存在则不再写入
        if self.wrong_record_file.exists():
            with open(self.wrong_record_file, "r") as f:
                lines = f.readlines()
            if self.doi in lines:
                return
        with open(self.wrong_record_file, "a") as f:
            f.write(self.doi + "\n")

    def download_pdf(self):
        if self.fpath.exists():
            fsize = _get_file_size(self.fpath, unit="KB")
            if fsize < self.check_size:
                # delete the wrong file
                os.remove(self.fpath)
                print(f"[bold yellow]The PDF file {self.fpath} is only {fsize:.2f} KB. It will be deleted and retry.")
            else:
                print("[bold #E6E6FA]-" * 120)
                print(f"[bold purple]The PDF file {self.fpath} already exists.")
                return
        self.url_index = 0
        already_downloaded = False
        self.try_times = 0
        while not already_downloaded:
            self.url_iterate()
            if not self.pdf_url:
                self.url_index += 1
                if self.url_index >= len(self.url_list):
                    print("Failed to download the PDF file.")
                    self.write_wrong_record()
                    return
                else:
                    self.try_times = 0
                    continue
            else:
                self.try_times += 1
            if self.try_times > self.try_times_each_url_max:
                self.url_index += 1
                if self.url_index >= len(self.url_list):
                    # print("Failed to download the PDF file.")
                    self.write_wrong_record()
                    return
            print(f"Downloading: {self.fname}...")
            try:
                response = requests.get(self.pdf_url, headers=self.headers, cookies=self.cookies)
                if response.status_code == 200:
                    with open(self.fpath, "wb") as f:
                        f.write(response.content)
                    fsize = _get_file_size(self.fpath, unit="KB")
                    if fsize < self.check_size:
                        # delete the wrong file
                        os.remove(self.fpath)
                        print(f"[bold yellow]The PDF file {self.fpath} is only {fsize:.2f} KB. It will be deleted and retry.")
                    else:
                        print(f"[bold green]Sucessful to download {self.fpath}")
                        already_downloaded = True
                else:
                    self.try_times = self.try_times_each_url_max + 1
                    print(f"Failed to download the PDF file. Status code: {response.status_code}")
                    print(f"[bold #AFEEEE]The website {self.url_list[self.url_index]} do not inlcude the PDF file.")
            except Exception as e:
                print(f"Failed to download the PDF file. Error: {e}")
            time.sleep(self.sleep)
            if self.try_times >= self.try_times_each_url_max:
                self.url_index += 1
                if self.url_index >= len(self.url_list):
                    print("\n[bold #CD5C5C]Failed to download the PDF file.")
                    self.write_wrong_record()
                    return
                if self.try_times == self.try_times_each_url_max:
                    print(f"Tried {self.try_times} times for {self.url_list[self.url_index-1]}.")
                    print("Try another URL...")


def _read_excel(file, col_name=r"DOI"):
    df = pd.read_excel(file)
    df_list = df[col_name].tolist()
    # 去掉nan
    df_list = [doi for doi in df_list if str(doi) != "nan"]
    return df_list


def _read_txt(file):
    with open(file, "r") as f:
        lines = f.readlines()
    # 去掉换行符以及空行
    lines = [line.strip() for line in lines if line.strip()]
    return lines


def download5doi(store_path=None, doi_list=None, txt_file=None, excel_file=None, col_name=r"DOI"):
    """
    Description:
        Download PDF files by DOI.

    Parameters:
        store_path: str, The path to store the PDF files.
        doi_list: list or str, The list of DOIs.
        txt_file: str, The path of the txt file that contains the DOIs.
        excel_file: str, The path of the excel file that contains the DOIs.
        col_name: str, The column name of the DOIs in the excel file. Default is 'DOI'.

    Returns:
        None

    Example:
        download5doi(doi_list='10.3389/feart.2021.698876')
        download5doi(store_path='I:\\Delete\\ref_pdf', doi_list='10.3389/feart.2021.698876')
        download5doi(store_path='I:\\Delete\\ref_pdf', doi_list=['10.3389/feart.2021.698876', '10.3389/feart.2021.698876'])
        download5doi(store_path='I:\\Delete\\ref_pdf', txt_file='I:\\Delete\\ref_pdf\\wrong_record.txt')
        download5doi(store_path='I:\\Delete\\ref_pdf', excel_file='I:\\Delete\\ref_pdf\\wrong_record.xlsx')
        download5doi(store_path='I:\\Delete\\ref_pdf', excel_file='I:\\Delete\\ref_pdf\\wrong_record.xlsx', col_name='DOI')
    """
    if not store_path:
        store_path = Path.cwd()
    else:
        store_path = Path(str(store_path))
    store_path.mkdir(parents=True, exist_ok=True)
    store_path = str(store_path)

    if doi_list:
        doi_list = ensure_list(doi_list)
    if txt_file:
        doi_list = _read_txt(txt_file)
    if excel_file:
        doi_list = _read_excel(excel_file, col_name)
    remove(Path(store_path) / "wrong_record.txt")
    print(f"Downloading {len(doi_list)} PDF files...")
    for doi in track(doi_list, description="Downloading..."):
        download = _Downloader(doi, store_path)
        download.download_pdf()


if __name__ == "__main__":
    store_path = r"F:\AAA-Delete\DOI_Reference\5\pdf"
    excel_file = r"F:\AAA-Delete\DOI_Reference\5\savedrecs.xls"
    download5doi(store_path, excel_file=excel_file)
