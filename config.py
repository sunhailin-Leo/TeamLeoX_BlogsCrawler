from typing import Dict, List

# 日志等级
LOG_LEVEL: int = 10

# API Server 配置
SERVER_HOST: str = "0.0.0.0"
SERVER_PORT: int = 12580

# 数据库配置

# MongoDB 配置，根据用户实际进行配置
# username 和 password 没有的不要设置为空字符串
MongoDBConfig: Dict = {
    "host": "127.0.0.1",
    "port": 27017,
    "database": "db_blogs_crawler",
    "username": None,
    "password": None,
    "maxPoolSize": 100,
    "minPoolSize": 0,
}

# Redis 配置，根据用户实际进行修改配置
RedisConfig: Dict = {"host": "127.0.0.1", "port": 6379, "password": "", "database": "0"}

# 多线程/进程任务配置
"""
多线程配置
"""
THREADS_NUM: int = 10

"""
进程池的个数
"""
PROCESS_NUM: int = 4

"""
进程任务状态
"""
PROCESS_STATUS_START: int = 10
PROCESS_STATUS_PENDING: int = 20
PROCESS_STATUS_RUNNING: int = 30
PROCESS_STATUS_EXIT: int = 40
PROCESS_STATUS_FAIL: int = 50

CODE_TO_STATUS_MAP: Dict = {
    10: "START",
    20: "PENDING",
    30: "RUNNING",
    40: "EXIT",
    50: "FAIL",
}

STATUS_TO_CODE: Dict = {
    "START": 10,
    "PENDING": 20,
    "RUNNING": 30,
    "EXIT": 40,
    "FAIL": 50,
}

# 爬虫配置
"""
当前支持的爬虫类别
"""
SPIDER_SUPPORT_LIST: List = ["csdn", "juejin", "segmentfault", "zhihu"]
