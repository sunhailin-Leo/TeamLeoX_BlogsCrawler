from spiders.juejin_spider import JuejinSpider


def call_juejin_spider():
    t = JuejinSpider(username="<用户名>", password="<密码>")
    t.login()


if __name__ == '__main__':
    call_juejin_spider()