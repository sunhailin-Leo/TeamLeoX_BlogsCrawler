class CrawlerBaseException(Exception):
    def __init__(self, *args):
        self.args = args


class LoginException(CrawlerBaseException):
    def __init__(
        self,
        code: int = 100,
        message: str = "登录失败",
        args=("登录失败",)
    ):
        self.args = args
        self.code = code
        self.message = message


class ParseDataException(CrawlerBaseException):
    def __init__(
        self,
        code: int = 101,
        message: str = "获取数据或解析数据异常",
        args=("获取数据或解析数据异常",),
    ):
        self.args = args
        self.code = code
        self.message = message
