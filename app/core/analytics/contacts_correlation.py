from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import hashlib


class ContactsCorrelationAnalyzer:
    """Analyzer for contacts correlation across multiple sources"""
    
    def __init__(self):
        self.contact_patterns = {
            'phone': r'(\+?62|0)[0-9]{8,13}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'whatsapp': r'wa\.me/[0-9]+',
            'telegram': r't\.me/[a-zA-Z0-9_]+'
        }
    
    def extract_contacts(self, data: str) -> Dict[str, List[str]]:
        """Extract contacts from text data"""
        contacts = {
            'phones': [],
            'emails': [],
            'whatsapp': [],
            'telegram': []
        }
        
        # Extract phone numbers
        phones = re.findall(self.contact_patterns['phone'], data)
        contacts['phones'] = list(set(phones))
        
        # Extract emails
        emails = re.findall(self.contact_patterns['email'], data)
        contacts['emails'] = list(set(emails))
        
        # Extract WhatsApp links
        whatsapp = re.findall(self.contact_patterns['whatsapp'], data)
        contacts['whatsapp'] = list(set(whatsapp))
        
        # Extract Telegram links
        telegram = re.findall(self.contact_patterns['telegram'], data)
        contacts['telegram'] = list(set(telegram))
        
        return contacts
    
    def normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        # Handle Indonesian phone numbers
        if digits.startswith('62'):
            return digits
        elif digits.startswith('0'):
            return '62' + digits[1:]
        else:
            return '62' + digits
    
    def create_contact_fingerprint(self, contact: str, contact_type: str) -> str:
        """Create unique fingerprint for contact"""
        if contact_type == 'phone':
            normalized = self.normalize_phone(contact)
            return hashlib.sha256(normalized.encode()).hexdigest()
        else:
            return hashlib.sha256(contact.lower().encode()).hexdigest()
    
    def analyze_contacts_correlation(self, evidence_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contacts correlation across evidence"""
        all_contacts = {}
        contact_sources = {}
        correlations = []
        
        # Process each evidence item
        for evidence in evidence_data:
            evidence_id = evidence.get('id')
            evidence_type = evidence.get('type')
            content = evidence.get('content', '')
            
            # Extract contacts from content
            contacts = self.extract_contacts(content)
            
            # Store contacts with source information
            for contact_type, contact_list in contacts.items():
                for contact in contact_list:
                    fingerprint = self.create_contact_fingerprint(contact, contact_type)
                    
                    if fingerprint not in all_contacts:
                        all_contacts[fingerprint] = {
                            'contact': contact,
                            'type': contact_type,
                            'sources': [],
                            'frequency': 0
                        }
                    
                    all_contacts[fingerprint]['sources'].append({
                        'evidence_id': evidence_id,
                        'evidence_type': evidence_type
                    })
                    all_contacts[fingerprint]['frequency'] += 1
        
        # Find correlations (contacts appearing in multiple sources)
        for fingerprint, contact_info in all_contacts.items():
            if len(contact_info['sources']) > 1:
                correlation = {
                    'contact': contact_info['contact'],
                    'type': contact_info['type'],
                    'frequency': contact_info['frequency'],
                    'sources': contact_info['sources'],
                    'significance': self._calculate_significance(contact_info)
                }
                correlations.append(correlation)
        
        # Sort by significance
        correlations.sort(key=lambda x: x['significance'], reverse=True)
        
        return {
            'total_contacts': len(all_contacts),
            'unique_contacts': len([c for c in all_contacts.values() if len(c['sources']) == 1]),
            'correlated_contacts': len(correlations),
            'correlations': correlations,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
    
    def _calculate_significance(self, contact_info: Dict[str, Any]) -> float:
        """Calculate significance score for contact correlation"""
        frequency = contact_info['frequency']
        source_count = len(contact_info['sources'])
        
        # Base score from frequency and source count
        base_score = (frequency * 0.4) + (source_count * 0.6)
        
        # Bonus for high-frequency contacts
        if frequency >= 5:
            base_score *= 1.5
        elif frequency >= 3:
            base_score *= 1.2
        
        # Normalize to 0-1 range
        return min(base_score / 10, 1.0)
    
    def generate_contact_network(self, correlations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate contact network visualization data"""
        nodes = []
        edges = []
        
        # Create nodes for each contact
        for i, correlation in enumerate(correlations):
            nodes.append({
                'id': f"contact_{i}",
                'label': correlation['contact'],
                'type': correlation['type'],
                'frequency': correlation['frequency'],
                'significance': correlation['significance']
            })
        
        # Create edges between contacts that appear together
        for i, corr1 in enumerate(correlations):
            for j, corr2 in enumerate(correlations[i+1:], i+1):
                # Check if contacts appear in same evidence
                sources1 = {s['evidence_id'] for s in corr1['sources']}
                sources2 = {s['evidence_id'] for s in corr2['sources']}
                
                if sources1.intersection(sources2):
                    edges.append({
                        'source': f"contact_{i}",
                        'target': f"contact_{j}",
                        'weight': len(sources1.intersection(sources2))
                    })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'total_nodes': len(nodes),
            'total_edges': len(edges)
        }
