FROM python:3.7
MAINTAINER sunhailin-Leo "379978424@qq.com"

# 暴露端口
EXPOSE 12580

# 复制项目到 Docker 中
COPY ./captcha /app/captcha
COPY ./pipeline /app/pipeline
COPY ./spiders /app/spiders
COPY ./utils /app/utils
COPY api_server.py /app/api_server.py
COPY call_spider.py /app/call_spider.py

# 项目配置
COPY config.py /app/config.py
COPY requirements.txt /app/requirement.txt

# 如果是国内服务器的话最好加上阿里云镜像地址
RUN pip install -r requirements.txt

CMD ["python", "api_server.py"]