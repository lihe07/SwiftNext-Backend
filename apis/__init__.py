import asyncio
from json import dumps

from sanic import Sanic, json, Request, Blueprint
from sanic.log import logger
from copy import deepcopy

app = Blueprint('apis', url_prefix='/api')


def register_apis():
    logger.info("注册API / => index")

    @app.get("/")
    def index(request: Request):
        session = deepcopy(request.ctx.session)
        session['expire_at'] = session['expire_at'].timestamp()
        return json({"message": "Hello!!", "session": session,
                     "session_need_update": request.ctx.session_need_update})

    logger.info("注册系统类API /system/ => system")
    import apis.system
    logger.info("注册用户类API /users/ => users")
    import apis.users
    logger.info("注册存储类API /storage/ => storage")
    import apis.storage
    logger.info("注册填报类API /records/ => records")
    import apis.records
    logger.info("注册项目类API /projects/ => projects")
    import apis.projects
    logger.info("注册通知类API /notifications/ => notifications")
    import apis.notifications
    logger.info("注册小组类API /groups/ => groups")
    import apis.groups
    logger.info("注册检测类API /detector/ => detector")
    import apis.detector
    logger.info("注册调查点类API /positions/ => positions")
    import apis.positions
    logger.info("注册API蓝图 /apis/ => apis")
    Sanic.get_app("SwiftNext").blueprint(app)


# 函数装饰器 用于检查用户权限
def perm(level):
    if type(level) == int:
        level = [level]

    def wrapper(func):
        async def _(request, *args, **kwargs):
            # 检验权限
            if request.ctx.session['permission'] in level:
                return await func(request, *args, **kwargs)
            else:
                return json({
                    "code": 1,
                    "message": {
                        "cn": "权限不足",
                        "en": "Permission denied"
                    },
                    "description": {
                        "allowed": level,
                        "current": request.ctx.session['permission']
                    }
                }, 403)

        return _

    return wrapper


# 重复执行数据库任务
async def try_until_success(func, *args, **kwargs):
    while True:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"数据库访问异常 {e}")
            await asyncio.sleep(0.1)


def get_ip(request):
    if request.headers.get("x-forwarded-for"):
        return request.headers.get("x-forwarded-for")
    else:
        return request.ip
