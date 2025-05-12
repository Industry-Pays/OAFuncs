#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-10-14 16:59:26
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2024-11-21 13:16:14
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_sign\\ocean.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''


import hashlib
import time
import warnings

import requests
from bs4 import BeautifulSoup
from rich import print

warnings.filterwarnings("ignore")

__all__ = ['sign_in_love_ocean']


def sign_in_love_ocean(email, password):
    '''
    吾爱海洋：https://www.52ocean.cn/
    email: str, 吾爱海洋的邮箱
    password: str, 吾爱海洋的密码
    '''
    def _get_login_hash():
        url = 'https://www.52ocean.cn/member.php?'
        para_login = {'mod': 'logging', 'action': 'login', 'infloat': 'yes',
                      'handlekey': 'login', 'inajax': '1', 'ajaxtarget': 'fwin_content_login'}
        response = s.get(url, params=para_login)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        login_hash = soup.find('form', attrs={'name': 'login'})['action'].split('loginhash=')[1]
        return login_hash

    def _get_login_formhash():
        url = 'https://www.52ocean.cn/member.php?'
        para_login = {'mod': 'logging', 'action': 'login', 'infloat': 'yes', 'handlekey': 'login', 'inajax': '1', 'ajaxtarget': 'fwin_content_login'}
        response = s.get(url, params=para_login)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        formhash = soup.find('input', attrs={'name': 'formhash'})['value']
        return formhash

    def _get_check_formhash():
        url = 'https://www.52ocean.cn/'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        formhash = soup.find('input', attrs={'name': 'formhash'})['value']
        return formhash

    def write_response(response, default_path=r'F:\response_吾爱海洋.txt'):
        with open(default_path, 'w', encoding='utf-8') as f:
            f.write('-'*350+'\n')
            f.write(time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime()) + '\n')
            f.write(response.text)
            f.write('-'*350+'\n')

    def _login():
        url = 'https://www.52ocean.cn/member.php?'
        mydata['password'] = hashlib.md5(mydata['password'].encode()).hexdigest()
        credentials = {
            'password': mydata['password'],
        }
        choose_login_ways = ['username', 'email']
        choose_login = choose_login_ways[1]
        credentials['selecti'] = choose_login_ways.index(choose_login)
        credentials['username'] = mydata[choose_login]
        query_params = {
            'mod': 'logging',
            'action': 'login',
            'loginsubmit': 'yes',
            'handlekey': 'login',
            'loginhash': _get_login_hash(),
            'inajax': '1',
        }
        from_data = {
            'formhash': _get_login_formhash(),
            'referer': 'https://www.52ocean.cn/',
            'loginfield': choose_login,
            'username': mydata[choose_login],
            'password': mydata['password'],
            'questionid': '0',
            'answer': '',
        }
        head = {
            'Origin': 'https://www.52ocean.cn',
            'Referer': 'https://www.52ocean.cn/member.php?',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        }
        response = s.post(url, params=query_params, data=from_data, headers=head)
        if '欢迎' in response.text:
            print('           [bold green]登录成功')
            try:
                rescookie = response.cookies
                cookie = requests.utils.dict_from_cookiejar(rescookie)
                return cookie
            except Exception as e:
                print('cookie 获取失败:', str(e))
        else:
            print('           [bold red]登录失败')

    def _check_in():
        url = 'https://www.52ocean.cn/plugin.php?id=zqlj_sign'
        query_params = {
            'sign': _get_check_formhash(),
        }
        head = {'X-Requested-With': 'XMLHttpRequest'}
        if cookie is not None:
            s.cookies.update(cookie)
        response = s.get(url, params=query_params, headers=head)
        response.raise_for_status()
        success_indicators = ['恭喜您，打卡成功！', '今日已打卡', '已经打过卡']
        if any(indicator in response.text for indicator in success_indicators):
            print('           [bold green]打卡完毕')
        else:
            print('           [bold red]打卡失败')

    def _get_info():
        url = 'https://www.52ocean.cn/plugin.php?id=zqlj_sign'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        sign_info = soup.find('ul', class_='xl xl1').find_all('li')
        print('[bold blue]-----------打卡动态-----------')
        for info in sign_info:
            k, v = info.get_text().split('：')
            if '当前' in k:
                k = k[2:]
            print(f'[bold blue]{k}:  [bold green]{v}')
        print('[bold blue]------------------------------')

    mydata = {'username': None, 'email': email, 'password': password}  # 不要修改关键字
    s = requests.Session()
    print('[bold purple]-----------吾爱海洋-----------')
    cookie = _login()
    _check_in()
    _get_info()
    s.close()


if __name__ == '__main__':
    # email = '16031215@qq.com'
    # password = 'xxxxx'
    # sign(email=email, password=password)
    pass
