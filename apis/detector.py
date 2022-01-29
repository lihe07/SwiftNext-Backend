"""
From NanoDet2
"""
import asyncio
import threading
from asyncio import as_completed
from concurrent.futures import ThreadPoolExecutor

import onnxruntime as rt
import numpy as np
import cv2
import socketio
from bson import ObjectId
from sanic import Sanic, Request, HTTPResponse, json, response
from sanic.log import logger

from operators import max_pooling, heatmap_top_k, median_blur

import config
from apis import perm, storage
from config import database

heatmap_top_k(np.random.rand(10, 10), 10)


def tile_edge(size, window_size):
    """
    平均切割一条边
    大概吧
    """
    num = size // window_size
    avg_size = size // num
    return num, avg_size


def split_batch(batches, batch_size):
    """
    将一个batch分成多个batch
    """
    return [np.array(batches[i:i + batch_size]) for i in range(0, len(batches), batch_size)]


def sigmoid(x):
    s = 1 / (1 + np.exp(-x))
    return s


class Pipeline:
    def __init__(self, model_path, window_size=(800, 800), batch_size=1):
        self.sess = rt.InferenceSession(model_path)
        self.hm_output = "220"
        self.input_size = (800, 800)
        self.window_size = window_size  # 宽 高
        self.batch_size = batch_size
        self.overlap = 10  # 两个框的重叠区域
        self.mean = np.array([1.785167, 1.533696, 1.380282]).reshape(1, 1, 3)
        self.std = np.array([1.667162, 1.44502, 1.320071]).reshape(1, 1, 3)
        self.num = 500  # 每张图片最多检测出的雨燕数量
        self.workers = 6  # 并行数量

    def predict_worker(self, batch, metadata):
        batch = np.array(batch).reshape(1, *batch.shape)
        hm = self.sess.run([self.hm_output], {'input.1': batch})[0]
        hm = sigmoid(hm)
        # 将hm和wh转换成原图的尺寸
        # 对hm应用nms
        hm = hm.reshape(200, 200)
        keep = max_pooling(hm, (3, 3), 1, 1)
        hm = hm * (keep == hm)
        hm = hm.reshape(200, 200)
        hm = cv2.resize(hm, None, fx=metadata['width_scale'] * 4, fy=metadata['height_scale'] * 4)
        return hm, metadata

    async def predict(self, img, task_id):
        """
        对单张图片执行预测
        """
        logger.info("Pipeline开始执行!")
        await sio.emit('pipeline_started', {'task_id': task_id})
        tiles, metadata = self.pre_process(img)
        full_hm = np.zeros((img.shape[0], img.shape[1]))

        # with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
        #     todo = []
        #     for batch, _metadata in zip(tiles, metadata):
        #         task = lambda: self.predict_worker(batch, _metadata)
        #         future = executor.submit(task)
        #         todo.append(future)
        #     for future in concurrent.futures.as_completed(todo):
        #         hm, metadata = future.result()
        #         ic(hm.max(), hm.min())
        #         assert metadata['start_x'] >= 0 and metadata['start_y'] >= 0
        #         assert metadata['end_x'] <= img.shape[1] and metadata['end_y'] <= img.shape[0]
        #         full_hm[metadata['start_y']: metadata['end_y'], metadata['start_x']: metadata['end_x']] += hm
        #
        i = 1
        for batch, metadata in zip(tiles, metadata):
            logger.info("进度: {}/{}".format(i, len(tiles)))
            await sio.emit('pipeline_progress', {'task_id': task_id, 'progress': i, 'total': len(tiles)})
            hm, metadata = self.predict_worker(batch, metadata)
            full_hm[metadata['start_y']: metadata['end_y'], metadata['start_x']: metadata['end_x']] += hm
            i += 1

        full_hm[full_hm > 1] = 1

        scores, points = heatmap_top_k(full_hm, self.num)
        result = []
        for score, point in zip(scores, points):
            result.append({
                "score": float(score),
                "x": int(point[1]),
                "y": int(point[0])
            })
        logger.info("Pipeline执行完毕!")

        return result

    def pre_process(self, img):
        """
        对单张图片进行预处理
        """
        img = img.astype(np.float32)
        img = ((img / 255. - self.mean) / self.std).astype(np.float32)
        # 开始裁剪
        origin_height, origin_width = img.shape[:-1]  # cv2坑人的宽高顺序
        window_width, window_height = self.window_size
        global_metadata = {
            "width_scale": 1.0,  # 宽度缩放比例
            "height_scale": 1.0,  # 高度缩放比例
        }
        # print("origin_height:", origin_height, "origin_width:", origin_width)
        # print("步骤一：全局变换")
        # 先进行一个全局的缩放 保证图片宽高都大于两倍的window_size
        if origin_height < (window_height * 2):
            global_metadata["height_scale"] = (window_height * 2) / origin_height
        if origin_width < (window_width * 2):
            global_metadata["width_scale"] = (window_width * 2) / origin_width
        # 执行变换
        img = cv2.resize(img, None, fx=global_metadata["width_scale"], fy=global_metadata["height_scale"])
        current_height, current_width = img.shape[:-1]
        # print("步骤二：裁剪")
        width_num, width_tile = tile_edge(current_width, window_width)
        height_num, height_tile = tile_edge(current_height, window_height)
        input_width, input_height = self.input_size

        # global_metadata["width_scale"] *= tile_width_scale
        # global_metadata["height_scale"] *= tile_height_scale
        # 开始裁剪
        tiles = []

        # 由左到右 由上到下
        metadata = []
        for yi in range(height_num):
            for xi in range(width_num):
                start_y = yi * height_tile
                end_y = start_y + height_tile
                start_x = xi * width_tile
                end_x = start_x + width_tile

                # 如果不是贴边的话，添加overlap
                if (start_x != 0) and ((end_x + self.overlap / 2) <= current_width):
                    start_x -= int(self.overlap / 2)
                    end_x += int(self.overlap / 2)
                    tile_width_scale = (width_tile + self.overlap) / input_width
                else:
                    tile_width_scale = width_tile / input_width

                if (start_y != 0) and ((end_y + self.overlap / 2) <= current_height):
                    start_y -= int(self.overlap / 2)
                    end_y += int(self.overlap / 2)
                    tile_height_scale = (height_tile + self.overlap) / input_height
                else:
                    tile_height_scale = height_tile / input_height

                # 确保不越界
                assert end_x <= current_width and end_y <= current_height, \
                    "越界了 {},{} {},{}".format(end_x, end_y, current_width, current_height)

                assert start_x >= 0 and start_y >= 0, "越界了 {},{}".format(start_x, start_y)

                tile = img[start_y:end_y, start_x:end_x]

                tile = cv2.resize(tile, None, fx=1 / tile_width_scale, fy=1 / tile_height_scale)
                tile = tile.transpose((2, 0, 1))  # 通道分离
                tiles.append(tile)

                metadata.append({
                    "start_x": start_x,
                    "start_y": start_y,
                    "end_x": end_x,
                    "end_y": end_y,
                    "width_scale": global_metadata["width_scale"] * tile_width_scale,
                    "height_scale": global_metadata["height_scale"] * tile_height_scale,
                })

        return tiles, metadata


