from alembic import context
from app.db import engine, Base
from app import models  # noqa: F401
from sqlalchemy import text

with engine.connect() as connection:
    schema = connection.scalar(text("SELECT current_schema()"))
    connection.commit()
    context.configure(connection=connection, target_metadata=Base.metadata, version_table_schema=schema)
    with context.begin_transaction():
        context.run_migrations()
