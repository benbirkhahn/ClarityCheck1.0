from pathlib import Path
from datetime import datetime
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from src.core.celery_app import celery_app
from src.core.database import sync_engine
from src.core.models import DBJob, DBFinding, JobStatus, Report, Finding, Location
from src.core.engine import engine as detection_engine
from src.core.analyzer import analyzer, AnalyzedFinding, TrapType, TrapImpact

@celery_app.task
def analyze_document_task(job_id: str, file_path: str):
    """
    Background task to analyze a document.
    """
    print(f"Starting analysis for job {job_id} on file {file_path}")
    
    with Session(sync_engine) as session:
        # Get Job
        job = session.get(DBJob, job_id)
        if not job:
            print(f"Job {job_id} not found!")
            return

        try:
            # Update status
            job.status = JobStatus.PROCESSING
            session.add(job)
            session.commit()
            
            # Run Analysis
            # Note: analyze accepts path or bytes. Since we saved to disk, use path.
            # However, detection_engine.analyze expects path and opens it with fitz.
            report = detection_engine.analyze(file_path)
            report.job_id = job.id
            
            # Run AI Trap Analysis
            analysis = analyzer.analyze(report)
            
            # Update Job Metadata
            job.risk_score = analysis.risk_score
            job.risk_level = analysis.risk_level
            job.executive_summary = analysis.executive_summary
            job.completed_at = datetime.utcnow()
            job.status = JobStatus.COMPLETED
            
            # Save Findings
            for af in analysis.findings:
                db_finding = DBFinding(
                    job_id=job.id,
                    detector=af.original.detector,
                    severity=af.original.severity,
                    page=af.original.location.page,
                    x=af.original.location.x,
                    y=af.original.location.y,
                    char_index=af.original.location.char_index,
                    content=af.original.content,
                    context=af.original.context,
                    explanation=af.original.explanation,
                    
                    # Analysis fields
                    trap_type=af.trap_type.value,
                    impact=af.impact.value,
                    decoded_text=af.decoded_text,
                    classification_reason=af.classification_reason,
                    recommended_action=af.recommended_action
                )
                session.add(db_finding)
            
            session.add(job)
            session.commit()
            print(f"Job {job_id} completed successfully.")
            
        except Exception as e:
            print(f"Job {job_id} failed: {e}")
            job.status = JobStatus.FAILED
            job.error = str(e)
            session.add(job)
            session.commit()
