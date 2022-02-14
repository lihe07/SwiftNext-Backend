import datetime

from mongoengine import Document, StringField, DateTimeField, ListField, ObjectIdField, IntField, BooleanField

import config
from models.storage import Attachment


class DetectConfig:
    mean = [1.785167, 1.533696, 1.380282]
    std = [1.667162, 1.44502, 1.320071]
    input_size = (800, 800)
    batch_size = 1
    heatmap_size = (200, 200)

    def __init__(self, window_size, overlap, tile_max_num, model_path):
        self.window_size = window_size
        self.overlap = overlap
        self.tile_max_num = tile_max_num
        self.model_path = model_path


class Detection(Document):
    creator = StringField(required=True)
    created_at = DateTimeField(required=True, default=datetime.datetime.utcnow)
    status = StringField(required=True, default="pending")
    attachment = StringField(required=True)
    # 一些检测配置部分
    window_size = IntField(required=True)
    overlap = IntField(required=True)
    tile_max_num = IntField(required=True)
    # 目前只有 resnet18 和 darknet
    model_name = StringField(required=True, regex="^(resnet18|darknet)$")

    meta = {
        'collection': 'detections',
        'allow_inheritance': True,
    }

    def get_detect_config(self) -> DetectConfig:
        return DetectConfig(
            (self.window_size, self.window_size),
            self.overlap,
            self.tile_max_num,
            config.resnet18 if self.model_name == "resnet18" else config.darknet
        )

    def get_image_path(self) -> str:
        attachment = Attachment.objects(id=self.attachment).first()
        return attachment.local_path


class ProcessingDetection(Detection):
    status = StringField(required=True, default="processing")
    current = IntField(required=True, default=0)
    total = IntField(required=True, default=0)


class FinishedDetection(Detection):
    status = StringField(required=True, default="finished")
    result = ListField(required=True)