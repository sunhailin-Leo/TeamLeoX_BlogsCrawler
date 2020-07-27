import os
import threading
from multiprocessing import Pool, Queue
from typing import Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler

from utils.decorator import synchronized
from utils.logger_utils import LogManager
from pipeline.redis_pipeline import RedisPipeline
from config import LOG_LEVEL, PROCESS_NUM, THREADS_NUM

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)


class AsyncThreadTask:
    """
    多线程任务 - ThreadPoolExecutor
    """

    executor = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        if cls.executor is None:
            cls.executor = ThreadPoolExecutor(max_workers=THREADS_NUM)
        return cls.executor


class AsyncProcessTask:
    """
    多进程任务 - ProcessPool
    """

    executor = None

    def __new__(cls, *args, **kwargs):
        if cls.executor is None:
            cls.executor = Pool(processes=PROCESS_NUM, maxtasksperchild=1)
        return cls.executor


class MultiProcessQueue:
    """
    多进程共享队列
    """

    process_queue = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        if cls.process_queue is None:
            cls.process_queue = Queue()
        return cls.process_queue


class AsyncSchedulerTask:
    """
    异步定时任务 - APScheduler
    """

    scheduler = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        if cls.scheduler is None:
            cls.scheduler = cls._init_scheduler()
        return cls.scheduler

    @staticmethod
    def _init_scheduler():
        redis_pool = RedisPipeline()

        job_stores: Dict = {
            "redis": RedisJobStore(
                db=1,
                jobs_key="blogs_crawler.jobs",
                run_times_key="blogs_crawler.run_times",
                connection_pool=redis_pool,
            )
        }
        executors = {
            "default": {"type": "threadpool", "max_workers": THREADS_NUM},
            "processpool": ProcessPoolExecutor(max_workers=PROCESS_NUM),
        }
        job_defaults = {"coalesce": False, "max_instances": 5, "misfire_grace_time": 60}
        background_scheduler = BackgroundScheduler(
            jobstores=job_stores, executors=executors, job_defaults=job_defaults
        )

        # 设置定时任务的 logger
        background_scheduler._logger = logger

        # 设置任务监听
        def init_scheduler_listener(event):
            if event.exception:
                logger.error("定时任务出现异常!")

        background_scheduler.add_listener(
            init_scheduler_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
        )

        # 清理任务
        background_scheduler.remove_all_jobs()

        # 启动定时任务对象
        background_scheduler.start()
        return background_scheduler


class AsyncTaskHandler:
    def __init__(self):
        self._thread_executor = AsyncThreadTask()
        self._process_executor = AsyncProcessTask()
        self._scheduler = AsyncSchedulerTask()

    def make_async_task_by_thread(self, callback: Callable, *callback_args):
        """
        通过线程池实现异步任务
        :param callback: 回调函数
        :param callback_args: 回调函数参数
        """
        thread_id = threading.currentThread().ident
        logger.debug(f"线程 ID: {thread_id}")
        function = self._thread_executor.submit(callback, *callback_args)
        logger.debug(f"线程 ID 的执行结果: {function.result()}")

    def make_async_task_by_process(self, callback: Callable, *callback_args):
        """
        通过进程池实现异步任务
        :param callback: 回调函数
        :param callback_args: 回调函数参数
        """
        process_id = os.getpid()
        logger.debug(f"进程 ID: {process_id}")
        function = self._process_executor.apply_async(callback, args=callback_args)
        logger.debug(f"进程 ID 的创建结果: {function.successful()}")

    def get_process_task_status(self, process_job_id: str):
        """
        获取进程任务的状态
        :param process_job_id: 进程任务 Id
        :return: 状态
        """
        pass

    def make_async_scheduler_task_by_interval(
        self,
        job_id: str,
        interval_seconds: int,
        callback: Callable,
        *,
        callback_kwargs: Optional[Dict] = None,
    ) -> bool:
        try:
            job_ids = [job.id for job in self._scheduler.get_jobs()]
            # 判断定时任务是否存在
            if job_id not in job_ids:
                self._scheduler.add_job(
                    func=callback,
                    trigger="interval",
                    id=job_id,
                    kwargs=callback_kwargs,
                    seconds=interval_seconds,
                )
                logger.info(f"定时任务: {job_id} 添加成功!")
            return True
        except Exception as err:
            logger.error(f"定时任务: {job_id} 添加失败!错误原因: {err}")
            return False

    def remove_async_scheduler(self, job_id: str):
        try:
            self._scheduler.remove_job(job_id=job_id)
        except Exception as err:
            logger.error(f"定时任务: {job_id} 移除失败!错误原因: {err}")
            return False
