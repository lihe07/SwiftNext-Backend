"""
错误响应函数
"""
import os.path

from sanic import Sanic, json, response
from sanic.exceptions import *

import config

app = Sanic.get_app("SwiftNext")


@app.exception(NotFound)
def not_found(request, exception):
    # return json({
    #     "code": 404,
    #     "description": {
    #         "url": request.url,
    #         "method": request.method,
    #     },
    #     "message": {
    #         "cn": "找不到对应资源!",
    #         "en": "Resource not found!"
    #     }
    # }, status=404)
    return response.file(os.path.join(config.dist_path, "index.html"))


@app.exception(ServerError)
def server_error(request, exception):
    return json({
        "code": 500,
        "description": str(exception),
        "message": {
            "cn": "服务器内部错误! 请联系管理员!",
            "en": "Internal Server Error! Please contact the administrator!"
        }
    }, status=500)


@app.exception(MethodNotSupported)
def method_not_supported(request, exception):
    return json({
        "code": 405,
        "description": {
            "url": request.url,
            "method": request.method,
        },
        "message": {
            "cn": "该资源不支持这种操作!",
            "en": "This resource don't support this operation!"
        }
    }, status=405)