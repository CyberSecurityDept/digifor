import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.case import Case, CasePerson
from app.models.evidence import EvidenceItem, CustodyTransfer
from app.models.analysis import Analysis, AnalysisResult, Correlation
from app.config import settings


class ReportGenerator:
    """Service for generating forensic reports"""
    
    def __init__(self):
        self.reports_dir = settings.reports_dir
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
    
    def generate_case_report(self, case_id: int, db: Session, report_type: str = "comprehensive") -> Dict[str, Any]:
        """Generate comprehensive case report"""
        # Get case data
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found")
        
        # Get related data
        persons = db.query(CasePerson).filter(CasePerson.case_id == case_id).all()
        evidence_items = db.query(EvidenceItem).filter(EvidenceItem.case_id == case_id).all()
        analyses = db.query(Analysis).filter(Analysis.case_id == case_id).all()
        correlations = db.query(Correlation).filter(Correlation.case_id == case_id).all()
        
        # Generate report data
        report_data = {
            'case': self._serialize_case(case),
            'persons': [self._serialize_person(p) for p in persons],
            'evidence_items': [self._serialize_evidence(e) for e in evidence_items],
            'analyses': [self._serialize_analysis(a) for a in analyses],
            'correlations': [self._serialize_correlation(c) for c in correlations],
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'report_type': report_type,
                'case_id': case_id,
                'total_evidence': len(evidence_items),
                'total_analyses': len(analyses),
                'total_correlations': len(correlations)
            }
        }
        
        # Generate different report formats
        if report_type == "comprehensive":
            return self._generate_comprehensive_report(report_data)
        elif report_type == "summary":
            return self._generate_summary_report(report_data)
        elif report_type == "evidence":
            return self._generate_evidence_report(report_data)
        elif report_type == "analysis":
            return self._generate_analysis_report(report_data)
        else:
            return self._generate_comprehensive_report(report_data)
    
    def generate_chain_of_custody_report(self, evidence_id: int, db: Session) -> Dict[str, Any]:
        """Generate Chain of Custody report for evidence item"""
        evidence = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
        if not evidence:
            raise ValueError(f"Evidence {evidence_id} not found")
        
        custody_transfers = db.query(CustodyTransfer).filter(
            CustodyTransfer.evidence_id == evidence_id
        ).order_by(CustodyTransfer.transfer_date).all()
        
        report_data = {
            'evidence': self._serialize_evidence(evidence),
            'custody_transfers': [self._serialize_custody_transfer(ct) for ct in custody_transfers],
            'report_metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'evidence_id': evidence_id,
                'total_transfers': len(custody_transfers)
            }
        }
        
        return self._generate_custody_report(report_data)
    
    def _generate_comprehensive_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive case report"""
        return {
            'report_type': 'comprehensive',
            'title': f"Comprehensive Forensic Report - {data['case']['case_number']}",
            'sections': [
                self._create_case_overview_section(data),
                self._create_persons_section(data),
                self._create_evidence_section(data),
                self._create_analysis_section(data),
                self._create_correlations_section(data),
                self._create_conclusions_section(data)
            ],
            'metadata': data['report_metadata']
        }
    
    def _generate_summary_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report"""
        return {
            'report_type': 'summary',
            'title': f"Case Summary - {data['case']['case_number']}",
            'sections': [
                self._create_case_overview_section(data),
                self._create_evidence_summary_section(data),
                self._create_analysis_summary_section(data)
            ],
            'metadata': data['report_metadata']
        }
    
    def _generate_evidence_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate evidence-focused report"""
        return {
            'report_type': 'evidence',
            'title': f"Evidence Report - {data['case']['case_number']}",
            'sections': [
                self._create_case_overview_section(data),
                self._create_evidence_section(data),
                self._create_custody_section(data)
            ],
            'metadata': data['report_metadata']
        }
    
    def _generate_analysis_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis-focused report"""
        return {
            'report_type': 'analysis',
            'title': f"Analysis Report - {data['case']['case_number']}",
            'sections': [
                self._create_case_overview_section(data),
                self._create_analysis_section(data),
                self._create_correlations_section(data),
                self._create_findings_section(data)
            ],
            'metadata': data['report_metadata']
        }
    
    def _generate_custody_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Chain of Custody report"""
        return {
            'report_type': 'custody',
            'title': f"Chain of Custody - {data['evidence']['evidence_number']}",
            'sections': [
                self._create_evidence_overview_section(data),
                self._create_custody_timeline_section(data),
                self._create_custody_verification_section(data)
            ],
            'metadata': data['report_metadata']
        }
    
    def _create_case_overview_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create case overview section"""
        case = data['case']
        return {
            'title': 'Case Overview',
            'content': {
                'case_number': case['case_number'],
                'title': case['title'],
                'description': case['description'],
                'status': case['status'],
                'priority': case['priority'],
                'case_type': case['case_type'],
                'incident_date': case['incident_date'],
                'reported_date': case['reported_date'],
                'jurisdiction': case['jurisdiction'],
                'case_officer': case['case_officer'],
                'created_at': case['created_at'],
                'updated_at': case['updated_at']
            }
        }
    
    def _create_persons_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create persons section"""
        persons = data['persons']
        return {
            'title': 'Persons Involved',
            'content': {
                'total_persons': len(persons),
                'persons': persons
            }
        }
    
    def _create_evidence_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create evidence section"""
        evidence_items = data['evidence_items']
        return {
            'title': 'Digital Evidence',
            'content': {
                'total_evidence': len(evidence_items),
                'evidence_items': evidence_items
            }
        }
    
    def _create_analysis_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create analysis section"""
        analyses = data['analyses']
        return {
            'title': 'Forensic Analysis',
            'content': {
                'total_analyses': len(analyses),
                'analyses': analyses
            }
        }
    
    def _create_correlations_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create correlations section"""
        correlations = data['correlations']
        return {
            'title': 'Data Correlations',
            'content': {
                'total_correlations': len(correlations),
                'correlations': correlations
            }
        }
    
    def _create_evidence_summary_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create evidence summary section"""
        evidence_items = data['evidence_items']
        return {
            'title': 'Evidence Summary',
            'content': {
                'total_evidence': len(evidence_items),
                'by_type': self._group_evidence_by_type(evidence_items),
                'by_status': self._group_evidence_by_status(evidence_items)
            }
        }
    
    def _create_analysis_summary_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create analysis summary section"""
        analyses = data['analyses']
        return {
            'title': 'Analysis Summary',
            'content': {
                'total_analyses': len(analyses),
                'by_type': self._group_analyses_by_type(analyses),
                'by_status': self._group_analyses_by_status(analyses)
            }
        }
    
    def _create_custody_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create custody section"""
        evidence_items = data['evidence_items']
        return {
            'title': 'Chain of Custody',
            'content': {
                'evidence_items': evidence_items
            }
        }
    
    def _create_findings_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create findings section"""
        analyses = data['analyses']
        correlations = data['correlations']
        
        findings = []
        for analysis in analyses:
            if analysis['findings']:
                findings.append({
                    'analysis_type': analysis['analysis_type'],
                    'findings': analysis['findings'],
                    'confidence': analysis['confidence_score']
                })
        
        return {
            'title': 'Key Findings',
            'content': {
                'findings': findings,
                'correlations': correlations
            }
        }
    
    def _create_evidence_overview_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create evidence overview section"""
        evidence = data['evidence']
        return {
            'title': 'Evidence Overview',
            'content': evidence
        }
    
    def _create_custody_timeline_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create custody timeline section"""
        transfers = data['custody_transfers']
        return {
            'title': 'Custody Timeline',
            'content': {
                'transfers': transfers
            }
        }
    
    def _create_custody_verification_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create custody verification section"""
        transfers = data['custody_transfers']
        return {
            'title': 'Custody Verification',
            'content': {
                'total_transfers': len(transfers),
                'verified_transfers': len([t for t in transfers if t['from_signature'] and t['to_signature']]),
                'transfers': transfers
            }
        }
    
    def _create_conclusions_section(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create conclusions section"""
        return {
            'title': 'Conclusions',
            'content': {
                'summary': 'Analysis completed successfully',
                'recommendations': [
                    'Review all evidence items',
                    'Verify chain of custody',
                    'Document all findings',
                    'Prepare for court presentation'
                ]
            }
        }
    
    def _group_evidence_by_type(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group evidence items by type"""
        groups = {}
        for item in evidence_items:
            item_type = item['item_type']
            groups[item_type] = groups.get(item_type, 0) + 1
        return groups
    
    def _group_evidence_by_status(self, evidence_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group evidence items by status"""
        groups = {}
        for item in evidence_items:
            status = item['status']
            groups[status] = groups.get(status, 0) + 1
        return groups
    
    def _group_analyses_by_type(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group analyses by type"""
        groups = {}
        for analysis in analyses:
            analysis_type = analysis['analysis_type']
            groups[analysis_type] = groups.get(analysis_type, 0) + 1
        return groups
    
    def _group_analyses_by_status(self, analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group analyses by status"""
        groups = {}
        for analysis in analyses:
            status = analysis['status']
            groups[status] = groups.get(status, 0) + 1
        return groups
    
    def _serialize_case(self, case: Case) -> Dict[str, Any]:
        """Serialize case object"""
        return {
            'id': case.id,
            'case_number': case.case_number,
            'title': case.title,
            'description': case.description,
            'case_type': case.case_type,
            'status': case.status,
            'priority': case.priority,
            'incident_date': case.incident_date.isoformat() if case.incident_date else None,
            'reported_date': case.reported_date.isoformat() if case.reported_date else None,
            'jurisdiction': case.jurisdiction,
            'case_officer': case.case_officer,
            'evidence_count': case.evidence_count,
            'analysis_progress': case.analysis_progress,
            'created_at': case.created_at.isoformat(),
            'updated_at': case.updated_at.isoformat() if case.updated_at else None,
            'closed_at': case.closed_at.isoformat() if case.closed_at else None,
            'tags': case.tags,
            'notes': case.notes,
            'is_confidential': case.is_confidential
        }
    
    def _serialize_person(self, person: CasePerson) -> Dict[str, Any]:
        """Serialize person object"""
        return {
            'id': person.id,
            'person_type': person.person_type,
            'full_name': person.full_name,
            'alias': person.alias,
            'date_of_birth': person.date_of_birth.isoformat() if person.date_of_birth else None,
            'nationality': person.nationality,
            'address': person.address,
            'phone': person.phone,
            'email': person.email,
            'social_media_accounts': person.social_media_accounts,
            'device_identifiers': person.device_identifiers,
            'description': person.description,
            'is_primary': person.is_primary,
            'created_at': person.created_at.isoformat(),
            'updated_at': person.updated_at.isoformat() if person.updated_at else None
        }
    
    def _serialize_evidence(self, evidence: EvidenceItem) -> Dict[str, Any]:
        """Serialize evidence object"""
        return {
            'id': evidence.id,
            'evidence_number': evidence.evidence_number,
            'item_type': evidence.item_type,
            'description': evidence.description,
            'source': evidence.source,
            'original_filename': evidence.original_filename,
            'file_size': evidence.file_size,
            'file_type': evidence.file_type,
            'file_extension': evidence.file_extension,
            'md5_hash': evidence.md5_hash,
            'sha1_hash': evidence.sha1_hash,
            'sha256_hash': evidence.sha256_hash,
            'status': evidence.status,
            'analysis_status': evidence.analysis_status,
            'is_encrypted': evidence.is_encrypted,
            'encryption_method': evidence.encryption_method,
            'current_custodian': evidence.current_custodian,
            'custody_chain': evidence.custody_chain,
            'analysis_notes': evidence.analysis_notes,
            'tags': evidence.tags,
            'is_sensitive': evidence.is_sensitive,
            'created_at': evidence.created_at.isoformat(),
            'updated_at': evidence.updated_at.isoformat() if evidence.updated_at else None
        }
    
    def _serialize_analysis(self, analysis: Analysis) -> Dict[str, Any]:
        """Serialize analysis object"""
        return {
            'id': analysis.id,
            'analysis_type': analysis.analysis_type,
            'analysis_name': analysis.analysis_name,
            'description': analysis.description,
            'status': analysis.status,
            'progress': analysis.progress,
            'started_at': analysis.started_at.isoformat() if analysis.started_at else None,
            'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
            'created_at': analysis.created_at.isoformat(),
            'results': analysis.results,
            'findings': analysis.findings,
            'confidence_score': analysis.confidence_score,
            'algorithm_version': analysis.algorithm_version,
            'error_message': analysis.error_message,
            'retry_count': analysis.retry_count,
            'is_automated': analysis.is_automated
        }
    
    def _serialize_correlation(self, correlation: Correlation) -> Dict[str, Any]:
        """Serialize correlation object"""
        return {
            'id': correlation.id,
            'correlation_type': correlation.correlation_type,
            'source_data': correlation.source_data,
            'target_data': correlation.target_data,
            'match_score': correlation.match_score,
            'match_type': correlation.match_type,
            'match_confidence': correlation.match_confidence,
            'context': correlation.context,
            'significance': correlation.significance,
            'created_at': correlation.created_at.isoformat(),
            'is_verified': correlation.is_verified
        }
    
    def _serialize_custody_transfer(self, transfer: CustodyTransfer) -> Dict[str, Any]:
        """Serialize custody transfer object"""
        return {
            'id': transfer.id,
            'from_custodian': transfer.from_custodian,
            'to_custodian': transfer.to_custodian,
            'transfer_date': transfer.transfer_date.isoformat(),
            'transfer_reason': transfer.transfer_reason,
            'transfer_method': transfer.transfer_method,
            'transfer_location': transfer.transfer_location,
            'evidence_condition': transfer.evidence_condition,
            'witness': transfer.witness,
            'notes': transfer.notes,
            'from_signature': transfer.from_signature,
            'to_signature': transfer.to_signature,
            'witness_signature': transfer.witness_signature
        }
    
    def save_report(self, report_data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save report to file"""
        if not filename:
            case_number = report_data['metadata']['case_id']
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{case_number}_{timestamp}.json"
        
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return filepath
