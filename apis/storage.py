"""
文件相关API
"""
import datetime
import hashlib
import io
import os.path
import uuid

import aiofiles
import bson.errors
import cv2
from bson import ObjectId
from sanic import Sanic, Request, HTTPResponse, response, json
from sanic.log import logger
from sanic.response import ResponseStream

from apis import perm, app
import config
import mimetypes


@app.post("/storage")
@perm([1, 2, 3])
async def upload(request: Request) -> HTTPResponse:
    """
    上传新的附件
    """

    if request.files.get("file") is not None:
        file = request.files.get("file")
        logger.info(file.type)
        mimetype, encoding = mimetypes.guess_type(file.name)
        if mimetype is None:
            return json({
                "code": 1001,
                "message": {
                    "cn": "无法猜测文件类型! 请确保文件后缀名完整",
                    "en": "Unable to guess file type! Please make sure the file extension is correct"
                },
            }, 400)
        # 保存本地
        ext = file.name.split('.')[-1] if len(file.name.split(".")) > 0 else None
        name = str(uuid.uuid4()) + "." + ext
        path = os.path.join(config.storage_dir, name)

        async with aiofiles.open(path, "wb") as f:
            await f.write(file.body)
            # while True:
            #     chunk = await request.stream.read()
            #     if not chunk:
            #         break
            #     await f.write(chunk)
        md5 = hashlib.md5(file.body).hexdigest()

        result = await config.database().storage.insert_one({
            "filename": file.name,
            "local_path": path,
            "mime_type": mimetype,
            "created_at": datetime.datetime.utcnow(),
            "owner": request.ctx.session['user']['uid'],
            "md5": md5
        })

        # todo: 文件名生成
        return json({
            "id": str(result.inserted_id),
        })
    else:
        return json({
            "code": 4,
            "message": {
                "cn": "请上传一个文件",
                "en": "Please upload a file"
            }
        }, 400)


async def check_md5(md5):
    if md5 is None:
        return False

    result = await config.database().storage.find_one({"md5": md5})
    if result is None:
        return False
    return result


@app.post("/storage/link")
@perm([1, 2, 3])
async def link(request: Request) -> HTTPResponse:
    # 为某个已经存在的文件生成一个新的数据库链接
    result = await check_md5(request.json.get("md5"))
    if result is False:
        return json({
            "code": 1001,
            "message": {
                "cn": "文件不存在",
                "en": "File not found"
            }
        }, 400)
    filename = request.json.get("name") if request.json.get("name") is not None else result["name"]
    inserted = await config.database().storage.insert_one({
        "md5": request.json.get("md5"),
        "owner": request.ctx.session['user']['uid'],
        "created_at": datetime.datetime.utcnow(),
        "local_path": result["local_path"],
        "mime_type": result["mime_type"],
        "filename": filename
    })
    return json({
        "id": str(inserted.inserted_id),
        "name": filename
    })


@app.get("/storage/inline/<fid>")
async def get_inline(request: Request, fid: str):
    """
    获取附件的内联链接
    """
    if fid is None:
        return json({
            "code": 4,
            "message": {
                "cn": "请指定一个文件ID",
                "en": "Please specify a file ID"
            }
        }, 400)
    try:
        result = await config.database().storage.find_one({"_id": ObjectId(fid)})
    except bson.errors.InvalidId:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    if result is None:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    return await response.file_stream(result["local_path"], mime_type=result["mime_type"], chunk_size=1024, headers={
        "Content-Disposition": "inline; filename=\"{}\"".format(result["filename"]),
        "Content-Type": result["mime_type"],
        "Cache-Control": "max-age=86400",  # 控制缓存 1天
    })


@app.get("/storage/inline/<fid>/w/<width>/h/<height>")
async def get_sized_image(request: Request, fid: str, width: int, height: int):
    """
    获取图片的缩略图
    :param request:
    :param fid:
    :param width:
    :param height:
    :return:
    """
    if fid is None:
        return json({
            "code": 4,
            "message": {
                "cn": "请指定一个文件ID",
                "en": "Please specify a file ID"
            }
        }, 400)
    try:
        result = await config.database().storage.find_one({"_id": ObjectId(fid)})
    except bson.errors.InvalidId:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    if result is None:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    if result["mime_type"] != "image/jpeg":
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不是图片",
                "en": "The specified file is not an image"
            },
            "description": {
                "file_id": fid,
                "mime_type": result["mime_type"]
            }
        }, 400)
    if width is None or height is None:
        return json({
            "code": 4,
            "message": {
                "cn": "请指定宽度和高度",
                "en": "Please specify width and height"
            }
        }, 400)
    if width <= 0 or height <= 0:
        return json({
            "code": 4,
            "message": {
                "cn": "宽度和高度必须大于0",
                "en": "Width and height must be greater than 0"
            }
        }, 400)
    img = cv2.imread(result["local_path"])
    img = cv2.resize(img, (width, height))
    content = cv2.imencode(".jpg", img)[1].tobytes()
    return response.raw(content, headers={
        "Content-Type": "image/jpeg",
        "Cache-Control": "max-age=86400",  # 控制缓存 1天
    })


@app.get("/storage/download/<fid>")
async def get_download(request: Request, fid: str):
    """
    以附件的形式发送某个文件
    :param request:
    :param fid:
    :return:
    """
    if fid is None:
        return json({
            "code": 4,
            "message": {
                "cn": "请指定一个文件ID",
                "en": "Please specify a file ID"
            }
        }, 400)
    try:
        result = await config.database().storage.find_one({"_id": ObjectId(fid)})
    except bson.errors.InvalidId:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    if result is None:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    return await response.file_stream(result["local_path"], mime_type=result["mime_type"], chunk_size=1024, headers={
        "Content-Disposition": "attachment; filename=\"{}\"".format(result["filename"]),
        "Content-Type": result["mime_type"],
        "Cache-Control": "max-age=86400",  # 控制缓存 1天
    })


def delete_attachments(attachments: list):
    """
    删除附件
    :param attachments:
    :return:
    """
    for attachment in attachments:
        # 如果这个文件在数据库只存在一次，那么就删除它
        md5 = attachment["md5"]
        count = config.database().storage.count_documents({"md5": md5})
        if count == 1:
            try:
                os.remove(attachment["local_path"])
            except FileNotFoundError:
                logger.warning("文件不存在: {}".format(attachment["local_path"]))
        config.database().storage.delete_one({"_id": attachment["_id"]})


@app.delete("/storage/<fid>")
@perm([1, 2, 3])
async def delete_attachment(request: Request, fid: str):
    """
    删除附件
    非管理员只能删除自己的
    :param request:
    :param fid:
    :return:
    """
    try:
        attachment = await config.database().storage.find_one({"_id": ObjectId(fid)})
    except bson.errors.InvalidId:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    if attachment is None:
        return json({
            "code": 4,
            "message": {
                "cn": "指定的文件不存在",
                "en": "The specified file does not exist"
            },
            "description": {
                "file_id": fid
            }
        }, 404)
    if attachment["owner"] != request.ctx.session['user']['uid']:
        return json({
            "code": 4,
            "message": {
                "cn": "您没有权限删除该文件",
                "en": "You do not have permission to delete this file"
            },
            "description": {
                "file_id": fid,
                "owner": attachment["owner"]
            }
        }, 403)

    delete_attachments([attachment])
    return response.empty(204)
