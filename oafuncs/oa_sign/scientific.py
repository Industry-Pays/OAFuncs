#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-10-14 18:29:52
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-10-14 18:57:39
FilePath: \\Python\\My_Funcs\\OAFuncs\\OAFuncs\\oa_sign\\scientific.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''


import time

import requests
from bs4 import BeautifulSoup
from rich import print

__all__ = ['sign_in_scientific_research']


def sign_in_scientific_research(email, password):
    '''
    科研通：https://www.ablesci.com/
    email: str, 科研通的邮箱
    password: str, 科研通的密码
    '''
    def get_login_csrf():
        url = 'https://www.ablesci.com/site/login'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        csrf = soup.find('meta', attrs={'name': 'csrf-token'})['content']
        return csrf

    def write_response(response, default_path=r'F:\response_科研通.txt'):
        with open(default_path, 'w', encoding='utf-8') as f:
            f.write('-'*350+'\n')
            f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + '\n')
            f.write(response.text)
            f.write('-'*350+'\n')

    def login():
        url = 'https://www.ablesci.com/site/login'
        from_data = {
            '_csrf': get_login_csrf(),
            'email': mydata['email'],
            'password': mydata['password'],
            'remember': 'on'
        }
        head = {
            'Origin': 'https://www.ablesci.com',
            'Referer': 'https://www.ablesci.com/site/login',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest'
        }
        response = s.post(url, data=from_data, headers=head)
        if '登录成功' in response.text:
            print('           [bold green]已登录')
            try:
                rescookie = response.cookies
                cookie = requests.utils.dict_from_cookiejar(rescookie)
                return cookie
            except Exception as e:
                print('cookie 获取失败:', str(e))
        else:
            print('           [bold red]未登录')

    def check_in():
        url = 'https://www.ablesci.com/user/sign'
        if cookie is not None:
            s.cookies.update(cookie)
        response = s.get(url)
        response.raise_for_status()
        success_indicators = ['签到成功', '已连续签到', '本次获得']
        if any(indicator in response.text for indicator in success_indicators):
            print('           [bold green]已签到')
        else:
            url = 'https://www.ablesci.com/'
            response = s.get(url)
            response.raise_for_status()
            if '已连续签到' in response.text:
                print('           [bold green]已签到')
            else:
                print('           [bold red]未签到')

    def check_in_r():
        # 先检查是否已经签到
        url = 'https://www.ablesci.com/'
        if cookie is not None:
            s.cookies.update(cookie)
        response = s.get(url)
        response.raise_for_status()
        if '已连续签到' in response.text:
            print('           [bold green]已签到')
        else:
            url = 'https://www.ablesci.com/user/sign'
            response = s.get(url)
            response.raise_for_status()
            success_indicators = ['签到成功', '已连续签到', '本次获得']
            if any(indicator in response.text for indicator in success_indicators):
                print('           [bold green]已签到')
            else:
                print('           [bold red]未签到')

    def get_info():
        url = 'https://www.ablesci.com/'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        credit = soup.find('a', attrs={'class': 'signin-points'}).text
        continuous = soup.find('span', attrs={'class': 'signin-days'}).text
        info = {'积分': credit[4:], '连续签到': continuous[5:]}
        print('[bold blue]-----------签到录-----------')
        for k, v in info.items():
            if '积分' in k:
                k = '当前积分'
                v = v.split(' ')[-1]
            print(f'[bold blue]{k}:  [bold green]{v}')
        print('[bold blue]----------------------------')

    mydata = {'email': email, 'password': password}  # 不要修改关键字
    s = requests.Session()
    print('[bold purple]-----------科研通-----------')
    cookie = login()
    check_in()
    get_info()
    s.close()


if __name__ == '__main__':
    # email = '16031215@qq.com'
    # password = 'xxxxx'
    # sign_in_research_connect(email, password)
    pass
