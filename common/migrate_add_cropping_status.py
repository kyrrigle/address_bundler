import peewee
from peewee import SqliteDatabase
from playhouse.migrate import SqliteMigrator, migrate
from .db import db
from .project import get_project


def column_exists(database, table_name, column_name):
    cursor = database.execute_sql(f"PRAGMA table_info({table_name});")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate_add_cropping_status():
    get_project()
    migrator = SqliteMigrator(db)
    if not column_exists(db, "student", "cropping_status"):
        migrate(
            migrator.add_column(
                "student",
                "cropping_status",
                peewee.CharField(null=False, default="not_cropped"),
            )
        )
        print("Added cropping_status column to student table.")
    else:
        print("cropping_status column already exists.")


if __name__ == "__main__":
    migrate_add_cropping_status()
