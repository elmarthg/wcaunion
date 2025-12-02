# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class ContactSubmission(Base):
    __tablename__ = "contact_submissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    role = Column(String(200), nullable=True)
    program = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class GetInvolvedSubmission(Base):
    __tablename__ = "get_involved_submissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False)
    phone = Column(String(50), nullable=True)
    role = Column(String(200), nullable=True)
    program = Column(String(200), nullable=True)
    interest_level = Column(String(200), nullable=True)  # e.g. "Help organize", "Stay updated"
    concerns = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
