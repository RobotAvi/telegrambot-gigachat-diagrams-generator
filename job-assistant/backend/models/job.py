from sqlalchemy import Column, String, Text, ForeignKey, Integer, Float, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import BaseModel

class ApplicationStatus(PyEnum):
    PENDING = "pending"
    APPLIED = "applied"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"

class Job(BaseModel):
    __tablename__ = "jobs"
    
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    
    # Salary info
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String, nullable=True)
    
    # Source info
    source = Column(String, nullable=False)  # hh.ru, superjob.ru, etc.
    external_id = Column(String, nullable=False)
    external_url = Column(String, nullable=False)
    
    # LLM analysis
    match_score = Column(Float, nullable=True)  # 0-100
    match_reasons = Column(Text, nullable=True)  # JSON string
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    applications = relationship("JobApplication", back_populates="job")

class JobApplication(BaseModel):
    __tablename__ = "job_applications"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    cover_letter = Column(Text, nullable=True)
    
    # Application tracking
    applied_at = Column(DateTime, nullable=True)
    response_received_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume")