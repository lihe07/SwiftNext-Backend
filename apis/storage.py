"""
文件相关API
"""
import os.path
import uuid

from sanic import Sanic, Request, HTTPResponse, response, json
from sanic.log import logger
from sanic.response import ResponseStream

from apis import perm
import config
import mimetypes

app = Sanic.get_app("SwiftNext")


@app.post("/storage/")
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
        _, ext = file.name.split(".")
        name = str(uuid.uuid4()) + "." + ext
        path = os.path.join(config.storage_dir, name)

        with open(path, "wb") as f:
            f.write(file.body)

        result = await config.database().storage.insert_one({
            "name": file.name,
            "local_path": path,
            "mime_type": mimetype,
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
    result = config.database().storage.find_one({"_id": fid})
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
    result = config.database().storage.find_one({"_id": fid})
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
