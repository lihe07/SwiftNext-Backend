"""
会话管理器
"""
import asyncio
import time
from concurrent.futures._base import CancelledError
from datetime import datetime

from bson import ObjectId
from sanic import Sanic, Request, HTTPResponse, json
import uuid

import config
from apis import try_until_success, get_ip
from config import database
from sanic.log import logger

app = Sanic.get_app("SwiftNext")


# 调试时，先不清理会话
# logger.warning("清空已有会话")
# database().sessions.delete_many({})


@app.middleware("request")
async def session_manager(request: Request):
    ip = get_ip(request)
    client_fingerprint = request.cookies.get("fingerprint")
    dummy_session = {
        "fingerprint": str(uuid.uuid4()),
        "login": False,
        "permission": 0,
        "ip": ip,
        "expire_at": datetime.utcnow() + config.session_lifetime,
    }
    if client_fingerprint is None:
        # 如果没有指纹，则创建一个新的会话
        request.ctx.session = dummy_session
        request.ctx.session_need_update = True
    else:
        # 如果有指纹，则从数据库中取得会话
        async def _():
            return await database().sessions.find_one({"fingerprint": str(client_fingerprint)}, {"_id": 0})

        session = await try_until_success(_)
        if session is None:
            # session已经过期
            logger.info(f"客户端session已经过期 {request.cookies.get('fingerprint')}")
            request.ctx.session = dummy_session
            request.ctx.session_need_update = True
        else:
            if session['ip'] != ip:
                if config.logout_on_ip_change:
                    logger.info(f"客户端的IP发生了变化，删除会话 {session['ip']} => {ip}")
                    await database().sessions.delete_one({"fingerprint": client_fingerprint})
                    request.ctx.session = dummy_session
                    request.ctx.session_need_update = True
                    return
                else:
                    logger.info(f"客户端的IP发生了变化，更新会话 {session['ip']} => {ip}")
                    session['ip'] = ip
                    await database().sessions.update_one({"fingerprint": client_fingerprint}, {"$set": {"ip": ip}})
            # 为这个session续命
            expire_time = datetime.utcnow() + config.session_lifetime
            session['expire_at'] = expire_time
            try:
                await database().sessions.update_one({"fingerprint": client_fingerprint},
                                                     {"$set": {"expire_at": expire_time}})
            except CancelledError:
                logger.warning("在为会话续命时发生了异常")
                await database().sessions.insert_one(session)

            if 'user' in session.keys():
                # 如果这个session是登录的，为其设置用户信息
                user = await database().users.find_one({"_id": ObjectId(session['user'])})
                user['uid'] = str(user['_id'])
                user.pop('_id')
                session['user'] = user
            request.ctx.session = session
            request.ctx.session_need_update = False


@app.middleware("response")
async def check_fingerprint(request: Request, response: HTTPResponse):
    """
    检查客户端的指纹
    """
    try:
        if request.ctx.session_need_update:
            # 清除旧会话
            await database().sessions.delete_one({"fingerprint": request.ctx.session['fingerprint']})
            response.cookies["fingerprint"] = request.ctx.session.get("fingerprint")
            response.cookies["fingerprint"]["samesite"] = "None"
            response.cookies["fingerprint"]["secure"] = True
            # response.cookies["fingerprint"]["domain"] = "localhost:3000"
            sess = request.ctx.session
            if 'user' in sess.keys():
                # 处理sess
                sess['user'] = sess['user']['uid']
            # 创建新的会话
            # logger.info(sess)
            try:
                await database().sessions.insert_one(sess)
            except:
                logger.error(f"无法创建新的会话 {request.ctx.session}")
            # return response
    except AttributeError:
        pass
