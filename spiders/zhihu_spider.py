import time
from typing import Dict, List, Optional

from urllib.parse import urlencode
from requests_toolbelt import MultipartEncoder

from config import LOG_LEVEL
from utils.logger_utils import LogManager
from utils.str_utils import check_is_json
from captcha.zhihu_captcha import ZhihuCaptcha
from utils.encrypt_utils import hmac_encrypt_sha1
from utils.image_utils import image_base64_to_pillow
from utils.js_utils import compile_js, zhihu_encrypt_js_code
from utils.exception_utils import LoginException, ParseDataException
from spiders import BaseSpider, BaseSpiderParseMethodType, CookieUtils
from utils.time_utils import datetime_str_change_fmt, timestamp_to_datetime_str

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)


class ZhiHuSpider(BaseSpider):
    def __init__(self, username: str, password: str):
        self._login_username: str = username
        self._login_password: str = password

        self._main_url: str = "https://www.zhihu.com"
        self._signin_url: str = f"{self._main_url}/signin"
        self._login_url: str = f"{self._main_url}/api/v3/oauth/sign_in"
        self._captcha_url: str = f"{self._main_url}/api/v3/oauth/captcha?lang=en"

        super().__init__()

        self._common_headers.update(
            {
                "referer": "https://www.zhihu.com/",
                "host": "www.zhihu.com",
                "accept-encoding": "gzip, deflate, br",
                "accept-language": "zh-CN,zh;q=0.9",
                "accept": "*/*",
            }
        )
        self._captcha_headers = {
            "referer": "https://www.zhihu.com/signin",
            "x-requested-with": "fetch",
            "x-zse-83": "3_2.0",
        }
        self._login_headers = {
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.zhihu.com",
            "referer": "https://www.zhihu.com/signin",
            "x-requested-with": "fetch",
            "x-zse-83": "3_2.0",
        }

        self._login_cookies = None
        self._login_user_info: Optional[Dict] = None
        self._login_user_url_token: str = ""
        self._blogs_data: List = []
        self._blogs_collection_data: List = []

    def parse_data_with_method(self, method: str):
        if method == BaseSpiderParseMethodType.LoginResult:
            self._parse_login_data()
        elif method == BaseSpiderParseMethodType.PersonalBlogs:
            self._parse_personal_blogs()
            self._parse_personal_collect_blogs()

    def _init_login(self) -> bool:
        """
        初始化登录准备
        :return: 是否初始化成功
        """
        self._session.headers.update(self._common_headers)
        self.make_request_with_session(
            session=self._session, url=self._signin_url, headers=self._common_headers
        )
        response = self.make_request_with_session(
            session=self._session, url=self._captcha_url, headers=self._captcha_headers
        )
        if check_is_json(data=response.content.decode()):
            if response.json()["show_captcha"]:
                self._captcha_headers.update(origin="https://www.zhihu.com")
                response = self.make_request_with_session(
                    session=self._session,
                    url=self._captcha_url,
                    headers=self._common_headers,
                    method="PUT",
                )
                if check_is_json(data=response.content.decode()):
                    img_base64 = response.json()["img_base64"].replace("\\n", "")

                    # 验证码识别
                    captcha_model = ZhihuCaptcha()
                    captcha_code = captcha_model.predict(
                        img=image_base64_to_pillow(img_str=img_base64),
                    )
                    post_data: dict = {"input_text": captcha_code}
                    data = MultipartEncoder(
                        fields=post_data, boundary="----WebKitFormBoundary"
                    )
                    headers = {
                        "content-type": data.content_type,
                        "origin": "https://www.zhihu.com",
                        "referer": "https://www.zhihu.com/signin",
                        "x-requested-with": "fetch",
                    }
                    response = self.make_request_with_session(
                        session=self._session,
                        url=self._captcha_url,
                        data=data,
                        headers=headers,
                        method="POST",
                    )
                    if check_is_json(response.content.decode()):
                        if response.json().get("success"):
                            return True
                        else:
                            logger.error(
                                f"验证码校验请求错误!当前接口返回结果:{response.content.decode()}"
                            )
                            return False
                    else:
                        logger.error("登录 --> 验证码校验请求失败")
                        return False
                else:
                    logger.error("登录 --> 获取验证码失败")
                    return False
            else:
                logger.error(
                    f"登录 --> 获取验证码接口数据发生变化!当前接口返回结果:{response.content.decode()}"
                )
                return False
        else:
            logger.error("登录 --> 获取验证码初始化失败")
            return False

    def login(self):
        if self._init_login():
            grant_type: str = "password"
            client_id: str = "c3cef7c66a1843f8b3a9e6a1e3160e20"
            source: str = "com.zhihu.web"
            timestamp: str = str(int(time.time() * 1000))
            signature: str = hmac_encrypt_sha1(
                key=b"d1b964811afb40118a12068ff74a12f4",
                encrypt_str=f"{grant_type}{client_id}{source}{timestamp}",
            )
            post_data: dict = {
                "client_id": client_id,
                "grant_type": grant_type,
                "source": source,
                "username": self._login_username,
                "password": self._login_password,
                "lang": "en",
                "ref_source": "other_https://www.zhihu.com/signin",
                "utm_source": "",
                "captcha": "",
                "timestamp": timestamp,
                "signature": signature,
            }
            js_code = compile_js(js_str=zhihu_encrypt_js_code)
            data = js_code.call("encrypt", urlencode(post_data))
            response = self.make_request_with_session(
                session=self._session,
                url=self._login_url,
                data=data,
                headers=self._login_headers,
                method="POST",
            )
            if check_is_json(data=response.content.decode()):
                json_response = response.json()
                if json_response.get("user_id"):
                    logger.debug(json_response)
                    self._login_cookies = json_response["cookie"]
                    self._session.cookies.update(self._login_cookies)
                    logger.info(f"登录 --> 登录成功!当前用户:{self._login_username}")
                    self._login_user_info = {"username": self._login_username}
                    self._login_user_info.update(json_response)
                elif json_response.get("error"):
                    error_code: int = json_response["error"]["code"]
                    error_msg: str = json_response["error"]["message"]
                    if error_code == 100005:
                        logger.error("登录 --> 用户名或密码错误!登录失败!")
                        raise LoginException()
                    elif error_code == 120005:
                        logger.error(f"登录 --> 登录失败!错误信息:{error_code}")
                        raise LoginException()
                    else:
                        logger.error(f"登录 --> 其他错误!错误信息:{error_msg}")
                        raise LoginException()
            else:
                logger.error("登录 --> 获取登录后的用户信息失败!登录失败!")
                raise LoginException()
        else:
            logger.error("登录 --> 失败")
            raise LoginException()

        if self._login_user_info is not None:
            self.parse_data_with_method(method=BaseSpiderParseMethodType.LoginResult)
        else:
            logger.error("登录 --> 获取用户数据失败!")
            raise LoginException()

    def _parse_login_data(self):
        include_params: str = "ad_type,available_message_types," \
                              "default_notifications_count," \
                              "follow_notifications_count," \
                              "vote_thank_notifications_count," \
                              "messages_count," \
                              "email,account_status,is_bind_phone," \
                              "visits_count,answer_count,articles_count," \
                              "gender,follower_count"
        self._personal_url: str = f"{self._main_url}/api/v4/me?include={include_params}"
        # 这个地方很重要
        request_cookie: str = CookieUtils(cookie_list=self._session.cookies.items()).to_str()
        response = self.make_request_with_session(
            session=self._session,
            url=self._personal_url,
            headers=self._common_headers,
        )
        if check_is_json(data=response.content.decode()):
            json_response = response.json()
            self._login_user_url_token = json_response["url_token"]

            self._common_headers.update(Cookie=request_cookie)
            followee_response = self.make_request(
                url=f"{self._main_url}/api/v4/members/{self._login_user_url_token}/followees",
                headers=self.get_default_headers(),
            )
            followee_count: int = 0
            if check_is_json(data=followee_response.text):
                followee_count = followee_response.json()["paging"]["totals"]

            personal_data: Dict = {
                "username": json_response["name"],
                "description": json_response["headline"],
                "avatarImg": json_response["avatar_url_template"],
                "followee": followee_count,
                "follower": json_response["follower_count"],
                "likeBlogs": 0,
            }
            # TODO 推送数据
            logger.debug(personal_data)
            self.parse_data_with_method(method=BaseSpiderParseMethodType.PersonalBlogs)
        else:
            logger.error("查询 --> 获取个人数据失败!")
            raise ParseDataException(message="获取个人数据失败!")

    def _parse_personal_blogs(self, next_params: Optional[str] = None):
        include_params: str = "data[*].comment_count,suggest_edit," \
                              "is_normal,thumbnail_extra_info," \
                              "thumbnail,can_comment,comment_permission," \
                              "admin_closed_comment,content,voteup_count," \
                              "created,updated,upvoted_followees,voting," \
                              "review_info,is_labeled,label_info;" \
                              "data[*].author.badge[?(type=best_answerer)].topics"
        if next_params is None:
            self._blogs_url: str = \
                f"{self._main_url}/api/v4/members/" \
                f"{self._login_user_url_token}/articles?include={include_params}" \
                f"&offset=0&limit=20&sort_by=created"
        else:
            self._blogs_url = next_params

        response = self.make_request(
            url=self._blogs_url,
            headers=self.get_default_headers(),
        )
        if check_is_json(response.content.decode()):
            json_response = response.json()
            for blogs in json_response["data"]:
                # 知乎的浏览者数据用赞同数代替
                blog_data: Dict = {
                    "blogId": blogs["id"],
                    "blogTitle": blogs["title"],
                    "blogHref": blogs["url"],
                    "blogViewers": blogs["voteup_count"],
                    "blogCreateTime": timestamp_to_datetime_str(timestamp=blogs["created"]),
                }
                self._blogs_data.append(blog_data)

            # TODO 推送数据
            logger.debug(self._blogs_data)

            if json_response["paging"]["is_end"] is not True:
                time.sleep(0.5)
                self._parse_personal_blogs(next_params=json_response["paging"]["next"])
        else:
            logger.error("获取个人博客数据失败!")
            raise ParseDataException()

    def _parse_personal_collect_blogs(self):
        include_params: str = "data[*].updated_time,answer_count,follower_count," \
                              "creator,description,is_following,comment_count,created_time"
        self._collection_url: str = \
            f"{self._main_url}/api/v4/people/" \
            f"{self._login_user_url_token}/collections?include={include_params}" \
            f"&offset=0&limit=20"
        response = self.make_request(
            url=self._collection_url,
            headers=self.get_default_headers(),
        )
        if check_is_json(data=response.content.decode()):
            json_response = response.json()
            collections_id: List = []
            for collections in json_response["data"]:
                collections_id.append(collections["id"])
            if len(collections_id) > 0:
                # 用闭包进行爬取
                def inner_spider(c_id: int, next_url: Optional[str] = None) -> bool:
                    req_params: str = "data[*].created,content.comment_count," \
                                      "suggest_edit,is_normal,thumbnail_extra_info," \
                                      "thumbnail,description,content,voteup_count," \
                                      "created,updated,upvoted_followees,voting," \
                                      "review_info,is_labeled,label_info," \
                                      "relationship.is_authorized,voting,is_author," \
                                      "is_thanked,is_nothelp,is_recognized;" \
                                      "data[*].author.badge[?(type=best_answerer)].topics"
                    if next_url is None:
                        collection_url: str = \
                            f"{self._main_url}/api/v4/favlists/" \
                            f"{c_id}/items?include={req_params}" \
                            f"&offset=0&limit=20"
                    else:
                        collection_url = next_url

                    inner_response = self.make_request(
                        url=collection_url,
                        headers=self.get_default_headers(),
                    )
                    if check_is_json(data=inner_response.content.decode()):
                        inner_json_response = inner_response.json()
                        for data in inner_json_response["data"]:
                            create_time = datetime_str_change_fmt(
                                time_str=data["created"],
                                prev_fmt="%Y-%m-%dT%H:%M:%SZ",
                            )
                            content = data["content"]

                            blog_id = content["id"]
                            blog_href = content["url"]
                            # 收藏夹中可以混入问题类型
                            if content["type"] == "answer":
                                title = content["question"]["title"]
                                blog_href = content["question"]["url"]
                            else:
                                title = content["title"]

                            # 封装数据
                            blog_data: Dict = {
                                "blogId": blog_id,
                                "blogTitle": title,
                                "blogHref": blog_href,
                                "blogViewers": content["voteup_count"],
                                "blogCreateTime": create_time,
                            }
                            self._blogs_collection_data.append(blog_data)

                        if inner_json_response["paging"]["is_end"] is not True:
                            time.sleep(1.5)
                            return inner_spider(
                                c_id=c_id,
                                next_url=inner_json_response["paging"]["next"],
                            )
                        else:
                            logger.info(f"收藏夹 ID: {c_id} 数据爬取完毕!")
                            return True
                    else:
                        logger.error("解析个人收藏博客数据失败!")
                        return False

                for index, collection_id in enumerate(collections_id):
                    logger.info(f"正在爬取第{index}个收藏夹数据...当前收藏夹 ID: {collection_id}")
                    is_continue = inner_spider(c_id=collection_id)
                    if is_continue is not True:
                        break
                logger.info(f"个人收藏博客获取完毕!数据长度: {len(self._blogs_collection_data)}")
            else:
                logger.info("个人收藏博客获取完毕!数据为空!")
        else:
            logger.error("获取个人收藏博客数据失败!")
            raise ParseDataException()
