"""
Document Store Service

Enhanced document storage with vector embeddings for semantic search
and cross-document retrieval.

Research contribution: Efficient multi-document indexing and retrieval.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib
import re

from app.core import logger


@dataclass
class Document:
    """Represents a stored document with metadata and embeddings."""
    id: str
    filename: str
    content: str
    summary: str
    upload_date: str
    file_type: str
    word_count: int
    entity_ids: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentStoreService:
    """
    Enhanced document storage service for multi-document intelligence.
    
    Features:
    - Full-text search
    - Keyword extraction
    - Document chunking for retrieval
    - Cross-document queries
    """
    
    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._keyword_index: Dict[str, set] = {}  # keyword -> doc_ids
        self._store_file = Path("data/document_store.json")
        self._load_store()
    
    def _load_store(self):
        """Load document store from disk."""
        try:
            if self._store_file.exists():
                with open(self._store_file, 'r') as f:
                    data = json.load(f)
                
                for doc_data in data.get("documents", []):
                    doc = Document(**doc_data)
                    self._documents[doc.id] = doc
                    
                    # Rebuild keyword index
                    for keyword in doc.keywords:
                        if keyword not in self._keyword_index:
                            self._keyword_index[keyword] = set()
                        self._keyword_index[keyword].add(doc.id)
                
                logger.info(f"Loaded document store: {len(self._documents)} documents")
        except Exception as e:
            logger.error(f"Failed to load document store: {e}")
    
    def _save_store(self):
        """Save document store to disk."""
        try:
            self._store_file.parent.mkdir(exist_ok=True)
            data = {
                "documents": [asdict(d) for d in self._documents.values()],
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "document_count": len(self._documents)
                }
            }
            with open(self._store_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save document store: {e}")
    
    def _extract_keywords(self, text: str, top_n: int = 20) -> List[str]:
        """Extract keywords from text using TF-based approach."""
        # Simple keyword extraction (can be enhanced with TF-IDF or KeyBERT)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Filter stopwords
        stopwords = {
            'the', 'and', 'for', 'that', 'this', 'with', 'are', 'was', 'were',
            'been', 'have', 'has', 'had', 'from', 'they', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'could', 'into', 'which', 'their',
            'there', 'here', 'where', 'when', 'what', 'who', 'how', 'all', 'each',
            'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'than',
            'too', 'very', 'just', 'also', 'now', 'only', 'even', 'back', 'after',
            'before', 'over', 'under', 'again', 'further', 'then', 'once', 'about'
        }
        
        filtered_words = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]
    
    def _chunk_document(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
        """Split document into overlapping chunks for retrieval."""
        chunks = []
        words = text.split()
        
        start = 0
        chunk_idx = 0
        
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk_text = ' '.join(words[start:end])
            
            chunks.append({
                "index": chunk_idx,
                "text": chunk_text,
                "start_word": start,
                "end_word": end
            })
            
            chunk_idx += 1
            start += chunk_size - overlap
        
        return chunks
    
    def add_document(
        self,
        doc_id: str,
        filename: str,
        content: str,
        summary: str,
        file_type: str,
        entity_ids: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Document:
        """
        Add a document to the store.
        
        Args:
            doc_id: Unique document ID
            filename: Original filename
            content: Full text content
            summary: Document summary
            file_type: File type (PDF, JPG, etc.)
            entity_ids: List of entity IDs found in document
            metadata: Additional metadata
            
        Returns:
            The created Document
        """
        # Extract keywords
        keywords = self._extract_keywords(content)
        
        # Create chunks
        chunks = self._chunk_document(content)
        
        doc = Document(
            id=doc_id,
            filename=filename,
            content=content,
            summary=summary,
            upload_date=datetime.utcnow().isoformat(),
            file_type=file_type,
            word_count=len(content.split()),
            entity_ids=entity_ids or [],
            keywords=keywords,
            chunks=chunks,
            metadata=metadata or {}
        )
        
        self._documents[doc_id] = doc
        
        # Update keyword index
        for keyword in keywords:
            if keyword not in self._keyword_index:
                self._keyword_index[keyword] = set()
            self._keyword_index[keyword].add(doc_id)
        
        self._save_store()
        logger.info(f"Added document {doc_id}: {filename}")
        
        return doc
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self._documents.get(doc_id)
    
    def get_all_documents(self) -> List[Document]:
        """Get all documents."""
        return list(self._documents.values())
    
    def search_by_keyword(self, keyword: str) -> List[Document]:
        """Search documents by keyword."""
        keyword_lower = keyword.lower()
        doc_ids = self._keyword_index.get(keyword_lower, set())
        return [self._documents[did] for did in doc_ids if did in self._documents]
    
    def search_full_text(self, query: str, max_results: int = 10) -> List[Tuple[Document, float]]:
        """
        Full-text search across all documents.
        
        Returns:
            List of (Document, relevance_score) tuples
        """
        query_words = set(query.lower().split())
        results = []
        
        for doc in self._documents.values():
            # Calculate simple relevance score
            content_lower = doc.content.lower()
            
            # Count query word matches
            matches = sum(1 for word in query_words if word in content_lower)
            
            # Boost for keyword matches
            keyword_matches = sum(1 for word in query_words if word in doc.keywords)
            
            score = matches + (keyword_matches * 2)
            
            if score > 0:
                results.append((doc, score))
        
        # Sort by score
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:max_results]
    
    def find_similar_documents(self, doc_id: str, top_n: int = 5) -> List[Tuple[str, float, List[str]]]:
        """
        Find documents similar to the given document based on shared keywords.
        
        Returns:
            List of (doc_id, similarity_score, shared_keywords)
        """
        doc = self._documents.get(doc_id)
        if not doc:
            return []
        
        doc_keywords = set(doc.keywords)
        similarities = []
        
        for other_id, other_doc in self._documents.items():
            if other_id == doc_id:
                continue
            
            other_keywords = set(other_doc.keywords)
            shared = doc_keywords & other_keywords
            
            if shared:
                # Jaccard similarity
                similarity = len(shared) / len(doc_keywords | other_keywords)
                similarities.append((other_id, similarity, list(shared)))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_n]
    
    def get_document_timeline(self) -> List[Dict[str, Any]]:
        """Get documents ordered by upload date."""
        docs = sorted(
            self._documents.values(),
            key=lambda d: d.upload_date,
            reverse=True
        )
        return [
            {
                "id": d.id,
                "filename": d.filename,
                "upload_date": d.upload_date,
                "word_count": d.word_count,
                "entity_count": len(d.entity_ids)
            }
            for d in docs
        ]
    
    def get_corpus_stats(self) -> Dict[str, Any]:
        """Get statistics about the document corpus."""
        if not self._documents:
            return {"document_count": 0}
        
        total_words = sum(d.word_count for d in self._documents.values())
        total_entities = sum(len(d.entity_ids) for d in self._documents.values())
        
        # Get top keywords across corpus
        all_keywords = []
        for doc in self._documents.values():
            all_keywords.extend(doc.keywords)
        
        keyword_freq = {}
        for kw in all_keywords:
            keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
        
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            "document_count": len(self._documents),
            "total_words": total_words,
            "total_entities": total_entities,
            "avg_words_per_doc": total_words / len(self._documents),
            "avg_entities_per_doc": total_entities / len(self._documents),
            "top_keywords": [{"keyword": kw, "count": c} for kw, c in top_keywords],
            "file_types": self._get_file_type_distribution()
        }
    
    def _get_file_type_distribution(self) -> Dict[str, int]:
        """Get distribution of file types."""
        distribution = {}
        for doc in self._documents.values():
            ft = doc.file_type
            distribution[ft] = distribution.get(ft, 0) + 1
        return distribution
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store."""
        if doc_id not in self._documents:
            return False
        
        doc = self._documents[doc_id]
        
        # Remove from keyword index
        for keyword in doc.keywords:
            if keyword in self._keyword_index:
                self._keyword_index[keyword].discard(doc_id)
        
        del self._documents[doc_id]
        self._save_store()
        
        logger.info(f"Deleted document {doc_id}")
        return True
    
    def clear_store(self):
        """Clear all documents."""
        self._documents.clear()
        self._keyword_index.clear()
        self._save_store()
        logger.info("Document store cleared")


# Singleton instance
document_store = DocumentStoreService()
