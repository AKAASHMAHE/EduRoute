from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.journey import Journey

__all__ = ["db", "Journey"]
