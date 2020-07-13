from typing import Optional

from redis import Redis, Connection, ConnectionPool
from redis.exceptions import RedisError, ConnectionError

from pipeline import RedisConfig
from utils.logger_utils import LogManager
from pipeline.decorator import synchronized

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=10
)


class RedisPipeline:
    redis_pool: Optional[ConnectionPool] = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        if cls.redis_pool is None:
            cls.redis_pool = cls._connect_redis()
        return cls.redis_pool

    @staticmethod
    def _connect_redis() -> Optional[ConnectionPool]:
        pool = ConnectionPool(
            connection_class=Connection(
                host=RedisConfig["host"],
                port=RedisConfig["port"],
                password=RedisConfig["password"],
                db=RedisConfig["database"],
                decode_responses=True,
            ),
        )
        try:
            test_instance = Redis(connection_pool=pool)
            test_instance.ping()
            logger.info("Redis 连接成功!")
            return pool
        except ConnectionError:
            logger.error("Redis 连接失败!")
            return None

    @staticmethod
    def get_redis_instance() -> Optional[Redis]:
        try:
            return Redis(connection_pool=RedisPipeline.redis_pool)
        except Exception as err:
            logger.error(err)
            return None

    def insert_key(
        self,
        key: str,
        value: str,
        *,
        expire_seconds: Optional[int],
        expire_milliseconds: Optional[int]
    ):
        instance = self.get_redis_instance()
        if instance is not None:
            try:
                instance.set(name=key, value=value, ex=expire_seconds, px=expire_milliseconds)
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
