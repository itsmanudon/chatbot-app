#!/usr/bin/env python3
"""
Example script demonstrating the chatbot API usage
"""

import requests
import json
import uuid
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class ChatbotClient:
    """Simple client for the chatbot API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id = str(uuid.uuid4())
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the API is healthy"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message and get AI response"""
        response = requests.post(
            f"{self.base_url}/chat",
            json={
                "message": message,
                "session_id": self.session_id
            }
        )
        return response.json()
    
    def get_history(self) -> Dict[str, Any]:
        """Get chat history for current session"""
        response = requests.get(
            f"{self.base_url}/session/{self.session_id}/history"
        )
        return response.json()
    
    def store_memory(self, content: str, memory_type: str, confidence: float = 0.8) -> Dict[str, Any]:
        """Manually store a memory"""
        response = requests.post(
            f"{self.base_url}/memory",
            params={
                "session_id": self.session_id,
                "content": content,
                "memory_type": memory_type,
                "confidence": confidence
            }
        )
        return response.json()


def main():
    """Demonstrate chatbot functionality"""
    print("=" * 60)
    print("🤖 Chatbot API Example")
    print("=" * 60)
    
    client = ChatbotClient()
    
    # Check health
    print("\n1. Checking API health...")
    health = client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Vector Store: {'✅' if health['services']['vector_store'] else '❌'}")
    print(f"   LLM: {'✅' if health['services']['llm'] else '❌'}")
    
    if not health['services']['llm']:
        print("\n⚠️  Warning: LLM not configured. Add API keys to .env file")
        print("   The example will continue but responses will be error messages.")
        input("\nPress Enter to continue...")
    
    # Example conversation
    print(f"\n2. Starting conversation (Session: {client.session_id[:8]}...)")
    
    messages = [
        "Hello! I'm learning Python programming.",
        "What's the best way to learn FastAPI?",
        "I prefer hands-on projects over tutorials.",
        "Can you suggest a project idea?"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n   Message {i}: {message}")
        response = client.send_message(message)
        
        print(f"   AI Reply: {response['reply'][:100]}...")
        
        if response['memory_suggestions']:
            print(f"   Memory Suggestions: {len(response['memory_suggestions'])}")
            for suggestion in response['memory_suggestions']:
                print(f"      - {suggestion['type']}: {suggestion['content'][:50]}...")
    
    # Get history
    print("\n3. Retrieving conversation history...")
    history = client.get_history()
    print(f"   Total messages: {len(history.get('history', []))}")
    
    # Store a memory
    print("\n4. Storing a custom memory...")
    memory_result = client.store_memory(
        content="User prefers Python and FastAPI for backend development",
        memory_type="preference",
        confidence=0.9
    )
    print(f"   Stored: {memory_result['status']}")
    print(f"   Memory ID: {memory_result['memory_id']}")
    
    # Test context awareness
    print("\n5. Testing context awareness...")
    context_message = "Based on what we discussed, what should I focus on?"
    print(f"   Question: {context_message}")
    
    response = client.send_message(context_message)
    print(f"   AI Reply: {response['reply'][:150]}...")
    
    print("\n" + "=" * 60)
    print("✅ Example completed!")
    print("=" * 60)
    print(f"\nSession ID: {client.session_id}")
    print("You can view this session in the database or via the API")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Make sure the backend is running:")
        print("   docker-compose up")
        print("   or")
        print("   cd backend && ./start.sh")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
