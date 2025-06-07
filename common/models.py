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
    image_name = CharField(null=True)
    image_valid = CharField(
        null=True,
        choices=[("unknown", "Unknown"), ("valid", "Valid"), ("invalid", "Invalid")],
        default="unknown",
    )

    class Meta:
        table_name = "student"
        indexes = [(("first_name", "last_name"), True)]
