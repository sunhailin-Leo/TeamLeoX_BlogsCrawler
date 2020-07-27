import os
import sys
import logging
from typing import Dict

from concurrent_log_handler import ConcurrentRotatingFileHandler


LOG_NAME: str = "service.log"
LOG_LEVEL_INT: int = 20

formatter_dict = {
    1: logging.Formatter(
        "日志时间【%(asctime)s】 - 日志名称【%(name)s】 - 文件【%(filename)s】 - "
        "第【%(lineno)d】行 - 日志等级【%(levelname)s】 - 日志信息【%(message)s】",
        "%Y-%m-%d %H:%M:%S",
    ),
    2: logging.Formatter(
        "%(asctime)s - %(name)s - %(filename)s - %(funcName)s - "
        "%(lineno)d - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    ),
    3: logging.Formatter(
        '%(asctime)s - %(name)s - 【File "%(pathname)s", '
        "line %(lineno)d, in %(funcName)s】 - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    ),
    # 一个模仿 traceback 异常的可跳转到打印日志地方的模板
    4: logging.Formatter(
        '%(asctime)s - %(name)s - "%(filename)s" - %(funcName)s - %(lineno)d - '
        '%(levelname)s - %(message)s - File "%(pathname)s", line %(lineno)d ',
        "%Y-%m-%d %H:%M:%S",
    ),
    # 支持日志跳转
    5: logging.Formatter(
        '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - '
        "%(funcName)s - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S",
    ),
    # 推荐模板
    6: logging.Formatter(
        "%(name)s - %(asctime)-15s - %(filename)s - %(lineno)d - "
        "%(levelname)s: %(message)s",
        "%Y-%m-%d %H:%M:%S",
    ),
    # 一个只显示简短文件名和所处行数的日志模板
    7: logging.Formatter("%(levelname)s - %(filename)s - %(lineno)d - %(message)s"),
    # uvicorn default 的 formatters -- without logger.Formatter
    8: '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - '
    "%(levelname)s - %(message)s",
    # uvicorn access 的 foramtters -- without logger.Formatter
    9: '%(asctime)s - %(name)s - "%(pathname)s:%(lineno)d" - %(funcName)s - '
    '%(levelname)s - %(client_addr)s - "%(request_line)s" - %(status_code)s',
}


class LogLevelException(Exception):
    def __init__(self, log_level):
        err = "设置的日志级别是 {0}，设置错误，请设置为 1 2 3 4 5 范围的数字".format(log_level)
        Exception.__init__(self, err)


class ColorHandler(logging.Handler):
    blue = 96 if os.name == "nt" else 36
    yellow = 93 if os.name == "nt" else 33

    def __init__(self, stream=None):
        """Initialize the handler. If stream is not specified, sys.stderr is used."""
        logging.Handler.__init__(self)
        if stream is None:
            stream = sys.stdout  # stderr无彩。
        self.stream = stream

    def flush(self):
        self.acquire()
        try:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        finally:
            self.release()

    def emit(self, record: logging.LogRecord):
        """
        30    40    黑色
        31    41    红色
        32    42    绿色
        33    43    黃色
        34    44    蓝色
        35    45    紫红色
        36    46    青蓝色
        37    47    白色
        """
        try:
            msg = self.format(record)
            stream = self.stream
            msg_color_dict = {
                10: "\033[0;32m%s\033[0m" % msg,
                20: "\033[0;%sm%s\033[0m" % (self.blue, msg),
                30: "\033[0;%sm%s\033[0m" % (self.yellow, msg),
                40: "\033[0;31m%s\033[0m" % msg,
                50: "\033[0;34m%s\033[0m" % msg,
            }
            try:
                msg_color = msg_color_dict[record.levelno]
            except KeyError:
                msg_color = msg
            stream.write(msg_color)
            stream.write("\n")
            self.flush()
        except Exception as err:
            print(err)
            self.handleError(record)

    def __repr__(self):
        level = logging.getLevelName(self.level)
        name = getattr(self.stream, "name", "")
        if name:
            name += " "
        return "<%s %s(%s)>" % (self.__class__.__name__, name, level)


class LogManager(object):
    """一个日志管理类，用于创建 logger 和添加 handler，支持将日志打印到控制台打印和写入日志文件和邮件。"""

    logger_name_list: list = []
    logger_list: list = []

    def __init__(self, logger_name=None):
        """
        :param logger_name: 日志名称，当为 None 时候创建 root 命名空间的日志
                            一般不要传 None，除非你确定需要这么做
        """
        self._logger_name = logger_name
        self.logger = logging.getLogger(logger_name)
        self._logger_level = None
        self._is_add_stream_handler = None
        self._do_not_use_color_handler = None
        self._log_path = None
        self._log_filename = None
        self._log_file_size = None
        self._formatter = None

    # 加 * 是为了强制在调用此方法时候使用关键字传参，如果以位置传参强制报错，
    # 因为此方法后面的参数中间可能以后随时会增加更多参数，造成之前的使用位置传参的代码参数意义不匹配。
    def get_logger_and_add_handlers(
        self,
        log_level_int: int = LOG_LEVEL_INT,
        *,
        is_add_stream_handler=True,
        do_not_use_color_handler=False,
        log_path=os.getcwd() + "/log",
        log_filename=LOG_NAME,
        log_file_size=100,
        formatter_template=5,
    ):
        """
       :param log_level_int: 日志输出级别，设置为 1 2 3 4 5，
                             分别对应原生 logging.DEBUG(10)，logging.INFO(20)，
                             logging.WARNING(30)，logging.ERROR(40)，logging.CRITICAL(50)级别
                             现在可以直接用 10 20 30 40 50。
       :param is_add_stream_handler: 是否打印日志到控制台, True / False
       :param do_not_use_color_handler: 是否禁止使用 color 彩色日志, True / False
       :param log_path: 设置存放日志的文件夹路径
       :param log_filename: 日志的名字，仅当 log_path 和 log_filename 都不为 None 时候才写入到日志文件。
       :param log_file_size: 日志大小，单位 M，默认 10M, 默认值 int
       :param formatter_template: 日志模板，1 为 formatter_dict 的详细模板，2 为简要模板, 5 为最好模板
       """
        self._logger_level = log_level_int * 10 if log_level_int < 10 else log_level_int
        self._is_add_stream_handler = is_add_stream_handler
        self._do_not_use_color_handler = do_not_use_color_handler
        self._log_path = log_path
        self._log_filename = log_filename
        self._log_file_size = log_file_size
        self._formatter = formatter_dict[formatter_template]
        self.__set_logger_level()
        self.__add_handlers()
        self.logger_name_list.append(self._logger_name)
        self.logger_list.append(self.logger)
        return self.logger

    def get_logger_without_handlers(self):
        """返回一个不带 handlers 的 logger, 就是一个带红色字体的 print 输出"""
        return self.logger

    def look_over_all_handlers(self):
        print(f"{self._logger_name}名字的日志的所有 handlers 是--> {self.logger.handlers}")

    def remove_all_handlers(self):
        for hd in self.logger.handlers:
            self.logger.removeHandler(hd)

    def remove_handler_by_handler_class(self, handler_class: type):
        """
        去掉指定类型的 handler
        :param handler_class: logging.StreamHandler,ColorHandler,
                             ConcurrentRotatingFileHandler,CompatibleSMTPSSLHandler的一种
        """
        if handler_class not in (
            ColorHandler,
            logging.StreamHandler,
            ConcurrentRotatingFileHandler,
        ):
            raise TypeError("设置的 handler 类型不正确")
        for handler in self.logger.handlers:
            if isinstance(handler, handler_class):
                self.logger.removeHandler(handler)

    def __set_logger_level(self):
        self.logger.setLevel(self._logger_level)

    def __remove_handlers_from_other_logger_when_logger_name_is_none(
        self, handler_class
    ):
        """
        当 logger name 为 None 时候需要移出其他 logger 的 handler，否则重复记录日志
        :param handler_class: handler 类型
        """
        if self._logger_name is None:
            for logger in self.logger_list:
                for handler in logger.handlers:
                    if isinstance(handler, handler_class):
                        logger.removeHandler(handler)

    @staticmethod
    def __judge_logger_contain_handler_class(logger: logging.Logger, handler_class):
        for h in logger.handlers + logging.getLogger().handlers:
            if isinstance(h, (handler_class,)):
                return True

    def __add_handlers(self):
        if self._is_add_stream_handler:
            if not self.__judge_logger_contain_handler_class(self.logger, ColorHandler):
                # 主要是阻止给 logger 反复添加同种类型的 handler 造成重复记录
                self.__remove_handlers_from_other_logger_when_logger_name_is_none(
                    ColorHandler
                )
                self.__add_stream_handler()

        if all([self._log_path, self._log_filename]):
            if not self.__judge_logger_contain_handler_class(
                self.logger, ConcurrentRotatingFileHandler
            ):
                self.__remove_handlers_from_other_logger_when_logger_name_is_none(
                    ConcurrentRotatingFileHandler
                )
                self.__add_file_handler()

    def __add_stream_handler(self):
        """
        日志显示到控制台
        """
        # stream_handler = logging.StreamHandler()
        # 不使用 streamhandler，使用自定义的彩色日志
        stream_handler = (
            ColorHandler()
            if not self._do_not_use_color_handler
            else logging.StreamHandler()
        )
        stream_handler.setLevel(self._logger_level)
        stream_handler.setFormatter(self._formatter)
        self.logger.addHandler(stream_handler)

    def __add_file_handler(self):
        """日志写入日志文件"""
        if not os.path.exists(self._log_path):
            os.mkdir(self._log_path)
        log_file = os.path.join(self._log_path, self._log_filename)
        rotate_file_handler = None
        if os.name == "nt":
            # windows 下用这个，非进程安全
            rotate_file_handler = ConcurrentRotatingFileHandler(
                log_file,
                maxBytes=self._log_file_size * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
        if os.name == "posix":
            # linux 下可以使用 ConcurrentRotatingFileHandler，进程安全的日志方式
            rotate_file_handler = ConcurrentRotatingFileHandler(
                log_file,
                maxBytes=self._log_file_size * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
        rotate_file_handler.setLevel(self._logger_level)
        rotate_file_handler.setFormatter(self._formatter)
        self.logger.addHandler(rotate_file_handler)


class LoggerMixin(object):
    subclass_logger_dict: dict = {}

    @property
    def logger(self):
        if self.__class__.__name__ + "1" not in self.subclass_logger_dict:
            logger_var = LogManager(
                self.__class__.__name__
            ).get_logger_and_add_handlers()
            self.subclass_logger_dict[self.__class__.__name__ + "1"] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[self.__class__.__name__ + "1"]

    @property
    def logger_with_file(self):
        if self.__class__.__name__ + "2" not in self.subclass_logger_dict:
            logger_var = LogManager(type(self).__name__).get_logger_and_add_handlers(
                log_filename=type(self).__name__ + ".log", log_file_size=50
            )
            self.subclass_logger_dict[self.__class__.__name__ + "2"] = logger_var
            return logger_var
        else:
            return self.subclass_logger_dict[self.__class__.__name__ + "2"]


UVICORN_LOGGING_CONFIG: Dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": formatter_dict[8],
            "use_colors": None,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": formatter_dict[9],
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}
