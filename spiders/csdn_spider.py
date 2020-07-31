import json
import time
import random
from typing import Dict, List, Optional

from utils.logger_utils import LogManager
from utils.str_utils import check_is_json
from config import LOG_LEVEL, PROCESS_STATUS_FAIL
from utils.time_utils import datetime_str_change_fmt
from utils.encrypt_utils import hmac_encrypt_sha256_base64
from utils.exception_utils import LoginException, ParseDataException
from spiders import BaseSpider, BaseSpiderParseMethodType, CookieUtils

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)

LOGIN_NVC_PARAMS_B: str = """
125#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
"""

LOGIN_NVC_PARAMS_E: str = """
jS2TkpulwWlv8ilzJWf9H-S8bL1JJrnIE2lV7o4fuQqvnRq-SVwN3Q0vqJ5u4urXzJ_lOngNU-cY9DTeWqd1JcFYQ-RNCzwg8Z1ybBil6v
TsUDHo4HroN9k34vtS9tXGPAkM4OKly4afOQO7E87qB0E28rrR_pELT_P5EVDUQVFIeWoHMw-ubHNiMEmlErB8rp54cGum-chHoWibAFLa
3A
"""

LOGIN_NVC_PARAMS_F: str = """
01GLjNbbmH8UWhAiEzX83KwNI3lC9V00ARgDZUu34j3iyH6ADgr2fAFFx_W58SqO5nABj1fjD-SvRyA35fCJpGIx91Xhof_ds3DDk_W93v
5vs1LuKxtJZEBbR4TOZDmhnTx1a2VE1kJ3WuBnALFldpbeYeBsfwcnoLUG4U2AaeDzKb6xO2lZmK5tDapwFM4jOd
"""

LOGIN_NVC_PARAMS_G: str = """
05a1C7nT4bR5hcbZlAujcdyUqj-hmwWIWF62L18I6YD0Zq9GgR1241OUjjsrSI5ZzLtEdzk8N2HP4tFtL9kvn0hKHFa2EanY_yio-07kE2
QsLEjfE-opr6KgTnb_U6eDzokhuyevLtgQPOyAt-9__2vSz1nsXUf7de1w2H24ICH0UoGf1PVulRu9SWqxIC_11Sw6rXSzmK03zhYYGLAs
J2mQ2XsZVLblqbG8y3CIL7HGghjaVb1HSHdVQCJQvqdxmBUfp4uVcOIBcr5xd-IUlf8AjJEiRiM1MzAVUVcqZOQuchFRN9jNXTTKXN-DhF
V--6Du2itvhdJfFyenQqpisFwJxm0s6_M0aEGyaBTaISaf0wKQihqVBhYrqNpQwqdFcYzabLSpBPZos-GvggJ6nEdBIhmW7SfHc-8IkbqR
flmSQ
"""

LOGIN_NVC_VALUE: Dict = {
    "a": "FFFF00000000016C467E",
    "b": LOGIN_NVC_PARAMS_B,
    "c": "1594521074963:0.632222524550413",
    "d": "nvc_login",
    "e": LOGIN_NVC_PARAMS_E,
    "f": LOGIN_NVC_PARAMS_F,
    "g": LOGIN_NVC_PARAMS_G,
    "h": {
        "key1": "code0",
        "nvcCode": 400,
        "umidToken": "T70CFCC5042E23C4BE90B43E4EFA527CD3B3F25AD97196823E7A37B1FAD",
        "ncSessionID": "5e701f27da8d",
    },
}

