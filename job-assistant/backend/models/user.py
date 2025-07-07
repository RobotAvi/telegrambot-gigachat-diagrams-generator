from sqlalchemy import Column, String, Boolean, Text
from .base import BaseModel

class User(BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Contact settings
    telegram_chat_id = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    
    # Email settings for sending applications
    email_address = Column(String, nullable=True)
    email_password = Column(String, nullable=True)  # Encrypted
    smtp_server = Column(String, default="smtp.gmail.com")
    smtp_port = Column(String, default="587")
    
    # Job search preferences
    job_search_enabled = Column(Boolean, default=False)
    search_keywords = Column(Text, nullable=True)  # JSON string
    preferred_locations = Column(Text, nullable=True)  # JSON string
    salary_min = Column(String, nullable=True)
    salary_max = Column(String, nullable=True)