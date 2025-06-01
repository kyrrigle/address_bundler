from peewee import SqliteDatabase

db = None  # Will be set dynamically

def init_db(db_path):
    global db
    db = SqliteDatabase(db_path)
    return db
