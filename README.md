<h1 align="center">TeamLeoX_BlogsCrawler</h1>
<p align="center">
    <em>Crawling personal data from mainstream blog sites</em>
</p>

## 📣 简介

* 收集个人在主流技术博客网站的博客数据，通过在一端上浏览多端的数据，减少打开多个网页或者多个 APP 的次数。

## ✨ 特性

* 尽可能少的使用第三方库（虽然第三方库的功能很强大，但是不想项目部署的时候特别累赘 [个人观点] ）
* 尽可能多的获取个人博客数据。
* 开发尽可能多且主流的博客爬虫。

## 💻 项目部署

* 环境配置:
    * 配置文件在项目根目录下的 `config.py` 下
    * 由于用到了 `PyExecJS` 因此需要一套 NPM 的环境（版本不限），但需要安装一个库 `npm i jsdom -g` 或者使用 `cnpm i jsdom -g` (需提前安装 `cnpm`)

* 源码部署:
    * 安装项目必要的依赖包 (Linux/Unix:`pip3 install -r requirements.txt` or Windows: `pip install -r requirements.txt`)
    * 安装完后启动 `api_server.py` 即 ==> (Linux/Unix:`python3 api_server.py` or Windows: `python api_server.py`)

* Dockerfile 部署:
    * 克隆源码后修改 `config.py` 中的配置后，进行镜像打包

* Docker-compose:
    * 使用项目根目录下的 `docker-compose.yml` 进行安装

## 📖 项目进度

* **项目目前主要的开发在集中在 dev 分支上, 在项目最终评审之前将会合并到 master 分支上**
* 1、目前支持的博客网站:
    * CSDN
    * 掘金
    * 思否
    * 知乎
    * 未完待续...
* 2、数据存储:
    * Cookie 持久化
    * 个人数据的存储
* 3、API 任务管理:
    * FastAPI
    * MultiProcessing.Queue
    
## 📖 API 文档

| 接口名称 | 接口路径 | 请求方式 | 请求参数
| ---- | ---- | ---- | ---- |
| 创建任务 | /api/v1/task/create | POST | {"taskType": "create", "taskArgs": {"spiderName": <爬虫名称>, "username": <用户名>, "password": <密码>}} |
| 查看任务状态 | /api/v1/task/checkTaskStatus | POST | {"taskType": "check": taskArgs": {"job_id": <创建任务接口返回的任务 ID>}} |
| 获取任务结果 | /api/v1/task/taskResult | POST | {"taskType": "getResult", "taskArgs": {"job_id": <创建任务接口返回的任务 ID>}} |


## ⛏ 代码质量

### 代码规范

使用 [flake8](http://flake8.pycqa.org/en/latest/index.html), [Codecov](https://codecov.io/) 以及 [pylint](https://www.pylint.org/) 提升代码质量。

## 😉 Author

* [@sunhailin-Leo](https://github.com/sunhailin-Leo)
* [@ElvisWai](https://github.com/ElvisWai)

## 📃 License

MIT [©sunhailin-Leo](https://github.com/sunhailin-Leo)