app = Sanic.get_app("SwiftNext")
sio = app.ctx.sio

pipeline = Pipeline(config.model_path)


@app.signal("swiftnext.detector.new_image")
async def do_detect(**context):
    result = await pipeline.predict(cv2.imread(context['image_path']), context['task_id'])
    await database().detections.find_one_and_update({"_id": ObjectId(context['task_id'])},
                                              {"$set": {"result": result, "finished": True}})
    await sio.emit("pipeline_finished", {"task_id": context['task_id']})


@app.post("/detector/task")
@perm([1, 2, 3])
async def new_task(request: Request) -> HTTPResponse:
    """
    新建检测任务
    :param request:
    :return:
    """

    db = database()
    attachment = await db.storage.find_one({"_id": ObjectId(request.json.get("attachment_id"))})
    if attachment is None:
        return json({
            "code": 4,
            "message": {
                "cn": "附件不存在",
                "en": "Attachment not found"
            }
        }, 404)
    if "image" not in attachment['mime_type']:
        return json({
            "code": 4,
            "message": {
                "cn": "附件不是图片",
                "en": "Attachment is not an image"
            }
        }, 400)

    image_path = attachment["local_path"]

    result = await db.detections.insert_one({"finished": False, "attachment": request.json.get("attachment_id")})
    task_id = str(result.inserted_id)

    # 开始检测
    app.add_task(
        app.dispatch("swiftnext.detector.new_image", context={'image_path': image_path, 'task_id': task_id})
    )
    # 这里不awaiting，因为这个任务是异步的

    return json({
        "id": task_id,
    }, 201)


@app.get("/detector/<task_id>")
@perm([1, 2, 3])
async def get_task_info(request: Request, task_id: str) -> HTTPResponse:
    result = await database().detections.find_one({"_id": ObjectId(task_id)})
    if result is None:
        return json({
            "code": 4,
            "message": {
                "cn": "任务不存在",
                "en": "Task not found"
            }
        }, 404)
    return json(result)


@app.delete("/detector/<task_id>")
@perm([1, 2, 3])
async def delete_task(request: Request, task_id: str) -> HTTPResponse:
    task = await database().detections.find_one({"_id": ObjectId(task_id)})
    if task is None:
        return json({
            "code": 4,
            "message": {
                "cn": "任务不存在",
                "en": "Task not found"
            }
        }, 404)

    attachment = await database().storage.find_one({"_id": ObjectId(task["attachment"])})

    if attachment is not None:
        storage.delete_attachments([attachment])

    result = await database().detections.delete_one({"_id": ObjectId(task_id)})
    return response.empty()
