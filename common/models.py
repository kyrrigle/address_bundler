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
    cropping_status = CharField(
        null=False,
        choices=[
            ("not_cropped", "Not Cropped"),
            ("cropped", "Cropped"),
            ("failed", "Failed"),
        ],
        default="not_cropped",
        help_text="Cropping status for student photo: not_cropped, cropped, or failed.",
    )

    @classmethod
    def get_students_needing_cropping(cls, force=False):
        """
        Returns a query for students who are validated but not yet cropped.
        """
        return cls.select().where(
            (force or cls.cropping_status == "not_cropped")
            & (cls.image_valid == "valid")
        )

    @classmethod
    def get_students_needing_signs(cls, force=False):
        """
        Returns a query for students who are validated but not yet cropped.
        """
        return cls.select().where(
            (force or cls.cropping_status == "cropped") & (cls.image_valid == "valid")
        )

    class Meta:
        table_name = "student"
        indexes = [(("first_name", "last_name"), True)]
