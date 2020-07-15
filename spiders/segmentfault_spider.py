import re
import time
from typing import Dict, List, Optional

from lxml import etree

from config import LOG_LEVEL
from utils.logger_utils import LogManager
from utils.time_utils import handle_different_time_str
from utils.exception_utils import LoginException, ParseDataException
from spiders import BaseSpider, BaseSpiderParseMethodType, CookieUtils

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)


class SegmentfaultSpider(BaseSpider):
    def __init__(self, username: str, password: str):
        self._main_url = "https://segmentfault.com"
        self._login_username = username
        self._login_password = password
        self._spider_name: str = f"segmentfault:{self._login_username}"

        self._cookies: Optional[str] = None

        super().__init__()

        self._cookies = self.get_cookies(spider_name=self._spider_name)
        self._user_url: Optional[str] = self.get_data(spider_name=f"{self._spider_name}:user_url")
        self._blogs_data: List = []

    @staticmethod
    def _parse_token(html_str: str) -> Optional[str]:
        overall_pat = re.compile(r"SF.token =.*?,\s+_\w+ = [\d,\[\]]+;", re.DOTALL)
        overall_res = overall_pat.search(html_str)
        if overall_res:
            overall_content = overall_res.group()
            filter_res = re.sub(r"(/\*[/a-zA-Z\d' ]+\*/)", "", overall_content)
            str_list = re.findall(r"(?<!//)'([a-zA-Z\d]+)'", filter_res, re.DOTALL)
            filter_list = re.findall(r"\[(\d+),(\d+)]", overall_content)
            ret = "".join(str_list)

            if filter_list:
                for m, n in filter_list:
                    ret = ret[: int(m)] + ret[int(n):]
            if len(ret) == 32:
                return ret
            else:
                return None
        else:
            return None

    def _get_token(self, url: str) -> Optional[str]:
        response = self.make_request(url=url, headers=self._common_headers)
        if response.status_code == 200:
            self._cookies = CookieUtils(cookie_list=response.cookies.items()).to_str()
            self.set_cookies(spider_name=self._spider_name, cookies=self._cookies)
            return self._parse_token(html_str=response.content.decode())
        else:
            return None

    def parse_data_with_method(self, method: str):
        if method == BaseSpiderParseMethodType.LoginResult:
            self._parse_login_data()
        elif method == BaseSpiderParseMethodType.PersonalBlogs:
            self._parse_personal_blogs()
        elif method == BaseSpiderParseMethodType.Finish:
            self.send_data()

    def login(self):
        if self._cookies is None:
            token = self._get_token(url=self._main_url)
            if token is None:
                raise LoginException()
            login_params: str = f"_={token}"
            login_url = f"{self._main_url}/api/user/login?{login_params}"

            # 思否通过判断 referer 结尾的斜杠登录跳转(所以后面会多一个斜杠拼接)
            self._common_headers.update(
                {
                    "cookie": self._cookies,
                    "origin": self._main_url,
                    "referer": self._main_url + "/",
                    "x-requested-with": "XMLHttpRequest",
                }
            )
            response = self.make_request(
                url=login_url,
                headers=self._common_headers,
                data={
                    "remember": "1",
                    "username": self._login_username,
                    "password": self._login_password,
                },
                method="POST",
            )
            if response.status_code == 200:
                main_response = self.make_request(
                    url=self._main_url, headers=self._common_headers
                )
                if response.status_code == 200:
                    selector = etree.HTML(main_response.content.decode())
                    user_href = selector.xpath(
                        "//a[@class='avatar-* dropdownBtn user-avatar']/@href"
                    )
                    if len(user_href) > 0:
                        logger.info("登录成功!")
                        self._user_url = f"{self._main_url}{user_href[0]}"
                        self.set_data(
                            spider_name=f"{self._spider_name}:user_url",
                            data=self._user_url,
                        )
                        self.parse_data_with_method(
                            method=BaseSpiderParseMethodType.LoginResult
                        )
                    else:
                        logger.error("获取个人页面链接失败!")
                        raise LoginException()
                else:
                    raise LoginException()
            else:
                self._cookies = None
                raise LoginException()
        else:
            self._common_headers.update(
                {
                    "cookie": self._cookies,
                    "origin": self._main_url,
                    "referer": self._main_url + "/",
                    "x-requested-with": "XMLHttpRequest",
                }
            )
            self.parse_data_with_method(method=BaseSpiderParseMethodType.PersonalBlogs)

    def _parse_login_data(self):
        personal_response = self.make_request(
            url=self._user_url, headers=self._common_headers
        )
        if personal_response.status_code == 200:
            selector = etree.HTML(personal_response.content.decode())

            try:
                # 个人数据
                username = selector.xpath(
                    "//h2[@class='profile__heading--name']/text()"
                )[0].strip()
                description = "".join(
                    selector.xpath("//div[@class='profile__desc']/p/text()")
                )
                avatar_img = selector.xpath(
                    "//div[@class='profile__heading--avatar-warp']/a/img/@src"
                )[0]
                followee = selector.xpath(
                    "//a[contains(@href, 'followed')]/span[@class='h5']/text()"
                )[0].replace(" 人", "")
                follower = selector.xpath(
                    "//a[contains(@href, 'following')]/span[@class='h5']/text()"
                )[0].replace(" 人", "")

                # TODO 思否暂时只能在个人动态的混杂数据中获取到点赞的文章,暂时不去解析
                like_blogs = 0

                personal_data: Dict = {
                    "username": username,
                    "description": description,
                    "avatarImg": avatar_img,
                    "followee": followee,
                    "follower": follower,
                    "likeBlogs": like_blogs,
                }
                logger.debug(personal_data)
                self.data_model.set_personal_data(data=personal_data)
                logger.info("获取个人主页数据成功!")
                self.parse_data_with_method(
                    method=BaseSpiderParseMethodType.PersonalBlogs
                )
            except IndexError:
                logger.error("解析个人主页数据失败!")
                raise ParseDataException()
        else:
            logger.error("打开个人主页失败!")
            raise LoginException()

    def _parse_personal_blogs(self, next_params: Optional[int] = None):
        if next_params is None:
            next_params = 1

        blogs_url: str = f"{self._user_url}/articles?page={next_params}"

        blogs_response = self.make_request(url=blogs_url, headers=self._common_headers)
        if blogs_response.status_code == 200:
            selector = etree.HTML(blogs_response.content.decode())
            try:
                for blog in selector.xpath("//ul[@class='profile-mine__content']/li"):
                    # TODO 思否获取文章阅读量需要进入文章解析，暂不做支持
                    # count = (
                    #     blog.xpath(
                    #         "div[@class='row']/div/span[@class='label label-warning  ']/text()"
                    #     )[0]
                    #     .replace(" ", "")
                    #     .replace("\n", "")
                    #     .replace("票", "")
                    # )
                    href_suffix = blog.xpath("div[@class='row']/div/a/@href")[0]
                    blog_href = f"{self._main_url}{href_suffix}"
                    blog_id = href_suffix.split("/")[-1]
                    blog_title = blog.xpath("div[@class='row']/div/a/text()")[0]
                    # 时间处理
                    time_str = blog.xpath(
                        "div[@class='row']/div/span[@class='profile-mine__content--date']/text()"
                    )[0].rstrip()
                    blog_time = handle_different_time_str(time_str=time_str)

                    blog_data: Dict = {
                        "blogId": blog_id,
                        "blogTitle": blog_title,
                        "blogHref": blog_href,
                        "blogViewers": 0,
                        "blogCreateTime": blog_time,
                    }
                    self._blogs_data.append(blog_data)

                next_page_element = selector.xpath("//li[@class='next']")
                if len(next_page_element) > 0:
                    time.sleep(1.5)
                    next_params += 1
                    self._parse_personal_blogs(next_params=next_params)
                else:
                    logger.debug(self._blogs_data)
                    self.data_model.set_personal_blogs_data(data=self._blogs_data)
                    logger.info("获取个人博客数据成功!")
                # 任务末尾
                self.parse_data_with_method(method=BaseSpiderParseMethodType.Finish)
            except (IndexError, Exception):
                logger.error("解析个人博客数据异常!")
                raise ParseDataException()
        else:
            logger.error("获取个人博客数据失败!")
            raise LoginException()

    def _test_cookies(self, cookies: Optional[str] = None) -> bool:
        user_url = self.get_data(spider_name=f"{self._spider_name}:user_url")
        test_user_url: str = f"{user_url}/about"
        test_request_headers: Dict = self.get_default_headers()
        test_request_cookies = self._cookies
        if cookies is not None:
            test_request_cookies = cookies
        test_request_headers.update({
            "cookie": test_request_cookies,
            "origin": self._main_url,
            "referer": self._main_url + "/",
            "x-requested-with": "XMLHttpRequest",
        })
        test_response = self.make_request(url=test_user_url, headers=test_request_headers)
        selector = etree.HTML(test_response.content.decode())
        title = "".join(selector.xpath("//title/text()"))
        if "登录" not in title:
            logger.info(f"当前思否账号为: {self._login_username}, 状态: 已登录")
            return True
        logger.error(f"当前思否登录状态: 已退出!")
        self._async_task.remove_async_scheduler(job_id=self._spider_name)
        return False
