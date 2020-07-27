import time
from typing import Dict
from multiprocessing import Queue

from utils.logger_utils import LogManager
from spiders.csdn_spider import CSDNSpider
from spiders.zhihu_spider import ZhiHuSpider
from spiders.juejin_spider import JuejinSpider
from spiders.segmentfault_spider import SegmentfaultSpider
from utils.async_task_utils import MultiProcessQueue
from pipeline.redis_pipeline import RedisPipelineHandler
from config import (
    LOG_LEVEL,
    PROCESS_STATUS_FAIL,
    PROCESS_STATUS_START,
    PROCESS_STATUS_RUNNING,
)

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)

# 多进程任务队列
message_queue: Queue = MultiProcessQueue()
# Redis
redis_task_key_prefix: str = "spider_task"
redis_handler = RedisPipelineHandler()


def _call_juejin_spider(task_id: str, username: str, password: str):
    task_redis_key: str = f"{redis_task_key_prefix}:{task_id}"
    t = JuejinSpider(task_id=task_id, username=username, password=password)
    t.login()
    redis_handler.insert_key(key=task_redis_key, value=str(PROCESS_STATUS_RUNNING))


def _call_zhihu_spider(task_id: str, username: str, password: str):
    task_redis_key: str = f"{redis_task_key_prefix}:{task_id}"
    zhihu = ZhiHuSpider(task_id=task_id, username=username, password=password)
    zhihu.login()
    redis_handler.insert_key(key=task_redis_key, value=str(PROCESS_STATUS_RUNNING))


def _call_segmentfault_spider(task_id: str, username: str, password: str):
    task_redis_key: str = f"{redis_task_key_prefix}:{task_id}"
    seg = SegmentfaultSpider(task_id=task_id, username=username, password=password)
    seg.login()
    redis_handler.insert_key(key=task_redis_key, value=str(PROCESS_STATUS_RUNNING))


def _call_csdn_spider(task_id: str, username: str, password: str):
    task_redis_key: str = f"{redis_task_key_prefix}:{task_id}"
    csdn = CSDNSpider(username=username, password=password)
    csdn.login()
    redis_handler.insert_key(key=task_redis_key, value=str(PROCESS_STATUS_RUNNING))


def task_parser(task_dict: Dict):
    task_id: str = task_dict["taskId"]
    spider_name: str = task_dict["spider"]
    username: str = task_dict["username"]
    password: str = task_dict["password"]

    if spider_name == "csdn":
        redis_handler.insert_key(
            key=f"{redis_task_key_prefix}:{task_id}", value=str(PROCESS_STATUS_START)
        )
        _call_csdn_spider(task_id=task_id, username=username, password=password)
    elif spider_name == "zhihu":
        redis_handler.insert_key(
            key=f"{redis_task_key_prefix}:{task_id}", value=str(PROCESS_STATUS_START)
        )
        _call_zhihu_spider(task_id=task_id, username=username, password=password)
    elif spider_name == "juejin":
        redis_handler.insert_key(
            key=f"{redis_task_key_prefix}:{task_id}", value=str(PROCESS_STATUS_START)
        )
        _call_juejin_spider(task_id=task_id, username=username, password=password)
    elif spider_name == "segmentfault":
        redis_handler.insert_key(
            key=f"{redis_task_key_prefix}:{task_id}", value=str(PROCESS_STATUS_START)
        )
        _call_segmentfault_spider(task_id=task_id, username=username, password=password)
    else:
        redis_handler.insert_key(
            key=f"{redis_task_key_prefix}:{task_id}", value=str(PROCESS_STATUS_FAIL)
        )
        logger.error(f"任务ID: {task_id}, 创建失败! 错误原因: 爬虫名称错误!")


def spider_task_receiver():
    while True:
        task = message_queue.get()
        logger.info(f"接收到的任务数据: {task}")
        task_parser(task_dict=task)
        time.sleep(1)
