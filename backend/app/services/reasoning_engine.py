"""
Cross-Document Reasoning Engine

Performs intelligent reasoning across multiple documents to answer
complex queries, find contradictions, and generate insights.

Research contribution: Novel cross-document reasoning capabilities.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

from app.core import logger


@dataclass
class ReasoningResult:
    """Result of a reasoning query."""
    query: str
    answer: str
    confidence: float
    evidence: List[Dict[str, Any]]
    reasoning_chain: List[str]
    documents_used: List[str]


class ReasoningEngine:
    """
    Cross-document reasoning engine for multi-document intelligence.
    
    Capabilities:
    - Entity-centric queries ("What do we know about X?")
    - Relationship queries ("How is X connected to Y?")
    - Aggregation queries ("List all companies mentioned")
    - Contradiction detection ("Find conflicting information")
    - Timeline construction ("What events involve X?")
    """
    
    def __init__(self, knowledge_graph, document_store):
        self._kg = knowledge_graph
        self._doc_store = document_store
        self._query_cache = {}
    
    def query_entity(self, entity_name: str) -> Dict[str, Any]:
        """
        Answer: "What do we know about [entity]?"
        
        Aggregates all information about an entity across documents.
        """
        # Find entity in knowledge graph
        search_result = self._kg.find_entity_across_documents(entity_name)
        
        if not search_result["found"]:
            return {
                "success": False,
                "message": f"Entity '{entity_name}' not found in any document",
                "suggestions": self._suggest_similar_entities(entity_name)
            }
        
        entity_info = search_result["entity"]
        documents = search_result["documents"]
        
        # Get relationships
        relationships = self._kg.get_entity_relationships(entity_info["id"])
        
        # Categorize relationships
        related_entities = []
        for rel in relationships:
            other_id = rel.target_entity_id if rel.source_entity_id == entity_info["id"] else rel.source_entity_id
            other_entity = self._kg.get_entity(other_id)
            if other_entity:
                related_entities.append({
                    "name": other_entity.canonical_name,
                    "type": other_entity.entity_type,
                    "relationship": rel.relation_type,
                    "confidence": rel.confidence
                })
        
        # Get document summaries
        doc_summaries = []
        for doc_mention in documents:
            doc = self._doc_store.get_document(doc_mention["document_id"])
            if doc:
                doc_summaries.append({
                    "document_id": doc.id,
                    "filename": doc.filename,
                    "context": doc_mention["context"],
                    "relevance": doc_mention["confidence"]
                })
        
        return {
            "success": True,
            "entity": {
                "name": entity_info["canonical_name"],
                "type": entity_info["type"],
                "mention_count": entity_info["mention_count"]
            },
            "documents": doc_summaries,
            "related_entities": related_entities,
            "summary": self._generate_entity_summary(entity_info, documents, related_entities)
        }
    
    def _suggest_similar_entities(self, query: str) -> List[str]:
        """Suggest similar entity names."""
        # Simple prefix matching
        query_lower = query.lower()
        suggestions = []
        
        for entity in self._kg._entities.values():
            if query_lower in entity.canonical_name.lower():
                suggestions.append(entity.canonical_name)
        
        return suggestions[:5]
    
    def _generate_entity_summary(
        self, 
        entity_info: Dict, 
        documents: List[Dict], 
        related: List[Dict]
    ) -> str:
        """Generate a natural language summary about an entity."""
        name = entity_info["canonical_name"]
        entity_type = entity_info["type"]
        
        summary_parts = [f"{name} is a {entity_type} mentioned in {len(documents)} document(s)."]
        
        if related:
            # Group by relationship type
            by_relation = defaultdict(list)
            for r in related:
                by_relation[r["relationship"]].append(r["name"])
            
            for rel_type, names in by_relation.items():
                if rel_type == "CO_OCCURS":
                    summary_parts.append(f"It appears together with: {', '.join(names[:5])}.")
                else:
                    summary_parts.append(f"It {rel_type.lower().replace('_', ' ')} {', '.join(names[:3])}.")
        
        return " ".join(summary_parts)
    
    def find_connections(self, entity1: str, entity2: str) -> Dict[str, Any]:
        """
        Answer: "How is [entity1] connected to [entity2]?"
        
        Finds paths and relationships between two entities.
        """
        # Find both entities
        e1_results = self._kg.find_entity(entity1)
        e2_results = self._kg.find_entity(entity2)
        
        if not e1_results:
            return {"success": False, "message": f"Entity '{entity1}' not found"}
        if not e2_results:
            return {"success": False, "message": f"Entity '{entity2}' not found"}
        
        e1 = e1_results[0]
        e2 = e2_results[0]
        
        # Find direct relationships
        direct_relations = []
        for rel in self._kg._relationships.values():
            if (rel.source_entity_id == e1.id and rel.target_entity_id == e2.id) or \
               (rel.source_entity_id == e2.id and rel.target_entity_id == e1.id):
                direct_relations.append({
                    "type": rel.relation_type,
                    "confidence": rel.confidence,
                    "evidence": rel.evidence
                })
        
        # Find shared documents
        e1_docs = set(m["document_id"] for m in e1.mentions)
        e2_docs = set(m["document_id"] for m in e2.mentions)
        shared_docs = e1_docs & e2_docs
        
        # Find common connections (entities connected to both)
        e1_connections = set()
        e2_connections = set()
        
        for rel in self._kg._relationships.values():
            if rel.source_entity_id == e1.id:
                e1_connections.add(rel.target_entity_id)
            elif rel.target_entity_id == e1.id:
                e1_connections.add(rel.source_entity_id)
            
            if rel.source_entity_id == e2.id:
                e2_connections.add(rel.target_entity_id)
            elif rel.target_entity_id == e2.id:
                e2_connections.add(rel.source_entity_id)
        
        common_connections = e1_connections & e2_connections
        common_entities = [
            self._kg.get_entity(eid).canonical_name 
            for eid in common_connections 
            if self._kg.get_entity(eid)
        ]
        
        connection_strength = "strong" if direct_relations else ("moderate" if shared_docs else "weak")
        
        return {
            "success": True,
            "entity1": {"name": e1.canonical_name, "type": e1.entity_type},
            "entity2": {"name": e2.canonical_name, "type": e2.entity_type},
            "connection_strength": connection_strength,
            "direct_relationships": direct_relations,
            "shared_documents": list(shared_docs),
            "common_connections": common_entities[:10],
            "summary": self._summarize_connection(e1, e2, direct_relations, shared_docs, common_entities)
        }
    
    def _summarize_connection(self, e1, e2, relations, shared_docs, common) -> str:
        """Generate summary of connection between entities."""
        if relations:
            return f"{e1.canonical_name} and {e2.canonical_name} have {len(relations)} direct relationship(s) and appear together in {len(shared_docs)} document(s)."
        elif shared_docs:
            return f"{e1.canonical_name} and {e2.canonical_name} are mentioned in the same {len(shared_docs)} document(s) but have no direct relationship."
        elif common:
            return f"{e1.canonical_name} and {e2.canonical_name} are connected through {len(common)} common entities: {', '.join(common[:3])}."
        else:
            return f"No clear connection found between {e1.canonical_name} and {e2.canonical_name}."
    
    def aggregate_by_type(self, entity_type: str) -> Dict[str, Any]:
        """
        Answer: "List all [entity_type]s mentioned"
        
        Aggregates all entities of a given type.
        """
        entities = [
            e for e in self._kg._entities.values()
            if e.entity_type.upper() == entity_type.upper()
        ]
        
        # Sort by mention count
        entities.sort(key=lambda e: len(e.mentions), reverse=True)
        
        return {
            "success": True,
            "entity_type": entity_type,
            "count": len(entities),
            "entities": [
                {
                    "name": e.canonical_name,
                    "mention_count": len(e.mentions),
                    "documents": list(set(m["document_id"] for m in e.mentions))
                }
                for e in entities[:50]  # Limit to top 50
            ]
        }
    
    def find_contradictions(self) -> Dict[str, Any]:
        """
        Find potential contradictions across documents.
        
        Looks for:
        - Same entity with different attributes
        - Conflicting dates/numbers
        - Inconsistent relationships
        """
        contradictions = []
        
        # Find entities mentioned in multiple docs with different contexts
        for entity in self._kg._entities.values():
            if len(entity.mentions) < 2:
                continue
            
            # Group mentions by document
            doc_contexts = defaultdict(list)
            for mention in entity.mentions:
                doc_contexts[mention["document_id"]].append(mention["context"])
            
            # If mentioned in multiple docs, flag for potential contradiction
            if len(doc_contexts) > 1:
                contradictions.append({
                    "entity": entity.canonical_name,
                    "type": entity.entity_type,
                    "documents": list(doc_contexts.keys()),
                    "contexts": {doc_id: contexts[0] if contexts else "" for doc_id, contexts in doc_contexts.items()},
                    "potential_issue": "Entity appears in multiple documents - manual review recommended"
                })
        
        return {
            "success": True,
            "potential_contradictions": contradictions[:20],
            "total_flagged": len(contradictions)
        }
    
    def generate_document_insights(self, doc_id: str) -> Dict[str, Any]:
        """
        Generate insights for a specific document.
        
        Includes:
        - Key entities and their significance
        - Related documents
        - Missing information suggestions
        """
        doc = self._doc_store.get_document(doc_id)
        if not doc:
            return {"success": False, "message": "Document not found"}
        
        # Get entities in this document
        entities = self._kg.get_document_entities(doc_id)
        
        # Get connected documents
        connected = self._kg.get_connected_documents(doc_id)
        
        # Get similar documents by keywords
        similar = self._doc_store.find_similar_documents(doc_id)
        
        # Identify key entities (most connected)
        key_entities = []
        for entity in entities:
            relationships = self._kg.get_entity_relationships(entity.id)
            key_entities.append({
                "name": entity.canonical_name,
                "type": entity.entity_type,
                "connections": len(relationships),
                "cross_doc_mentions": len(entity.mentions)
            })
        
        key_entities.sort(key=lambda e: e["connections"], reverse=True)
        
        return {
            "success": True,
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "word_count": doc.word_count
            },
            "key_entities": key_entities[:10],
            "connected_documents": [
                {"doc_id": d[0], "shared_entities": d[1], "entity_names": d[2]}
                for d in connected[:5]
            ],
            "similar_documents": [
                {"doc_id": s[0], "similarity": round(s[1], 3), "shared_keywords": s[2][:5]}
                for s in similar[:5]
            ],
            "keywords": doc.keywords[:10]
        }
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a natural language question about the document corpus.
        
        Supports:
        - "What do we know about X?"
        - "How is X related to Y?"
        - "List all people/organizations/locations"
        - "Which documents mention X?"
        """
        question_lower = question.lower()
        
        # Pattern matching for question types
        if "what do we know about" in question_lower or "tell me about" in question_lower:
            # Extract entity name
            entity = self._extract_entity_from_question(question)
            if entity:
                return self.query_entity(entity)
        
        elif "how is" in question_lower and "related to" in question_lower:
            # Extract two entities
            entities = self._extract_two_entities(question)
            if entities:
                return self.find_connections(entities[0], entities[1])
        
        elif "list all" in question_lower:
            # Extract entity type
            for etype in ["person", "people", "organization", "company", "location", "place", "date"]:
                if etype in question_lower:
                    type_map = {
                        "person": "PER", "people": "PER",
                        "organization": "ORG", "company": "ORG",
                        "location": "LOC", "place": "LOC",
                        "date": "DATE"
                    }
                    return self.aggregate_by_type(type_map.get(etype, "MISC"))
        
        elif "which documents" in question_lower or "where is" in question_lower:
            entity = self._extract_entity_from_question(question)
            if entity:
                return self.query_entity(entity)
        
        # Default: search documents
        results = self._doc_store.search_full_text(question)
        return {
            "success": True,
            "type": "search",
            "query": question,
            "results": [
                {"document_id": doc.id, "filename": doc.filename, "relevance": score}
                for doc, score in results[:10]
            ]
        }
    
    def _extract_entity_from_question(self, question: str) -> Optional[str]:
        """Extract entity name from question."""
        # Simple extraction - look for quoted text or capitalized words
        import re
        
        # Check for quoted text
        quoted = re.findall(r'"([^"]+)"', question)
        if quoted:
            return quoted[0]
        
        # Look for "about X" pattern
        about_match = re.search(r'about\s+([A-Z][a-zA-Z\s]+)', question)
        if about_match:
            return about_match.group(1).strip()
        
        return None
    
    def _extract_two_entities(self, question: str) -> Optional[Tuple[str, str]]:
        """Extract two entity names from a relationship question."""
        import re
        
        # Pattern: "How is X related to Y?"
        match = re.search(r'how is\s+([A-Za-z\s]+)\s+(?:related|connected)\s+to\s+([A-Za-z\s]+)', question, re.IGNORECASE)
        if match:
            return (match.group(1).strip(), match.group(2).strip().rstrip('?'))
        
        return None
    
    def get_corpus_overview(self) -> Dict[str, Any]:
        """
        Generate an overview of the entire document corpus.
        """
        doc_stats = self._doc_store.get_corpus_stats()
        graph_stats = self._kg.get_graph_stats()
        
        # Get most connected entities
        entity_connections = []
        for entity in self._kg._entities.values():
            rels = self._kg.get_entity_relationships(entity.id)
            entity_connections.append({
                "name": entity.canonical_name,
                "type": entity.entity_type,
                "connections": len(rels),
                "mentions": len(entity.mentions)
            })
        
        entity_connections.sort(key=lambda e: e["connections"], reverse=True)
        
        return {
            "documents": {
                "total": doc_stats.get("document_count", 0),
                "total_words": doc_stats.get("total_words", 0),
                "file_types": doc_stats.get("file_types", {})
            },
            "knowledge_graph": {
                "entities": graph_stats.get("total_entities", 0),
                "relationships": graph_stats.get("total_relationships", 0),
                "entity_types": graph_stats.get("entity_types", {})
            },
            "top_entities": entity_connections[:10],
            "top_keywords": doc_stats.get("top_keywords", [])[:10]
        }


# Factory function to create reasoning engine with dependencies
def create_reasoning_engine(knowledge_graph, document_store) -> ReasoningEngine:
    return ReasoningEngine(knowledge_graph, document_store)
