#!/bin/bash
# Quick start script for the chatbot backend

echo "=================================================="
echo "🚀 Chatbot Backend Quick Start"
echo "=================================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file"
        echo ""
        echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
        echo "   - PINECONE_API_KEY (optional)"
        echo "   - OPENAI_API_KEY or ANTHROPIC_API_KEY"
        echo ""
        echo "Press Enter to continue or Ctrl+C to exit and configure .env first"
        read
    else
        echo "❌ .env.example not found!"
        exit 1
    fi
fi

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Dependencies installed"
echo ""
echo "🗄️  Starting backend server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
