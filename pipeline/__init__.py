from typing import Dict

# 数据库配置

# MongoDB 配置，根据用户实际进行配置
# username 和 password 没有的不要设置为空字符串
MongoDBConfig: Dict = {
    "host": "127.0.0.1",
    "port": 27017,
    "database": "TeamLeoX",
    "username": None,
    "password": None,
    "maxPoolSize": 100,
    "minPoolSize": 0,
}

# Redis 配置，根据用户实际进行修改配置
RedisConfig: Dict = {
    "host": "127.0.0.1",
    "port": 6379,
    "password": None,
    "database": "0",
}
