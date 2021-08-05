# -*- encoding: utf-8 -*-
from pymongo import MongoClient

# config.py 保存了项目的配置
# created by lihe07 on 2021.8.4

with open('./DATABASE') as f:
    DATABASE = f.read()
BIND_IP = "0.0.0.0"
PORT = 2000
ORIGINS = ['*']
CLIENT_LIFT_TIME = 300

client = MongoClient(DATABASE)
