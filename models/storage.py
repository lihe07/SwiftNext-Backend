from mongoengine import Document, StringField, IntField, ListField, ReferenceField, DateTimeField, BooleanField
from datetime import datetime


class Attachment(Document):
    filename = StringField(required=True)
    mime_type = StringField(required=True)
    created_at = DateTimeField(required=True, default=datetime.utcnow)
    owner = StringField(required=True)
    md5 = StringField(required=True)
    local_path = StringField(required=True)

    meta = {
        'collection': 'storage',
    }
