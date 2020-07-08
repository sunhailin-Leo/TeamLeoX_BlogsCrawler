from spiders.juejin_spider import JuejinSpider


def call_juejin_spider():
    t = JuejinSpider(username="<用户名>", password="<密码>")
    t.login()


# Elvis_Lee Code - 2020-07-09
if __name__ == '__main__':
    call_juejin_spider()
