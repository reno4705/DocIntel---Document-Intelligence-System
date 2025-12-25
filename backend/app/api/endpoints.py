"""
Multi-Document Intelligence API Endpoints

Provides endpoints for:
- Document upload and processing
- Knowledge graph queries
- Cross-document reasoning
- Entity and relationship queries
"""

import uuid
import time
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Body
from typing import List, Dict, Any

from app.core import logger, settings
from app.schemas import (
    DocumentResponse,
    DocumentUploadResponse,
    ProcessingStats,
    ErrorResponse,
    QuestionRequest
)
from app.services import (
    ocr_service, 
    nlp_service, 
    knowledge_graph, 
    document_store,
    reasoning_engine
)
from app.utils import file_handler


router = APIRouter()


# ==================== Document Endpoints ====================

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a document.
    
    The document will be:
    1. OCR processed to extract text
    2. Analyzed for named entities (NER)
    3. Summarized
    4. Added to the knowledge graph
    5. Indexed for cross-document queries
    """
    start_time = time.time()
    temp_path = None
    doc_id = str(uuid.uuid4())
    
    try:
        file_content = await file.read()
        await file.seek(0)
        
        is_valid, error_message = file_handler.validate_file(
            file.filename, 
            len(file_content)
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message
            )
        
        temp_path, content = await file_handler.save_temp_file(file)
        file_extension = file_handler.get_file_extension(file.filename)
        
        logger.info(f"Processing file: {file.filename}")
        
        # Step 1: OCR extraction
        extracted_text = ocr_service.extract_text_from_file(content, file_extension)
        
        if not extracted_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text could be extracted from the document"
            )
        
        # Step 2: NER and summarization
        analysis_result = nlp_service.analyze_text(extracted_text)
        
        # Step 3: Add entities to knowledge graph
        entity_dicts = [
            {"text": e.text, "label": e.label, "score": e.score}
            for e in analysis_result.entities
        ]
        
        kg_entities = knowledge_graph.add_entities_from_document(
            doc_id=doc_id,
            entities=entity_dicts,
            full_text=extracted_text
        )
        
        entity_ids = [e.id for e in kg_entities]
        
        # Step 4: Add to document store
        doc_store_entry = document_store.add_document(
            doc_id=doc_id,
            filename=file.filename,
            content=extracted_text,
            summary=analysis_result.summary,
            file_type=file_extension.replace(".", "").upper(),
            entity_ids=entity_ids
        )
        
        processing_time = round(time.time() - start_time, 3)
        
        # Build response
        document = DocumentResponse(
            id=doc_id,
            filename=file.filename,
            upload_date=datetime.utcnow(),
            extracted_text=extracted_text,
            summary=analysis_result.summary,
            entities=analysis_result.entities,
            processing_time=processing_time,
            file_type=file_extension.replace(".", "").upper(),
            text_length=len(extracted_text),
            word_count=len(extracted_text.split()),
            entity_count=len(analysis_result.entities),
            keywords=doc_store_entry.keywords[:10]
        )
        
        logger.info(f"Document processed: {doc_id} ({len(kg_entities)} entities added to knowledge graph)")
        
        return DocumentUploadResponse(
            success=True,
            message=f"Document processed successfully. {len(kg_entities)} entities added to knowledge graph.",
            data=document
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )
    finally:
        if temp_path:
            file_handler.cleanup_temp_file(temp_path)


@router.post(
    "/upload/batch",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def upload_documents_batch(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple documents at once.
    
    All documents will be processed and added to the knowledge graph.
    """
    results = []
    errors = []
    
    for file in files:
        start_time = time.time()
        temp_path = None
        doc_id = str(uuid.uuid4())
        
        try:
            file_content = await file.read()
            await file.seek(0)
            
            is_valid, error_message = file_handler.validate_file(
                file.filename, 
                len(file_content)
            )
            
            if not is_valid:
                errors.append({"filename": file.filename, "error": error_message})
                continue
            
            temp_path, content = await file_handler.save_temp_file(file)
            file_extension = file_handler.get_file_extension(file.filename)
            
            logger.info(f"Processing file: {file.filename}")
            
            # OCR extraction
            extracted_text = ocr_service.extract_text_from_file(content, file_extension)
            
            if not extracted_text.strip():
                errors.append({"filename": file.filename, "error": "No text extracted"})
                continue
            
            # NER and summarization
            analysis_result = nlp_service.analyze_text(extracted_text)
            
            # Add to knowledge graph
            entity_dicts = [
                {"text": e.text, "label": e.label, "score": e.score}
                for e in analysis_result.entities
            ]
            
            kg_entities = knowledge_graph.add_entities_from_document(
                doc_id=doc_id,
                entities=entity_dicts,
                full_text=extracted_text
            )
            
            entity_ids = [e.id for e in kg_entities]
            
            # Add to document store
            document_store.add_document(
                doc_id=doc_id,
                filename=file.filename,
                content=extracted_text,
                summary=analysis_result.summary,
                file_type=file_extension.replace(".", "").upper(),
                entity_ids=entity_ids
            )
            
            processing_time = round(time.time() - start_time, 3)
            
            results.append({
                "id": doc_id,
                "filename": file.filename,
                "entities_added": len(kg_entities),
                "processing_time": processing_time
            })
            
            logger.info(f"Batch: processed {file.filename} ({len(kg_entities)} entities)")
            
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})
            logger.error(f"Batch upload error for {file.filename}: {str(e)}")
        finally:
            if temp_path:
                file_handler.cleanup_temp_file(temp_path)
    
    return {
        "success": True,
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "message": f"Processed {len(results)} documents, {len(errors)} failed"
    }


