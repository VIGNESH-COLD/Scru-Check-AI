"""
User and Authentication Database Models
Extends the database with User model for RBAC
"""

from datetime import datetime, timedelta
from typing import Optional
import os
import secrets

try:
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scrucheck.db")

Base = declarative_base() if SQLALCHEMY_AVAILABLE else object


if SQLALCHEMY_AVAILABLE:
    
    class User(Base):
        """User model with role-based access control."""
        __tablename__ = "users"
        
        id = Column(Integer, primary_key=True, index=True)
        username = Column(String(50), unique=True, index=True, nullable=False)
        email = Column(String(100), unique=True, index=True, nullable=False)
        password_hash = Column(String(255), nullable=False)
        full_name = Column(String(100))
        role = Column(String(20), default="faculty")  # faculty, hod, coe, auditor
        department = Column(String(50))
        is_active = Column(Boolean, default=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        last_login = Column(DateTime, nullable=True)
    

    class ExternalAccessToken(Base):
        """Temporary access tokens for external examiners."""
        __tablename__ = "external_access_tokens"
        
        id = Column(Integer, primary_key=True, index=True)
        token = Column(String(64), unique=True, index=True, nullable=False)
        paper_ids = Column(JSON)  # List of paper IDs accessible
        created_by = Column(String(100))
        created_at = Column(DateTime, default=datetime.utcnow)
        expires_at = Column(DateTime, nullable=False)
        is_revoked = Column(Boolean, default=False)
        access_count = Column(Integer, default=0)
        last_accessed = Column(DateTime, nullable=True)
    

    class AuditLog(Base):
        """Immutable audit log for all actions."""
        __tablename__ = "audit_logs"
        
        id = Column(Integer, primary_key=True, index=True)
        timestamp = Column(DateTime, default=datetime.utcnow)
        actor = Column(String(100))
        action = Column(String(50))
        target = Column(String(200))
        details = Column(JSON)
        ip_address = Column(String(50))
    

    class Policy(Base):
        """Department policies and rules."""
        __tablename__ = "policies"
        
        id = Column(Integer, primary_key=True, index=True)
        rule_id = Column(String(100), unique=True)
        version = Column(Integer, default=1)
        department = Column(String(50))
        regulation = Column(String(20))
        exam_type = Column(String(50))
        rules = Column(JSON)
        created_by = Column(String(100))
        effective_from = Column(DateTime)
        effective_until = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
    

    class AnalysisReport(Base):
        """Stored analysis reports."""
        __tablename__ = "analysis_reports"
        
        id = Column(Integer, primary_key=True, index=True)
        paper_id = Column(String(100), unique=True, index=True)
        timestamp = Column(DateTime, default=datetime.utcnow)
        overall_status = Column(String(20))
        findings = Column(JSON)
        data = Column(JSON)  # Stores the full analysis dictionary (RESULTS_STORE equivalent)
        created_by = Column(String(100))
        department = Column(String(50))


# Database initialization
engine = None
SessionLocal = None


async def init_db():
    """Initialize database tables."""
    global engine, SessionLocal
    
    if not SQLALCHEMY_AVAILABLE:
        print("⚠️ SQLAlchemy not available, using in-memory storage")
        return
    
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Database initialized with User and RBAC tables")


def get_db():
    """Get database session."""
    if SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_external_token() -> str:
    """Generate a secure random token for external access."""
    return secrets.token_urlsafe(48)
