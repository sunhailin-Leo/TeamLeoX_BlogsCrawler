from typing import Dict, List, Optional

from bson import ObjectId
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import BulkWriteError, ConnectionFailure

from config import LOG_LEVEL
from pipeline import MongoDBConfig
from utils.decorator import synchronized
from utils.logger_utils import LogManager

logger = LogManager(__name__).get_logger_and_add_handlers(
    formatter_template=5, log_level_int=LOG_LEVEL
)


class MongoDBPipeline:
    mongo_client: Optional[MongoClient] = None

    @synchronized
    def __new__(cls, *args, **kwargs):
        if cls.mongo_client is None:
            cls.mongo_client = cls._connect_mongo()
        return cls.mongo_client

    @staticmethod
    def _connect_mongo() -> Optional[MongoClient]:
        client: MongoClient = MongoClient(
            host=MongoDBConfig["host"],
            port=MongoDBConfig["port"],
            username=MongoDBConfig["username"],
            password=MongoDBConfig["password"],
            maxPoolSize=MongoDBConfig["maxPoolSize"],
            minPoolSize=MongoDBConfig["minPoolSize"],
        )
        try:
            client.admin.command("ismaster")
            logger.info("MongoDB 数据连接成功!")
            return client
        except ConnectionFailure:
            logger.error("MongoDB 数据库连接失败!")
            return None

    def __del__(self):
        client: MongoClient = MongoDBPipeline.mongo_client
        client.close()

    @staticmethod
    def connection_close():
        client: MongoClient = MongoDBPipeline.mongo_client
        client.close()


class MongoDBHandler:
    def __init__(self):
        self._mongo_client: MongoClient = MongoDBPipeline()
        self._mongo_db_client = self._mongo_client[MongoDBConfig["database"]]

    def get_mongo_instance(self) -> Optional[Database]:
        try:
            return self._mongo_db_client
        except Exception as err:
            logger.error(err)
            return None

    def insert_one(self, col_name: str, doc: Dict) -> bool:
        try:
            col_instance = self._mongo_db_client[col_name]
            col_instance.insert_one(document=doc)
            return True
        except Exception as err:
            logger.error(err)
            return False

    def insert_one_return_id(self, col_name: str, doc: Dict) -> Optional[str]:
        try:
            col_instance = self._mongo_db_client[col_name]
            insert_res = col_instance.insert_one(document=doc)
            return insert_res.inserted_id
        except Exception as err:
            logger.error(err)
            return None

    def insert_many(self, col_name: str, doc_list: List[Dict]) -> bool:
        try:
            doc_list_length: int = len(doc_list)
            col_instance = self._mongo_db_client[col_name]
            insert_res = col_instance.insert_many(documents=doc_list)
            return len(insert_res.inserted_ids) == doc_list_length
        except BulkWriteError as err:
            logger.warning(err)
            return True
        except Exception as err:
            logger.error(err)
            return False

    def find_data(
        self,
        col_name: str,
        *,
        query: Optional[Dict] = None,
        col_show: Optional[Dict] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        data_id: Optional[str] = None
    ) -> Optional[List]:
        try:
            col_instance = self._mongo_db_client[col_name]
            if query is None:
                query = {}

            if data_id is not None:
                query.update({"_id": ObjectId(data_id)})

            if (page is not None and page_size is not None) and (page >= 0 and page_size >= 0):
                offset = page * page_size
                return list(col_instance.find(query, col_show).limit(page_size).skip(offset))

            return list(col_instance.find(query, col_show))
        except Exception as err:
            logger.error(err)
            return None

    def update(
        self,
        col_name: str,
        data: Dict,
        *,
        query: Optional[Dict] = None,
        data_id: Optional[str] = None,
    ) -> bool:
        try:
            col_instance = self._mongo_db_client[col_name]

            if query is None:
                query = {}

            if data_id is None:
                query.update({"_id": ObjectId(data_id)})

            col_instance.find_one_and_update(query, {"$set": data})
            return True
        except Exception as err:
            logger.error(err)
            return False

    def upsert(
        self,
        col_name: str,
        data: Dict,
        *,
        query: Optional[Dict] = None,
    ) -> Optional[str]:
        try:
            if query is None:
                query = {}

            col_instance = self._mongo_db_client[col_name]
            # {"$set": data}
            res = col_instance.update_one(query, {"$set": data}, upsert=True)
            # matched_count  匹配到的行数
            # modified_count 修改的行数
            # upserted_id    upserted_id
            # 新数据返回 0, 0, _id<MongoDB ObjectID>
            if res.upserted_id is not None:
                # New Data
                return str(res.upserted_id)
            else:
                return "Exist"
        except Exception as err:
            logger.error(err)
            return None

    def upsert_many(
        self,
        col_name: str,
        data: List[Dict],
        *,
        query: Optional[Dict] = None,
    ):
        try:
            if query is None:
                query = {}

            col_instance = self._mongo_db_client[col_name]
            # {"$set": data}
            res = col_instance.update_many(query, {"$set": data}, upsert=True)
            # matched_count  匹配到的行数
            # modified_count 修改的行数
            # upserted_id    upserted_id
            # 新数据返回 0, 0, _id<MongoDB ObjectID>
            if res.upserted_id is not None:
                # New Data
                return str(res.upserted_id)
            else:
                return "Exist"
        except Exception as err:
            logger.error(err)
            return None
