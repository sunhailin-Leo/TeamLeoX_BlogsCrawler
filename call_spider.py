from spiders.juejin_spider import JuejinSpider
from spiders.zhihu_spider import ZhiHuSpider
from spiders.segmentfault_spider import SegmentfaultSpider
from spiders.csdn_spider import CSDNSpider


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


def call_csdn_spider():
    csdn = CSDNSpider(username=TEST_USERNAME, password=TEST_PASSWORD)
    csdn.login()


if __name__ == '__main__':
    import time

    # TODO LIST
    """
    1、将目前这个 TODO LIST 之外的 TODO 工作完成。
    2、编写一个任务接收器。
    3、利用多进程去启动下面的爬虫，而不使用线程。因为会导致线程嵌套，给 debug 带来影响。
    4、设计一个高层的 API 将整个爬虫的调用更加简单。
    5、利用 Flask 或者 fastapi 设计 Restful 接口对接前端进行数据查询。
    6、完善测试用例
    """

    call_juejin_spider()
    # call_zhihu_spider()
    # call_segmentfault_spider()
    # call_csdn_spider()
    while True:
        time.sleep(2)
