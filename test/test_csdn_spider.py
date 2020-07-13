from nose.tools import assert_equal, assert_not_equal

from spiders.csdn_spider import CSDNSpider

FAKE_USERNAME = "123456789"
FAKE_PASSWORD = "abcdefg"


# 切记在 push 之前记得把真实的用户名和密码进行替换
def test_login_success_jujin_spider():
    spider = CSDNSpider(username=FAKE_USERNAME, password=FAKE_PASSWORD)
    spider.login()
    assert_not_equal(spider._login_cookies, None)


def test_login_failure_jujin_spider():
    spider = CSDNSpider(username=FAKE_USERNAME, password=FAKE_PASSWORD)
    try:
        spider.login()
    except ValueError as ex:
        assert_equal(ex.args[0], "登录失败!")
