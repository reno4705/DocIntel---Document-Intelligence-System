"""
LLM Service - Gemini-powered intelligent document processing

Provides:
- Document Q&A chatbot
- Universal smart extraction (any document type)
- Cross-document reasoning
- Conversation memory
"""

import os
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

import google.generativeai as genai
from app.core import logger, settings

# Configure Gemini - get from settings (which loads from .env)
GEMINI_API_KEY = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured successfully")


class LLMService:
    def __init__(self):
        self._model = None
        self._chat_sessions: Dict[str, Any] = {}  # session_id -> chat history
        
    @property
    def model(self):
        if self._model is None and GEMINI_API_KEY:
            logger.info("Initializing Gemini model...")
            self._model = genai.GenerativeModel('gemini-2.0-flash')
        return self._model
    
    def is_available(self) -> bool:
        """Check if LLM service is available."""
        return bool(GEMINI_API_KEY and self.model)
    
    # ==================== CHAT / Q&A ====================
    
    def chat(
        self, 
        message: str, 
        context_documents: List[Dict[str, Any]] = None,
        session_id: str = "default",
        knowledge_graph_context: str = ""
    ) -> Dict[str, Any]:
        """
        Chat with documents using RAG (Retrieval-Augmented Generation).
        
        Args:
            message: User's question
            context_documents: Relevant document chunks to use as context
            session_id: Session ID for conversation memory
            knowledge_graph_context: Additional context from knowledge graph
        
        Returns:
            Response with answer and citations
        """
        if not self.is_available():
            return {
                "success": False,
                "answer": "LLM service not available. Please configure GEMINI_API_KEY.",
                "citations": []
            }
        
        try:
            # Build context from documents
            doc_context = ""
            citations = []
            
            if context_documents:
                doc_context = "\n\n--- DOCUMENT CONTEXT ---\n"
                for i, doc in enumerate(context_documents[:5]):  # Limit to 5 docs
                    doc_context += f"\n[Document {i+1}: {doc.get('filename', 'Unknown')}]\n"
                    doc_context += f"{doc.get('content', doc.get('text', ''))[:2000]}\n"
                    citations.append({
                        "doc_id": doc.get("id", ""),
                        "filename": doc.get("filename", "Unknown"),
                        "relevance": doc.get("relevance", 0)
                    })
            
            # Build prompt
            system_prompt = """You are an intelligent document assistant. Your job is to:
1. Answer questions about the documents provided in the context
2. Always cite which document your answer comes from
3. If the answer is not in the documents, say so clearly
4. Be concise but thorough
5. If asked to compare or analyze across documents, do so

Format your response clearly. When citing, mention the document name."""

            full_prompt = f"""{system_prompt}

{doc_context}

{f"--- KNOWLEDGE GRAPH INFO ---{chr(10)}{knowledge_graph_context}" if knowledge_graph_context else ""}

--- USER QUESTION ---
{message}

Please provide a helpful answer based on the document context above."""

            # Get or create chat session
            if session_id not in self._chat_sessions:
                self._chat_sessions[session_id] = {
                    "history": [],
                    "created": datetime.utcnow().isoformat()
                }
            
            # Generate response with retry logic for rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(full_prompt)
                    answer = response.text
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        raise
            
            # Store in history
            self._chat_sessions[session_id]["history"].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            self._chat_sessions[session_id]["history"].append({
                "role": "assistant", 
                "content": answer,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "success": True,
                "answer": answer,
                "citations": citations,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return {
                "success": False,
                "answer": f"Error processing your question: {str(e)}",
                "citations": []
            }
    
    # ==================== UNIVERSAL SMART EXTRACTION ====================
    
    def extract_information(
        self, 
        text: str, 
        document_type: str = "auto",
        custom_fields: List[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured information from ANY document type.
        
        Args:
            text: Document text
            document_type: Type hint (auto, invoice, contract, report, letter, form, etc.)
            custom_fields: Optional list of specific fields to extract
        
        Returns:
            Structured extraction with detected fields
        """
        if not self.is_available():
            return {
                "success": False,
                "document_type": "unknown",
                "extracted_fields": {},
                "key_points": [],
                "error": "LLM service not available"
            }
        
        try:
            # Build extraction prompt
            if custom_fields:
                fields_instruction = f"Extract these specific fields: {', '.join(custom_fields)}"
            else:
                fields_instruction = """Automatically detect and extract ALL relevant fields such as:
- Names (people, companies, organizations)
- Dates (any dates mentioned with their context)
- Amounts/Numbers (money, quantities, percentages)
- Addresses/Locations
- Reference numbers (invoice #, contract #, order #, etc.)
- Contact information (phone, email, website)
- Key terms and conditions
- Action items or requirements
- Any other important structured data"""

            prompt = f"""Analyze this document and extract structured information.

--- DOCUMENT TEXT ---
{text[:4000]}

--- INSTRUCTIONS ---
1. First, identify what type of document this is (invoice, contract, letter, report, form, resume, medical record, etc.)
2. {fields_instruction}
3. List 3-5 key points or summary of the document
4. Identify any action items or important deadlines

Respond in this exact JSON format:
{{
    "document_type": "detected type",
    "confidence": 0.95,
    "extracted_fields": {{
        "field_name": "value",
        "another_field": "value"
    }},
    "key_points": [
        "Key point 1",
        "Key point 2"
    ],
    "action_items": [
        "Action item if any"
    ],
    "dates_mentioned": [
        {{"date": "Jan 15, 2024", "context": "due date"}}
    ],
    "entities": {{
        "people": ["Name 1"],
        "organizations": ["Org 1"],
        "locations": ["Location 1"]
    }}
}}

Return ONLY valid JSON, no other text."""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response - extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            try:
                extracted = json.loads(response_text)
                extracted["success"] = True
                return extracted
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response
                return {
                    "success": True,
                    "document_type": "unknown",
                    "extracted_fields": {},
                    "key_points": [response_text[:500]],
                    "raw_response": response_text
                }
                
        except Exception as e:
            logger.error(f"Extraction error: {str(e)}")
            return {
                "success": False,
                "document_type": "unknown", 
                "extracted_fields": {},
                "key_points": [],
                "error": str(e)
            }
    
    # ==================== CROSS-DOCUMENT ANALYSIS ====================
    
    def analyze_documents(
        self,
        documents: List[Dict[str, Any]],
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Analyze multiple documents together.
        
        Args:
            documents: List of documents with text content
            analysis_type: Type of analysis (summary, compare, timeline, contradictions)
        
        Returns:
            Analysis results
        """
        if not self.is_available():
            return {"success": False, "error": "LLM service not available"}
        
        try:
            # Build document summaries
            doc_summaries = ""
            for i, doc in enumerate(documents[:10]):  # Limit to 10 docs
                text = doc.get("content", doc.get("text", ""))[:1000]
                doc_summaries += f"\n[Document {i+1}: {doc.get('filename', 'Unknown')}]\n{text}\n"
            
            prompts = {
                "summary": f"""Provide a comprehensive summary of these documents:
{doc_summaries}

Summarize:
1. Main themes across all documents
2. Key information from each
3. Overall insights""",
                
                "compare": f"""Compare and contrast these documents:
{doc_summaries}

Identify:
1. Similarities between documents
2. Differences between documents
3. Connections or relationships""",
                
                "timeline": f"""Extract a timeline from these documents:
{doc_summaries}

Create a chronological timeline of events, dates, and milestones mentioned.""",
                
                "contradictions": f"""Find any contradictions or inconsistencies across these documents:
{doc_summaries}

Identify:
1. Any conflicting information
2. Inconsistent dates or numbers
3. Contradictory statements"""
            }
            
            prompt = prompts.get(analysis_type, prompts["summary"])
            response = self.model.generate_content(prompt)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "result": response.text,
                "documents_analyzed": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # ==================== CONVERSATION MANAGEMENT ====================
    
    def get_chat_history(self, session_id: str = "default") -> List[Dict]:
        """Get chat history for a session."""
        if session_id in self._chat_sessions:
            return self._chat_sessions[session_id]["history"]
        return []
    
    def clear_chat_history(self, session_id: str = "default") -> bool:
        """Clear chat history for a session."""
        if session_id in self._chat_sessions:
            self._chat_sessions[session_id]["history"] = []
            return True
        return False
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs."""
        return list(self._chat_sessions.keys())


# Singleton instance
llm_service = LLMService()
