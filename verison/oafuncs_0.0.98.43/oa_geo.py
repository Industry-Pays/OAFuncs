
__all__ = ["earth_distance"]


def earth_distance(lon1, lat1, lon2, lat2):
    """
    计算两点间的距离（km）
    """
    from math import asin, cos, radians, sin, sqrt
    # 将经纬度转换为弧度
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine公式
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371  # 地球半径（公里）
    return c * r



if __name__ == "__main__":
    pass
