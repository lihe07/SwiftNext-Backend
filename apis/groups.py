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
        group['created_at'] = group['created_at'].timestamp()
    return json(groups)


@app.post("/groups")
@perm([2, 3])
async def create_group(request: Request) -> HTTPResponse:
    group_name = request.json.get('name')
    points = request.json.get('points')
    invalid_field = json({
        "code": 4,
        "message": {
            "cn": "参数无效",
            "en": "Invalid parameters"
        }
    }, 400)
    if not group_name or not points:
        return invalid_field
    if not isinstance(points, list):
        return invalid_field
    if len(points) < 1:
        return json({
            "code": 4,
            "message": {
                "cn": "至少需要创建一个调查点",
                "en": "At least need to create one survey point"
            }
        }, 400)
    for point in points:
        name = point.get('name')
        longitude = point.get('longitude')
        latitude = point.get('latitude')
        if not name or not longitude or not latitude:
            return invalid_field

    result = await database().groups.insert_one({
        "name": group_name,
        "created_at": datetime.datetime.utcnow(),
        "managers": [request.ctx.session['user']['uid']],
    })
    group_id = str(result.inserted_id)
    for point in points:
        await database().positions.insert_one({
            "belongs_to": group_id,
            "name": point['name'],
            "longitude": point['longitude'],
            "latitude": point['latitude'],
        })
    await database().users.update_one({"_id": ObjectId(request.ctx.session['user']['uid'])}, {
        "$set": {
            "groups": [group_id]
        }
    })
    return json({
        "id": group_id
    })


@app.get("/groups/<group_id>")
async def get_group(request: Request, group_id: str) -> HTTPResponse:
    try:
        group = await database().groups.find_one({"_id": ObjectId(group_id)})
        if group is None:
            return json({
                "code": 1001,
                "message": {
                    "cn": "小组不存在",
                    "en": "Group does not exist"
                }
            }, 404)
        group['id'] = str(group['_id'])
        del group['_id']
        group['created_at'] = group['created_at'].timestamp()
        return json(group)
    except bson.errors.InvalidId:
        return json({
            "code": 4,
            "message": {
                "cn": "小组不存在",
                "en": "Group does not exist"
            }
        }, 404)


@app.get("/groups/<group_id>/members")
@perm([1, 2, 3])
async def get_group_members(request: Request, group_id: str) -> HTTPResponse:
    """
    获取某个小组的成员ID
    """
    try:
        group = await database().groups.find_one({"_id": ObjectId(group_id)})
        if group is None:
            return json({
                "code": 1001,
                "message": {
                    "cn": "小组不存在",
                    "en": "Group does not exist"
                }
            }, 404)
        members = await database().users.find({"groups": {"$elemMatch": {"$eq": group_id}}}, {'_id': 1}).to_list(None)
        return json([str(member['_id']) for member in members])
    except bson.errors.InvalidId:
        return json({
            "code": 1001,
            "message": {
                "cn": "小组不存在",
                "en": "Group does not exist"
            }
        }, 404)


@app.patch("/groups/<group_id>")
@perm([2, 3])
async def edit_group(request: Request, group_id: str) -> HTTPResponse:
    # 先检查小组是否存在
    try:
        group = await database().groups.find_one({"_id": ObjectId(group_id)})
        if group is None:
            return json({
                "code": 4,
                "message": {
                    "cn": "小组不存在",
                    "en": "Group does not exist"
                }
            }, 404)
    except bson.errors.InvalidId:
        return json({
            "code": 4,
            "message": {
                "cn": "小组不存在",
                "en": "Group does not exist"
            }
        }, 404)
    # 检查是否有权限
    if request.ctx.session['user']['uid'] not in group['managers']:
        return json({
            "code": 1,
            "message": {
                "cn": "您没有权限修改该小组",
                "en": "You have no permission to edit this group"
            }
        }, 403)
    # 检查有无非法字段
    allowed_fields = ['name', 'cover', 'managers']
    for field in request.json:
        if field not in allowed_fields:
            return json({
                "code": 4,
                "message": {
                    "cn": "非法字段",
                    "en": "Illegal field"
                }
            }, 400)
    # 执行修改
    await database().groups.update_one({"_id": ObjectId(group_id)}, {
        "$set": request.json
    })
    return await get_group(request, group_id)



@app.delete("/groups/<group_id>/members/<member_id>")
@perm([1, 2, 3])
async def quit_group(request: Request, group_id: str, member_id: str) -> HTTPResponse:
    # 如果是管理员，则不能退出小组
    if request.ctx.session['user']['uid'] in (await database().groups.find_one({"_id": ObjectId(group_id)}))['managers']:
        return json({
            "code": 1001,
            "message": {
                "cn": "您是小组管理员，退出小组前请先转让管理权或者解散小组",
                "en": "You are the group manager, you can not quit the group"
            }
        }, 400)

    try:
        group = await database().groups.find_one({"_id": ObjectId(group_id)})
        if group is None:
            return json({
                "code": 1001,
                "message": {
                    "cn": "小组不存在",
                    "en": "Group does not exist"

                }
            }, 404)
        await database().users.update_one({"_id": ObjectId(member_id)}, {
            "$pull": {
                "groups": group_id
            }
        })
        group = await database().groups.find_one({"_id": ObjectId(group_id)})
        group['id'] = str(group['_id'])
        del group['_id']
        return json(group)
    except bson.errors.InvalidId:
        return json({
            "code": 1001,
            "message": {
                "cn": "小组不存在",
                "en": "Group does not exist"
            }
        }, 404)
