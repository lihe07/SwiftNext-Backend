import datetime

from motor.motor_asyncio import AsyncIOMotorClient

# 数据库位置
mongo_uri = 'mongodb://192.168.1.42:27017/'

# 存储用户上传内容
storage_dir = './storage'
# 服务器监听地址
host = '::'
port = 8000
# 子进程
workers = 6
# 在切换IP时退出登陆
logout_on_ip_change = False
# session的寿命
session_lifetime = datetime.timedelta(seconds=3600)
# 合法的Origins
# debug时无效
allowed_origins = ['http://localhost:3000', 'https://www.bwrrc.org', 'http://192.168.1.50:3000']
# 通知用邮箱
notify_email = 'notify@bwrrc.org.cn'
# 邮件服务器
smtp_server = 'smtp.exmail.qq.com'
# 邮件服务器端口
smtp_port = 25
# 邮件服务器用户名
smtp_user = notify_email
# 邮件服务器密码
smtp_password = 'BwR2C@2022bEijIng'

model_path = "./model.best.onnx"


def database():
    return AsyncIOMotorClient(mongo_uri).swiftnext


def client():
    return AsyncIOMotorClient(mongo_uri)
