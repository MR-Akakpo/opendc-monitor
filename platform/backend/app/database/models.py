from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from datetime import datetime, timezone

from app.database.connection import Base

class Equipment(Base):
    __tablename__ = 'equipment'

    id = Column(Integer, primary_key=True, index=True)
    site = Column(String(100), default='STELLARIX_DC01')
    system = Column(String(100), index=True)
    zone = Column(String(100), nullable=True)
    name = Column(String(150), index=True)
    metric = Column(String(100), nullable=True)
    mqtt_topic = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Event(Base):
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), index=True)
    severity = Column(String(50), index=True)
    site = Column(String(100), default='STELLARIX_DC01')
    system = Column(String(100), index=True)
    zone = Column(String(100), nullable=True)
    equipment = Column(String(150), index=True)
    metric = Column(String(100), nullable=True)
    value = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ActiveAlarm(Base):
    __tablename__ = 'active_alarms'

    id = Column(Integer, primary_key=True, index=True)
    alarm_key = Column(String(300), unique=True, index=True)
    severity = Column(String(50), index=True)
    site = Column(String(100), default='STELLARIX_DC01')
    system = Column(String(100), index=True)
    zone = Column(String(100), nullable=True)
    equipment = Column(String(150), index=True)
    metric = Column(String(100), nullable=True)
    value = Column(Float, nullable=True)
    status = Column(String(50), default='ACTIVE')
    raised_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
