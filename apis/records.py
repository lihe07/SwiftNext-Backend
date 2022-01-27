import datetime

from sanic import Sanic, json, Request, HTTPResponse
from config import database
from bson import ObjectId
from apis import perm

app = Sanic.get_app("SwiftNext")


@app.get("/records/<record_id>")
@perm([1, 2, 3])
async def get_record(request: Request, record_id: str) -> HTTPResponse:
    record = await database().records.find_one({"_id": ObjectId(record_id)})
    if record is None:
        return json({
            "code": 4,
            "message": {
                "cn": "找不到相关填报记录",
                "en": "No record found"
            }
        }, 404)
    return json(record)


@app.get("/records/user/<uid>")
@perm([1, 2, 3])
async def get_user_record(request: Request, uid: str) -> HTTPResponse:
    uid = ObjectId(uid)
    records = await database().records.find({"uid": uid})
    engaged_records = await database().records.find(
        {"collaborators": {"$elemMatch": {"$eq": uid}}})  # 所有collaborators中包含uid的记录
    return json(list(records) + list(engaged_records))


@app.post("/records")
@perm([1, 2, 3])
async def new_record(request: Request) -> HTTPResponse:
    """
    新建填报
    必备字段：group_id, num, time, project
    可选字段：collaborators, specific_location, origination, related_detections, attachments
    """
    record = request.json
    record["_id"] = ObjectId()
    # record["uid"] = request.user["_id"]
    record['uid'] = request.ctx.session['user']['uid']
    record["group_id"] = record["group_id"]
    record["time"] = int(record["time"])
    record["num"] = int(record["num"])
    record["project"] = record["project"]
    if "collaborators" in record:
        # 检查collaborators是否为有效用户
        for collaborator in record["collaborators"]:
            if not await database().users.find_one({"_id": ObjectId(collaborator)}):
                return json({
                    "code": 4,
                    "message": {
                        "cn": "合作者不存在",
                        "en": "Invalid collaborator"
                    },
                    "description": {
                        "id": collaborator
                    }
                }, 400)
    if "specific_location" in record:
        longitude, latitude = record["specific_location"][0], record["specific_location"][1]
        if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
            return json({
                "code": 4,
                "message": {
                    "cn": "经纬度超出范围",
                    "en": "Invalid longitude or latitude"
                },
                "description": {
                    "longitude": longitude,
                    "latitude": latitude
                }
            }, 400)
    if "origination" in record:
        # 检查朝向是否为有效值
        if record["origination"] > 360 or record["origination"] < 0:
            return json({
                "code": 4,
                "message": {
                    "cn": "朝向超出范围",
                    "en": "Invalid origination"
                },
                "description": {
                    "origination": record["origination"]
                }
            }, 400)

    if "related_detections" in record:
        record["related_detections"] = [ObjectId(d) for d in record["related_detections"]]
    if "attachments" in record:
        record["attachments"] = [ObjectId(a) for a in record["attachments"]]
    await database().records.insert_one(record)
    return json(record)


@app.get("/records")
@perm([1, 2, 3])
async def get_records(request: Request) -> HTTPResponse:
    """
    查询符合条件的填报记录
    :param request:
    :return:
    """
    query = {}
    if "uid" in request.args.keys():
        query["uid"] = request.args.get("uid")
    if "project" in request.args.keys():
        query["project"] = request.args.get("project")
    if "group" in request.args.keys():
        query["group_id"] = request.args.get("group")
    if "from" in request.args.keys():
        query["time"] = {
            "$gte": datetime.datetime.utcfromtimestamp(int(request.args.get("from")))
        }
    if "to" in request.args.keys():
        if "time" not in query.keys():
            query["time"] = {"$lte": datetime.datetime.utcfromtimestamp(int(request.args.get("to")))}
        else:
            query["time"]["$lte"] = datetime.datetime.utcfromtimestamp(int(request.args.get("to")))
    if "num" in request.args.keys():
        nums = int(request.args.get("num"))
    else:
        nums = None
    # 执行查询
    records = await database().records.find(query).to_list(nums)
    return json(records)