@router.get("/documents")
async def get_documents():
    """Get all documents in the corpus."""
    try:
        docs = document_store.get_all_documents()
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "upload_date": d.upload_date,
                "word_count": d.word_count,
                "entity_count": len(d.entity_ids),
                "keywords": d.keywords[:5]
            }
            for d in docs
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document with full details."""
    try:
        doc = document_store.get_document(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get entities for this document
        entities = knowledge_graph.get_document_entities(doc_id)
        
        return {
            "id": doc.id,
            "filename": doc.filename,
            "content": doc.content,
            "summary": doc.summary,
            "upload_date": doc.upload_date,
            "word_count": doc.word_count,
            "file_type": getattr(doc, 'file_type', 'Unknown'),
            "keywords": doc.keywords,
            "entities": [
                {
                    "name": e.canonical_name,
                    "type": e.entity_type,
                    "mentions": len(e.mentions)
                }
                for e in entities
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.get("/documents/{doc_id}/insights")
async def get_document_insights(doc_id: str):
    """Get AI-generated insights for a document."""
    try:
        insights = reasoning_engine.generate_document_insights(doc_id)
        return insights
    except Exception as e:
        logger.error(f"Failed to generate insights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate insights"
        )


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the corpus."""
    try:
        success = document_store.delete_document(doc_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        return {"success": True, "message": "Document deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


# ==================== Knowledge Graph Endpoints ====================

@router.get("/knowledge-graph")
async def get_knowledge_graph():
    """Get the full knowledge graph for visualization."""
    try:
        graph = knowledge_graph.export_for_visualization()
        stats = knowledge_graph.get_graph_stats()
        return {
            "nodes": graph["nodes"],
            "edges": graph["edges"],
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to get knowledge graph: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge graph"
        )


@router.get("/knowledge-graph/stats")
async def get_graph_stats():
    """Get knowledge graph statistics."""
    try:
        return knowledge_graph.get_graph_stats()
    except Exception as e:
        logger.error(f"Failed to get graph stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# ==================== Reasoning Endpoints ====================

@router.get("/query/entity/{entity_name}")
async def query_entity(entity_name: str):
    """
    Query: "What do we know about [entity]?"
    
    Returns all information about an entity across all documents.
    """
    try:
        result = reasoning_engine.query_entity(entity_name)
        return result
    except Exception as e:
        logger.error(f"Entity query failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query failed"
        )


@router.get("/query/connection")
async def query_connection(entity1: str, entity2: str):
    """
    Query: "How is [entity1] connected to [entity2]?"
    
    Finds relationships and connections between two entities.
    """
    try:
        result = reasoning_engine.find_connections(entity1, entity2)
        return result
    except Exception as e:
        logger.error(f"Connection query failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query failed"
        )


@router.get("/query/entities/{entity_type}")
async def query_entities_by_type(entity_type: str):
    """
    Query: "List all [entity_type]s"
    
    Returns all entities of a given type (PERSON, ORG, LOC, DATE, etc.)
    """
    try:
        result = reasoning_engine.aggregate_by_type(entity_type)
        return result
    except Exception as e:
        logger.error(f"Entity type query failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query failed"
        )


@router.post("/query/ask")
async def ask_question(request: QuestionRequest):
    """
    Ask a natural language question about the document corpus.
    
    Supported questions:
    - "What do we know about X?"
    - "How is X related to Y?"
    - "List all people/organizations/locations"
    - "Which documents mention X?"
    """
    try:
        result = reasoning_engine.answer_question(request.question)
        return result
    except Exception as e:
        logger.error(f"Question answering failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Query failed"
        )


@router.get("/query/contradictions")
async def find_contradictions():
    """Find potential contradictions across documents."""
    try:
        result = reasoning_engine.find_contradictions()
        return result
    except Exception as e:
        logger.error(f"Contradiction detection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis failed"
        )


# ==================== Search Endpoints ====================

@router.get("/search")
async def search_documents(q: str, max_results: int = 10):
    """Full-text search across all documents."""
    try:
        results = document_store.search_full_text(q, max_results)
        return {
            "query": q,
            "results": [
                {
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "relevance": score,
                    "summary": doc.summary[:200] + "..." if len(doc.summary) > 200 else doc.summary
                }
                for doc, score in results
            ]
        }
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# ==================== Overview Endpoints ====================

@router.get("/overview")
async def get_corpus_overview():
    """Get an overview of the entire document corpus."""
    try:
        return reasoning_engine.get_corpus_overview()
    except Exception as e:
        logger.error(f"Failed to get overview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overview"
        )


@router.get("/stats")
async def get_stats():
    """Get corpus statistics."""
    try:
        doc_stats = document_store.get_corpus_stats()
        graph_stats = knowledge_graph.get_graph_stats()
        
        return {
            "total_documents": doc_stats.get("document_count", 0),
            "total_entities": graph_stats.get("total_entities", 0),
            "total_relationships": graph_stats.get("total_relationships", 0),
            "entity_types": graph_stats.get("entity_types", {}),
            "file_types": doc_stats.get("file_types", {}),
            "top_keywords": doc_stats.get("top_keywords", [])
        }
    except Exception as e:
        logger.error(f"Failed to retrieve stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy", 
        "version": settings.APP_VERSION,
        "service": "Multi-Document Intelligence System"
    }


@router.delete("/reset")
async def reset_system():
    """Reset the entire system (clear all data). Use with caution!"""
    try:
        document_store.clear_store()
        knowledge_graph.clear_graph()
        return {"success": True, "message": "System reset complete"}
    except Exception as e:
        logger.error(f"Reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reset failed"
        )


# ==================== AI Chat Endpoints ====================

@router.post("/chat")
async def chat_with_documents(
    message: str = Body(..., embed=True),
    session_id: str = Body("default", embed=True)
):
    """
    Chat with your documents using AI.
    
    Ask any question about your uploaded documents and get intelligent answers
    with citations to the source documents.
    """
    from app.services import llm_service
    
    if not llm_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available. Please configure GEMINI_API_KEY."
        )
    
    try:
        # Search for relevant documents
        search_results = document_store.search_full_text(message, max_results=5)
        
        # Prepare document context
        context_docs = []
        for doc, score in search_results:
            context_docs.append({
                "id": doc.id,
                "filename": doc.filename,
                "content": doc.content[:2000],
                "relevance": score
            })
        
        # Get knowledge graph context
        kg_context = ""
        entities = knowledge_graph.search_entities(message)
        if entities:
            kg_context = f"Related entities: {', '.join([e.canonical_name for e in entities[:5]])}"
        
        # Chat with LLM
        result = llm_service.chat(
            message=message,
            context_documents=context_docs,
            session_id=session_id,
            knowledge_graph_context=kg_context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.post("/extract")
async def extract_information(
    document_id: str = Body(None, embed=True),
    text: str = Body(None, embed=True),
    custom_fields: List[str] = Body(None, embed=True)
):
    """
    Extract structured information from a document using AI.
    
    Works with ANY document type - invoices, contracts, reports, letters, forms, etc.
    The AI automatically detects the document type and extracts relevant fields.
    """
    from app.services import llm_service
    
    if not llm_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available. Please configure GEMINI_API_KEY."
        )
    
    try:
        # Get text from document if document_id provided
        if document_id and not text:
            doc = document_store.get_document(document_id)
            if not doc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            text = doc.content
        
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either document_id or text must be provided"
            )
        
        # Extract information
        result = llm_service.extract_information(
            text=text,
            custom_fields=custom_fields
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )


@router.post("/analyze")
async def analyze_documents(
    document_ids: List[str] = Body(None, embed=True),
    analysis_type: str = Body("summary", embed=True)
):
    """
    Analyze multiple documents together using AI.
    
    Analysis types:
    - summary: Get a comprehensive summary across all documents
    - compare: Compare and contrast documents
    - timeline: Extract chronological timeline
    - contradictions: Find inconsistencies
    """
    from app.services import llm_service
    
    if not llm_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available. Please configure GEMINI_API_KEY."
        )
    
    try:
        # Get documents
        if document_ids:
            docs = [document_store.get_document(did) for did in document_ids]
            docs = [d for d in docs if d]  # Filter None
        else:
            # Use all documents
            docs = document_store.get_all_documents()[:10]
        
        if not docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No documents found"
            )
        
        # Prepare document data
        doc_data = [
            {"id": d.id, "filename": d.filename, "content": d.content}
            for d in docs
        ]
        
        # Analyze
        result = llm_service.analyze_documents(
            documents=doc_data,
            analysis_type=analysis_type
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str = "default"):
    """Get chat history for a session."""
    from app.services import llm_service
    
    history = llm_service.get_chat_history(session_id)
    return {"session_id": session_id, "history": history}


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str = "default"):
    """Clear chat history for a session."""
    from app.services import llm_service
    
    llm_service.clear_chat_history(session_id)
    return {"success": True, "message": "Chat history cleared"}


