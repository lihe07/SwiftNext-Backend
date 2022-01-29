import datetime

from sanic import Sanic, json, Request, HTTPResponse, response
from config import database
from bson import ObjectId
from apis import perm

app = Sanic.get_app("SwiftNext")


@app.get("/positions/<position_id>")
@perm([1, 2, 3])
async def get_position(request: Request, position_id: str) -> HTTPResponse:
    """
    获取某个调查点的经纬度
    :param request:
    :param position_id:
    :return:
    """
    result = await database().positions.find_one({"_id": ObjectId(position_id)})
    if result:
        return json({
            "longitude": result["longitude"],
            "latitude": result["latitude"]
        })
    else:
        return json({
            "code": 4,
            "message": {
                "cn": "调查点不存在",
                "en": "Position not found"
            }
        }, 404)


@app.post("/positions")
@perm([2, 3])
async def new_position(request: Request) -> HTTPResponse:
    group_id = request.json.get("group_id")
    longitude = request.json.get("longitude")
    latitude = request.json.get("latitude")
    name = request.json.get("name")
    # 检查经纬度
    if not longitude or not latitude:
        return json({
            "code": 4,
            "message": {
                "cn": "经纬度不能为空",
                "en": "Longitude and latitude cannot be empty"
            }
        }, 400)
    # 检查经纬度范围
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        return json({
            "code": 4,
            "message": {
                "cn": "经纬度范围不正确",
                "en": "Longitude and latitude range is incorrect"
            }
        }, 400)
    # 检查组是否存在
    group = await database().groups.find_one({"_id": ObjectId(group_id)})
    if not group:
        return json({
            "code": 4,
            "message": {
                "cn": "调查小组不存在",
                "en": "Group not found"
            }
        }, 404)
    # 添加调查点
    result = await database().positions.insert_one({
        "belongs_to": group_id,
        "longitude": longitude,
        "latitude": latitude,
        "created_at": datetime.datetime.utcnow()
    })
    return json({
        "id": str(result.inserted_id)
    })
