#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-04-04 20:21:59
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-04-04 20:21:59
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\_script\\email.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""




import random
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from rich import print

__all__ = ["send"]


def _email_info():
    email_dict = {
        "liukun0312@vip.qq.com": [4, 13, -10, 2, -10, 4, -7, -8, 8, -1, 3, -2, -11, -6, -9, -7],
        "756866877@qq.com": [4, -2, -3, 13, 12, 8, -6, 9, -12, 13, -10, -12, -11, -12, -4, -11],
        "99138763@qq.com": [0, 6, 12, 2, 9, 9, 4, -1, 11, -7, -12, 6, -11, -3, -5, -11],
        "1031260@qq.com": [-1, -5, -9, 9, -3, 4, -8, -7, -12, -2, 0, -9, -11, -3, -7, -10],
    }
    keys = list(email_dict.keys())
    choose_email = random.randint(0, len(keys) - 1)
    msg_from = keys[choose_email]
    return msg_from, email_dict[msg_from]


def _decode_password(password):
    return "".join([chr(i + 109) for i in password])


def _send_message(title, content, msg_to):
    # 1. 连接邮箱服务器
    con = smtplib.SMTP_SSL("smtp.qq.com", 465)

    # 2. 登录邮箱
    msg_from, password = _email_info()
    con.login(msg_from, _decode_password(password))

    # 3. 准备数据
    # 创建邮件对象
    msg = MIMEMultipart()

    # 设置邮件主题
    subject = Header(title, "utf-8").encode()
    msg["Subject"] = subject

    # 设置邮件发送者
    msg["From"] = msg_from

    # 设置邮件接受者
    msg["To"] = msg_to

    # # 添加html内容
    # content = """
    # <h2>我是正文中的标题</h2>
    # <p>邮件正文描述性文字1</p>
    # <p>邮件正文描述性文字2</p>
    # <img src='https://www.baidu.com/img/bd_logo1.png'>
    # <center>百度图片</center>
    # <a href='https://www.baidu.com'>百度一下</a>
    # """
    # html = MIMEText(content, 'html', 'utf-8')
    # msg.attach(html)

    # or
    # content = '发送内容'
    msg.attach(MIMEText(content, "plain", "utf-8"))

    # 4.发送邮件
    con.sendmail(msg_from, msg_to, msg.as_string())
    con.quit()

    print(f"已通过{msg_from}成功向{msg_to}发送邮件！")
    print("发送内容为：\n{}\n\n".format(content))


def send(title="Title", content=None, send_to="16031215@qq.com"):
    """
    Description: 发送邮件

    Args:
        title: 邮件标题
        content: 邮件内容
        send_to: 发送对象

    Returns:
        None

    Example:
        send(title='Title', content='Content', '123@qq.com')
    """
    if content is None:
        # 避免发送空邮件，或有人误调用
        return
    else:
        _send_message(title, content, send_to)


if __name__ == "__main__":
    send()