@router.get("/ai/status")
async def get_ai_status():
    """Check if AI service is available."""
    from app.services import llm_service
    
    return {
        "available": llm_service.is_available(),
        "service": "Gemini Pro",
        "features": ["chat", "extraction", "analysis"] if llm_service.is_available() else []
    }


# ==================== Intelligence Endpoints ====================

@router.get("/intelligence/corpus")
async def get_corpus_intelligence():
    """
    Get comprehensive intelligence across all documents.
    
    Returns:
    - Key stakeholders and their roles
    - Timeline of events
    - Key decisions made
    - Key findings/conclusions
    - Projects/products mentioned
    - Document type breakdown
    """
    from app.services import intelligence_service
    from dataclasses import asdict
    
    try:
        # Get all documents
        docs = document_store.get_all_documents()
        
        if not docs:
            return {
                "document_count": 0,
                "message": "No documents uploaded yet"
            }
        
        # Analyze each document
        doc_intelligence = []
        for doc in docs:
            intel = intelligence_service.analyze_document(
                doc_id=doc.id,
                text=doc.content,
                filename=doc.filename
            )
            doc_intelligence.append(intel)
        
        # Generate corpus-wide intelligence
        corpus_intel = intelligence_service.generate_corpus_intelligence(doc_intelligence)
        
        return corpus_intel
        
    except Exception as e:
        logger.error(f"Intelligence extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intelligence extraction failed: {str(e)}"
        )


