import time
from datetime import datetime


def timestamp_to_datetime_str(timestamp: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    时间戳转 datetime 字符串
    :param timestamp: 时间戳
    :param fmt: 时间格式
    :return: 结果
    """
    return time.strftime(fmt, time.localtime(timestamp))


def datetime_str_change_fmt(
    time_str: str, prev_fmt: str, next_fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
    """
    时间字符串转换格式
    :param time_str: 时间字符串
    :param prev_fmt: 之前的格式
    :param next_fmt: 之后的格式
    :return: 结果
    """
    return datetime.strptime(time_str, prev_fmt).strftime(next_fmt)
