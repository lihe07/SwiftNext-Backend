import datetime
import uuid

import bson.errors
from sanic import Sanic, response, Request, HTTPResponse, json
from config import database
from bson import ObjectId
from apis import perm

app = Sanic.get_app("SwiftNext")


@app.get("/groups/check_invitation/<invitation_id>")
@perm([1, 2, 3])
async def check_invitation(request: Request, invitation_id: str) -> HTTPResponse:
    try:
        result = await database().invitations.find_one({"_id": ObjectId(invitation_id), 'type': 'group'})
    except bson.errors.InvalidId:
        return json({
            "code": 1001,
            "message": {
                "cn": "邀请码无效或已过期",
                "en": "Invitation code is invalid or expired"
            }
        }, 404)
    if result:
        group_id = result['group_id']
        group = await database().groups.find_one({"_id": ObjectId(group_id)})
        if group:
            group['id'] = str(group['_id'])
            del group['_id']
            return json({
                "group": group
            })
    return json({
        "code": 1001,
        "message": {
            "cn": "邀请码无效或已过期",
            "en": "Invitation code is invalid or expired"
        }
    }, 404)


@app.post("/groups/invitation")
@perm([2, 3])
async def create_invitation(request: Request) -> HTTPResponse:
    group_id = request.json.get('group_id')
    expire_at = request.json.get('expire_at')
    if not group_id or not expire_at:
        return json({
            "code": 4,
            "message": {
                "cn": "缺少参数",
                "en": "Missing parameters"
            }
        }, 400)
    group = await database().groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        return json({
            "code": 4,
            "message": {
                "cn": "群组不存在",
                "en": "Group does not exist"
            }
        }, 404)
    if request.ctx.session['permission'] == 2:
        # 小组长只能邀请自己创建的群组
        if request.ctx.session['user']['uid'] not in group['managers']:
            return json({
                "code": 4,
                "message": {
                    "cn": "您不是该群组的管理员",
                    "en": "You are not the administrator of the group"
                }
            }, 403)
    invitation = {
        "_id": ObjectId(uuid.uuid4()),
        "type": 'group',
        "group_id": group_id,
        "expire_at": datetime.datetime.fromtimestamp(expire_at),
    }
    result = await database().invitations.insert_one(invitation)
    return json({
        "id": str(result.inserted_id)
    })


@app.get("/groups/apply_invitation/<invitation_id>")
@perm([1, 2, 3])
async def apply_invitation(request: Request, invitation_id: str) -> HTTPResponse:
    try:
        result = await database().invitations.find_one({"_id": ObjectId(invitation_id), 'type': 'group'})
    except bson.errors.InvalidId:
        return json({
            "code": 1001,
            "message": {
                "cn": "邀请码无效或已过期",
                "en": "Invitation code is invalid or expired"
            }
        }, 404)
    if result:
        group_id = result['group_id']
        group = await database().groups.find_one({"_id": ObjectId(group_id)})
        if group:
            # 修改用户的群组信息
            await database().users.update_one({"_id": ObjectId(request.ctx.session['user']['uid'])}, {
                "$set": {
                    "group_id": group_id,
                }
            })
            group['id'] = str(group['_id'])
            del group['_id']
            return json({
                "group": group
            })
    return json({
        "code": 1001,
        "message": {
            "cn": "邀请码无效或已过期",
            "en": "Invitation code is invalid or expired"
        }
    }, 404)


@app.get("/groups/manageable")
@perm([2, 3])
async def get_manageable_groups(request: Request) -> HTTPResponse:
    """
    获取自己管理的小组
    :param request:
    :return:
    """
    groups = await database().groups.find({"managers": {"$elemMatch": {"$eq": request.ctx.session['user']['uid']}}}) \
        .to_list(None)
    for group in groups:
        group['id'] = str(group['_id'])
        del group['_id']
    return json(groups)
