运行命令 
``python test.python-html-thread.py -p=[爬取数量,12倍数] -cur=[地区编码]D -re=[地区编码]``

例如：
``python test.python-html-thread-bak.py -p=12 -cur=USD -re=US``

数据配置在 ``Config.py``:

![img.png](img.png)

redis配置在启动类 ``test.python-html-thread.py``:

![img_1.png](img_1.png)

sql数据库编码utf8mb4文件在 ``sql\crm-python-data-crawl.sql``

![img_v3_02d3_cc689abb-62eb-4826-8199-e8f89806e10g](https://github.com/user-attachments/assets/99af503b-99c2-4917-a515-800461264244)
![image](https://github.com/user-attachments/assets/38728f64-6082-44ff-a48d-18ad830946be)
![image](https://github.com/user-attachments/assets/3ab66f77-c874-4dac-9d0e-55c68e474919)
![image](https://github.com/user-attachments/assets/fa501d16-b785-4ad1-85e2-6baba5aa607b)
