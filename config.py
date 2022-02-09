import datetime
import smtplib

from motor.motor_asyncio import AsyncIOMotorClient
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr

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
# 模型的地址
model_path = "./model.best.onnx"
# dist的位置 包括favicon.ico和index.html
dist_path = "../SwiftNext-Frontend/dist"
# assets的位置
assets_path = "../SwiftNext-Frontend/dist/assets"


def database():
    return AsyncIOMotorClient(mongo_uri).swiftnext


def client():
    return AsyncIOMotorClient(mongo_uri)


def get_email_message(name, code, expire_minutes, lang):
    if lang == "en":
        with open("./verify_code.en.html") as f:
            template = f.read()
        subject = "Verification code for SwiftNext"
    else:
        with open("./verify_code.cn.html") as f:
            template = f.read()
        subject = "SwiftNext验证码"
    template = template.replace("%username%", name)
    template = template.replace("%code%", str(code))
    template = template.replace("%expire%", str(expire_minutes))
    message = MIMEText(template, 'html', 'utf-8')
    message['From'] = formataddr(("SwiftNext", smtp_user))
    message['To'] = Header(name, 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    return message


def get_smtp():
    obj = smtplib.SMTP(smtp_server, smtp_port)
    obj.login(smtp_user, smtp_password)
    return obj