@router.get("/intelligence/document/{doc_id}")
async def get_document_intelligence(doc_id: str):
    """
    Get detailed intelligence for a specific document.
    """
    from app.services import intelligence_service
    from dataclasses import asdict
    
    try:
        doc = document_store.get_document(doc_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        intel = intelligence_service.analyze_document(
            doc_id=doc.id,
            text=doc.content,
            filename=doc.filename
        )
        
        return asdict(intel)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document intelligence failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intelligence extraction failed: {str(e)}"
        )


@router.get("/intelligence/stakeholders")
async def get_stakeholder_network():
    """
    Get stakeholder network across all documents.
    Shows who communicated with whom, their roles, and document involvement.
    """
    from app.services import intelligence_service
    from collections import defaultdict
    
    try:
        docs = document_store.get_all_documents()
        
        # Build comprehensive stakeholder map
        stakeholder_map = defaultdict(lambda: {
            "roles": set(),
            "documents": [],
            "connections": set()
        })
        
        for doc in docs:
            intel = intelligence_service.analyze_document(doc.id, doc.content, doc.filename)
            
            doc_people = []
            for s in intel.stakeholders:
                name = s["name"]
                stakeholder_map[name]["roles"].add(s["role"])
                stakeholder_map[name]["documents"].append({
                    "id": doc.id,
                    "title": intel.title,
                    "role": s["role"]
                })
                doc_people.append(name)
            
            # Build connections (people in same document)
            for i, p1 in enumerate(doc_people):
                for p2 in doc_people[i+1:]:
                    stakeholder_map[p1]["connections"].add(p2)
                    stakeholder_map[p2]["connections"].add(p1)
        
        # Format output
        stakeholders = []
        for name, data in stakeholder_map.items():
            stakeholders.append({
                "name": name,
                "roles": list(data["roles"]),
                "document_count": len(data["documents"]),
                "documents": data["documents"][:10],
                "connections": list(data["connections"])[:10],
                "connection_count": len(data["connections"])
            })
        
        # Sort by document count
        stakeholders.sort(key=lambda x: x["document_count"], reverse=True)
        
        return {
            "total_stakeholders": len(stakeholders),
            "stakeholders": stakeholders[:50]
        }
        
    except Exception as e:
        logger.error(f"Stakeholder extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/intelligence/timeline")
