"""
Groq LLM Service for Intelligent Document Analysis (Improved)

Enhanced forensic analysis with:
- Document scoring and risk ranking
- Evidence extraction with direct quotes
- Relationship mapping between actors
- Deeper causal analysis
- Automatic API key fallback on rate limit
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from groq import Groq
from app.core import logger, settings

# Load .env file
load_dotenv()

# Get API keys from environment (primary and fallback)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_KEY_SECONDARY = os.getenv("GROQ_API_KEY_SECONDARY", "")


class GroqService:
    """
    Enhanced intelligent document analysis using Groq's Llama 3.3.
    
    Forensic-grade extraction:
    - Risk scoring for documents
    - Direct quotes as evidence
    - Actor relationships and hierarchies
    - Red flag detection
    - Causal chain analysis
    
    Features automatic API key fallback when rate limited.
    """
    
    def __init__(self):
        self._clients = {}  # Cache clients by API key
        self._model = "llama-3.3-70b-versatile"
        self._current_key_index = 0
        self._api_keys = [k for k in [GROQ_API_KEY, GROQ_API_KEY_SECONDARY] if k]
    
    def _get_client(self, key_index: int = None):
        """Get or create a Groq client for the specified key index."""
        if key_index is None:
            key_index = self._current_key_index
        
        if key_index >= len(self._api_keys):
            return None
        
        api_key = self._api_keys[key_index]
        if api_key not in self._clients:
            self._clients[api_key] = Groq(api_key=api_key)
        
        return self._clients[api_key]
    
    @property
    def client(self):
        """Get the current active client."""
        return self._get_client(self._current_key_index)
    
    def _switch_to_fallback(self):
        """Switch to the next available API key."""
        if self._current_key_index < len(self._api_keys) - 1:
            self._current_key_index += 1
            logger.info(f"Switched to fallback API key #{self._current_key_index + 1}")
            return True
        return False
    
    def _reset_to_primary(self):
        """Reset to primary API key."""
        self._current_key_index = 0
    
    def is_available(self) -> bool:
        """Check if Groq service is available."""
        return len(self._api_keys) > 0 and self.client is not None
    
    def _make_api_call(self, messages: List[Dict], temperature: float = 0.1, max_tokens: int = 2500) -> Any:
        """
        Make API call with automatic fallback on rate limit.
        """
        last_error = None
        
        # Try each available API key
        for attempt in range(len(self._api_keys)):
            try:
                client = self._get_client(self._current_key_index)
                if client is None:
                    continue
                
                response = client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
                
            except Exception as e:
                error_str = str(e)
                last_error = e
                
                # Check if it's a rate limit error
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    logger.warning(f"Rate limit hit on API key #{self._current_key_index + 1}: {error_str[:100]}")
                    
                    # Try to switch to fallback key
                    if self._switch_to_fallback():
                        logger.info("Retrying with fallback API key...")
                        continue
                    else:
                        logger.error("All API keys exhausted (rate limited)")
                        raise Exception(f"All API keys rate limited. Please wait and try again. Last error: {error_str}")
                else:
                    # For non-rate-limit errors, don't switch keys
                    raise e
        
        # If we get here, all keys failed
        raise last_error if last_error else Exception("No API keys available")
    
    def analyze_document(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Perform deep forensic analysis on a document.
        
        Enhanced with:
        - Risk scoring (1-10)
        - Direct evidence quotes
        - Red flag detection
        - Relationship indicators
        """
        if not self.is_available():
            return {"error": "Groq API not configured", "available": False}
        
        if not text or len(text.strip()) < 50:
            return {"error": "Text too short for analysis"}
        
        text_to_analyze = text[:8000] if len(text) > 8000 else text
        
        prompt = f"""You are a forensic document analyst investigating corporate documents. Analyze this document with a critical eye for accountability and evidence.

DOCUMENT TEXT:
{text_to_analyze}

Extract the following in JSON format. Be SPECIFIC - use exact names, dates, and QUOTE directly from the document.

{{
  "document_type": "specific type (memo, test_report, approval_form, specification, invoice, meeting_minutes, correspondence)",
  "title": "exact title or subject line from document",
  "date": "primary date (YYYY-MM-DD format if possible)",
  "organization": "organization name",
  
  "risk_score": {{
    "score": 1-10,
    "reason": "why this score - what makes this document significant or routine"
  }},
  
  "evidence": [
    {{
      "quote": "EXACT quote from the document (copy verbatim)",
      "significance": "why this quote matters for accountability",
      "type": "admission/decision/knowledge/instruction/finding"
    }}
  ],
  
  "stakeholders": [
    {{
      "name": "EXACT name as written",
      "role": "specific role (author/approver/recipient/investigator/manager)",
      "action": "what they specifically did (signed, approved, requested, received)",
      "knowledge_level": "what this document shows they knew"
    }}
  ],
  
  "decisions": [
    {{
      "decision": "exact decision made",
      "decision_maker": "who made it",
      "date": "when",
      "impact": "consequence or significance of this decision"
    }}
  ],
  
  "findings": [
    {{
      "finding": "specific finding or conclusion",
      "evidence_quote": "supporting quote from document",
      "implications": "what this finding implies"
    }}
  ],
  
  "red_flags": [
    {{
      "flag": "concerning element identified",
      "quote": "supporting evidence from document",
      "concern_level": "high/medium/low"
    }}
  ],
  
  "timeline_events": [
    {{"date": "date", "event": "what happened", "actors": ["who was involved"]}}
  ],
  
  "key_numbers": [
    {{"value": "dollar amount, percentage, or quantity", "context": "what it refers to"}}
  ],
  
  "relationships_indicated": [
    {{"from": "person A", "to": "person B", "relationship": "reports_to/communicated_with/approved_by/requested_from"}}
  ]
}}

Return ONLY valid JSON. Extract REAL information - do not make up names or quotes."""

        try:
            messages = [
                {"role": "system", "content": "You are a forensic document analyst. Extract specific, verifiable information with exact quotes. Never fabricate - only report what's actually in the document."},
                {"role": "user", "content": prompt}
            ]
            response = self._make_api_call(messages, temperature=0.1, max_tokens=2500)
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            result = json.loads(result_text)
            result["analysis_success"] = True
            result["filename"] = filename
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response as JSON: {e}")
            return {"error": "Failed to parse analysis", "raw_response": result_text[:500]}
        except Exception as e:
            logger.error(f"Groq analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def extract_accountability_trail(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build a comprehensive accountability trail with:
        - Actor network and relationships
        - Evidence chain with quotes
        - Risk-ranked findings
        - Causal connections between events
        """
        if not self.is_available():
            return {"error": "Groq API not configured"}
        
        # Prepare detailed document summaries with evidence
        doc_summaries = []
        for doc in documents[:15]:  # Limit for context
            summary = f"[{doc.get('filename', 'Unknown')}]\n"
            summary += f"Date: {doc.get('date', 'Unknown')} | Type: {doc.get('document_type', 'Unknown')}\n"
            
            # Include risk score if available
            if doc.get('risk_score'):
                rs = doc['risk_score']
                if isinstance(rs, dict):
                    summary += f"Risk Score: {rs.get('score', 'N/A')}/10 - {rs.get('reason', '')}\n"
            
            # Include stakeholders with their actions
            if doc.get('stakeholders'):
                people = []
                for s in doc['stakeholders'][:5]:
                    if s and s.get('name'):
                        action = s.get('action', s.get('role', ''))
                        people.append(f"{s['name']} ({action})")
                if people:
                    summary += f"People: {', '.join(people)}\n"
            
            # Include evidence quotes
            if doc.get('evidence'):
                for ev in doc['evidence'][:2]:
                    if ev and ev.get('quote'):
                        summary += f"Evidence: \"{ev['quote'][:150]}...\" ({ev.get('type', '')})\n"
            
            # Include red flags
            if doc.get('red_flags'):
                flags = [f.get('flag', '') for f in doc['red_flags'][:2] if f]
                if flags:
                    summary += f"Red Flags: {'; '.join(flags)}\n"
            
            # Include decisions
            if doc.get('decisions'):
                for d in doc['decisions'][:2]:
                    if d and d.get('decision'):
                        summary += f"Decision: {d['decision'][:100]} (by {d.get('decision_maker', 'unknown')})\n"
            
            # Include key numbers
            if doc.get('key_numbers'):
                nums = [f"{n.get('value', '')} ({n.get('context', '')})" for n in doc['key_numbers'][:3] if n]
                if nums:
                    summary += f"Numbers: {', '.join(nums)}\n"
            
            doc_summaries.append(summary)
        
        combined = "\n---\n".join(doc_summaries)
        
        prompt = f"""You are an investigative analyst building an accountability case from corporate documents. Analyze these document summaries to construct a comprehensive accountability trail.

DOCUMENT EVIDENCE:
{combined}

Create a forensic analysis report in JSON format:

{{
  "executive_summary": "2-3 sentence summary of what these documents reveal about accountability",
  
  "key_actors": [
    {{
      "name": "person name",
      "role": "their organizational role",
      "involvement_summary": "specific description of what they knew and did",
      "key_actions": ["list of specific actions they took"],
      "documents_involved": ["documents they appear in"],
      "accountability_level": "high/medium/low - how central are they",
      "evidence_strength": "strong/moderate/weak - how well documented"
    }}
  ],
  
  "actor_relationships": [
    {{
      "from": "person A",
      "to": "person B", 
      "relationship": "reports_to/approved_by/communicated_with/supervised",
      "evidence": "document showing this relationship"
    }}
  ],
  
  "timeline": [
    {{
      "date": "date",
      "event": "what happened",
      "significance": "why this matters for accountability",
      "actors_involved": ["names"],
      "source_document": "document name",
      "evidence_quote": "key quote if available"
    }}
  ],
  
  "causal_chain": [
    {{
      "cause": "earlier event or decision",
      "effect": "resulting event or outcome",
      "connection_strength": "direct/indirect/implied"
    }}
  ],
  
  "red_flags": [
    {{
      "issue": "concerning finding",
      "severity": "critical/high/medium/low",
      "evidence": "supporting quote or document",
      "actors_implicated": ["names"]
    }}
  ],
  
  "evidence_summary": [
    {{
      "claim": "factual claim that can be made",
      "supporting_documents": ["list of documents supporting this"],
      "key_quote": "strongest supporting quote",
      "confidence": "high/medium/low"
    }}
  ],
  
  "patterns_detected": [
    {{
      "pattern": "recurring theme or behavior",
      "instances": ["specific examples"],
      "significance": "why this pattern matters"
    }}
  ],
  
  "knowledge_timeline": [
    {{
      "date": "when",
      "who_knew": ["names"],
      "what_they_knew": "specific knowledge",
      "source": "document"
    }}
  ],
  
  "recommendations": [
    "specific follow-up actions for investigation"
  ],
  
  "summary": "comprehensive 3-4 sentence summary of accountability findings"
}}

Be specific and cite actual evidence. Don't fabricate - only include what's supported by the documents."""

        try:
            messages = [
                {"role": "system", "content": "You are a forensic investigator analyzing corporate documents to establish accountability. Be thorough, specific, and evidence-based."},
                {"role": "user", "content": prompt}
            ]
            response = self._make_api_call(messages, temperature=0.2, max_tokens=4000)
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Accountability trail extraction failed: {str(e)}")
            return {"error": str(e)}
    
    def answer_question(self, question: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Answer questions with evidence-based responses including quotes.
        """
        if not self.is_available():
            return {"error": "Groq API not configured"}
        
        context = ""
        for doc in context_docs[:5]:
            context += f"\n[Document: {doc.get('filename', 'Unknown')}]\n"
            context += doc.get('content', '')[:2000] + "\n"
        
        prompt = f"""Based on these documents, answer the question with specific evidence.

DOCUMENTS:
{context}

QUESTION: {question}

Provide an evidence-based answer. Include EXACT QUOTES from the documents to support your answer.

Format as JSON:
{{
  "answer": "your detailed answer",
  "confidence": "high/medium/low",
  "evidence": [
    {{
      "document": "filename",
      "quote": "EXACT quote from document supporting the answer",
      "relevance": "how this quote supports the answer"
    }}
  ],
  "related_findings": ["other relevant facts discovered"],
  "limitations": "what the documents don't tell us"
}}"""

        try:
            messages = [
                {"role": "system", "content": "You are a research analyst providing evidence-based answers. Always cite specific quotes from documents."},
                {"role": "user", "content": prompt}
            ]
            response = self._make_api_call(messages, temperature=0.3, max_tokens=2000)
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
            
            return json.loads(result_text)
            
        except Exception as e:
            logger.error(f"Question answering failed: {str(e)}")
            return {"error": str(e), "answer": f"Failed to answer: {str(e)}"}


# Singleton instance
groq_service = GroqService()
