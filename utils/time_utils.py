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


def handle_different_time_str(time_str: str) -> str:
    if "今天" in time_str:
        return datetime_str_change_fmt(
            time_str=f"{datetime.now().strftime('%Y-%m-%d')} {time_str.split(' ')[-1]}",
            prev_fmt="%Y-%m-%d %H:%M"
        )
    elif "月" in time_str:
        year_str: int = datetime.now().year
        return datetime_str_change_fmt(
            time_str=f"{year_str}年{time_str}",
            prev_fmt="%Y年%m月%d日",
        )
    else:
        return datetime_str_change_fmt(time_str=time_str, prev_fmt="%Y-%m-%d")
