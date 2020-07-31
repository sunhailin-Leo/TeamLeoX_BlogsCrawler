from typing import Optional

from redis import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError

from utils.decorator import synchronized
from utils.logger_utils import LogManager
from config import LOG_LEVEL, RedisConfig

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)


class RedisPipeline:
    redis_pool: Optional[ConnectionPool] = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        if cls.redis_pool is None:
            cls.redis_pool = cls._connect_redis()
        return cls.redis_pool

    def __init__(self):
        pass

    @staticmethod
    def _connect_redis() -> Optional[ConnectionPool]:
        pool = ConnectionPool(
            host=RedisConfig["host"],
            port=RedisConfig["port"],
            password=RedisConfig["password"],
            db=RedisConfig["database"],
            decode_responses=True,
        )
        try:
            test_instance = Redis(connection_pool=pool)
            if test_instance.ping() is not True:
                logger.error("Redis 连接失败!")
                return None
            logger.info("Redis 连接成功!")
            return pool
        except ConnectionError:
            logger.error("Redis 连接失败!")
            return None


class RedisPipelineHandler:
    def __init__(self):
        self._pool = RedisPipeline()

    def get_redis_instance(self) -> Optional[Redis]:
        try:
            return Redis(connection_pool=self._pool)
        except Exception as err:
            logger.error(err)
            return None

    def insert_key(
        self,
        key: str,
        value: str,
        *,
        expire_seconds: Optional[int] = None,
        expire_milliseconds: Optional[int] = None,
    ):
        instance = self.get_redis_instance()
        if instance is not None:
            try:
                instance.set(
                    name=key, value=value, ex=expire_seconds, px=expire_milliseconds
                )
                return True
            except RedisError as err:
                logger.error(err)
                return False
        else:
            logger.error("从 Redis 连接池获取连接失败!")
            return False

    def find_key(self, key: str) -> Optional[str]:
        instance = self.get_redis_instance()
        if instance is not None:
            try:
                return instance.get(name=key)
            except RedisError as err:
                logger.error(err)
                return None
        else:
            logger.error("从 Redis 连接池获取连接失败!")
            return None
