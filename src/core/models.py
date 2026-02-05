"""Data models for ClarityCheck."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Location(BaseModel):
    """Location of a finding within a document."""
    page: int
    x: Optional[float] = None
    y: Optional[float] = None
    char_index: Optional[int] = None


class Finding(BaseModel):
    """A single accessibility issue detected in a document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    detector: str
    severity: Severity
    location: Location
    content: str
    context: str
    explanation: str


class Report(BaseModel):
    """Analysis report for a document."""
    job_id: str
    filename: str
    total_pages: int
    findings: list[Finding] = []
    summary: dict[str, int] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Job(BaseModel):
    """A document processing job."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    report: Optional[Report] = None


# --- Database Models ---

from typing import List
from sqlmodel import SQLModel, Relationship, Field as SQLModelField

class DBJob(SQLModel, table=True):
    __tablename__ = "jobs"
    id: str = SQLModelField(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    filename: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = SQLModelField(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    
    findings: List["DBFinding"] = Relationship(back_populates="job")
    
    # Analysis results
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    executive_summary: Optional[str] = None

class DBFinding(SQLModel, table=True):
    __tablename__ = "findings"
    id: Optional[int] = SQLModelField(default=None, primary_key=True)
    job_id: str = SQLModelField(foreign_key="jobs.id")
    
    detector: str
    severity: Severity
    page: int
    x: Optional[float] = None
    y: Optional[float] = None
    char_index: Optional[int] = None
    content: str
    context: str
    explanation: str
    
    # Analysis enrichment
    trap_type: Optional[str] = None
    impact: Optional[str] = None
    decoded_text: Optional[str] = None
    classification_reason: Optional[str] = None
    recommended_action: Optional[str] = None
    
    job: DBJob = Relationship(back_populates="findings")
