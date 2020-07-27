from typing import Dict, Optional
from multiprocessing import Queue, Process

import uvicorn
from pydantic import BaseModel
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter, _rate_limit_exceeded_handler
from fastapi import Query, FastAPI, Request, BackgroundTasks

from utils.encrypt_utils import md5_str
from call_spider import spider_task_receiver
from utils.async_task_utils import MultiProcessQueue
from pipeline.redis_pipeline import RedisPipelineHandler
from utils.logger_utils import LogManager, UVICORN_LOGGING_CONFIG
from config import (
    LOG_LEVEL,
    SERVER_HOST,
    SERVER_PORT,
    SPIDER_SUPPORT_LIST,
    PROCESS_STATUS_FAIL,
)

logger = LogManager("fastapi").get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="BlogsCrawler-Management",
    description="BlogsCrawler-API",
    version="1.0.0",
    openapi_prefix="",
    openapi_url="/fastapi/data_manger.json",
    docs_url="/fastapi/docs",
    redoc_url="/fastapi/redoc",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app_api_router: str = "/api/v1"
app_redis_handler = RedisPipelineHandler()
message_queue: Queue = MultiProcessQueue()
logger.info("项目启动成功!")


class TaskRequest(BaseModel):
    taskType: str = Query(None, title="任务类型", description="任务类型：create，check，getResult")
    taskArgs: Optional[Dict] = Query(
        None, title="任务参数", description="json object；后台校验参数完整性"
    )


class TaskResponse(BaseModel):
    code: str = "000000"
    message: str = "success"
    taskId: Optional[str] = None


def error_response(code: str = "999999", message: str = "error") -> TaskResponse:
    response = TaskResponse()
    response.code = code
    response.message = message
    return response


def success_response(
    code: str = "000000", message: str = "success", data: Optional[str] = None
) -> TaskResponse:
    response = TaskResponse()
    response.code = code
    response.message = message
    response.taskId = data
    return response


def submit_async_task(task_id: str, spider_name: str, username: str, password: str):
    """
    提交异步任务
    :param task_id: 任务 ID
    :param spider_name: 爬虫名称
    :param username: 爬虫登录的用户名
    :param password: 爬虫登录的密码
    """
    # 生成任务 ID
    task_dict: Dict = {
        "taskId": task_id,
        "spider": spider_name,
        "username": username,
        "password": password,
    }
    message_queue.put(task_dict)
    logger.info(f"任务创建成功! 任务ID: {task_id}")


@app.post(
    path=f"{app_api_router}/task/create",
    response_model=TaskResponse,
    response_model_include={"code", "message"},
)
@limiter.limit("1/seconds")
def create_task(request: Request, task: TaskRequest, background_task: BackgroundTasks):
    """
    接口请求参数：
    taskType：操作类型
    taskArgs：具体的数据

    0、这个接口需要做限流
    1、利用 FastAPI 的 BackgroundTask 去传递任务信息
    2、前端在收到这个接口返回之后去请求 checkTaskStatus 获取任务的状态
    3、BackgroundTask 往进程队列发送任务
    """

    if task.taskType != "create":
        return error_response(message="ErrorTaskType")

    # 参数校验
    task_args: Optional[Dict] = task.taskArgs
    if task_args is None or isinstance(task.taskArgs, dict) is not True:
        return error_response(message="ErrorTaskArgs")

    spider_name: Optional[str] = task_args.get("spiderName")
    if spider_name is None:
        return error_response(message="ErrorTaskArgs")
    spider_name = spider_name.lower()
    if spider_name not in SPIDER_SUPPORT_LIST:
        return error_response(message="ErrorTaskArgs - spiderName is Error")

    spider_username: Optional[str] = task_args.get("username")
    if spider_username is None:
        return error_response(message="ErrorTaskArgs")

    spider_password: Optional[str] = task_args.get("password")
    if spider_password is None:
        return error_response(message="ErrorTaskArgs")

    # 任务 ID
    task_id: str = md5_str(
        encrypt_str=f"{spider_name}-*-{spider_username}-*-{spider_password}"
    )

    task_result = app_redis_handler.find_key(key=f"spider_task:{task_id}")
    if task_result is not None and task_result == str(PROCESS_STATUS_FAIL):
        # 通过 BackgroundTask 提交异步任务
        background_task.add_task(
            submit_async_task, task_id, spider_name, spider_username, spider_password
        )
        return success_response(data=task_id)
    else:
        return error_response(message="Task is Exist! Do not duplicate create!")


@app.post(
    path=f"{app_api_router}/task/checkTaskStatus",
    response_model=TaskResponse,
    response_model_include={"code", "message"},
)
def check_task(task: TaskRequest):
    if task.taskType != "check":
        return error_response(message="ErrorTaskType")
    """
    1、通过 redis 获取任务的状态
    2、返回任务状态，当任务状态为 RUNNING 时则可以请求 taskResult 接口获取任务对应的数据
    """
    if task.taskArgs != {} and task.taskArgs is not None:
        job_id = task.taskArgs.get("job_id")
        if job_id is None:
            return error_response(message="ErrorTaskArgs")

        job_status = app_redis_handler.find_key(key=job_id)
        if job_status is None:
            return error_response(message="Non exist task!")

        return success_response(data=job_status)
    return error_response(message="ErrorTaskArgs")


@app.post(
    path=f"{app_api_router}/task/taskResult",
    response_model=TaskResponse,
    response_model_include={"code", "message"},
)
def get_task_result(task: TaskRequest):
    if task.taskType != "getResult":
        return error_response(message="ErrorTaskType")
    # TODO 获取任务结果


if __name__ == "__main__":
    # 子进程
    sub_process = Process(target=spider_task_receiver)
    sub_process.start()
    # 启动 API 服务
    uvicorn.run(
        app=app, host=SERVER_HOST, port=SERVER_PORT, log_config=UVICORN_LOGGING_CONFIG
    )
