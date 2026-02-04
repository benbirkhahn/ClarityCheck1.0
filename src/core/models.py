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
