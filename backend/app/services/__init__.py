from .ocr_service import ocr_service
from .nlp_service import nlp_service
from .knowledge_graph import knowledge_graph
from .document_store import document_store
from .reasoning_engine import create_reasoning_engine
from .llm_service import llm_service
from .intelligence_service import intelligence_service
from .groq_service import groq_service

# Create reasoning engine with dependencies
reasoning_engine = create_reasoning_engine(knowledge_graph, document_store)
