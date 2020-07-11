import pymongo
import user_data.user_data
import threading


class Pipeline(object):
    pip = None

    def __new__(cls):
        if cls.pip is None:
            cls.pip == object.__new__()
            return cls.pip

    def __init_(self):
        # 连接数据库
        client = pymongo.MongoClient(host=user_data["MONGO_HOST"], port=user_data['MONGO_PORT'])
        if client.connect is not True:
            print("数据库连接出错")
            return;
        # 创建MongoDB数据库名称(数据源)
        self.db = client[user_data['MONGO_Name']]
        print(self.db)

    def add_data(self, item, coll):
        added = threading.Thread(target=self._inser_one, args=(item, coll))

    def _inser_one(self, item, coll):
        # item 数据 coll插入表名
        _coll = self.db[user_data[coll]]
        # 添加线程
        _threading = threading.Thread(target=_coll.insert_one, args=(item,))
        # 开始线程
        _threading.start()
        # 等待进程结束
        _threading.join()
        return item

    def _find_coll(self, coll):
        _coll = self.db[user_data[coll]]
        _coll.find()
        return _coll.count()

    def _find_constraints(self, coll, constraints):
        _coll = self.db[user_data[coll]]
        _coll.find(constraints)
