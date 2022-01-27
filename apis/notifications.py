from sanic import Sanic, Request, HTTPResponse, json
from apis import perm
from config import database

app = Sanic.get_app("SwiftNext")


@app.get("/notifications")
async def get_my_notifications(request: Request) -> HTTPResponse:
    if "num" in request.args.keys():
        num = int(request.args.get("num"))
    else:
        num = None
    return json(await database().notifications.find({
        "to": request.ctx.session.get("uid")
    }).to_list(length=num))
