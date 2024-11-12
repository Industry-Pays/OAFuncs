#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-11-09 13:58:28
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-11-11 16:12:20
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_down\\refs_pdf.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
'''

import os
import random
import re
import time
from pathlib import Path

import pandas as pd
import requests
from rich import print
from rich.progress import track

__all__ = ['download5doi']


def _get_file_size(file_path, unit='KB'):
    # 检查文件是否存在
    if not os.path.exists(file_path):
        return "文件不存在"

    # 获取文件大小（字节）
    file_size = os.path.getsize(file_path)

    # 单位转换字典
    unit_dict = {
        'PB': 1024**5,
        'TB': 1024**4,
        'GB': 1024**3,
        'MB': 1024**2,
        'KB': 1024
    }

    # 检查传入的单位是否合法
    if unit not in unit_dict:
        return "单位不合法，请选择PB、TB、GB、MB、KB中的一个"

    # 转换文件大小到指定单位
    converted_size = file_size / unit_dict[unit]

    return converted_size


class _Downloader:
    '''
    根据doi下载文献pdf
    '''

    def __init__(self, doi, store_path):
        self.url_list = [r'https://sci-hub.se',
                         r'https://sci-hub.ren',
                         r'https://sci-hub.st',
                         r'https://sci-hub.ru',
                         ]
        self.base_url = None
        self.url = None
        self.doi = doi
        self.pdf_url = None
        self.pdf_path = None
        self.headers = {'User-Agent': self.get_ua().encode('utf-8')}
        # 10.1175/1520-0493(1997)125<0742:IODAOO>2.0.CO;2.pdf
        # self.fname = doi.replace(r'/', '_') + '.pdf'
        self.fname = re.sub(r'[/<>:"?*|]', '_', doi) + '.pdf'
        self.store_path = Path(store_path)
        self.fpath = self.store_path / self.fname
        self.wrong_record_file = self.store_path / 'wrong_record.txt'
        self.sleep = 5
        self.cookies = None
        self.check_size = 50
        self.url_index = 0
        self.try_times_each_url_max = 3
        self.try_times = 0

    def get_ua(self):
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
        return ua

    def get_pdf_url(self):
        print('[bold #E6E6FA]-'*100)
        print(f"DOI: {self.doi}")
        print(f"Requesting: {self.url}...")
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:
            self.cookies = response.cookies
            text = response.text.replace('\\', '')
            # text = text.replace(' ', '')  # It is important to remove the space
            # print(text)
            pattern = re.compile(
                r'onclick = "location.href=\'(.*?\.pdf\?download=true)\'"')
            match = pattern.search(text)
            if match:
                got_url = match.group(1)
                if r'http' not in got_url:
                    if got_url[:2] == '//':
                        self.pdf_url = 'https:' + got_url
                    else:
                        self.pdf_url = self.base_url + got_url
                else:
                    self.pdf_url = got_url
                print(f"URL: {self.pdf_url}")
            else:
                print(f'[bold #AFEEEE]The website {
                    self.url_list[self.url_index]} do not inlcude the PDF file.')
                self.try_times = self.try_times_each_url_max+1
        else:
            print(f"Failed to retrieve the webpage. Status code: {
                  response.status_code}")
            print(f'[bold #AFEEEE]The website {
                self.url_list[self.url_index]} do not inlcude the PDF file.')
            self.try_times = self.try_times_each_url_max+1

    def url_iterate(self):
        if self.url_index >= len(self.url_list):
            return
        url = self.url_list[self.url_index]
        self.base_url = url
        self.url = url + '/' + self.doi
        self.get_pdf_url()
        # for url in self.url_list:
        #     self.url = url + self.doi
        #     self.get_pdf_url()
        #     if self.pdf_url:
        #         break

    def write_wrong_record(self):
        with open(self.wrong_record_file, 'a') as f:
            f.write(self.doi + '\n')

    def download_pdf(self):
        if self.fpath.exists():
            fsize = _get_file_size(self.fpath, unit='KB')
            if fsize < self.check_size:
                # delete the wrong file
                os.remove(self.fpath)
                print(f"[bold yellow]The PDF file {
                      self.fpath} is only {fsize:.2f} KB. It will be deleted and retry.")
            else:
                print('[bold #E6E6FA]-'*100)
                print(f"[bold purple]The PDF file {
                      self.fpath} already exists.")
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
                response = requests.get(
                    self.pdf_url, headers=self.headers, cookies=self.cookies)
                if response.status_code == 200:
                    with open(self.fpath, 'wb') as f:
                        f.write(response.content)
                    fsize = _get_file_size(self.fpath, unit='KB')
                    if fsize < self.check_size:
                        # delete the wrong file
                        os.remove(self.fpath)
                        print(f"[bold yellow]The PDF file {
                              self.fpath} is only {fsize:.2f} KB. It will be deleted and retry.")
                    else:
                        print(f"[bold green]Sucessful to download {
                              self.fpath}")
                        already_downloaded = True
                else:
                    self.try_times = self.try_times_each_url_max+1
                    print(f"Failed to download the PDF file. Status code: {
                          response.status_code}")
                    print(f'[bold #AFEEEE]The website {
                        self.url_list[self.url_index]} do not inlcude the PDF file.')
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
                    print(f'Tried {self.try_times} times for {
                          self.url_list[self.url_index-1]}.')
                    print("Try another URL...")


def read_excel(file, col_name=r'DOI'):
    df = pd.read_excel(file)
    df_list = df[col_name].tolist()
    # 去掉nan
    df_list = [doi for doi in df_list if str(doi) != 'nan']
    return df_list


def read_txt(file):
    with open(file, 'r') as f:
        lines = f.readlines()
    # 去掉换行符以及空行
    lines = [line.strip() for line in lines if line.strip()]
    return lines


def download5doi(store_path=None, doi_list=None, txt_file=None, excel_file=None, col_name=r'DOI'):
    '''
    Description: Download PDF files by DOI.

    Args:
        store_path: str, The path to store the PDF files.
        doi_list: list or str, The list of DOIs.
        txt_file: str, The path of the txt file that contains the DOIs.
        excel_file: str, The path of the excel file that contains the DOIs.
        col_name: str, The column name of the DOIs in the excel file. Default is 'DOI'.

    Returns:
        None

    Example:
        download5doi(doi_list='10.3389/feart.2021.698876')
        download5doi(store_path=r'I:\Delete\ref_pdf', doi_list='10.3389/feart.2021.698876')
        download5doi(store_path=r'I:\Delete\ref_pdf', doi_list=['10.3389/feart.2021.698876', '10.3389/feart.2021.698876'])
        download5doi(store_path=r'I:\Delete\ref_pdf', txt_file=r'I:\Delete\ref_pdf\wrong_record.txt')
        download5doi(store_path=r'I:\Delete\ref_pdf', excel_file=r'I:\Delete\ref_pdf\wrong_record.xlsx')
        download5doi(store_path=r'I:\Delete\ref_pdf', excel_file=r'I:\Delete\ref_pdf\wrong_record.xlsx', col_name='DOI')
    '''
    if not store_path:
        store_path = Path.cwd()
    else:
        store_path = Path(str(store_path))
    store_path.mkdir(parents=True, exist_ok=True)
    store_path = str(store_path)

    # 如果doi_list是str，转换为list
    if isinstance(doi_list, str) and doi_list:
        doi_list = [doi_list]
    if txt_file:
        doi_list = read_txt(txt_file)
    if excel_file:
        doi_list = read_excel(excel_file, col_name)
    print(f"Downloading {len(doi_list)} PDF files...")
    for doi in track(doi_list, description='Downloading...'):
        download = _Downloader(doi, store_path)
        download.download_pdf()


if __name__ == '__main__':
    store_path = r'I:\Delete\ref_pdf'
    # download5doi(store_path, doi_list='10.1007/s00382-022-06260-x')
    download5doi(store_path, excel_file=r'I:\Delete\ref_pdf\savedrecs.xls')
