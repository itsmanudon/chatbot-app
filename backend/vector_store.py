import os
from typing import List, Dict, Any
import uuid

class VectorStore:
    """Pinecone vector database integration for embeddings"""
    
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        self.index_name = os.getenv("PINECONE_INDEX_NAME", "chatbot-memory")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        
        self.pc = None
        self.index = None
        self.embedding_model = None
        
        if self.api_key:
            self._initialize()
    
    def _initialize(self):
        """Initialize Pinecone and embedding model"""
        try:
            from pinecone import Pinecone, ServerlessSpec
            from sentence_transformers import SentenceTransformer
            
            self.pc = Pinecone(api_key=self.api_key)
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            # Create index if it doesn't exist
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # Dimension for all-MiniLM-L6-v2
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region=self.environment)
                )
            
            self.index = self.pc.Index(self.index_name)
        except Exception as e:
            print(f"Warning: Could not initialize Pinecone: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.embedding_model:
            return []
        return self.embedding_model.encode(text).tolist()
    
    def store_embedding(self, text: str, metadata: Dict[str, Any]) -> str:
        """Store text embedding in Pinecone"""
        if not self.index:
            return ""
        
        vector_id = str(uuid.uuid4())
        embedding = self.generate_embedding(text)
        
        if embedding:
            self.index.upsert(vectors=[(vector_id, embedding, metadata)])
        
        return vector_id
    
    def search_similar(self, query: str, top_k: int = 5, filter: Dict = None) -> List[Dict]:
        """Search for similar embeddings"""
        if not self.index:
            return []
        
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            }
            for match in results.matches
        ]
    
    def is_available(self) -> bool:
        """Check if vector store is available"""
        return self.index is not None

# Global instance
vector_store = VectorStore()
