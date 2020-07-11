import time
from typing import Dict, List, Tuple, Optional

from config import LOG_LEVEL
from utils.logger_utils import LogManager
from utils.time_utils import datetime_str_change_fmt
from utils.exception_utils import LoginException, ParseDataException
from spiders import BaseSpider, BaseSpiderParseMethodType, CookieUtils
from utils.str_utils import check_is_phone_number, check_is_email_address

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)


class JuejinSpider(BaseSpider):
    def __init__(self, username: str, password: str):
        self._main_url = "https://juejin.im/auth/type"
        self._blogs_url = "https://timeline-merger-ms.juejin.im/v1/get_entry_by_self"
        self._like_blogs_url = "https://user-like-wrapper-ms.juejin.im/v1/user"

        self._login_username = username
        self._login_password = password

        self._login_cookies: Optional[str] = None
        self._login_token: Optional[str] = None
        self._login_uid: Optional[str] = None
        self._login_client_id: Optional[str] = None

        self._response_data = None

        self._blogs_data: List = []
        self._like_blogs_data: List = []
        self._like_blogs_total_page: int = 0

        super().__init__()

    def _check_username(self) -> Optional[Tuple[str, Dict]]:
        """
        解析用户名
        :return: 结果
        """
        phone_login = check_is_phone_number(data=self._login_username)
        email_login = check_is_email_address(data=self._login_username)
        login_data: Dict = {"password": self._login_password}

        if phone_login is None and email_login is None:
            raise ValueError("Your login username is illegal!")

        if phone_login is not None:
            login_data.update(phoneNumber=self._login_username)
            return f"{self._main_url}/phoneNumber", login_data

        if email_login is not None:
            login_data.update(email=self._login_username)
            return f"{self._main_url}/email", login_data

        return None

    def parse_data_with_method(self, method: str):
        if method == BaseSpiderParseMethodType.LoginResult:
            self._parse_login_data()
        elif method == BaseSpiderParseMethodType.PersonalBlogs:
            self._parse_personal_blogs()
            self._parse_personal_like_blogs()

    def login(self):
        login_url, login_data = self._check_username()
        response = self.make_request(
            url=login_url, headers=self._common_headers, method="POST", json=login_data
        )
        if response.content.decode() != "":
            logger.info("登录成功!")
            self._response_data = response.json()
            self._login_cookies = CookieUtils(
                cookie_list=response.cookies.items()
            ).to_str()
            logger.debug(self._login_cookies)
            self.parse_data_with_method(method=BaseSpiderParseMethodType.LoginResult)
        else:
            logger.error("登录失败!")
            raise LoginException()

    def _parse_login_data(self):
        # 公共参数
        self._login_token = self._response_data["token"]
        self._login_uid = self._response_data["userId"]
        self._login_client_id = self._response_data["clientId"]

        # 个人数据
        username = self._response_data["user"]["username"]
        description = self._response_data["user"]["selfDescription"]
        avatar_img = self._response_data["user"]["avatarLarge"]
        followee = self._response_data["user"]["followeesCount"]
        follower = self._response_data["user"]["followersCount"]
        like_blogs = self._response_data["user"]["collectedEntriesCount"]

        personal_data: Dict = {
            "username": username,
            "description": description,
            "avatarImg": avatar_img,
            "followee": followee,
            "follower": follower,
            "likeBlogs": like_blogs,
        }
        # TODO 推送数据
        logger.debug(personal_data)
        self.parse_data_with_method(method=BaseSpiderParseMethodType.PersonalBlogs)

    def _parse_personal_blogs(self, next_params: Optional[str] = None):
        req_data: dict = {
            "src": "web",
            "uid": self._login_uid,
            "device_id": self._login_client_id,
            "token": self._login_token,
            "targetUid": self._login_uid,
            "type": "post",
            "limit": "20",
            "order": "createdAt",
        }
        if next_params is not None:
            req_data.update(before=next_params)

        url_params: str = ""
        for index, data in enumerate(req_data.items()):
            if index == 0:
                url_params += f"?{data[0]}={data[1]}"
            else:
                url_params += f"&{data[0]}={data[1]}"
        blogs_url: str = f"{self._blogs_url}{url_params}"
        response = self.make_request(url=blogs_url, headers=self._common_headers)
        if response.content.decode() != "":
            self._response_data = response.json()
            if self._response_data is not None and self._response_data["m"] == "ok":
                next_page_variable = None
                entry_list = self._response_data["d"]["entrylist"]
                if len(entry_list) > 0:
                    for personal_blog in entry_list:
                        blog_create_time = datetime_str_change_fmt(
                            time_str=personal_blog["createdAt"],
                            prev_fmt="%Y-%m-%dT%H:%M:%S.%fZ",
                        )

                        blog_data: Dict = {
                            "blogId": personal_blog["objectId"],
                            "blogTitle": personal_blog["title"],
                            "blogHref": personal_blog["originalUrl"],
                            "blogViewers": personal_blog["viewsCount"],
                            "blogCreateTime": blog_create_time,
                        }
                        self._blogs_data.append(blog_data)
                        next_page_variable = personal_blog["verifyCreatedAt"]

                if self._response_data["d"]["total"] > 20:
                    time.sleep(0.5)
                    self._parse_personal_blogs(next_params=next_page_variable)
                else:
                    # TODO 推送数据
                    logger.debug(self._blogs_data)
                    logger.info("获取个人博客数据成功!")
        else:
            logger.error("查询个人博客失败!")
            raise LoginException()

    def _parse_personal_like_blogs(self, page_no: int = 0):
        like_blogs_url: str = f"{self._like_blogs_url}/{self._login_uid}/like/entry?page={page_no}&pageSize=20"
        self._common_headers.update(
            {
                "X-Juejin-Client": str(self._login_client_id),
                "X-Juejin-Src": "web",
                "X-Juejin-Token": self._login_token,
                "X-Juejin-Uid": self._login_uid,
            }
        )
        response = self.make_request(url=like_blogs_url, headers=self._common_headers)
        if response.content.decode() != "":
            self._response_data = response.json()
            if (
                self._response_data is not None
                and self._response_data["m"] == "success"
            ):
                logger.info(f"当前正在获取第{page_no + 1}页的数据!")
                if page_no == 0:
                    total_count = self._response_data["d"]["total"]
                    total_pages = total_count // 20
                    rest_count = total_count % 20
                    if rest_count != 0:
                        total_pages += 1
                    self._like_blogs_total_page = total_pages

                entry_list = self._response_data["d"]["entryList"]
                if len(entry_list) > 0:
                    for entry_data in entry_list:
                        if entry_data is None:
                            continue
                        blog_data: Dict = {
                            "blogId": entry_data["objectId"],
                            "blogTitle": entry_data["title"],
                            "blogHref": entry_data["originalUrl"],
                            "blogViewers": entry_data["viewsCount"],
                            "blogCreateTime": datetime_str_change_fmt(
                                time_str=entry_data["createdAt"],
                                prev_fmt="%Y-%m-%dT%H:%M:%S.%fZ",
                            ),
                        }
                        self._like_blogs_data.append(blog_data)

                page_no += 1
                if page_no <= self._like_blogs_total_page:
                    # TODO 后面考虑多线程进行任务拆分，并发获取数据
                    time.sleep(0.5)
                    self._parse_personal_like_blogs(page_no=page_no)
                else:
                    # TODO 推送数据
                    logger.debug(self._like_blogs_data)
                    logger.info("获取个人点赞博客成功!")
        else:
            logger.error("查询个人点赞博客失败!")
            raise ParseDataException()
