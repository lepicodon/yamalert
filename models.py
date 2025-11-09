# models.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class Admin(Base, UserMixin):
    """Admin user model for authentication."""
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Template(Base):
    """Template stored in the database.

    Each row represents either a Prometheus rule file or an Alertmanager config.
    """
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True)

    # Human‑readable name
    name = Column(String(120), nullable=False)

    # ``rule`` or ``alertmanager``
    type = Column(String(30), nullable=False)

    # For grouping (e.g. Telegraf, VMware, Ping, etc.)
    job_category = Column(String(100), nullable=True)

    # For finer grain (e.g. CPU, Memory, Disk, Latency)
    sensor_type = Column(String(100), nullable=True)

    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)

    def to_dict(self):
        """Convert the template to a dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "job_category": self.job_category,
            "sensor_type": self.sensor_type,
            "description": self.description,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    # The actual YAML content as a string
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('name', name='uix_template_name'),
    )
