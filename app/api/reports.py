from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import os

from app.database import get_db
from app.models.user import User
from app.models.case import Case
from app.api.auth import get_current_active_user
from app.services.report_service import ReportGenerator

router = APIRouter()


@router.post("/cases/{case_id}/generate")
def generate_case_report(
    case_id: int,
    report_type: str = Query("comprehensive", description="Report type: comprehensive, summary, evidence, analysis"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate report for a specific case"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Validate report type
    valid_types = ["comprehensive", "summary", "evidence", "analysis"]
    if report_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}"
        )
    
    try:
        # Generate report
        report_generator = ReportGenerator()
        report_data = report_generator.generate_case_report(case_id, db, report_type)
        
        # Save report to file
        filename = f"case_{case_id}_{report_type}_{case.case_number}.json"
        filepath = report_generator.save_report(report_data, filename)
        
        return {
            "message": "Report generated successfully",
            "case_id": case_id,
            "report_type": report_type,
            "filename": filename,
            "filepath": filepath,
            "report_data": report_data
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )


@router.get("/cases/{case_id}/reports")
def list_case_reports(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all reports for a case"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Get reports directory
    reports_dir = os.path.join("data", "reports")
    if not os.path.exists(reports_dir):
        return {"reports": []}
    
    # Find reports for this case
    case_reports = []
    for filename in os.listdir(reports_dir):
        if filename.startswith(f"case_{case_id}_") and filename.endswith(".json"):
            filepath = os.path.join(reports_dir, filename)
            file_stat = os.stat(filepath)
            
            case_reports.append({
                "filename": filename,
                "filepath": filepath,
                "size": file_stat.st_size,
                "created_at": file_stat.st_ctime,
                "modified_at": file_stat.st_mtime
            })
    
    # Sort by creation time (newest first)
    case_reports.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {
        "case_id": case_id,
        "total_reports": len(case_reports),
        "reports": case_reports
    }


@router.get("/cases/{case_id}/reports/{filename}")
def get_case_report(
    case_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific case report"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Check if report exists
    filepath = os.path.join("data", "reports", filename)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )
    
    # Verify filename belongs to this case
    if not filename.startswith(f"case_{case_id}_"):
        raise HTTPException(
            status_code=400,
            detail="Report does not belong to this case"
        )
    
    try:
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        return report_data
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading report: {str(e)}"
        )


@router.delete("/cases/{case_id}/reports/{filename}")
def delete_case_report(
    case_id: int,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a specific case report"""
    # Check if case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(
            status_code=404,
            detail="Case not found"
        )
    
    # Check if report exists
    filepath = os.path.join("data", "reports", filename)
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )
    
    # Verify filename belongs to this case
    if not filename.startswith(f"case_{case_id}_"):
        raise HTTPException(
            status_code=400,
            detail="Report does not belong to this case"
        )
    
    try:
        os.remove(filepath)
        return {"message": "Report deleted successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting report: {str(e)}"
        )


@router.post("/evidence/{evidence_id}/custody-report")
def generate_custody_report(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate Chain of Custody report for evidence item"""
    try:
        # Generate custody report
        report_generator = ReportGenerator()
        report_data = report_generator.generate_chain_of_custody_report(evidence_id, db)
        
        # Save report to file
        filename = f"custody_evidence_{evidence_id}.json"
        filepath = report_generator.save_report(report_data, filename)
        
        return {
            "message": "Custody report generated successfully",
            "evidence_id": evidence_id,
            "filename": filename,
            "filepath": filepath,
            "report_data": report_data
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating custody report: {str(e)}"
        )


@router.get("/reports/stats")
def get_report_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get report generation statistics"""
    reports_dir = os.path.join("data", "reports")
    
    if not os.path.exists(reports_dir):
        return {
            "total_reports": 0,
            "total_size": 0,
            "by_type": {},
            "recent_reports": []
        }
    
    total_reports = 0
    total_size = 0
    by_type = {}
    recent_reports = []
    
    for filename in os.listdir(reports_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(reports_dir, filename)
            file_stat = os.stat(filepath)
            
            total_reports += 1
            total_size += file_stat.st_size
            
            # Determine report type from filename
            if "comprehensive" in filename:
                report_type = "comprehensive"
            elif "summary" in filename:
                report_type = "summary"
            elif "evidence" in filename:
                report_type = "evidence"
            elif "analysis" in filename:
                report_type = "analysis"
            elif "custody" in filename:
                report_type = "custody"
            else:
                report_type = "unknown"
            
            by_type[report_type] = by_type.get(report_type, 0) + 1
            
            recent_reports.append({
                "filename": filename,
                "type": report_type,
                "size": file_stat.st_size,
                "created_at": file_stat.st_ctime
            })
    
    # Sort recent reports by creation time
    recent_reports.sort(key=lambda x: x['created_at'], reverse=True)
    recent_reports = recent_reports[:10]  # Top 10 most recent
    
    return {
        "total_reports": total_reports,
        "total_size": total_size,
        "by_type": by_type,
        "recent_reports": recent_reports
    }
