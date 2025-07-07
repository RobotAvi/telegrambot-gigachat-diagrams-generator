from sqlalchemy import Column, String, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship
from .base import BaseModel

class Resume(BaseModel):
    __tablename__ = "resumes"
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)  # Original resume text
    
    # Parsed resume fields
    skills = Column(Text, nullable=True)  # JSON string
    experience = Column(Text, nullable=True)  # JSON string
    education = Column(Text, nullable=True)  # JSON string
    languages = Column(Text, nullable=True)  # JSON string
    
    # LLM processed summary
    summary = Column(Text, nullable=True)
    key_skills = Column(Text, nullable=True)  # JSON string
    
    # File info
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=True)  # pdf, docx, txt
    
    # Relationship
    user = relationship("User", back_populates="resumes")