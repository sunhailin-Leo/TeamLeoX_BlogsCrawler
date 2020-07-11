from spiders.juejin_spider import JuejinSpider
from spiders.zhihu_spider import ZhiHuSpider
from spiders.segmentfault_spider import SegmentfaultSpider


TEST_USERNAME: str = "<用户名>"
TEST_PASSWORD: str = "<密码>"


def call_juejin_spider():
    t = JuejinSpider(username=TEST_USERNAME, password=TEST_PASSWORD)
    t.login()


def call_zhihu_spider():
    zhihu = ZhiHuSpider(username=TEST_USERNAME, password=TEST_PASSWORD)
    zhihu.login()


def call_segmentfault_spider():
    seg = SegmentfaultSpider(username=TEST_USERNAME, password=TEST_PASSWORD)
    seg.login()


if __name__ == '__main__':
    call_juejin_spider()
    call_zhihu_spider()
    call_segmentfault_spider()
