import pymongo
import user_date.user_date

class Pipeline(object):
    def _init_(self):
        #连接数据库
        client =pymongo.MongoClient(host = user_date["MONGO_HOST"],port=user_date['MONGO_PORT'])
        # 创建MongoDB数据库名称(数据源)
        self.db = client[user_date['MONGO_Name']]
        print(self.db)

    def _inser_one(self,item,coll):
        #item 数据 coll插入表名
        _coll=self.db[user_date[coll]]
        _coll.insert_one(item)
        return item

    def _find_coll(self,coll):
        _coll = self.db[user_date[coll]]
        _coll.find()
        return _coll.count()

    def _find_constraints(self,coll,constraints):
        _coll = self.db[user_date[coll]]
        _coll.find(constraints)