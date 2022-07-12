import datetime as dt

from mongoengine import Document, DateTimeField, StringField


class Event(Document):
    created_at = DateTimeField(default=dt.datetime.utcnow)
    target_document_id = StringField()
    metadata = StringField()
