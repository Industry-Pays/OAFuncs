#!/usr/bin/env python
# coding=utf-8
"""
Author: Liu Kun && 16031215@qq.com
Date: 2025-03-09 16:31:45
LastEditors: Liu Kun && 16031215@qq.com
LastEditTime: 2025-03-09 16:31:45
FilePath: \\Python\\My_Funcs\\OAFuncs\\oafuncs\\oa_model\\wrf\\little_r.py
Description:
EditPlatform: vscode
ComputerInfo: XPS 15 9510
SystemInfo: Windows 11
Python Version: 3.12
"""

__all__ = ["header_record", "data_record", "ending_record", "tail_record"]

import sys


def header_record(Latitude, Longitude, ID, Platform, Elevation, Bogus, Date, SLP, name):
    """
    Latitude  : F20.5 纬度，浮点数，总共20位，小数点后保留5位
    Lontitude : F20.5 经度，浮点数，总共20位，小数点后保留5位
    Platform  : A40 FM 编码的浮标编号，总共40位
    Elevation : F20.5  浮标高度，单位为米，浮点数，总共20位，小数点后保留5位
    Bogus     : logical 标志数据是否有效，True为无效，False为有效
    Date      : A20 日期，总共20位
    """
    # 存放header record的字典
    dict_header = {}
    dict_header["Latitude"] = str_F20p5(Latitude)
    dict_header["Longitude"] = str_F20p5(Longitude)
    dict_header["ID"] = str_A40_Front_Space(ID)
    dict_header["Name"] = str_A40_Front_Space(name)
    dict_header["Platform"] = str_A40_Front_Space(Platform)
    dict_header["Source"] = "                                     N/A"  # A40
    dict_header["Elevation"] = str_F20p5(Elevation)
    dict_header["ValidFields"] = "         1"  # I10
    dict_header["NumErrors"] = "   -888888"  # I10
    dict_header["NumWarnings"] = "   -888888"  # I10
    dict_header["SequenceNumber"] = "       890"  # I10
    dict_header["NumDuplicates"] = "   -888888"  # I10
    dict_header["IsSounding"] = "         F"  # logical 10
    dict_header["IsBogus"] = str_L10(Bogus)
    dict_header["Discard"] = "         F"  # logical 10
    dict_header["UnixTime"] = "   -888888"  # I10
    dict_header["JulianDay"] = "   -888888"  # I10
    dict_header["Date"] = str_A20_Behind_Space(Date)
    dict_header["SLP-QC"] = str_F13p5(SLP) + "      0"  # F13.5 I7
    dict_header["RefPressure-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["GroundTemp-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["SST-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["SFCPressure-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["Precip-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["DailyMaxT-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["DailyMinT-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["NightMinT-TC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["3hrPresChange-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["24hrChange-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["CloudCover-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["Ceiling-QC"] = "-888888.00000      0"  # F13.5 I7
    dict_header["PrecipitableWater-QC"] = "-888888.00000      0"  # F13.5 I7

    # 生成文件头的字符串，固定长度为620
    header_str = ""
    for iKey in dict_header.keys():
        header_str = header_str + dict_header[iKey]
    if len(header_str) != 620:
        print("Error: The header record len =", len(header_str), ",The correct length should be 620!")
        sys.exit(1)
    return header_str


def data_record(Pressure, Height, Temperature, DewPoint, WindSpeed, WindDirection, WindU, WindV, RelativeHumidity, Thickness):
    """
    Pressure         : F13.5, Pa
    Height           : F13.5, m
    Temperature      : F13.5, K
    DewPoint         : F13.5, K
    WindSpeed        : F13.5, m/s
    WindDirection    : F13.5, deg
    WindU            : F13.5, m/s
    WindV            : F13.5, m/s
    RelativeHumidity : F13.5, %
    Thickness        : F13.5, m
    """
    dict_data = {}
    dict_data["Pressure"] = str_F13p5(Pressure)  # F13.5
    dict_data["QC1"] = "      0"  # I7
    dict_data["Height"] = str_F13p5(Height)  # F13.5
    dict_data["QC2"] = "      0"  # I7
    dict_data["Temperature"] = str_F13p5(Temperature)  # F13.5
    dict_data["QC3"] = "      0"  # I7
    dict_data["DewPoint"] = str_F13p5(DewPoint)  # F13.5
    dict_data["QC4"] = "      0"  # I7
    dict_data["WindSpeed"] = str_F13p5(WindSpeed)  # F13.5
    dict_data["QC5"] = "      0"  # I7
    dict_data["WindDirection"] = str_F13p5(WindDirection)  # F13.5
    dict_data["QC6"] = "      0"  # I7
    dict_data["WindU"] = str_F13p5(WindU)  # F13.5
    dict_data["QC7"] = "      0"  # I7
    dict_data["WindV"] = str_F13p5(WindV)  # F13.5
    dict_data["QC8"] = "      0"  # I7
    dict_data["RelativeHumidity"] = str_F13p5(RelativeHumidity)  # F13.5
    dict_data["QC9"] = "      0"  # I7
    dict_data["Thickness"] = str_F13p5(Thickness)  # F13.5
    dict_data["QC10"] = "      0"  # I7

    # 生成数据记录，固定长度为200
    data_str = ""
    for iKey in dict_data.keys():
        data_str = data_str + dict_data[iKey]
    if len(data_str) != 200:
        print("Error: The data record len =", len(data_str), ",The correct length should be 200!")
        sys.exit(1)
    return data_str


def ending_record():
    ending_str = "-777777.00000      0-777777.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0-888888.00000      0"
    return ending_str


def tail_record(ValidFields):
    """
    ValidFields : integer
    """
    NumErrors = "      0"
    NumWarnings = "      0"
    tail_str = str_I7(ValidFields) + NumErrors + NumWarnings
    if len(tail_str) != 21:
        print("Error: The tail record len =", len(tail_str), ",The correct length should be 21!")
        sys.exit(1)
    return tail_str


# 将浮点数格式化为长度为13位，小数点后保留5位的字符串，并在前面添加合适的空格
def str_F13p5(float):
    a = "%.5f" % float
    space = " " * (13 - len(a))
    return space + str(a)


# 将浮点数格式化为长度为20位，小数点后保留5位的字符串，并在前面添加合适的空格
def str_F20p5(float):
    a = "%.5f" % float
    space = " " * (20 - len(a))
    return space + str(a)


# 将字符串格式化为长度为40位的字符串，并在前面添加合适的空格。如果原始字符串超过了40位，会将其截断为前40位。
def str_A40_Front_Space(string):
    # valid string in Front of space
    string0 = str(string).strip()
    space = " " * (40 - len(string0))
    return string0 + space


# 将字符串格式化为长度为20位的字符串，并在后面添加合适的空格。如果原始字符串超过了20位，会将其截断为前20位。
def str_A20_Behind_Space(string):
    # valid string Behind space
    string0 = str(string).strip()
    space = " " * (20 - len(string0))
    return space + string0


# 将整数格式化为长度为10位的字符串，并在前面添加合适的空格
def str_I10(int0):
    space = " " * (10 - len(int0))
    return space + str(int0)


# 将整数格式化为长度为7位的字符串，并在前面添加合适的空格
def str_I7(int0):
    space = " " * (7 - len(str(int0)))
    return space + str(int0)


# 将布尔值格式化为长度为10位的字符串，如果为True则返回字符串'         T'，如果为False则返回字符串'         F'
def str_L10(logical):
    if logical:
        string = "         T"
    else:
        string = "         F"
    return string