LOGIN_DATA_UA_TOKEN: str = """
125#aygcaGbAcW0rKgC5pcf+s/0VjION3ytfLw/It235Bpp98NcIsgtoX/m/YDIxnomZKnlw41bUZuu1qN9GQYeK2lwn1mhClkKVOdJzVG
1ctKzCAYdo50aCvL9ehPaPVitqHn2ODxiaATcsUNt7q2aKK2BFIzqwGj0TbHqTGzGpObTk9xblqLlC0M/tqOXo3OR+EzlpLWbXFhEA8VwA
+DMenPn9wNtgtzIjbVUSYi9BEwfKeLzCenFVFEg2e2DOKRhsow1Pfh3FDtq5lOzrLyJ53z3LH8beKvZ4G56WT6WjajeXNbs29jDn1QJpGc
qQwybwka0pM3SpV/5w9rcFlQXMe5JM562cku4bbew2H18fVaO2kiJZ1Zpt9SVk2rTDMXbT/s7tJDcavt1+13L/ATbJrwX6+uvPCRQJ2paN
B8NWs6g+7IasL+/q7CuE0gv0ERxZtIyb5/spPQu2Xq/llnuYOaoQf+Ra53o4YSYaAymOUYy3f2kG9yHxT8AWY09ieaFBUba4ym8BPQxIcm
FgNREsCC2V+MutPFxyAcI9FLtBgqGanhFAyuCDvBuCuJk3fLiJaS+FjVR3NQdjxZnSWfF7gLwhEBfOsut13UJF2Oa2MqHXVRCU1SoFKkya
HCvdamdoQJkPhmBy8dwv0S9D/sZMHx3SYXYlh4IUqjYwetz6kp7NztjIBampU4Z50LaTO5l6JVzVlDkb1tngU6e/1FEsWgEQdgAidVgzRW
PqdNgkpZ9vD23WoonX17FXhA/YyU4PpXImFsJGog3eEZCosxeEJyRVmiPCM6JYUjcScvsOcgDbUgsi1p54gkHw2jVU9gs4hDi4ZBfmdjDw
3jh4pME4XbEEforg//ffrTPST3EwTSHbr/fSkAKPPkO20Nhz/f1ErDiccL/8a/L2JgCnFEuKY9BWIbqdAeKj3udxFVGhiy2SSgPkfkpjJZ
+7kaCkEa/JYNOoFCblyAyL2BVB2/2sub2W+Ky6XDeGmRexvSM/3TQ/5V4CfpvWc7V/w0etgKBIPFdDo3Vqk9C9s9vtP6ex5ymdWUDJdZD7
itEs1jo0i6VGlWhxXzrYGCu08eunqJwQmDThIMyN67Zpr9ZglwY/resqitPBb02vacz/EdiSJVK83SPlnrwkGGXYWil+G8dmYeMlqX3aKJ
GBOoFm7NxZxfIm7Zxq225lf/HNbSQFwCfiRa8AIc6hg114va2Cd+WMoS9jANudnXumwrF479Sk8J9V7OMC9NxDR5itCdX0NIZIfpQNU2z5
SIJT88WOWcehUOPXxhkIx91plFgGfcUCkyPcQFwGgE4a/kF/WWSKlLllt2QXDUX442gtr34NcElzohgdJp8rmXbfZKWwZQc90vUly1DOC4
8xCqwVe9G1dTUmF6sQy/v0LGk2ZPQbZt6at20ETjWzyc3/ymk9mV2tDDGND4PXe4IcbSP3nwDAPeGYXAEkU8GaTy/tZ9qJ56gVobZ0sY5d
pmO5TwHu5V89crpEpJGQQnrIJVBKSWAu9RhvS8Xq5eX1kaHvPEeDPjL6mAUA0XfVAYf7pLhzzExvOXNHiL2DWxpnfxOfhjx8+HarOoZluj
PfNFhn5DGl2HVYnag8I9w5G3sTKkrQGIm9xx//A62=
"""

LOGIN_DATA_WEB_UMID_TOKEN: str = "T1FE96933802C3FDF25B8F260ED7E83A847014FDE2B370B583731346DE5"