async def get_timeline():
    """
    Get chronological timeline of events across all documents.
    """
    from app.services import intelligence_service
    
    try:
        docs = document_store.get_all_documents()
        
        all_events = []
        for doc in docs:
            intel = intelligence_service.analyze_document(doc.id, doc.content, doc.filename)
            
            # Add document date as an event
            if intel.date:
                all_events.append({
                    "date": intel.date,
                    "type": "document",
                    "title": intel.title,
                    "document_id": doc.id,
                    "document_type": intel.document_type,
                    "description": f"Document: {intel.title}"
                })
            
            # Add extracted events
            for event in intel.events:
                all_events.append({
                    "date": event.get("date", "Unknown"),
                    "type": "event",
                    "title": intel.title,
                    "document_id": doc.id,
                    "description": event.get("description", "")
                })
        
        return {
            "total_events": len(all_events),
            "events": all_events[:100]
        }
        
    except Exception as e:
        logger.error(f"Timeline extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/intelligence/decisions")
async def get_decisions():
    """
    Get all decisions and key findings across documents.
    """
    from app.services import intelligence_service
    
    try:
        docs = document_store.get_all_documents()
        
        all_decisions = []
        all_findings = []
        
        for doc in docs:
            intel = intelligence_service.analyze_document(doc.id, doc.content, doc.filename)
            
            for decision in intel.decisions:
                all_decisions.append({
                    "text": decision.get("text", ""),
                    "document_id": doc.id,
                    "document_title": intel.title,
                    "date": intel.date
                })
            
            for finding in intel.findings:
                all_findings.append({
                    "text": finding,
                    "document_id": doc.id,
                    "document_title": intel.title,
                    "document_type": intel.document_type
                })
        
        return {
            "total_decisions": len(all_decisions),
            "decisions": all_decisions[:50],
            "total_findings": len(all_findings),
            "findings": all_findings[:50]
        }
        
    except Exception as e:
        logger.error(f"Decision extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== Groq AI Analysis Endpoints ====================

@router.get("/ai/groq/status")
async def get_groq_status():
    """Check if Groq AI service is available."""
    from app.services import groq_service
    
    return {
        "available": groq_service.is_available(),
        "service": "Groq Llama 3.3 70B",
        "features": ["document_analysis", "accountability_trail", "question_answering"] if groq_service.is_available() else []
    }


@router.post("/ai/analyze-document/{doc_id}")
async def analyze_document_with_ai(doc_id: str):
    """
    Perform deep AI analysis on a document using Groq.
    
    Extracts:
    - Research activities (studies, tests)
    - Stakeholders and roles
    - Decisions and approvals
    - Key findings
    - Timeline events
    """
    from app.services import groq_service
    
    if not groq_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq AI service not configured. Add GROQ_API_KEY to .env"
        )
    
    doc = document_store.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        result = groq_service.analyze_document(doc.content, doc.filename)
        return result
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai/analyze-batch")
async def analyze_documents_batch(doc_ids: List[str] = Body(...), max_docs: int = 10):
    """
    Analyze multiple documents and extract structured intelligence.
    """
    from app.services import groq_service
    
    if not groq_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq AI service not configured"
        )
    
    results = []
    for doc_id in doc_ids[:max_docs]:
        doc = document_store.get_document(doc_id)
        if doc:
            try:
                analysis = groq_service.analyze_document(doc.content, doc.filename)
                analysis["doc_id"] = doc_id
                results.append(analysis)
            except Exception as e:
                results.append({"doc_id": doc_id, "error": str(e)})
    
    return {"analyzed": len(results), "results": results}


