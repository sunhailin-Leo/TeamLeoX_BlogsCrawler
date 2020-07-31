import re
import json
from typing import Optional

# 字符串正则规则
phone_number_pattern = r"[1][^1269]\d{9}"
email_address_pattern = r"[^\._][\w\._-]+@(?:[A-Za-z0-9]+\.)+[A-Za-z]+$"


def _check_string_is_match_pattern(data: str, re_pattern: str) -> Optional[str]:
    """
    校验字符串是否匹配正则表达式
    :param data: 字符串
    :param re_pattern: 正则表达式变量
    :return: 结果
    """
    p = re.compile(re_pattern)
    match_result = p.match(data)
    return data if match_result else None


def check_is_phone_number(data: Optional[str]) -> Optional[str]:
    """
    校验字符串是否为手机号
    :param data: 字符串
    :return: 结果
    """
    if data is None:
        raise ValueError("Method parameters can not be None!")
    else:
        return _check_string_is_match_pattern(
            data=data, re_pattern=phone_number_pattern
        )


def check_is_email_address(data: Optional[str]) -> Optional[str]:
    """
    校验字符串是否为邮件地址
    :param data: 字符串
    :return: 结果
    """
    if data is None:
        raise ValueError("Method parameters can not be None!")
    else:
        return _check_string_is_match_pattern(
            data=data, re_pattern=email_address_pattern
        )


def check_is_json(data: Optional[str]) -> bool:
    """
    校验字符串是否为 json 格式
    :param data: 字符串
    :return: 结果
    """
    if data is None:
        raise ValueError("Method parameters can not be None!")
    else:
        try:
            json.loads(data)
        except ValueError:
            return False
        return True


def str_to_lower(data: str) -> str:
    """
    将数据中的字符换成小写
    :param data: 字符串
    :return: 结果
    """
    return data.lower()
