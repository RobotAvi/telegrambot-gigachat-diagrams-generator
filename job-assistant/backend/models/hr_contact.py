from sqlalchemy import Column, String, Text, Boolean
from .base import BaseModel

class HRContact(BaseModel):
    __tablename__ = "hr_contacts"
    
    company = Column(String, nullable=False)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    linkedin_url = Column(String, nullable=True)
    position = Column(String, nullable=True)
    
    # Contact info
    phone = Column(String, nullable=True)
    telegram = Column(String, nullable=True)
    
    # Engagement tracking
    contacted = Column(Boolean, default=False)
    last_contact_date = Column(String, nullable=True)
    response_received = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    
    # Source info
    source = Column(String, nullable=True)  # linkedin, company_website, etc.
    verified = Column(Boolean, default=False)