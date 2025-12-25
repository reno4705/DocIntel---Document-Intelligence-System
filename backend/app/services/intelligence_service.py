"""
Corporate Document Intelligence Service

Research-worthy document analysis that extracts:
1. Structured data (forms, tables, key-value pairs)
2. Decisions and actions
3. Timeline events
4. Key findings and conclusions
5. Stakeholder roles and responsibilities
6. Cross-document patterns

This goes beyond basic NER to provide ACTIONABLE INTELLIGENCE.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

from app.core import logger


@dataclass
class DocumentIntelligence:
    """Structured intelligence extracted from a document."""
    document_id: str
    document_type: str  # form, report, memo, letter, specification, test_result, etc.
    title: str
    date: Optional[str]
    
    # Key structured data
    key_fields: Dict[str, Any]  # Extracted form fields, key-value pairs
    
    # People and roles
    stakeholders: List[Dict[str, str]]  # name, role (author, recipient, approver, etc.)
    
    # Actions and decisions
    decisions: List[Dict[str, Any]]  # decision text, decision_maker, date
    action_items: List[Dict[str, Any]]  # action, responsible_party, deadline
    
    # Key findings
    findings: List[str]  # Important conclusions, results, observations
    
    # Timeline events
    events: List[Dict[str, Any]]  # event description, date, participants
    
    # Document relationships
    references: List[str]  # Other documents referenced
    related_projects: List[str]  # Projects, products, initiatives mentioned


class IntelligenceService:
    """
    Extracts meaningful intelligence from documents.
    
    Unlike basic NER which just finds names, this service:
    - Understands document structure
    - Extracts decisions and their context
    - Builds timelines
    - Identifies key findings
    - Maps stakeholder roles
    """
    
    def __init__(self):
        # Document type patterns
        self.doc_type_patterns = {
            'specification': r'specif|spec\.|blend|formula|design',
            'meeting_report': r'meeting|minutes|agenda|conference',
            'memo': r'memo|memorandum|to:|from:',
            'test_result': r'test|assay|analysis|result|lab|experiment',
            'authorization': r'authorization|approval|change.*order|request',
            'letter': r'dear|sincerely|regards',
            'invoice': r'invoice|bill|payment|amount due',
            'contract': r'agreement|contract|terms|conditions',
            'report': r'report|summary|findings|conclusion'
        }
        
        # Date patterns
        self.date_patterns = [
            r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
            r'\b(\d{1,2}-\d{1,2}-\d{2,4})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b',
            r'\b(\d{4}-\d{2}-\d{2})\b'
        ]
        
        # Role/responsibility patterns
        self.role_patterns = {
            'author': [r'written by[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)', 
                      r'prepared by[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
                      r'from[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)'],
            'recipient': [r'to[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
                         r'attention[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
                         r'original to[:\s-]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)'],
            'approver': [r'approved by[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
                        r'authorized by[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)'],
            'cc': [r'cc[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
                   r'copies? to[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)'],
            'investigator': [r'investigator[s]?[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)'],
            'responsible': [r'responsibility[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)',
                           r'responsible[:\s]*([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)']
        }
        
        # Key-value extraction patterns
        self.kv_patterns = [
            r'^([A-Z][A-Za-z\s]+)[:\-]+\s*(.+)$',
            r'^([A-Z][A-Z\s]+)[:\-]+\s*(.+)$'
        ]
    
    def analyze_document(self, doc_id: str, text: str, filename: str = "") -> DocumentIntelligence:
        """
        Perform comprehensive intelligence extraction on a document.
        """
        text_lower = text.lower()
        
        # 1. Determine document type
        doc_type = self._classify_document_type(text_lower, filename)
        
        # 2. Extract dates
        dates = self._extract_dates(text)
        primary_date = dates[0] if dates else None
        
        # 3. Extract title
        title = self._extract_title(text, filename)
        
        # 4. Extract key fields (structured data)
        key_fields = self._extract_key_fields(text, doc_type)
        
        # 5. Extract stakeholders with roles
        stakeholders = self._extract_stakeholders(text)
        
        # 6. Extract decisions
        decisions = self._extract_decisions(text)
        
        # 7. Extract action items
        action_items = self._extract_action_items(text)
        
        # 8. Extract key findings
        findings = self._extract_findings(text, doc_type)
        
        # 9. Build timeline events
        events = self._extract_timeline_events(text, dates)
        
        # 10. Find document references
        references = self._extract_references(text)
        
        # 11. Identify related projects/products
        related_projects = self._extract_projects(text)
        
        return DocumentIntelligence(
            document_id=doc_id,
            document_type=doc_type,
            title=title,
            date=primary_date,
            key_fields=key_fields,
            stakeholders=stakeholders,
            decisions=decisions,
            action_items=action_items,
            findings=findings,
            events=events,
            references=references,
            related_projects=related_projects
        )
    
    def _classify_document_type(self, text: str, filename: str) -> str:
        """Classify document type based on content and filename."""
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        scores = {}
        for doc_type, pattern in self.doc_type_patterns.items():
            matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
            matches += len(re.findall(pattern, filename_lower, re.IGNORECASE)) * 2
            scores[doc_type] = matches
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return "general"
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract all dates from text."""
        dates = []
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        return list(set(dates))[:10]  # Limit to 10 unique dates
    
    def _extract_title(self, text: str, filename: str) -> str:
        """Extract document title."""
        lines = text.strip().split('\n')
        
        # Look for title patterns
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 5 and len(line) < 100:
                # Skip lines that look like metadata
                if not re.match(r'^(date|from|to|cc|page|form)[\s:]+', line, re.IGNORECASE):
                    if line.isupper() or (len(line.split()) <= 10 and line[0].isupper()):
                        return line
        
        # Fallback to filename
        if filename:
            return filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
        
        return "Untitled Document"
    
    def _extract_key_fields(self, text: str, doc_type: str) -> Dict[str, Any]:
        """Extract structured key-value fields based on document type."""
        fields = {}
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Look for key: value patterns
            for pattern in self.kv_patterns:
                match = re.match(pattern, line)
                if match:
                    key = match.group(1).strip().lower().replace(' ', '_')
                    value = match.group(2).strip()
                    if len(key) < 30 and len(value) < 200:
                        fields[key] = value
            
            # Look for labeled fields with dashes/underscores
            labeled = re.match(r'^([A-Za-z\s]+)[-_]+\s*(.+)$', line)
            if labeled:
                key = labeled.group(1).strip().lower().replace(' ', '_')
                value = labeled.group(2).strip()
                if len(key) < 30 and len(value) < 200 and key not in fields:
                    fields[key] = value
        
        return fields
    
    def _extract_stakeholders(self, text: str) -> List[Dict[str, str]]:
        """Extract people and their roles."""
        stakeholders = []
        seen_names = set()
        
        for role, patterns in self.role_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    name = match.strip()
                    if name and len(name) > 3 and name not in seen_names:
                        # Clean up name
                        name = re.sub(r'\s+', ' ', name)
                        if not re.match(r'^(Mr|Mrs|Ms|Dr|The|A|An)\b', name):
                            stakeholders.append({"name": name, "role": role})
                            seen_names.add(name)
        
        return stakeholders[:20]  # Limit
    
    def _extract_decisions(self, text: str) -> List[Dict[str, Any]]:
        """Extract decisions and their context."""
        decisions = []
        
        # Patterns that indicate decisions
        decision_patterns = [
            r'(?:decided|agreed|approved|authorized|confirmed|determined)[:\s]+(.{20,200})',
            r'(?:decision|approval|authorization)[:\s]+(.{20,200})',
            r'(?:it was|has been) (?:decided|agreed|approved)[:\s]*(.{20,200})',
            r'(?:we will|will be|shall be)[:\s]+(.{20,150})'
        ]
        
        for pattern in decision_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                decision_text = match.strip()
                if len(decision_text) > 20:
                    decisions.append({
                        "text": decision_text[:300],
                        "type": "decision"
                    })
        
        return decisions[:10]
    
    def _extract_action_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract action items and tasks."""
        actions = []
        
        action_patterns = [
            r'(?:action|task|todo|to do)[:\s]+(.{20,200})',
            r'(?:must|should|need to|required to)[:\s]+(.{20,150})',
            r'(?:responsibility)[:\s]+(.{20,150})'
        ]
        
        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                actions.append({"action": match.strip()[:200]})
        
        return actions[:10]
    
    def _extract_findings(self, text: str, doc_type: str) -> List[str]:
        """Extract key findings, conclusions, and results."""
        findings = []
        
        # Patterns for findings
        finding_patterns = [
            r'(?:conclusion|result|finding|summary)[:\s]+(.{30,300})',
            r'(?:concluded|found|determined|showed|indicated)[:\s]+(.{30,250})',
            r'(?:is judged|was found to be|is considered)[:\s]+(.{20,200})'
        ]
        
        for pattern in finding_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                finding = match.strip()
                if len(finding) > 20:
                    findings.append(finding[:300])
        
        # Look for CONCLUSION section
        conclusion_match = re.search(
            r'CONCLUSION[S]?[:\s]*(.{30,500}?)(?=\n\n|\n[A-Z]{3,}|$)', 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        if conclusion_match:
            findings.insert(0, conclusion_match.group(1).strip()[:300])
        
        return findings[:5]
    
    def _extract_timeline_events(self, text: str, dates: List[str]) -> List[Dict[str, Any]]:
        """Build timeline of events from the document."""
        events = []
        
        # Look for date + context patterns
        for date in dates:
            # Find context around the date
            pattern = rf'.{{0,50}}{re.escape(date)}.{{0,100}}'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                events.append({
                    "date": date,
                    "description": match.strip()[:150]
                })
        
        return events[:10]
    
    def _extract_references(self, text: str) -> List[str]:
        """Find references to other documents."""
        references = []
        
        # Look for document number patterns
        doc_patterns = [
            r'(?:document|doc|ref|reference)[\s#\.]*(\d+[-/]?\d*)',
            r'(?:sample|form|report)[\s#\.no]*(\d+)',
            r'(?:see|refer to|attached)[:\s]+(.{10,50})'
        ]
        
        for pattern in doc_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend([m.strip() for m in matches if len(m.strip()) > 2])
        
        return list(set(references))[:10]
    
    def _extract_projects(self, text: str) -> List[str]:
        """Identify projects, products, or initiatives mentioned."""
        projects = []
        
        # Look for product/project names (capitalized multi-word phrases)
        project_patterns = [
            r'(?:project|product|brand|program)[:\s]+([A-Z][A-Za-z\s]+)',
            r'\b([A-Z][A-Z\s]{3,30})\b(?:\s+(?:project|product|brand|program))?'
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                name = match.strip()
                if len(name) > 3 and len(name) < 50:
                    projects.append(name)
        
        return list(set(projects))[:10]
    
    def generate_corpus_intelligence(self, documents: List[DocumentIntelligence]) -> Dict[str, Any]:
        """
        Generate cross-document intelligence from multiple documents.
        """
        if not documents:
            return {}
        
        # Aggregate stakeholders across documents
        all_stakeholders = defaultdict(lambda: {"roles": set(), "documents": []})
        for doc in documents:
            for s in doc.stakeholders:
                name = s["name"]
                all_stakeholders[name]["roles"].add(s["role"])
                all_stakeholders[name]["documents"].append(doc.document_id)
        
        # Build stakeholder summary
        stakeholder_summary = [
            {
                "name": name,
                "roles": list(data["roles"]),
                "document_count": len(data["documents"]),
                "documents": data["documents"][:5]
            }
            for name, data in sorted(
                all_stakeholders.items(), 
                key=lambda x: len(x[1]["documents"]), 
                reverse=True
            )[:20]
        ]
        
        # Aggregate timeline
        all_events = []
        for doc in documents:
            for event in doc.events:
                event["document_id"] = doc.document_id
                all_events.append(event)
        
        # Sort events by date (basic sorting)
        # In a real system, you'd parse and properly sort dates
        
        # Aggregate decisions
        all_decisions = []
        for doc in documents:
            for decision in doc.decisions:
                decision["document_id"] = doc.document_id
                decision["date"] = doc.date
                all_decisions.append(decision)
        
        # Aggregate findings
        all_findings = []
        for doc in documents:
            for finding in doc.findings:
                all_findings.append({
                    "finding": finding,
                    "document_id": doc.document_id,
                    "document_type": doc.document_type
                })
        
        # Document type distribution
        type_counts = defaultdict(int)
        for doc in documents:
            type_counts[doc.document_type] += 1
        
        # Related projects across corpus
        all_projects = defaultdict(int)
        for doc in documents:
            for project in doc.related_projects:
                all_projects[project] += 1
        
        top_projects = sorted(all_projects.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "document_count": len(documents),
            "document_types": dict(type_counts),
            "key_stakeholders": stakeholder_summary,
            "timeline_events": all_events[:30],
            "key_decisions": all_decisions[:20],
            "key_findings": all_findings[:15],
            "projects_products": [{"name": p[0], "mentions": p[1]} for p in top_projects],
            "date_range": self._get_date_range(documents)
        }
    
    def _get_date_range(self, documents: List[DocumentIntelligence]) -> Dict[str, str]:
        """Get the date range of documents."""
        dates = [d.date for d in documents if d.date]
        if not dates:
            return {"earliest": "Unknown", "latest": "Unknown"}
        return {"earliest": min(dates), "latest": max(dates)}


# Singleton instance
intelligence_service = IntelligenceService()
