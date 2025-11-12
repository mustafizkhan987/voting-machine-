from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from database import Base
import hashlib
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)

class Behavior(Base):
    __tablename__ = "behaviors"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    action = Column(String)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    score = Column(Float)
    level = Column(String)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    hash = Column(String, default="")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hash = hashlib.sha256(f"{self.user_id}{self.action}{self.timestamp}".encode()).hexdigest()

class MerkleTree(Base):
    __tablename__ = "merkle_trees"
    id = Column(Integer, primary_key=True, index=True)
    root_hash = Column(String)
    leaves = Column(Text)  # JSON of leaves
