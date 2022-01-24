from sanic import Sanic, Request
import config
from sanic.log import logger
import apis

logger.info("创建APP实例")
app = Sanic("SwiftNext")

logger.info("创建SocketIO实例")
__import__("sio")

logger.info("注册API")
apis.register_apis()

logger.info("注册错误处理器")
__import__("errors")

logger.info("启动会话管理器")
__import__("sessions")

logger.info("启动VerTeX保护器")
__import__("vertex")

if __name__ == '__main__':
    logger.info(f"服务运行在 {config.host}:{config.port}")
    app.run(host=config.host, port=config.port, workers=config.workers, auto_reload=True)
