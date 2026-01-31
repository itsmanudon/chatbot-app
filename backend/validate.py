#!/usr/bin/env python3
"""
Validation script to test the chatbot backend structure
"""

import os
import sys

def test_file_structure():
    """Test that all required files exist"""
    required_files = [
        'main.py',
        'database.py',
        'llm_adapter.py',
        'memory_engine.py',
        'vector_store.py',
        'schemas.py',
        'requirements.txt',
        '.env.example',
        'Dockerfile'
    ]
    
    print("📁 Checking file structure...")
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (missing)")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("\n✅ All required files present")
    return True

def test_syntax():
    """Test Python syntax of all files"""
    import ast
    
    python_files = [
        'main.py',
        'database.py', 
        'llm_adapter.py',
        'memory_engine.py',
        'vector_store.py',
        'schemas.py'
    ]
    
    print("\n🔍 Checking Python syntax...")
    errors = []
    
    for file in python_files:
        try:
            with open(file, 'r') as f:
                ast.parse(f.read())
            print(f"  ✓ {file}")
        except SyntaxError as e:
            print(f"  ✗ {file}: {e}")
            errors.append(file)
    
    if errors:
        print(f"\n❌ Syntax errors in: {', '.join(errors)}")
        return False
    
    print("\n✅ All Python files have valid syntax")
    return True

def test_requirements():
    """Check requirements.txt has necessary packages"""
    print("\n📦 Checking requirements.txt...")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'psycopg2-binary',
        'sqlalchemy',
        'pinecone-client',
        'openai',
        'anthropic',
        'sentence-transformers'
    ]
    
    with open('requirements.txt', 'r') as f:
        content = f.read().lower()
    
    missing = []
    for package in required_packages:
        if package.lower() in content:
            print(f"  ✓ {package}")
        else:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        return False
    
    print("\n✅ All required packages in requirements.txt")
    return True

def test_env_example():
    """Check .env.example has necessary variables"""
    print("\n🔐 Checking .env.example...")
    
    required_vars = [
        'DATABASE_URL',
        'PINECONE_API_KEY',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'DEFAULT_AI_PROVIDER'
    ]
    
    with open('.env.example', 'r') as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var in content:
            print(f"  ✓ {var}")
        else:
            print(f"  ✗ {var} (missing)")
            missing.append(var)
    
    if missing:
        print(f"\n❌ Missing variables: {', '.join(missing)}")
        return False
    
    print("\n✅ All required environment variables in .env.example")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Chatbot Backend Validation")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_syntax,
        test_requirements,
        test_env_example
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
