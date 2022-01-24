import socketio
from sanic import Sanic

app = Sanic.get_app("SwiftNext")

sio = socketio.AsyncServer(async_mode='sanic')
sio.attach(app)

app.ctx.sio = sio
