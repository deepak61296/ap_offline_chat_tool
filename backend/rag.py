"""
RAG Module for ArduPilot AI Assistant
Retrieves relevant documentation from ChromaDB for Ask mode queries
"""

import chromadb
from typing import List, Dict, Optional


class ArduPilotRAG:
    """RAG system for ArduPilot documentation"""
    
    def __init__(self, db_path: str = "C:/Projects/ardupilot_chat_training/data/vectordb"):
        """Initialize RAG system"""
        self.db_path = db_path
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """Initialize ChromaDB connection"""
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_collection("ardupilot_wiki")
            print(f"[OK] RAG system initialized with {self.collection.count()} documents")
        except Exception as e:
            print(f"[WARNING] RAG system not available: {e}")
            self.collection = None
    
    def search(self, query: str, n_results: int = 3, vehicle_type: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Search documentation for relevant context
        
        Args:
            query: User's question
            n_results: Number of results to return
            vehicle_type: Filter by vehicle type (copter/plane/rover)
        
        Returns:
            List of relevant documentation chunks
        """
        if not self.collection:
            return []
        
        try:
            # Build query filters
            where = None
            if vehicle_type:
                where = {"vehicle_type": vehicle_type}
            
            # Search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Format results
            docs = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                # ChromaDB uses L2 distance, lower is better
                # Convert to relevance score (inverse of distance, normalized)
                relevance = 1.0 / (1.0 + distance)  # Range: 0 to 1, higher is better
                
                # Only include if distance is reasonable (< 2.0 means somewhat relevant)
                if distance < 2.0:
                    docs.append({
                        'text': doc,
                        'title': metadata.get('title', 'Unknown'),
                        'vehicle_type': metadata.get('vehicle_type', 'common'),
                        'source_url': metadata.get('source_url', ''),
                        'relevance': relevance,
                        'distance': distance
                    })
            
            return docs
        
        except Exception as e:
            print(f"RAG search error: {e}")
            return []
    
    def get_context(self, query: str, max_length: int = 1500) -> str:
        """
        Get formatted context for AI prompt
        
        Args:
            query: User's question
            max_length: Maximum context length in characters
        
        Returns:
            Formatted context string
        """
        docs = self.search(query, n_results=3)
        
        if not docs:
            return ""
        
        context_parts = ["RELEVANT DOCUMENTATION:\n"]
        current_length = len(context_parts[0])
        
        for i, doc in enumerate(docs, 1):
            # Get source URL if available
            source_url = doc.get('source_url', '')
            source_info = f" - {source_url}" if source_url else ""
            
            # Format document with URL
            doc_text = f"\n[Source {i}: {doc['title']}{source_info}]\n{doc['text']}\n"
            
            # Check if adding this would exceed limit
            if current_length + len(doc_text) > max_length:
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "".join(context_parts)


# Global RAG instance
_rag_instance = None


def get_rag() -> ArduPilotRAG:
    """Get or create RAG instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = ArduPilotRAG()
    return _rag_instance
