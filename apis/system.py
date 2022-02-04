"""
系统类API /system
"""
import asyncio

from sanic import Sanic, HTTPResponse, Request, json
from websocket import WebSocket
import hashlib
import psutil
from json import dumps


app = Sanic.get_app("SwiftNext")


@app.post("/system/encrypt")
async def encrypt(request: Request) -> HTTPResponse:
    """
    使用加密密码的方式加密明文
    """
    # 加盐并加密
    return json({
        "encrypted": hashlib.md5(
            f"ここで振り返る{request.json.get('content')}"
            f"もうすぐだよ{request.json.get('content')}"
            f"知らない世界も{request.json.get('content')}"
            f"歩いてみよう"
                .encode("utf-8")).hexdigest()
    })


@app.get("/system/memory")
async def get_memory(request: Request) -> HTTPResponse:
    """
    获取系统内存信息
    """
    # 获取系统内存信息
    mem = psutil.virtual_memory()
    return json({
        "total_capacity": mem.total,
        "used_capacity": mem.used,
    })


@app.websocket("/memory")
async def memory(request: Request, ws: WebSocket):
    """
    监听系统内存变化
    """
    # 初始化内存信息
    mem = psutil.virtual_memory()
    # 发送初始化内存信息
    await ws.send(dumps({
        "total_capacity": mem.total,
        "used_capacity": mem.used,
    }))
    # 循环监听内存变化
    while True:
        # 获取内存信息
        mem = psutil.virtual_memory()
        # 发送内存信息
        await ws.send(dumps({
            "total_capacity": mem.total,
            "used_capacity": mem.used,
        }))
        # 等待1秒
        await asyncio.sleep(1)

