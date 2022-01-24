"""
系统类API /system
"""
from sanic import Sanic, HTTPResponse, Request, json
import hashlib
import psutil

import vertex

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


@app.ctx.sio.on("memory")
async def memory(sid, data):
    # 获取系统内存信息
    mem = psutil.virtual_memory()
    data = {
        "total_capacity": mem.total,
        "used_capacity": mem.used,
    }
    app.ctx.sio.emit("memory", data)
