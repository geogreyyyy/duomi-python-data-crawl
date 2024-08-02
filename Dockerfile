FROM python:2.7

COPY . /app
RUN pip config set global.index-url http://mirrors.aliyun.com/pypi/simple/
RUN pip config set install.trusted-host mirrors.aliyun.com
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install redis  DBUtils==1.3 xlwt selenium

#CMD ["python", "app.py"]
CMD ls