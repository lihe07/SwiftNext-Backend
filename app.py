
from sanic import Sanic, Request
import config
from sanic.log import logger
import apis
from sanic_cors import CORS

logger.info("创建APP实例")
app = Sanic("SwiftNext")
app.config['REQUEST_MAX_SIZE'] = 200 * 1024 * 1024
app.config['CORS_SUPPORTS_CREDENTIALS'] = True

CORS_OPTIONS = {"resources": r'/*', "origins": "*", "methods": ["GET", "POST", "HEAD", "OPTIONS", "DELETE", "PUT", "PATCH"]}

CORS(app, automatic_options=True, methods=["GET", "POST", "HEAD", "OPTIONS", "DELETE", "PUT", "PATCH"])

logger.info("注册错误处理器")
__import__("errors")

logger.info("启动会话管理器")
__import__("sessions")

logger.info("启动VerTeX保护器")
__import__("vertex")

logger.info("注册前端")
__import__("frontend")

logger.info("注册API")
apis.register_apis()

if __name__ == '__main__':
    logger.info(f"服务运行在 {config.host}:{config.port}")
    app.run(host=config.host, port=config.port, workers=config.workers, auto_reload=True)
