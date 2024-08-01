import sys

sys.path.append("..")
from MySqlCon import Mysql


mysql = Mysql()
mysql.getAll("select ")