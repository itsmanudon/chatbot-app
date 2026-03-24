#!/usr/bin/env python3
"""
Simple API test without requiring external services
Tests the application structure and basic functionality
"""

import os
import sys

# Set mock environment variables for testing
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'
os.environ['DEFAULT_AI_PROVIDER'] = 'openai'

def test_schemas():
    """Test schema definitions"""
    print("📋 Testing schemas...")
    try:
        from schemas import ChatRequest, ChatResponse, MemorySuggestion, SessionSummary, ChatHistoryMessage
        from datetime import datetime
        
        # Test ChatRequest
        request = ChatRequest(
            message="Hello, world!",
            session_id="test-session-123"
        )
        assert request.message == "Hello, world!"
        print("  ✓ ChatRequest schema works")
        
        # Test MemorySuggestion
        suggestion = MemorySuggestion(
            type="preference",
            content="Test preference",
            confidence=0.8,
            context="Test context"
        )
        assert suggestion.type == "preference"
        print("  ✓ MemorySuggestion schema works")
        
        # Test ChatResponse
        response = ChatResponse(
            reply="Hello!",
            memory_suggestions=[suggestion]
        )
        assert response.reply == "Hello!"
        assert len(response.memory_suggestions) == 1
        print("  ✓ ChatResponse schema works")

        # Test SessionSummary
        now = datetime.utcnow()
        summary = SessionSummary(
            session_id="abc-123",
            title="Hello, world!",
            preview="I can help you.",
            message_count=5,
            last_message_at=now,
        )
        assert summary.message_count == 5
        print("  ✓ SessionSummary schema works")

        # Test ChatHistoryMessage
        hist_msg = ChatHistoryMessage(
            id="msg-1",
            role="user",
            content="Hello",
            timestamp=now,
        )
        assert hist_msg.role == "user"
        print("  ✓ ChatHistoryMessage schema works")
        
        return True
    except Exception as e:
        print(f"  ✗ Schema test failed: {e}")
        return False

def test_database_models():
    """Test database model definitions"""
    print("\n🗄️ Testing database models...")
    try:
        from database import Base, ChatMessage, MemoryContext
        
        # Check that models have required fields
        assert hasattr(ChatMessage, '__tablename__')
        assert ChatMessage.__tablename__ == 'chat_messages'
        print("  ✓ ChatMessage model defined")
        
        assert hasattr(MemoryContext, '__tablename__')
        assert MemoryContext.__tablename__ == 'memory_contexts'
        print("  ✓ MemoryContext model defined")
        
        return True
    except Exception as e:
        print(f"  ✗ Database model test failed: {e}")
        return False

def test_llm_adapter_structure():
    """Test LLM adapter structure"""
    print("\n🤖 Testing LLM adapter...")
    try:
        from llm_adapter import LLMAdapter, OpenAIProvider, AnthropicProvider
        
        # Test that adapter can be instantiated
        adapter = LLMAdapter()
        assert hasattr(adapter, 'providers')
        assert hasattr(adapter, 'get_response')
        print("  ✓ LLMAdapter instantiated")
        
        # Check providers exist
        assert 'openai' in adapter.providers
        assert 'anthropic' in adapter.providers
        print("  ✓ Providers registered")
        
        return True
    except Exception as e:
        print(f"  ✗ LLM adapter test failed: {e}")
        return False

def test_vector_store_structure():
    """Test vector store structure"""
    print("\n🔍 Testing vector store...")
    try:
        from vector_store import VectorStore
        
        # Test that vector store can be instantiated without API key
        store = VectorStore()
        assert hasattr(store, 'generate_embedding')
        assert hasattr(store, 'store_embedding')
        assert hasattr(store, 'search_similar')
        print("  ✓ VectorStore instantiated")
        
        # Should not be available without API key
        assert not store.is_available()
        print("  ✓ VectorStore correctly reports unavailable without API key")
        
        return True
    except Exception as e:
        print(f"  ✗ Vector store test failed: {e}")
        return False

def test_memory_engine_structure():
    """Test memory engine structure"""
    print("\n🧠 Testing memory engine...")
    try:
        from memory_engine import MemoryEngine
        
        # Test that memory engine can be instantiated
        engine = MemoryEngine()
        assert hasattr(engine, 'store_chat_message')
        assert hasattr(engine, 'store_memory_context')
        assert hasattr(engine, 'retrieve_relevant_context')
        assert hasattr(engine, 'get_full_session_history')
        assert hasattr(engine, 'get_all_sessions')
        assert hasattr(engine, 'delete_session')
        print("  ✓ MemoryEngine instantiated")
        
        return True
    except Exception as e:
        print(f"  ✗ Memory engine test failed: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app structure"""
    print("\n🚀 Testing FastAPI app...")
    try:
        from main import app
        
        # Check app exists and has routes
        assert app is not None
        print("  ✓ FastAPI app created")
        
        # Check routes exist
        routes = [route.path for route in app.routes]
        assert "/" in routes
        assert "/health" in routes
        assert "/chat" in routes
        assert "/sessions" in routes
        assert "/session/{session_id}/history" in routes
        assert "/session/{session_id}" in routes
        print("  ✓ Required routes defined")
        
        return True
    except Exception as e:
        print(f"  ✗ FastAPI app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Running Integration Tests")
    print("=" * 60)
    
    tests = [
        test_schemas,
        test_database_models,
        test_llm_adapter_structure,
        test_vector_store_structure,
        test_memory_engine_structure,
        test_fastapi_app
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if all(results):
        print(f"✅ ALL TESTS PASSED! ({passed}/{total})")
        print("=" * 60)
        return 0
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total} passed)")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