class CSDNSpider(BaseSpider):
    def __init__(self, task_id: str, username: str, password: str):
        self._task_id = task_id
        self._login_username = username
        self._login_password = password

        self._spider_name: str = f"csdn:{self._login_username}"
        self._login_cookies: Optional[str] = None

        self._blog_main_url: str = "https://blog.csdn.net"
        self._login_main_url: str = "https://passport.csdn.net"
        self._personal_main_url: str = "https://me.csdn.net"

        super().__init__()

        self._check_hvc_data: Dict = {
            "nvcValue": json.dumps(LOGIN_NVC_VALUE),
            "source": "pc_password",
        }
        self._login_data: Dict = {
            "loginType": "1",
            "pwdOrVerifyCode": self._login_password,
            "userIdentification": self._login_username,
            "uaToken": LOGIN_DATA_UA_TOKEN,
            "webUmidToken": LOGIN_DATA_WEB_UMID_TOKEN,
        }
        self._request_headers = self.get_default_headers()
        self._request_headers.update({"content-type": "application/json"})

        self._login_cookies = self.get_cookies(self._spider_name)
        self._username: Optional[str] = None

        self._personal_collection_ids: List = []
        self._like_blogs_data: List = []

        self._api_key: str = "203803574"
        self._api_nonce_template: str = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
        self._api_encrypt_key: bytes = b"9znpamsyl2c7cdrr9sas0le9vbc3r6ba"
        self._blogs_data: List = []

    def parse_data_with_method(self, method: str):
        if method == BaseSpiderParseMethodType.LoginResult:
            self._parse_login_data()
        elif method == BaseSpiderParseMethodType.PersonalBlogs:
            self._parse_personal_blogs()
            self._parse_personal_like_blogs()
        elif method == BaseSpiderParseMethodType.Finish:
            self.send_data()

    def login(self):
        if self._login_cookies is None:
            hvc_response = self.make_request_with_session(
                session=self._session,
                url=f"{self._login_main_url}/v1/api/riskControl/checkHVC",
                headers=self._request_headers,
                json=self._check_hvc_data,
                method="POST",
            )
            if hvc_response.status_code != 200:
                logger.error("登录 --> 登录预认证失败!")
                raise LoginException()

            if check_is_json(data=hvc_response.content.decode()) is not True:
                logger.error("登录 --> 登录预认证数据返回失败!")
                raise LoginException()

            hvc_json_response = hvc_response.json()
            if hvc_json_response["message"] != "success":
                logger.error(f"登录 --> 登录预认证失败!返回结果: {hvc_json_response}")
                raise LoginException()
            logger.debug(f"预认证返回结果: {hvc_json_response}")

            login_response = self.make_request_with_session(
                session=self._session,
                url=f"{self._login_main_url}/v1/register/pc/login/doLogin",
                headers=self._request_headers,
                json=self._login_data,
                method="POST",
            )
            if login_response.status_code != 200:
                logger.error("登录 --> 登录请求失败!")
                raise LoginException()

            if check_is_json(data=login_response.content.decode()) is not True:
                logger.error("登录 --> 登录请求返回失败!")
                raise LoginException()

            login_json_response = login_response.json()
            if login_json_response["message"] == "success":
                logger.debug(f"登录返回结果: {login_json_response}")
                self._username = login_json_response["username"]
                logger.info(f"登录 --> 登录成功!当前用户名: {self._login_username}")
                self._login_cookies = CookieUtils(
                    cookie_list=login_response.cookies.items()
                ).to_str()
                self.set_cookies(
                    spider_name=self._spider_name, cookies=self._login_cookies
                )
                self._request_headers.update(Cookie=self._login_cookies)
                self.parse_data_with_method(
                    method=BaseSpiderParseMethodType.LoginResult
                )
            else:
                logger.error(f"登录 --> 登录异常!返回结果: {login_json_response}")
                self.update_task_status(
                    task_id=self._task_id, data=str(PROCESS_STATUS_FAIL)
                )
                raise LoginException()
        else:
            self._request_headers.update(Cookie=self._login_cookies)
            self.parse_data_with_method(method=BaseSpiderParseMethodType.PersonalBlogs)

    def _parse_login_data(self):
        personal_data_url: str = f"{self._personal_main_url}/api/user/show"
        json_req_data: Dict = {"username": self._login_username}
        personal_data_response = self.make_request(
            url=personal_data_url,
            headers=self._request_headers,
            json=json_req_data,
            method="POST",
        )
        if (
            personal_data_response.status_code != 200
            or check_is_json(data=personal_data_response.content.decode()) is not True
        ):
            logger.error("获取个人数据异常!")
            self.update_task_status(
                task_id=self._task_id, data=str(PROCESS_STATUS_FAIL)
            )
            raise LoginException()

        personal_data_json = personal_data_response.json()
        if personal_data_json["message"] != "成功":
            logger.error("获取个人数据失败!")
            self.update_task_status(
                task_id=self._task_id, data=str(PROCESS_STATUS_FAIL)
            )
            raise ParseDataException()

        data = personal_data_json["data"]
        personal_data: Dict = {
            "username": self._username,
            "description": data["selfdesc"],
            "avatarImg": data["avatarurl"],
            "followee": 0,
            "follower": 0,
            "likeBlogs": 0,
        }

        # 获取关注量
        follower_api_url: str = f"{self._personal_main_url}/api/relation/get?username={self._username}"
        follower_response = self.make_request(
            url=follower_api_url, headers=self._request_headers
        )

        if (
            follower_response.status_code != 200
            or check_is_json(data=follower_response.content.decode()) is not True
        ):
            logger.error("获取个人关注数据异常!")
            self.update_task_status(
                task_id=self._task_id, data=str(PROCESS_STATUS_FAIL)
            )
            raise ParseDataException()

        follower_json_response = follower_response.json()
        if follower_json_response["message"] == "成功":
            personal_data["followee"] = follower_json_response["data"]["fans_num"]
            personal_data["follower"] = follower_json_response["data"]["follow_num"]

        # 获取个人收藏的博客数
        collections_response = self.make_request(
            url=f"{self._personal_main_url}/api/favorite/folderList",
            headers=self._request_headers,
        )

        if (
            collections_response.status_code != 200
            or check_is_json(collections_response.content.decode()) is not True
        ):
            logger.error("获取个人收藏数据异常!")
            self.update_task_status(
                task_id=self._task_id, data=str(PROCESS_STATUS_FAIL)
            )
            raise ParseDataException()

        collection_json_response = collections_response.json()
        if collection_json_response["message"] == "成功":
            collection_count = 0
            for collection in collection_json_response["data"]["result"]:
                favorite_num = collection["FavoriteNum"]
                if favorite_num != 0:
                    collection_count += collection["FavoriteNum"]
                    self._personal_collection_ids.append(collection["ID"])
            personal_data["likeBlogs"] = collection_count

        # 写入数据
        logger.debug(personal_data)
        self.data_model.set_personal_data(data=personal_data)
        self.parse_data_with_method(method=BaseSpiderParseMethodType.PersonalBlogs)

    def _parse_personal_blogs(self, page_no: int = 0):
        """
        这个接口比较高级 https://bizapi.csdn.net/blog-console-api/v1/article/list?pageSize=20
        应该说是整个 https://bizapi.csdn.net 的接口都挺高级
        请求头内部通过自定义一套加密字符串和私钥进行 HMAC-SHA256 加密
        """
        api_main_url: str = "https://bizapi.csdn.net"
        api_suffix: str = "/blog-console-api/v1/article/list?pageSize=20"
        if page_no != 0:
            api_suffix = f"/blog-console-api/v1/article/list?page={page_no}pageSize=20"

        # 生成 x-ca-nonce
        nonce: str = ""
        for nonce_char in self._api_nonce_template:
            n = int(16 * random.random()) | 0
            nonce += (
                hex(n if n == 3 else n | 8)[2:] if nonce_char in "xy" else nonce_char
            )

        # 生成 x-ca-signature
        encrypt_str: str = f"GET\napplication/json, text/plain, */*\n\n\n\n" f"x-ca-key:{self._api_key}\nx-ca-nonce:{nonce}\n{api_suffix}"
        signature = hmac_encrypt_sha256_base64(
            key=self._api_encrypt_key, encrypt_str=encrypt_str
        )
        api_headers: Dict = self.get_default_headers()
        api_headers.update(
            {
                "Cookie": self._login_cookies,
                "x-ca-key": self._api_key,
                "x-ca-nonce": nonce,
                "x-ca-signature": signature,
                "x-ca-signature-headers": "x-ca-key,x-ca-nonce",
                "origin": "https://mp.csdn.net",
                "referer": "https://mp.csdn.net/console/article",
                "accept": "application/json, text/plain, */*",
            }
        )
        api_response = self.make_request(
            url=f"{api_main_url}{api_suffix}", headers=api_headers
        )

        if (
            api_response.status_code != 200
            or check_is_json(data=api_response.content.decode()) is not True
        ):
            logger.error("获取个人博客数据失败!")
            self.update_task_status(
                task_id=self._task_id, data=str(PROCESS_STATUS_FAIL)
            )
            raise ParseDataException()

        api_json_response = api_response.json()
        if api_json_response["msg"] != "success":
            logger.error("获取个人博客数据失败!")
            self.update_task_status(
                task_id=self._task_id, data=str(PROCESS_STATUS_FAIL)
            )
            raise ParseDataException()

        blogs_list_data = api_json_response["data"]["list"]
        if len(blogs_list_data) > 0:
            for blogs in blogs_list_data:
                # https://blog.csdn.net/sinat_28177969/article/details/54138163
                blog_id: str = blogs["ArticleId"]
                blog_href: str = f"{self._blog_main_url}/{self._username}/article/details/{blog_id}"
                blog_create_time = datetime_str_change_fmt(
                    time_str=blogs["PostTime"], prev_fmt="%Y年%m月%d日 %H:%M:%S"
                )

                blog_data: Dict = {
                    "blogId": blog_id,
                    "blogTitle": blogs["Title"],
                    "blogHref": blog_href,
                    "blogViewers": blogs["ViewCount"],
                    "blogCreateTime": blog_create_time,
                }
                self._blogs_data.append(blog_data)

            # 文章有不同状态的，只取 enable 的，其他状态的文章，外部无法访问
            if api_json_response["data"]["count"]["enable"] > 20:
                time.sleep(1)
                page_no += 1
                self._parse_personal_blogs(page_no=page_no)
            else:
                logger.debug(self._blogs_data)
                self.data_model.set_personal_blogs_data(data=self._blogs_data)
                logger.info("获取个人博客数据成功!")
        else:
            logger.info("获取个人博客数据成功!个人博客数据为空!")

    def _parse_personal_like_blogs(self):
        if len(self._personal_collection_ids) > 0:
            for collection_id in self._personal_collection_ids:
                # 用闭包去获取每个有数据的收藏夹的文章数据
                def inner_spider(c_id: int, page_no: int = 1):
                    like_blogs_url: str = f"{self._personal_main_url}/api/favorite/listByFolder?" f"folderID={c_id}&page={page_no}&pageSize=10&sources="
                    inner_response = self.make_request(
                        url=like_blogs_url, headers=self._request_headers
                    )
                    if (
                        inner_response.status_code != 200
                        or check_is_json(data=inner_response.content.decode())
                        is not True
                    ):
                        logger.error("获取个人收藏夹数据失败!")
                        raise ParseDataException

                    inner_json_response = inner_response.json()
                    if inner_json_response["message"] == "成功":
                        collection_data_list = inner_json_response["data"]["list"]
                        if len(collection_data_list) > 0:
                            logger.info(f"正在获取收藏夹: {collection_id} 的第 {page_no} 的数据!")
                            for collection_data in collection_data_list:
                                blog_data: Dict = {
                                    "blogId": collection_data["ID"],
                                    "blogTitle": collection_data["Title"],
                                    "blogHref": collection_data["URL"],
                                    "blogViewers": 0,
                                    "blogCreateTime": collection_data["DatelineString"],
                                }
                                self._like_blogs_data.append(blog_data)

                            # 请求下一页
                            page_no += 1
                            time.sleep(0.5)
                            inner_spider(c_id=c_id, page_no=page_no)

                try:
                    inner_spider(c_id=collection_id)
                except (ParseDataException, Exception):
                    logger.error("获取个人收藏博客失败!")
                    break

            logger.debug(self._like_blogs_data)
            self.data_model.set_personal_like_blogs_data(data=self._like_blogs_data)
            logger.info("获取个人收藏博客成功!")
        # 任务末尾
        self.parse_data_with_method(method=BaseSpiderParseMethodType.Finish)

    def _test_cookies(self, cookies: Optional[str] = None) -> bool:
        test_url: str = f"{self._personal_main_url}/api/favorite/folderList"
        test_request_headers: Dict = self.get_default_headers()
        test_request_cookies = self._login_cookies
        if cookies is not None:
            test_request_cookies = cookies
        test_request_headers.update(Cookie=test_request_cookies)
        test_response = self.make_request(url=test_url, headers=test_request_headers)
        if (
            test_response.status_code != 200
            or check_is_json(test_response.content.decode()) is not True
        ):
            logger.error(f"当前 CSDN 账号登录状态: 已退出!")
            self._async_task.remove_async_scheduler(job_id=self._spider_name)
            return False

        test_json_response = test_response.json()
        if test_json_response["code"] == 200:
            logger.info(f"当前 CSDN 账号为: {self._login_username}, 状态: 已登录")
            return True
        else:
            logger.error(f"当前 CSDN 账号登录状态: 已退出!")
            return False
