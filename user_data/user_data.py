# 用户数据（账号密码）

# MongoDB 配置，根据用户实际进行修改（填写）
# 数据库地址
MONGO_HOST = "localhost"
# 数据库IP
MONGO_PORT = 27017
# 数据库库名
MONGO_Name = "TeamLeoX"
# 数据库用户名
MONGO_USER_NAME = ""
# 数据库用户密码
MONGO_USER_PASSWORD = ""
# Mongodb 数据库可以建立的最大连接数
MONGO_CONNECTIONS_PER_HOST = 20
# Mongodb 与数据库建立连接的超时时间20min 20*60*1000
MONGO_CONNECT_TIME_OUT = 1200000
# Mongodb 一个线程获取到数据库连接的最大阻塞时间 5min 5*60*1000
MONGO_MAX_WAIT_TIME = 300000

# 表单
COLL = ["zhihu", "juejin"]
