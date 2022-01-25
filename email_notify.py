"""
一些关于通知 / 邮件的工具函数
"""
import smtplib
from email.mime.text import MIMEText

import config

with open("./verify_code.cn.html", "r") as f:
    verify_code_html_cn = f.read()

with open("./verify_code.en.html", "r") as f:
    verify_code_html_en = f.read()


def client():
    """
    获取一个新的邮件客户端
    """
    obj = smtplib.SMTP()
    obj.connect(config.host, config.port)
    obj.login(config.smtp_user, config.smtp_password)
    return obj


def send_verify_code(code, receiver, expire_minutes=5, username="DummyUser", lang="cn"):
    """
    发送邮件验证码
    """
    obj = client()
    if lang == "cn":
        subject = "SwiftNext: 邮箱验证码"
        body = verify_code_html_cn.format(code=code, username=username, expire=expire_minutes)
    else:
        subject = "SwiftNext: Email Verification Code"
        body = verify_code_html_en.format(code=code, username=username, expire=expire_minutes)
    msg = MIMEText(body, 'html', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = "SwiftNext"
    msg['To'] = username

    obj.sendmail(config.smtp_user, receiver, msg.as_string())
