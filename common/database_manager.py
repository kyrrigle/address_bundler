import os
import sqlite3
from peewee import SqliteDatabase, Model, TextField, IntegerField, DateTimeField
from datetime import datetime
from .db import db


class ProjectConfig(Model):
    """Project configuration key-value store"""

    key = TextField(unique=True)
    value = TextField()
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = "project_config"


class ProjectMetadata(Model):
    """Project metadata"""

    name = TextField()
    created_at = DateTimeField(default=datetime.now)
    last_accessed = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = "project_metadata"


class DatabaseManager:
    """Manages database schema and migrations"""

    def __init__(self, project):
        self.project = project

    def ensure_schema(self):
        """Ensure all tables exist with current schema"""
        self._create_core_tables()
        self._run_migrations()

    def _create_core_tables(self):
        """Create project_config and project_metadata tables"""
        # Import existing models to ensure they're created too
        from .models import Student

        # Create all tables
        db.create_tables(
            [
                ProjectConfig,
                ProjectMetadata,
                Student,
            ],
            safe=True,
        )

    def _run_migrations(self):
        """Run any pending schema migrations"""
        # Check for schema version and run migrations as needed
        # For now, this is a placeholder for future migrations
        pass

    def get_schema_version(self) -> int:
        """Get current database schema version"""
        try:
            config = ProjectConfig.get(ProjectConfig.key == "schema_version")
            return int(config.value)
        except (ProjectConfig.DoesNotExist, ValueError):
            return 1

    def set_schema_version(self, version: int):
        """Set database schema version"""
        config, created = ProjectConfig.get_or_create(
            key="schema_version", defaults={"value": str(version)}
        )
        if not created:
            config.value = str(version)
            config.updated_at = datetime.now()
            config.save()
