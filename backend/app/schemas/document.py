from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class EntityItem(BaseModel):
    text: str
    label: str
    score: float = Field(ge=0.0, le=1.0)
    start: Optional[int] = None
    end: Optional[int] = None


class DocumentResponse(BaseModel):
    id: str
    filename: str
    upload_date: datetime
    extracted_text: str
    summary: str
    entities: List[EntityItem]
    processing_time: float
    file_type: str
    text_length: int
    word_count: int = 0
    entity_count: int = 0
    keywords: List[str] = []


class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    data: Optional[DocumentResponse] = None


class AnalysisResult(BaseModel):
    summary: str
    entities: List[EntityItem]


# Knowledge Graph Models
class KGEntity(BaseModel):
    id: str
    canonical_name: str
    entity_type: str
    mention_count: int
    documents: List[str] = []


class KGRelationship(BaseModel):
    source: str
    target: str
    relation_type: str
    confidence: float


class KnowledgeGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]


# Reasoning Models
class EntityQueryResponse(BaseModel):
    success: bool
    entity: Optional[Dict[str, Any]] = None
    documents: List[Dict[str, Any]] = []
    related_entities: List[Dict[str, Any]] = []
    summary: str = ""
    message: str = ""


class ConnectionQueryResponse(BaseModel):
    success: bool
    entity1: Optional[Dict[str, Any]] = None
    entity2: Optional[Dict[str, Any]] = None
    connection_strength: str = ""
    direct_relationships: List[Dict[str, Any]] = []
    shared_documents: List[str] = []
    common_connections: List[str] = []
    summary: str = ""
    message: str = ""


class QuestionRequest(BaseModel):
    question: str


class QuestionResponse(BaseModel):
    success: bool
    query: str
    answer_type: str = ""
    results: Any = None
    message: str = ""


# Corpus Models
class CorpusOverview(BaseModel):
    documents: Dict[str, Any]
    knowledge_graph: Dict[str, Any]
    top_entities: List[Dict[str, Any]]
    top_keywords: List[Dict[str, Any]]


class DocumentInsights(BaseModel):
    success: bool
    document: Dict[str, Any]
    key_entities: List[Dict[str, Any]]
    connected_documents: List[Dict[str, Any]]
    similar_documents: List[Dict[str, Any]]
    keywords: List[str]


class ProcessingStats(BaseModel):
    total_documents: int
    total_entities: int
    total_relationships: int
    entity_types: Dict[str, int]
    file_types: Dict[str, int]
    top_keywords: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
