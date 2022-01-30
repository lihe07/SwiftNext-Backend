"""
文件相关API
"""
import datetime
import os.path
import uuid

import bson.errors
from bson import ObjectId
from sanic import Sanic, Request, HTTPResponse, response, json
from sanic.log import logger
from sanic.response import ResponseStream

from apis import perm
import config
import mimetypes

app = Sanic.get_app("SwiftNext")


@app.post("/storage")
@perm([1, 2, 3])
async def upload(request: Request) -> HTTPResponse:
    """
    上传新的附件
    """
    # logger.info(request.files)
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

        with open(path, "wb") as f:
            f.write(file.body)

        result = await config.database().storage.insert_one({
            "name": file.name,
            "local_path": path,
            "mime_type": mimetype,
            "created_at": datetime.datetime.utcnow(),
            "owner": request.ctx.session['user']['uid']
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
        "Content-Disposition": "inline; filename=\"{}\"".format(result["name"]),
        "Content-Type": result["mime_type"],
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
        "Content-Disposition": "attachment; filename=\"{}\"".format(result["name"]),
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
