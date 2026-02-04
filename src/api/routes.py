"""API routes for ClarityCheck."""

from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from src.core.engine import engine
from src.core.models import Job, JobStatus, Report
from src.core.analyzer import analyzer, TrapAnalysis

router = APIRouter()

# In-memory storage (replace with DB later)
jobs: dict[str, Job] = {}
analyses: dict[str, TrapAnalysis] = {}
uploaded_files: dict[str, bytes] = {}  # Store original PDFs for sanitization


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF for analysis."""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create job
    job = Job(filename=file.filename)
    jobs[job.id] = job
    
    try:
        # Read file and analyze
        pdf_bytes = await file.read()
        uploaded_files[job.id] = pdf_bytes  # Store for later sanitization
        job.status = JobStatus.PROCESSING
        
        report = engine.analyze_bytes(pdf_bytes, file.filename)
        report.job_id = job.id
        
        # Run AI trap analysis
        analysis = analyzer.analyze(report)
        analyses[job.id] = analysis
        
        job.report = report
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.error = str(e)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "filename": job.filename,
        "total_findings": len(report.findings),
        "risk_score": analysis.risk_score,
        "risk_level": analysis.risk_level,
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@router.get("/jobs/{job_id}/report")
async def get_report(job_id: str):
    """Get raw detection report."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Job not completed: {job.status}")
    
    return job.report


@router.get("/jobs/{job_id}/analysis")
async def get_analysis(job_id: str):
    """Get full AI trap analysis with classifications."""
    if job_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analyses[job_id]
    
    # Return structured analysis
    return {
        "filename": analysis.filename,
        "total_pages": analysis.total_pages,
        "risk_score": analysis.risk_score,
        "risk_level": analysis.risk_level,
        "executive_summary": analysis.executive_summary,
        "summary_by_type": analysis.summary,
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
            for f in analysis.findings
        ]
    }


@router.get("/jobs/{job_id}/sanitize")
async def sanitize_document(job_id: str):
    """
    Get sanitized PDF with AI traps removed.
    
    Returns the PDF with hidden text removed/neutralized.
    """
    if job_id not in jobs or job_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Job not completed")
    
    # Import here to avoid circular imports
    from src.core.sanitizer import sanitize_pdf
    
    original_pdf = uploaded_files[job_id]
    analysis = analyses.get(job_id)
    
    try:
        sanitized_pdf = sanitize_pdf(original_pdf, job.report, analysis)
        
        return Response(
            content=sanitized_pdf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="sanitized_{job.filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sanitization failed: {e}")
