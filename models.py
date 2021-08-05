# -*- encoding: utf-8 -*-
from pydantic import BaseModel
from typing import Optional, List, Any
import threading
import time
import logging
from fastapi import HTTPException

import config
import utils

try:
    import orjson as json
except ImportError:
    import json


class LoginUser(BaseModel):
    email: str
    password: str


class User(BaseModel):
    user_id: str
    email: str
    password: str
    username: str


class Client(BaseModel):
    client_id: str
    user: Optional[Any] = False
    ip: Optional[str] = None

    def get_password(self) -> str:
        """
        获取和这个client通信的专属密码
        :return: 通信密钥
        """
        return utils.get_client_password(self.client_id)

    def encrypt_data(self, data: dict) -> str:
        """
        为这个客户端加密数据
        :param data: 源数据
        :return: 加密后的字符
        """
        data = utils.encrypt(json.dumps(data), self.get_password())
        return data


class _Client(BaseModel):
    cid: str

    def __init__(self, cid: str):
        if clients[cid]:
            self.client = clients[cid]
        else:
            raise HTTPException(status_code=403, detail='client id错误!', error_code=2)


class ClientCache(threading.Thread):
    """
    用于保存client的对象
    键值对模式
    """

    def __init__(self) -> None:
        super().__init__()
        self._data = {}
        self.start()  # 开启线程

    def run(self) -> None:
        """
        主循环
        """
        while self.is_alive():
            # 只要线程存活就一直走
            new_data = {}
            for k, v in self._data.items():
                expired_time = v['expired_time']
                if expired_time >= time.time():
                    # 这个客户端没有超时
                    new_data[k] = v
                else:
                    # 客户端超时了
                    # v['client_obj'].set_expired(True)
                    # print('客户端超时')
                    logging.warning('客户端超时!')
            self._data = new_data
            time.sleep(1)

    def __len__(self) -> int:
        """
        获取存活的client的个数
        :return: 客户端个数
        """
        return len(self._data.keys())

    def __getitem__(self, item: str) -> Client or None:
        obj = self._data.get(item)
        if obj:
            if obj['expired_time'] < time.time():
                # 客户端超时了
                return None
            else:
                # 返回客户端对象
                return obj['client_obj']
        else:
            return None

    def __contains__(self, item: str) -> bool:
        return item in self._data.keys()

    def heartbeat(self, client_id: str) -> bool:
        """
        客户端心跳 延长客户端寿命
        :param client_id: 客户端的ID
        :return 是否成功
        """
        if client_id in self._data.keys():
            expired_time = self._data[client_id]['expired_time']
            if expired_time < time.time():
                return False
            # 更新存活时间
            self._data[client_id]['expired_time'] += config.CLIENT_LIFT_TIME
            return True
        else:
            return False

    def get_expired_time(self, client_id: str) -> int or None:
        """
        获取客户端过期时间
        :param client_id: 客户端id
        :return: 过期时间 或者 None
        """
        if client_id in self._data.keys():
            return self._data[client_id]['expired_time']
        else:
            return None

    def create_new_client(self) -> Client:
        """
        创建一个新的客户端
        :return: Client对象
        """
        new_client_config = {
            'client_id': utils.gen_client_id(),
        }
        new_client = Client(**new_client_config)  # 创建一个新的client
        new_data = {
            'client_obj': new_client,  # 可以看作给这个新的client创建了一个引用 它指向内存中的new_client
            'expired_time': time.time() + config.CLIENT_LIFT_TIME
        }
        self._data[new_client_config['client_id']] = new_data
        return new_client  # 返回的也是一个引用 保证new_client在内存中只有一个


clients = ClientCache()
