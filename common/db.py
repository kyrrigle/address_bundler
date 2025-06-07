from peewee import SqliteDatabase, Proxy

db = Proxy()  # Use a Proxy for deferred initialization

def init_db(db_path):
    db.initialize(SqliteDatabase(db_path))
    return db
