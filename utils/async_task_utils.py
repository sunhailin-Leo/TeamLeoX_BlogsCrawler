import threading
from typing import Dict, Optional, Callable

from concurrent.futures import ThreadPoolExecutor
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.schedulers.background import BackgroundScheduler

from config import LOG_LEVEL
from utils.decorator import synchronized
from utils.logger_utils import LogManager
from pipeline.redis_pipeline import RedisPipeline

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)


class AsyncTask:
    executor = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        if cls.executor is None:
            cls.executor = ThreadPoolExecutor()
        return cls.executor


class AsyncSchedulerTask:
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
                connection_pool=redis_pool
            ),
        }
        executors = {
            "default": {"type": "threadpool", "max_workers": 10},
            "processpool": ProcessPoolExecutor(max_workers=5)
        }
        job_defaults = {
            "coalesce": False,
            "max_instances": 5,
            "misfire_grace_time": 60,
        }
        background_scheduler = BackgroundScheduler(
            jobstores=job_stores,
            executors=executors,
            job_defaults=job_defaults,
        )

        # 设置定时任务的 logger
        background_scheduler._logger = logger

        # 设置任务监听
        def init_scheduler_listener(event):
            if event.exception:
                logger.error("定时任务出现异常!")

        background_scheduler.add_listener(init_scheduler_listener, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

        # 清理任务
        background_scheduler.remove_all_jobs()

        # 启动定时任务对象
        background_scheduler.start()
        return background_scheduler


class AsyncTaskHandler:
    def __init__(self):
        self._executor = AsyncTask()
        self._scheduler = AsyncSchedulerTask()

    def make_async_task(self, callback: Callable, *callback_args):
        thread_id = threading.currentThread().ident
        logger.debug(f"线程 ID: {thread_id}")
        function = self._executor.submit(callback, *callback_args)
        logger.debug(f"线程 ID 的执行结果: {function.result()}")

    def make_async_scheduler_task_by_interval(
        self,
        job_id: str,
        interval_seconds: int,
        callback: Callable,
        *,
        callback_kwargs: Optional[Dict] = None
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
