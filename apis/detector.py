from json import dumps, loads

import bson.errors
import mongoengine.errors
from bson import ObjectId
from sanic import Sanic, Request, HTTPResponse, json, response
from sanic.log import logger
from websocket import WebSocket

import config
from apis import perm, storage, app
from config import database
from models.detections import Detection, FinishedDetection, ProcessingDetection

from models import to_response
from concurrent.futures import ThreadPoolExecutor

# Rust FFI
import swift_det_lib



_app = Sanic.get_app("SwiftNext")


@app.post("/detector")
@perm([1, 2, 3])
async def create_task(request: Request) -> HTTPResponse:
    """
    新创建任务
    """
    try:
        task = Detection(**request.json, creator=request.ctx.session['user']['uid'])
        task.save()
        detect_config = task.get_detect_config()
        task_id = task.id

        def progress_callback(current, total):
            logger.info("Task: {} Progress: {}/{}".format(task_id, current, total))
            _task = Detection.objects(id=str(task_id)).first()
            if _task is None:
                raise RuntimeError("Task: {} Not Found, cancelled?".format(task_id))
            _task.status = "processing"
            _task.current = current
            _task.total = total
            _task.save()

        async def do_detect():
            logger.info("Task: {} Start Detecting".format(task_id))
            result = swift_det_lib.do_detect(task.get_image_path(), detect_config, progress_callback, do_nms=False)
            logger.info("Task: {} Finished Detecting".format(task_id))
            _task = Detection.objects(id=str(task_id)).first()
            _task.status = "finished"
            _task.result = result
            _task.save()

        # 启动一个新任务
        _ = _app.add_task(do_detect())
        # 无需await
        return json({
            "task_id": str(task_id),
        })
    except bson.errors.InvalidDocument as e:
        logger.error(e)
        return json({
            "code": 4,
            "message": {
                "cn": "参数错误",
                "en": "Invalid parameters"
            }
        }, 400)


@app.get("/detector/<task_id>/status")
@perm([1, 2, 3])
async def get_task_status(request: Request, task_id: str) -> HTTPResponse:
    """
    获取某个任务的状态
    不返回任务的结果 节省带宽
    """
    try:
        task = Detection.objects(id=task_id).first()
    except mongoengine.errors.ValidationError as e:
        return json({
            "code": 4,
            "message": {
                "cn": "任务不存在",
                "en": "Task not found"
            }
        }, 404)
    if task is None:
        return json({
            "code": 4,
            "message": {
                "cn": "任务不存在",
                "en": "Task not found"
            }
        }, 404)
    if task.status == "processing":
        return json({"status": "processing", "current": task.current, "total": task.total})
    return json({"status": task.status})


@app.get("/detector/<task_id>")
@perm([1, 2, 3])
async def get_task_info(request: Request, task_id: str) -> HTTPResponse:
    try:
        task = Detection.objects(id=task_id).first()
    except mongoengine.errors.ValidationError as e:
        return json({
            "code": 4,
            "message": {
                "cn": "参数错误",
                "en": "Invalid parameters"
            },
            "description": str(e)
        }, 400)
    if task is None:
        return json({
            "code": 4,
            "message": {
                "cn": "任务不存在",
                "en": "Task not found"
            }
        }, 404)
    if request.args.get("threshold") is not None:
        threshold = float(request.args.get("threshold"))
    else:
        threshold = task.threshold
    boxes = []
    for bbox in task.result:
        if bbox["score"] >= threshold:
            boxes.append(bbox)
    task.result = boxes

    return to_response(task)


@app.put("/detector/<task_id>")
@perm([1, 2, 3])
async def update_task_result(request: Request, task_id: str) -> HTTPResponse:
    detection = Detection.objects(id=task_id).first()
    if detection is None:
        return json({
            "code": 4,
            "message": {
                "cn": "任务不存在",
                "en": "Task not found"
            }
        }, 404)
    # 执行修改
    if request.json.get("result") is not None:
        detection.result = request.json.get("result")
    if request.json.get("threshold") is not None:
        detection.threshold = request.json.get("threshold")
    detection.save()
    return to_response(detection.reload())


@app.delete("/detector/<task_id>")
@perm([1, 2, 3])
async def delete_task(request: Request, task_id: str) -> HTTPResponse:
    x = Detection.objects(id=task_id).first()
    if x is None:
        return json({
            "code": 4,
            "message": {
                "cn": "任务不存在或尚未完成",
                "en": "Task not found"
            }
        }, 404)
    x.delete()
    return response.empty()


@app.post("/detector/compute")
async def compute_number(request: Request) -> HTTPResponse:
    """
    计算多个检测结果的总数 / 最大值
    """
    func = sum
    if request.json.get("method") == "max":
        func = max
    task_ids = request.json.get("tasks")
    threshold = request.json.get("threshold")
    tasks = database().detections.find({"_id": {"$in": [ObjectId(task_id) for task_id in task_ids]}})
    nums = []
    async for task in tasks:
        result = task["result"]
        result = [r for r in result if r["score"] >= threshold]
        nums.append(len(result))
    if len(nums) == 0:
        return json(0)
    return json(func(nums))


@app.get("/detector/mine")
@perm([1, 2, 3])
async def get_user_detections(request: Request) -> HTTPResponse:
    uid = request.ctx.session['user']['uid']
    detections = Detection.objects(creator=uid)
    return to_response(detections)
