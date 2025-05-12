#!/usr/bin/env python
# coding=utf-8
'''
Author: Liu Kun && 16031215@qq.com
Date: 2024-10-14 16:14:50
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-04-04 20:37:13
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_sign\\meteorological.py
Description:  
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.11
'''


import warnings
from rich import print
from bs4 import BeautifulSoup
import requests
import time
import hashlib
warnings.filterwarnings("ignore")

__all__ = ['sign_in_meteorological_home']

def sign_in_meteorological_home(email, password):
    '''
    气象家园：http://bbs.06climate.com/
    email: str, 气象家园的邮箱
    password: str, 气象家园的密码
    '''
    def get_login_hash():
        url = 'http://bbs.06climate.com/member.php?mod=logging&action=login'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        login_hash = soup.find('form', attrs={'name': 'login'})['action'].split('loginhash=')[1]
        return login_hash

    def get_login_formhash():
        url = 'http://bbs.06climate.com/member.php?mod=logging&action=login'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        formhash = soup.find('input', attrs={'name': 'formhash'})['value']
        return formhash

    def get_check_formhash():
        url = 'http://bbs.06climate.com/'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        formhash = soup.find('input', attrs={'name': 'formhash'})['value']
        return formhash

    def write_response(response, default_path=r'F:\response_气象家园.txt'):
        with open(default_path, 'w', encoding='utf-8') as f:
            f.write('-'*350+'\n')
            f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + '\n')
            f.write(response.text)
            f.write('-'*350+'\n')

    def login():
        url = 'http://bbs.06climate.com/member.php?'
        # 登录密码需要转码
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
            'loginhash': get_login_hash(),
            'inajax': '1',
        }
        from_data = {
            'formhash': get_login_formhash(),
            'referer': 'http://bbs.06climate.com/',
            'loginfield': choose_login,
            'username': mydata[choose_login],
            'password': mydata['password'],
            'questionid': '0',
            'answer': '',
        }
        head = {
            'Host': 'bbs.06climate.com',
            'Origin': 'http://bbs.06climate.com',
            'Referer': 'http://bbs.06climate.com/member.php?mod=logging&action=login',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
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

    def check_in():
        url = 'http://bbs.06climate.com/plugin.php?'
        query_params = {
            'id': 'dsu_amupper',
            'ppersubmit': 'true',
            'formhash': get_check_formhash(),
            'infloat': 'yes',
            'handlekey': 'dsu_amupper',
            'inajax': '1',
            'ajaxtarget': 'fwin_content_dsu_amupper'
        }
        head = {'X-Requested-With': 'XMLHttpRequest'}
        if cookie is not None:
            s.cookies.update(cookie)
        response = s.get(url, params=query_params, headers=head)
        response.raise_for_status()
        success_indicators = ['累计签到', '连续签到', '特奖励', '明日签到', '另奖励', '连续签到', '再连续签到', '奖励', '签到完毕']
        if any(indicator in response.text for indicator in success_indicators):
            print('           [bold green]签到完毕')
        else:
            print('           [bold red]签到失败')

    def get_info():
        url = 'http://bbs.06climate.com/'
        response = s.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        credit = soup.find('a', attrs={'id': 'extcreditmenu'}).text
        user_group = soup.find('a', attrs={'id': 'g_upmine'}).text
        cumulate = soup.select('.pperwbm .times')[0].text
        continuous = soup.select('.pperwbm .times')[1].text
        last_sign = soup.select('.pperwbm .times')[2].text
        info = {credit.split(': ')[0]: credit.split(':')[1], user_group.split(': ')[0]: user_group.split(':')[1], '累计签到': cumulate+'次', '连续签到': continuous+'次', '上次签到': last_sign}

        print('[bold blue]-----------签到信息-----------')
        for k, v in info.items():
            if '积分' in k:
                k = '当前积分'
                v = v.split(' ')[-1]
            if '用户组' in k:
                k = '现用户组'
                v = v.split(' ')[-1]
            print(f'[bold blue]{k}:  [bold green]{v}')
        print('[bold blue]------------------------------')

    mydata = {'username': None, 'email': email, 'password': password}
    s = requests.Session()
    print('[bold purple]-----------气象家园-----------')
    cookie = login()
    check_in()
    get_info()
    s.close()



if __name__ == '__main__':
    # email = '16031215@qq.com'
    # password = 'xxxxx'
    # sign(email=email, password=password)
    pass