# -*- encoding: utf-8 -*-
import gzip
import hashlib
import json
import time
import uuid
from Crypto.Cipher import AES
import base64


def encrypt_password(password_str: str) -> str:
    """
    加密密码明文
    :param password_str: 密码明文
    :return: 加密后的密码
    """
    salted = f"IOjdjoa{password_str}Saplajtjioa{password_str}"  # 加盐
    return hashlib.sha256(salted.encode()).hexdigest()  # sha256加密


def gen_client_id() -> str:
    """
    生成一个32位的client id
    :return: 随机的32位client id
    """
    return hashlib.md5(f'{uuid.uuid1()}'.encode()).hexdigest()


def get_client_password(client_id: str) -> str:
    """
    获取和client通信的密码
    :param client_id: client的id
    :return: 通信密码
    """
    salted = f"abhuidhaui{client_id}dasjjdioaj{client_id}"
    return hashlib.md5(salted.encode()).hexdigest()


def pad(data: str, target_length=16) -> str:
    """
    补全字符位数
    :param data:原始数据
    :param target_length: 目标长度
    :return: 补全后的数据
    """
    pad_str = '\0' * (target_length - (len(data) % target_length))
    return data + pad_str


def unpad(data: bytes) -> bytes:
    """
    去除补全
    :param data: 原始数据
    :return: 去除补全后的数据
    """
    return data.replace(b'\x00', b'')


def encrypt(data: str, password: str) -> str:
    """
    加密数据
    :param data: 要加密的源数据
    :param password: 密码
    :return: 加密后的数据
    """
    bs = AES.block_size
    data = base64.b16encode(data.encode()).decode()  # 将data转换为base16编码
    data = pad(data, bs)
    cipher = AES.new(password.encode(), AES.MODE_ECB)
    data = cipher.encrypt(data)
    data = gzip.compress(data)
    return base64.b16encode(data).decode()


def decrypt(data, password):
    cipher = AES.new(password.encode(), AES.MODE_ECB)
    data = base64.b16decode(data)
    data = gzip.decompress(data)
    data = cipher.decrypt(data)
    data = base64.b16decode(unpad(data)).decode()
    return data