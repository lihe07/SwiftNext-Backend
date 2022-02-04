"""
Vertex保护机制
"""
import datetime

from sanic import json, Sanic, Request, HTTPResponse, response
from sanic.log import logger
import random
import config
from apis import get_ip

app = Sanic.get_app("SwiftNext")


@app.middleware("request")
async def before_request(request: Request):
    """
    通用反CC
    """
    # 调试时不限制
    # if request.headers.get('origin') not in config.allowed_origins:
    if False:
        ip = get_ip(request)
        logger.warning(f"[{request.headers.get('origin')}] 不在Origin白名单内 IP: {ip}")
        return json({
            "code": 403,
            "message": {
                "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
                "en": "Your request has been judged as an illegal request, and has been recorded!"
            },
            "description": {
                "type": "无法确认发送者安全性",
                "ip_banned": False
            }
        }, 403)
    # logger.info(request.method)
    # if request.method == "OPTIONS":
    #     return response.empty()


# @app.middleware("response")
# async def cors(request, response):
#     response.headers['Access-Control-Allow-Origin'] = request.headers.get('origin')
#     response.headers['Access-Control-Allow-Credentials'] = 'true'
#     response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
#     response.headers[
#         'Access-Control-Allow-Headers'] = 'origin, content-type, accept, authorization, x-xsrf-token, x-request-id'


# # 一个函数装饰器，用于记录请求频率
# def protect(level):
#     """
#     请求level共有1, 2, 3
#     低、中、高
#     :param level:
#     :return:
#     """
#
#     def wrapper(func):
#         # 低保护
#         async def low(request, *args, **kwargs):
#             if random.random() > 0.7:
#                 # 30%触发检测
#                 db = config.database()
#                 coll = db.vertex_log
#                 ip = get_ip(request)
#                 result = await coll.find_one({'ip': ip})
#                 if result is None:
#                     await coll.insert_one({'ip': ip, "update_time": datetime.datetime.utcnow()})
#                 else:
#                     delta = datetime.datetime.utcnow() - result['update_time']
#                     if delta.microseconds < 200:
#                         # 两次请求时间间隔小于200毫秒
#                         return json({
#                             "code": 403,
#                             "message": {
#                                 "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                                 "en": "Your request has been judged as an illegal request, and has been recorded!"
#                             },
#                             "description": {
#                                 "type": "请求过于频繁",
#                                 "ip_banned": False
#                             }
#                         }, 403)
#                     await coll.update_one({'ip': ip}, {'$set': {'update_time': datetime.datetime.utcnow()}})
#             return await func(request, *args, **kwargs)
#
#         async def mid(request, *args, **kwargs):
#             if random.random() > 0.5:
#                 # 50%触发检测
#                 if request.headers.get("host") is None:
#                     return json({
#                         "code": 403,
#                         "message": {
#                             "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                             "en": "Your request has been judged as an illegal request, and has been recorded!"
#                         },
#                         "description": {
#                             "type": "无法确认发送者安全性",
#                             "ip_banned": False
#                         }
#                     }, 403)
#                 if request.headers.get("referer") is None:
#                     return json({
#                         "code": 403,
#                         "message": {
#                             "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                             "en": "Your request has been judged as an illegal request, and has been recorded!"
#                         },
#                         "description": {
#                             "type": "无法确认发送者安全性",
#                             "ip_banned": False
#                         }
#                     }, 403)
#                 if request.headers.get("user-agent") is None:
#                     return json({
#                         "code": 403,
#                         "message": {
#                             "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                             "en": "Your request has been judged as an illegal request, and has been recorded!"
#                         },
#                         "description": {
#                             "type": "无法确认发送者安全性",
#                             "ip_banned": False
#                         }
#                     }, 403)
#                 db = config.database()
#                 coll = db.vertex_log
#                 ip = get_ip(request)
#                 result = await coll.find_one({'ip': ip})
#                 if result is None:
#                     await coll.insert_one({'ip': ip, "update_time": datetime.datetime.utcnow()})
#                 else:
#                     delta = datetime.datetime.utcnow() - result['update_time']
#                     if delta.microseconds < 300:
#                         # 两次请求时间间隔小于300毫秒
#                         return json({
#                             "code": 403,
#                             "message": {
#                                 "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                                 "en": "Your request has been judged as an illegal request, and has been recorded!"
#                             },
#                             "description": {
#                                 "type": "请求过于频繁",
#                                 "ip_banned": False
#                             }
#                         }, 403)
#                     await coll.update_one({'ip': ip}, {'$set': {'update_time': datetime.datetime.utcnow()}})
#             return await func(request, *args, **kwargs)
#
#         async def hgh(request, *args, **kwargs):
#             if random.random() > 0.3:
#                 # 70%触发检测
#                 if request.headers.get("host") is None:
#                     return json({
#                         "code": 403,
#                         "message": {
#                             "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                             "en": "Your request has been judged as an illegal request, and has been recorded!"
#                         },
#                         "description": {
#                             "type": "无法确认发送者安全性",
#                             "ip_banned": False
#                         }
#                     }, 403)
#                 if request.headers.get("referer") is None:
#                     return json({
#                         "code": 403,
#                         "message": {
#                             "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                             "en": "Your request has been judged as an illegal request, and has been recorded!"
#                         },
#                         "description": {
#                             "type": "无法确认发送者安全性",
#                             "ip_banned": False
#                         }
#                     }, 403)
#                 if request.headers.get("user-agent") is None:
#                     return json({
#                         "code": 403,
#                         "message": {
#                             "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                             "en": "Your request has been judged as an illegal request, and has been recorded!"
#                         },
#                         "description": {
#                             "type": "无法确认发送者安全性",
#                             "ip_banned": False
#                         }
#                     }, 403)
#                 db = config.database()
#                 coll = db.vertex_log
#                 ip = get_ip(request)
#                 result = await coll.find_one({'ip': ip})
#                 if result is None:
#                     await coll.insert_one({'ip': ip, "update_time": datetime.datetime.utcnow()})
#                 else:
#                     delta = datetime.datetime.utcnow() - result['update_time']
#                     if delta.microseconds < 500:
#                         # 两次请求时间间隔小于500毫秒
#                         return json({
#                             "code": 403,
#                             "message": {
#                                 "cn": "您发送的请求被判定为非法请求，该请求已被记录，多次违规将被封禁！",
#                                 "en": "Your request has been judged as an illegal request, and has been recorded!"
#                             },
#                             "description": {
#                                 "type": "请求过于频繁",
#                                 "ip_banned": False
#                             }
#                         }, 403)
#                     await coll.update_one({'ip': ip}, {'$set': {'update_time': datetime.datetime.utcnow()}})
#             return await func(request, *args, **kwargs)
#
#         if level == 1:
#             return low
#         elif level == 2:
#             return mid
#         elif level == 3:
#             return hgh
#
#     return wrapper
