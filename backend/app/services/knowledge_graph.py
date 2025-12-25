"""
Knowledge Graph Service

Builds and manages a knowledge graph from extracted document entities.
Enables cross-document entity linking and relationship discovery.

Research contribution: Automated knowledge graph construction from unstructured documents.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
from datetime import datetime
import hashlib

from app.core import logger


@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""
    id: str
    text: str
    canonical_name: str  # Normalized form
    entity_type: str  # PERSON, ORG, LOCATION, DATE, etc.
    mentions: List[Dict[str, Any]] = field(default_factory=list)  # Where this entity appears
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def add_mention(self, doc_id: str, context: str, confidence: float):
        self.mentions.append({
            "document_id": doc_id,
            "context": context,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat()
        })


@dataclass
class Relationship:
    """Represents a relationship between two entities."""
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str  # WORKS_FOR, LOCATED_IN, MENTIONED_WITH, etc.
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    
    def add_evidence(self, doc_id: str, sentence: str, confidence: float):
        self.evidence.append({
            "document_id": doc_id,
            "sentence": sentence,
            "confidence": confidence
        })
        # Update overall confidence
        self.confidence = sum(e["confidence"] for e in self.evidence) / len(self.evidence)


class KnowledgeGraphService:
    """
    Service for building and querying knowledge graphs from documents.
    
    Features:
    - Entity deduplication and canonicalization
    - Relationship extraction
    - Cross-document entity linking
    - Graph queries and traversal
    """
    
    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._entity_index: Dict[str, Set[str]] = defaultdict(set)  # text -> entity_ids
        self._doc_entities: Dict[str, Set[str]] = defaultdict(set)  # doc_id -> entity_ids
        self._graph_file = Path("data/knowledge_graph.json")
        self._load_graph()
    
    def _generate_id(self, text: str, entity_type: str) -> str:
        """Generate unique ID for entity."""
        content = f"{text.lower()}:{entity_type}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _canonicalize(self, text: str, entity_type: str) -> str:
        """Normalize entity text to canonical form."""
        # Basic canonicalization - can be enhanced with NLP
        canonical = text.strip()
        
        # Remove common prefixes/suffixes
        prefixes = ["Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "The "]
        for prefix in prefixes:
            if canonical.startswith(prefix):
                canonical = canonical[len(prefix):].strip()
        
        # Title case for names
        if entity_type in ["PERSON", "ORG"]:
            canonical = canonical.title()
        
        return canonical
    
    def _load_graph(self):
        """Load knowledge graph from disk."""
        try:
            if self._graph_file.exists():
                with open(self._graph_file, 'r') as f:
                    data = json.load(f)
                    
                for entity_data in data.get("entities", []):
                    entity = Entity(**entity_data)
                    self._entities[entity.id] = entity
                    self._entity_index[entity.text.lower()].add(entity.id)
                    for mention in entity.mentions:
                        self._doc_entities[mention["document_id"]].add(entity.id)
                
                for rel_data in data.get("relationships", []):
                    rel = Relationship(**rel_data)
                    self._relationships[rel.id] = rel
                    
                logger.info(f"Loaded knowledge graph: {len(self._entities)} entities, {len(self._relationships)} relationships")
        except Exception as e:
            logger.error(f"Failed to load knowledge graph: {e}")
    
    def _save_graph(self):
        """Save knowledge graph to disk."""
        try:
            self._graph_file.parent.mkdir(exist_ok=True)
            data = {
                "entities": [asdict(e) for e in self._entities.values()],
                "relationships": [asdict(r) for r in self._relationships.values()],
                "metadata": {
                    "last_updated": datetime.utcnow().isoformat(),
                    "entity_count": len(self._entities),
                    "relationship_count": len(self._relationships)
                }
            }
            with open(self._graph_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save knowledge graph: {e}")
    
    def add_entity(
        self, 
        text: str, 
        entity_type: str, 
        doc_id: str, 
        context: str = "",
        confidence: float = 1.0
    ) -> Entity:
        """
        Add or update an entity in the knowledge graph.
        
        Args:
            text: Entity text
            entity_type: Type (PERSON, ORG, LOC, etc.)
            doc_id: Source document ID
            context: Surrounding text for context
            confidence: Extraction confidence score
            
        Returns:
            The created or updated Entity
        """
        canonical = self._canonicalize(text, entity_type)
        entity_id = self._generate_id(canonical, entity_type)
        
        # Check if entity exists
        if entity_id in self._entities:
            entity = self._entities[entity_id]
            entity.add_mention(doc_id, context, confidence)
        else:
            entity = Entity(
                id=entity_id,
                text=text,
                canonical_name=canonical,
                entity_type=entity_type
            )
            entity.add_mention(doc_id, context, confidence)
            self._entities[entity_id] = entity
            self._entity_index[text.lower()].add(entity_id)
        
        self._doc_entities[doc_id].add(entity_id)
        self._save_graph()
        
        return entity
    
    def add_entities_from_document(
        self, 
        doc_id: str, 
        entities: List[Dict[str, Any]], 
        full_text: str
    ) -> List[Entity]:
        """
        Add multiple entities from a document.
        
        Args:
            doc_id: Document ID
            entities: List of entity dicts with text, label, score
            full_text: Full document text for context extraction
            
        Returns:
            List of created/updated entities
        """
        added_entities = []
        
        for entity_data in entities:
            text = entity_data.get("text", "")
            entity_type = entity_data.get("label", "MISC")
            confidence = entity_data.get("score", 1.0)
            
            # Extract context (surrounding text)
            context = self._extract_context(full_text, text)
            
            entity = self.add_entity(
                text=text,
                entity_type=entity_type,
                doc_id=doc_id,
                context=context,
                confidence=confidence
            )
            added_entities.append(entity)
        
        # Detect co-occurrence relationships
        self._detect_cooccurrence_relationships(doc_id, added_entities)
        
        return added_entities
    
    def _extract_context(self, full_text: str, entity_text: str, window: int = 100) -> str:
        """Extract surrounding context for an entity."""
        pos = full_text.lower().find(entity_text.lower())
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(full_text), pos + len(entity_text) + window)
        
        return full_text[start:end].strip()
    
    def _detect_cooccurrence_relationships(self, doc_id: str, entities: List[Entity]):
        """Detect relationships between entities that appear in the same document."""
        entity_ids = [e.id for e in entities]
        
        # Create CO_OCCURS relationships for entities in same document
        for i, e1_id in enumerate(entity_ids):
            for e2_id in entity_ids[i+1:]:
                if e1_id != e2_id:
                    self.add_relationship(
                        source_id=e1_id,
                        target_id=e2_id,
                        relation_type="CO_OCCURS",
                        doc_id=doc_id,
                        sentence=f"Both mentioned in document {doc_id}",
                        confidence=0.5
                    )
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        doc_id: str,
        sentence: str,
        confidence: float = 1.0
    ) -> Optional[Relationship]:
        """Add or update a relationship between entities."""
        if source_id not in self._entities or target_id not in self._entities:
            return None
        
        # Create relationship ID
        rel_id = f"{source_id}_{relation_type}_{target_id}"
        
        if rel_id in self._relationships:
            rel = self._relationships[rel_id]
            rel.add_evidence(doc_id, sentence, confidence)
        else:
            rel = Relationship(
                id=rel_id,
                source_entity_id=source_id,
                target_entity_id=target_id,
                relation_type=relation_type,
                confidence=confidence
            )
            rel.add_evidence(doc_id, sentence, confidence)
            self._relationships[rel_id] = rel
        
        self._save_graph()
        return rel
    
    def find_entity(self, text: str) -> List[Entity]:
        """Find entities matching the given text."""
        text_lower = text.lower()
        entity_ids = self._entity_index.get(text_lower, set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    def search_entities(self, query: str, limit: int = 10) -> List[Entity]:
        """
        Search for entities matching a query string.
        Performs partial matching on entity names.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching entities
        """
        query_lower = query.lower()
        results = []
        
        for entity in self._entities.values():
            # Check if query matches entity name or canonical name
            if (query_lower in entity.text.lower() or 
                query_lower in entity.canonical_name.lower()):
                results.append(entity)
                if len(results) >= limit:
                    break
        
        # Sort by mention count (most mentioned first)
        results.sort(key=lambda e: len(e.mentions), reverse=True)
        return results[:limit]
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        return self._entities.get(entity_id)
    
    def get_entity_relationships(self, entity_id: str) -> List[Relationship]:
        """Get all relationships for an entity."""
        relationships = []
        for rel in self._relationships.values():
            if rel.source_entity_id == entity_id or rel.target_entity_id == entity_id:
                relationships.append(rel)
        return relationships
    
    def get_document_entities(self, doc_id: str) -> List[Entity]:
        """Get all entities mentioned in a document."""
        entity_ids = self._doc_entities.get(doc_id, set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    def get_connected_documents(self, doc_id: str) -> List[Tuple[str, int, List[str]]]:
        """
        Find documents connected to the given document through shared entities.
        
        Returns:
            List of (doc_id, shared_entity_count, shared_entity_names)
        """
        # Get entities in this document
        doc_entities = self._doc_entities.get(doc_id, set())
        
        # Find other documents that share entities
        connected = defaultdict(set)
        for entity_id in doc_entities:
            entity = self._entities.get(entity_id)
            if entity:
                for mention in entity.mentions:
                    other_doc_id = mention["document_id"]
                    if other_doc_id != doc_id:
                        connected[other_doc_id].add(entity.canonical_name)
        
        # Format results
        results = [
            (other_doc, len(shared), list(shared))
            for other_doc, shared in connected.items()
        ]
        
        # Sort by number of shared entities
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def find_entity_across_documents(self, entity_text: str) -> Dict[str, Any]:
        """
        Find an entity and all its mentions across documents.
        
        Returns:
            Dict with entity info and all document mentions
        """
        entities = self.find_entity(entity_text)
        
        if not entities:
            return {"found": False, "entity": None, "documents": []}
        
        # Take the first matching entity
        entity = entities[0]
        
        return {
            "found": True,
            "entity": {
                "id": entity.id,
                "canonical_name": entity.canonical_name,
                "type": entity.entity_type,
                "mention_count": len(entity.mentions)
            },
            "documents": [
                {
                    "document_id": m["document_id"],
                    "context": m["context"],
                    "confidence": m["confidence"]
                }
                for m in entity.mentions
            ]
        }
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph."""
        entity_types = defaultdict(int)
        relationship_types = defaultdict(int)
        
        for entity in self._entities.values():
            entity_types[entity.entity_type] += 1
        
        for rel in self._relationships.values():
            relationship_types[rel.relation_type] += 1
        
        return {
            "total_entities": len(self._entities),
            "total_relationships": len(self._relationships),
            "total_documents": len(self._doc_entities),
            "entity_types": dict(entity_types),
            "relationship_types": dict(relationship_types),
            "avg_mentions_per_entity": sum(
                len(e.mentions) for e in self._entities.values()
            ) / max(len(self._entities), 1)
        }
    
    def export_for_visualization(self) -> Dict[str, Any]:
        """Export graph in format suitable for visualization (D3.js, Cytoscape)."""
        nodes = []
        edges = []
        
        for entity in self._entities.values():
            nodes.append({
                "id": entity.id,
                "label": entity.canonical_name,
                "type": entity.entity_type,
                "size": len(entity.mentions)
            })
        
        for rel in self._relationships.values():
            edges.append({
                "id": rel.id,
                "source": rel.source_entity_id,
                "target": rel.target_entity_id,
                "type": rel.relation_type,
                "weight": rel.confidence
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def clear_graph(self):
        """Clear the entire knowledge graph."""
        self._entities.clear()
        self._relationships.clear()
        self._entity_index.clear()
        self._doc_entities.clear()
        self._save_graph()
        logger.info("Knowledge graph cleared")


# Singleton instance
knowledge_graph = KnowledgeGraphService()
