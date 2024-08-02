FROM python:3.12.4

COPY . /app
RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple/
RUN pip config set install.trusted-host mirrors.aliyun.com
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install requests redis  DBUtils xlwt selenium pymysql
RUN pip install lxml

CMD ["python", "python-request-affiliate.py", "-p=10000"]
