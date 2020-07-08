from random import choice
from typing import AbstractSet, Optional, Dict, List, Tuple, Union

import requests
from requests import Response


class UserAgentPool:
    def __init__(self):
        self._ua_list: List = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15",
        ]

    def get_user_agent(self) -> str:
        return choice(self._ua_list)


class CookieUtils:
    def __init__(self, cookie_list: AbstractSet[Tuple]):
        self._cookie_list = cookie_list

    def to_str(self) -> str:
        cookies: str = ""
        if len(self._cookie_list) > 0:
            for item in self._cookie_list:
                cookies += f"{item[0]}={item[1]}; "
        return cookies


class BaseSpider:
    def __init__(self):
        self._common_headers: Dict = {"User-Agent": UserAgentPool().get_user_agent()}

    @staticmethod
    def make_request(
        url: str,
        headers: dict,
        *,
        method: str = "GET",
        data: Union[str, dict, None] = None,
        json: Union[str, dict, None] = None
    ) -> Response:
        return requests.request(method=method, url=url, headers=headers, data=data, json=json)

    def login(self):
        raise NotImplemented("登录方法必须实现!")

    def parse_data(self):
        pass

    def parse_data_with_method(self, method: str):
        pass


class BaseSpiderParseMethodType:
    LoginResult: str = "Login"
    PersonalBlogs: str = "PersonalBlogs"


