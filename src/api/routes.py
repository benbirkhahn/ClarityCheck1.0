"""API routes for ClarityCheck."""

import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models import (
    JobStatus, Report, Finding, Location, Severity,
    DBJob, DBFinding
)
from src.core.analyzer import AnalyzedFinding, TrapType, TrapImpact, TrapAnalysis
from src.core.database import get_session
from src.workers.tasks import analyze_document_task

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """Upload a PDF for analysis (Async)."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create Job in DB
    job = DBJob(filename=file.filename, status=JobStatus.PENDING)
    session.add(job)
    await session.commit()
    await session.refresh(job)
    
    try:
        # Save file to disk
        file_path = UPLOAD_DIR / f"{job.id}.pdf"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Dispatch Celery Task
        analyze_document_task.delay(job.id, str(file_path))
        
        # Update status to indicate queued
        # (Optional, as Pending is fine, but we can set to Processing explicitly if we want)
        # We leave it as PENDING or updated by worker to PROCESSING
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        session.add(job)
        await session.commit()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    
    return {
        "job_id": job.id,
        "status": "queued",
        "filename": job.filename,
        "message": "Analysis started in background"
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, session: AsyncSession = Depends(get_session)):
    """Get job status."""
    job = await session.get(DBJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs/{job_id}/report")
async def get_report(job_id: str, session: AsyncSession = Depends(get_session)):
    """Get raw detection report."""
    query = select(DBJob).where(DBJob.id == job_id).options(selectinload(DBJob.findings))
    result = await session.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Job not completed: {job.status}")
    
    # Reconstruct Engine Report
    findings = []
    summary = {}
    
    for dbf in job.findings:
        findings.append(Finding(
            id=str(dbf.id), 
            detector=dbf.detector,
            severity=dbf.severity,
            location=Location(
                page=dbf.page,
                x=dbf.x,
                y=dbf.y,
                char_index=dbf.char_index
            ),
            content=dbf.content,
            context=dbf.context,
            explanation=dbf.explanation
        ))
        summary[dbf.detector] = summary.get(dbf.detector, 0) + 1
    
    return Report(
        job_id=job.id,
        filename=job.filename,
        total_pages=0,
        findings=findings,
        summary=summary,
        created_at=job.created_at
    )


@router.get("/jobs/{job_id}/analysis")
async def get_analysis(job_id: str, session: AsyncSession = Depends(get_session)):
    """Get full AI trap analysis with classifications."""
    query = select(DBJob).where(DBJob.id == job_id).options(selectinload(DBJob.findings))
    result = await session.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # If not completed, return basic info
    if job.status != JobStatus.COMPLETED:
         return {
            "filename": job.filename,
            "status": job.status,
            "risk_score": None
        }

    analyzed_findings = []
    summary = {}
    
    for dbf in job.findings:
        # Reconstruct AnalyzedFinding
        original = Finding(
            id=str(dbf.id),
            detector=dbf.detector,
            severity=dbf.severity,
            location=Location(
                page=dbf.page,
                x=dbf.x,
                y=dbf.y,
                char_index=dbf.char_index
            ),
            content=dbf.content,
            context=dbf.context,
            explanation=dbf.explanation
        )
        
        af = AnalyzedFinding(
            original=original,
            trap_type=TrapType(dbf.trap_type) if dbf.trap_type else TrapType.UNKNOWN,
            impact=TrapImpact(dbf.impact) if dbf.impact else TrapImpact.INFO,
            decoded_text=dbf.decoded_text or "",
            classification_reason=dbf.classification_reason or "",
            recommended_action=dbf.recommended_action or ""
        )
        analyzed_findings.append(af)
        
        key = af.trap_type.value
        summary[key] = summary.get(key, 0) + 1
    
    return {
        "filename": job.filename,
        "total_pages": 0,
        "risk_score": job.risk_score,
        "risk_level": job.risk_level,
        "executive_summary": job.executive_summary,
        "summary_by_type": summary,
        "findings": [
            {
                "page": f.original.location.page,
                "trap_type": f.trap_type.value,
                "impact": f.impact.value,
                "hidden_text": f.original.context,
                "decoded_text": f.decoded_text,
                "detection_method": f.original.detector,
                "classification_reason": f.classification_reason,
                "recommendation": f.recommended_action,
            }
            for f in analyzed_findings
        ]
    }


@router.get("/jobs/{job_id}/sanitize")
async def sanitize_document(
    job_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get sanitized PDF with AI traps removed.
    """
    query = select(DBJob).where(DBJob.id == job_id).options(selectinload(DBJob.findings))
    result = await session.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # Check for file on disk
    file_path = UPLOAD_DIR / f"{job.id}.pdf"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Source file not found on disk")

    # Import here to avoid circular imports
    from src.core.sanitizer import sanitize_pdf
    
    with open(file_path, "rb") as f:
        original_pdf_bytes = f.read()
    
    # Reconstruct Engine Report (Simplified)
    findings = []
    for dbf in job.findings:
        findings.append(Finding(
            id=str(dbf.id),
            detector=dbf.detector,
            severity=dbf.severity,
            location=Location(
                page=dbf.page,
                x=dbf.x,
                y=dbf.y,
                char_index=dbf.char_index
            ),
            content=dbf.content,
            context=dbf.context,
            explanation=dbf.explanation
        ))
    
    report = Report(job_id=job.id, filename=job.filename, total_pages=0, findings=findings)
    
    # Reconstruct minimal analysis object
    analyzed_findings = []
    for dbf in job.findings:
        analyzed_findings.append(AnalyzedFinding(
            original=findings[0] if findings else None, # Needs generic mock if empty
            trap_type=TrapType(dbf.trap_type) if dbf.trap_type else TrapType.UNKNOWN,
            impact=TrapImpact(dbf.impact) if dbf.impact else TrapImpact.INFO,
            decoded_text="", classification_reason="", recommended_action=""
        ))
        
    analysis = TrapAnalysis(
        filename=job.filename, total_pages=0, risk_score=job.risk_score or 0, risk_level=job.risk_level or "UNKNOWN",
        findings=analyzed_findings, summary={}, executive_summary=""
    )
    
    try:
        sanitized_pdf = sanitize_pdf(original_pdf_bytes, report, analysis)
        
        return Response(
            content=sanitized_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="sanitized_{job.filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sanitization failed: {e}")
