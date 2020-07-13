import pymongo
from pymongo.errors import ConnectionFailure

from pipeline import MongoDBConfig
from pipeline.decorator import synchronized
from utils.logger_utils import LogManager

logger = LogManager(__name__, ).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=10
)


class MongoDBPipeline:
    mongo_client = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        """
        :type kwargs: object
        """
        if cls.mongo_client is None:
            cls.mongo_client = super().__new__(cls)
        return cls.mongo_client

    def _connect_mongo(self) -> bool:
        client = pymongo.MongoClient(
            host=self._mongo_config["host"],
            port=self._mongo_config["port"],
            username=self._mongo_config["username"],
            password=self._mongo_config["password"],
            maxPoolSize=self._mongo_config["maxPoolSize"],
            minPoolSize=self._mongo_config["minPoolSize"],
        )
        try:
            client.admin.command('ismaster')
            self._mongo_db_instance = client[self._mongo_config["database"]]
            return True
        except ConnectionFailure:
            logger.error("MongoDB 数据库连接失败!")
            return False

    def __init__(self):
        self._mongo_db_instance = None
        self._mongo_config = MongoDBConfig
        is_connect = self._connect_mongo()
        if is_connect:
            logger.info("MongoDB 数据库连接成功!")

    def insert_one(self):
        pass

    def find(self):
        pass

    def delete(self):
        pass

    def update(self):
        pass
