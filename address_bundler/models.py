from peewee import Model, CharField, FloatField
from .db import db


class BaseModel(Model):
    class Meta:
        database = db


class Student(BaseModel):
    first_name = CharField(null=False)
    last_name = CharField(null=False)
    address = CharField(null=False)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    bundle_key = CharField(null=True)

    class Meta:
        table_name = "student"
        indexes = [
            (('first_name', 'last_name'), True)
        ]