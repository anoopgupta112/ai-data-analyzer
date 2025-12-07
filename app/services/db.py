from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import time
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

load_dotenv()
MYSQL_URL = os.getenv("MYSQL_URL") or "postgresql://Anoop_2:1234@localhost:5432/ai_analyzer"
engine = create_engine(MYSQL_URL, pool_pre_ping=True, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)  # e.g., "HR"
    fields = Column(JSON)  # predefined fields structure

class Form(Base):
    __tablename__ = "forms"
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(String(64), unique=True, index=True)
    fields = Column(JSON)  # List of field dicts
    submissions = relationship("Submission", back_populates="form")

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(String(64), ForeignKey("forms.form_id"))
    data = Column(JSON)  # Dict of field_name: value
    form = relationship("Form", back_populates="submissions")

# Create tables if not exist
def init_db(max_retries=10, delay=3):
    retries = 0
    while retries < max_retries:
        try:
            Base.metadata.create_all(bind=engine)
            return
        except OperationalError as e:
            print(f"[init_db] Database not ready, retrying in {delay} seconds... ({retries+1}/{max_retries})")
            time.sleep(delay)
            retries += 1
    raise Exception("[init_db] Could not connect to the database after multiple retries.")