@router.get("/ai/accountability-trail")
async def get_accountability_trail(limit: int = 20):
    """
    Build an accountability trail across all documents.
    
    Answers: "Who knew what, and when did they know it?"
    
    Returns:
    - Key actors and their involvement
    - Chronological timeline of events
    - Notable patterns identified
    """
    from app.services import groq_service
    
    if not groq_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq AI service not configured"
        )
    
    try:
        # Get all documents
        docs = document_store.get_all_documents()
        
        if not docs:
            return {"error": "No documents available"}
        
        # First, analyze a sample of documents
        analyzed_docs = []
        for doc in docs[:limit]:
            try:
                analysis = groq_service.analyze_document(doc.content, doc.filename)
                if analysis.get("analysis_success"):
                    analyzed_docs.append(analysis)
            except:
                continue
        
        if not analyzed_docs:
            return {"error": "Could not analyze any documents"}
        
        # Build accountability trail
        trail = groq_service.extract_accountability_trail(analyzed_docs)
        trail["documents_analyzed"] = len(analyzed_docs)
        
        return trail
        
    except Exception as e:
        logger.error(f"Accountability trail failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai/chat")
async def chat_with_groq(
    message: str = Body(..., embed=True),
    session_id: str = Body(default="default")
):
    """
    Chat with documents using Groq AI (replaces Gemini chat).
    """
    from app.services import groq_service
    
    if not groq_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq AI service not configured"
        )
    
    try:
        # Get all documents for context
        all_docs = document_store.get_all_documents()
        
        # Search for relevant documents based on message
        message_words = set(message.lower().split())
        scored_docs = []
        for doc in all_docs:
            content_lower = doc.content.lower()
            score = sum(1 for word in message_words if word in content_lower)
            if score > 0:
                scored_docs.append((doc, score))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        docs = [d[0] for d in scored_docs[:5]]
        
        if not docs:
            docs = all_docs[:3]  # Use first 3 docs if no matches
        
        context_docs = [{"filename": d.filename, "content": d.content} for d in docs]
        result = groq_service.answer_question(message, context_docs)
        
        return {
            "answer": result.get("answer", "I couldn't generate a response"),
            "citations": [{"filename": c.get("document", "")} for c in result.get("citations", [])]
        }
        
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai/extract-document")
async def extract_document_info(
    document_id: str = Body(..., embed=True)
):
    """
    Extract structured information from a document using Groq AI.
    """
    from app.services import groq_service
    
    if not groq_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq AI service not configured"
        )
    
    try:
        doc = document_store.get_document(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        result = groq_service.analyze_document(doc.content, doc.filename)
        
        return {
            "document_type": result.get("document_type", "Unknown"),
            "extracted_fields": {
                "title": result.get("title"),
                "date": result.get("date"),
                "organization": result.get("organization"),
            },
            "key_points": result.get("key_facts", []),
            "entities": {
                "people": [s.get("name") for s in result.get("stakeholders", []) if s.get("name")],
                "organizations": [result.get("organization")] if result.get("organization") else [],
                "locations": []
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/ai/ask")
async def ask_question_about_documents(
    question: str = Body(..., embed=True),
    doc_ids: List[str] = Body(default=None)
):
    """
    Ask a question about the documents using AI.
    
    If doc_ids provided, searches only those documents.
    Otherwise, searches all documents for relevant context.
    """
    from app.services import groq_service
    
    if not groq_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Groq AI service not configured"
        )
    
    try:
        # Get relevant documents
        if doc_ids:
            docs = [document_store.get_document(did) for did in doc_ids]
            docs = [d for d in docs if d]
        else:
            # Search for relevant documents
            all_docs = document_store.get_all_documents()
            # Simple relevance: search for question keywords in content
            question_words = set(question.lower().split())
            scored_docs = []
            for doc in all_docs:
                content_lower = doc.content.lower()
                score = sum(1 for word in question_words if word in content_lower)
                if score > 0:
                    scored_docs.append((doc, score))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            docs = [d[0] for d in scored_docs[:5]]
        
        if not docs:
            return {"answer": "No relevant documents found", "citations": []}
        
        # Prepare context
        context_docs = [{"filename": d.filename, "content": d.content} for d in docs]
        
        result = groq_service.answer_question(question, context_docs)
        return result
        
    except Exception as e:
        logger.error(f"Question answering failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
