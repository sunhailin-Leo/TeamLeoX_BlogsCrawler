from random import choice
from typing import Any, Dict, List, Tuple, Union, Optional, AbstractSet

import requests
from requests import Response
from requests_toolbelt import MultipartEncoder

from utils.async_task_utils import AsyncTaskHandler
from pipeline.mongodb_pipeline import MongoDBHandler
from pipeline.redis_pipeline import RedisPipelineHandler


# 爬虫 User-Agent 工具类
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


# 爬虫 Cookie 工具类
class CookieUtils:
    def __init__(self, cookie_list: AbstractSet[Tuple]):
        self._cookie_list = cookie_list

    def to_str(self) -> str:
        cookies: str = ""
        if len(self._cookie_list) > 0:
            for item in self._cookie_list:
                cookies += f"{item[0]}={item[1]}; "
        return cookies


# 爬虫操作枚举类
class BaseSpiderParseMethodType:
    LoginResult: str = "Login"
    PersonalBlogs: str = "PersonalBlogs"
    Finish: str = "Finish"


class BaseSpider:
    def __init__(self):
        self.data_model = BlogsDataModel()
        self._session = requests.Session()
        self._common_headers: Dict = {"User-Agent": UserAgentPool().get_user_agent()}

        self._redis_instance = RedisPipelineHandler()
        self._async_task = AsyncTaskHandler()

    @staticmethod
    def make_request(
        url: str,
        headers: dict,
        *,
        method: str = "GET",
        data: Union[str, dict, MultipartEncoder, None] = None,
        json: Union[str, dict, None] = None,
    ) -> Response:
        return requests.request(
            method=method, url=url, headers=headers, data=data, json=json
        )

    @staticmethod
    def make_request_with_session(
        session,
        url: str,
        headers: dict,
        *,
        method: str = "GET",
        data: Union[str, dict, MultipartEncoder, None] = None,
        json: Union[str, dict, None] = None,
    ) -> Response:
        return session.request(
            method=method, url=url, headers=headers, data=data, json=json
        )

    @staticmethod
    def get_default_headers() -> Dict:
        return {"User-Agent": UserAgentPool().get_user_agent()}

    def login(self):
        raise NotImplemented("登录方法必须实现!")

    def parse_data_with_method(self, method: str):
        raise NotImplemented("解析数据方法必须实现!")

    def _call_children_method(self, data: Optional[Any] = None):
        # 此处用 getattr 去实现父类调用子类的方法
        child_method = getattr(self, "_test_cookies")
        if data is None:
            return child_method()
        return child_method(data)

    def get_cookies(self, spider_name: str) -> Optional[str]:
        find_result = self._redis_instance.find_key(key=spider_name)
        if find_result is not None:
            # 测试这个 cookie 是否可用
            if self._call_children_method(data=find_result):
                # 在有 Cookie 的时候，重新启动时先调用 get_cookies -> self._call_children_method
                # 此时没有定时任务存在，因此需要插入一个定时任务探测 Cookie 的有效性
                self._async_task.make_async_scheduler_task_by_interval(
                    job_id=spider_name,
                    interval_seconds=200,
                    callback=self._call_children_method,
                )
                return find_result
            else:
                # TODO 当返回 False 的时候需要清空当前 spider_name 下的所有 key-value
                # TODO 然后通过 getattr 去调用 login 方法
                return None
        return None

    def set_cookies(self, spider_name: str, cookies: str) -> bool:
        is_insert = self._redis_instance.insert_key(key=spider_name, value=cookies)
        if is_insert:
            # 通过一个定时任务去定时轮训这个 cookie 是否有效
            self._async_task.make_async_scheduler_task_by_interval(
                job_id=spider_name,
                interval_seconds=200,
                callback=self._call_children_method,
            )
            return True
        else:
            return False

    def get_data(self, spider_name: str) -> Optional[str]:
        return self._redis_instance.find_key(key=spider_name)

    def set_data(self, spider_name: str, data: str) -> bool:
        return self._redis_instance.insert_key(key=spider_name, value=data)

    def send_data(self):
        # 发送数据
        self.data_model.push_data()

    def remove_cookie_scheduler(self, spider_name: str):
        pass

    def update_task_status(self, task_id: str, data: str) -> bool:
        return self._redis_instance.insert_key(key=f"spider_task:{task_id}", value=data)


# 数据封装类
class BlogsDataModel:
    def __init__(self):
        self._personal_data: dict = {}
        self._personal_blogs_data: dict = {}
        self._personal_like_blogs_data: dict = {}

        self._async_task = AsyncTaskHandler()
        self._mongo_instance = MongoDBHandler()
        self._mongo_collection_name: Dict = {
            "personal": "c_personal",
            "personalBlogs": "c_personal_blogs",
            "personalLikeBlogs": "c_personal_like_blogs",
        }

    def set_personal_data(self, data: dict):
        self._personal_data = data
        return self

    def set_personal_blogs_data(self, data: dict):
        self._personal_blogs_data = data
        return self

    def set_personal_like_blogs_data(self, data: dict):
        self._personal_like_blogs_data = data
        return self

    def _show_model(self):
        return {
            "personal": self._personal_data,
            "personalBlogs": self._personal_blogs_data,
            "personalLikeBlogs": self._personal_like_blogs_data,
        }

    def to_dict(self):
        return self._show_model()

    def _deal_mongo_index(self, col_name: str, is_unique: bool = True):
        index_query: List = []
        # [("索引字段名", 1)]
        if col_name == "c_personal":
            index_query = [("username", 1)]
        elif col_name == "c_personal_blogs":
            index_query = [("blogId", 1)]
        elif col_name == "c_personal_like_blogs":
            index_query = [("blogId", 1)]

        self._mongo_instance.get_mongo_instance()[col_name].create_index(
            index_query, unique=is_unique
        )

    def _deal_data(self) -> bool:
        for key, data in self.to_dict().items():
            col_name: str = self._mongo_collection_name[key]
            self._deal_mongo_index(col_name=col_name)

            if data != {} and data is not None:
                if isinstance(data, list):
                    self._mongo_instance.insert_many(col_name=col_name, doc_list=data)
                else:
                    self._mongo_instance.insert_one(col_name=col_name, doc=data)
        return True

    def push_data(self):
        self._async_task.make_async_task_by_thread(self._deal_data)
