FROM python:3.12.4

RUN pip config set global.index-url -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn
RUN pip install --upgrade pip
RUN pip install requests
RUN pip install redis
RUN pip install DBUtils
RUN pip install xlwt
RUN pip install selenium -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install pymysql
RUN pip install lxml -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install cryptography

