# models.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


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
            "content": self.content
        }

    # The actual YAML content as a string
    content = Column(Text, nullable=False)
