from sanic import Sanic, json, Request, HTTPResponse, response
from config import database
from apis import perm
from bson import ObjectId

app = Sanic.get_app("SwiftNext")


@app.get("/projects")
async def get_all_projects(_) -> HTTPResponse:
    projects = await database().projects.find({}).to_list(None)
    processed = []
    for proj in projects:
        proj['id'] = str(proj['_id'])
        del proj['_id']
        processed.append(proj)

    return json(processed)


@app.post("/projects")
@perm([3])
async def create_project(request: Request) -> HTTPResponse:
    if 'title' not in request.json.keys():
        return json({
            "code": 4,
            "message": {
                "cn": "缺少title参数",
                "en": "Missing title parameter"
            }
        }, 406)
    if 'start_time' not in request.json.keys():
        return json({
            "code": 4,
            "message": {
                "cn": "缺少start_time参数",
                "en": "Missing start_week parameter"
            }
        }, 406)
    if 'duration' not in request.json.keys():
        return json({
            "code": 4,
            "message": {
                "cn": "缺少duration参数",
                "en": "Missing duration parameter"
            }
        }, 406)
    if 'running' not in request.json.keys():
        return json({
            "code": 4,
            "message": {
                "cn": "缺少running参数",
                "en": "Missing running parameter"
            }
        }, 406)
    data = request.json
    project = await database().projects.insert_one(data)
    return json({"id": str(project.inserted_id)})


@app.post("/projects/<project_id>/set_running")
async def set_running(request: Request, project_id: str) -> HTTPResponse:
    """
    设置某个项目的运行状态
    """
    running = request.json.get("running")
    if running is None:
        return json({
            "code": 4,
            "message": {
                "cn": "缺少running参数",
                "en": "Missing running parameter"
            }
        }, 406)

    if running:
        # 将所有的任务设置为未运行
        await database().projects.update_many({}, {"$set": {"running": False}})
        # 启动该项目
        await database().projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"running": True}})
    else:
        await database().projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"running": False}})

    return await get_all_projects(request)


@app.get("/projects/<project_id>")
@perm([1, 2, 3])
async def get_project(request: Request, project_id: str) -> HTTPResponse:
    """
    尝试查询一个项目
    :param request:
    :param project_id:
    :return:
    """
    project = await database().projects.find_one({"_id": ObjectId(project_id)})
    if project is None:
        return json({
            "code": 4,
            "message": {
                "cn": "项目不存在",
                "en": "Project not found"
            }
        }, 404)
    project['id'] = str(project['_id'])
    del project['_id']
    return json(project)


@app.patch("/projects/<project_id>/")
@perm([3])
async def patch_project(request: Request, project_id: str) -> HTTPResponse:
    # 允许 title, start_week, duration, running 字段
    if 'title' in request.json.keys():
        await database().projects.update_one({"_id": ObjectId(project_id)}, {"$set": {"title": request.json['title']}})
    if 'start_week' in request.json.keys():
        await database().projects.update_one({"_id": ObjectId(project_id)},
                                             {"$set": {"start_week": request.json['start_week']}})
    if 'duration' in request.json.keys():
        await database().projects.update_one({"_id": ObjectId(project_id)},
                                             {"$set": {"duration": request.json['duration']}})
    if 'running' in request.json.keys():
        await set_running(request, project_id)

    return response.empty()

@app.delete("/projects/<project_id>")
@perm([3])
async def delete_project(request: Request, project_id: str) -> HTTPResponse:
    """
    删除一个项目
    :param request:
    :param project_id:
    :return:
    """
    await database().projects.delete_one({"_id": ObjectId(project_id)})
    return response.empty()