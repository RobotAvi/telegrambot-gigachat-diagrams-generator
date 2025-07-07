from sqlalchemy import Column, String, Text, ForeignKey, Integer, Boolean, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import BaseModel

class NotificationType(PyEnum):
    JOB_FOUND = "job_found"
    APPLICATION_SENT = "application_sent"
    HR_CONTACTED = "hr_contacted"
    RESPONSE_RECEIVED = "response_received"
    ERROR = "error"
    SYSTEM = "system"

class Notification(BaseModel):
    __tablename__ = "notifications"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Related entities
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    telegram_sent = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User")
    job = relationship("Job")
    application = relationship("JobApplication")