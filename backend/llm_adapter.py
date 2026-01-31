import os
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], context: str = "") -> str:
        """Generate a response from the AI provider"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI: {e}")
    
    def generate_response(self, messages: List[Dict[str, str]], context: str = "") -> str:
        if not self.client:
            return "OpenAI is not configured. Please set OPENAI_API_KEY."
        
        try:
            # Prepend context if available
            if context:
                messages = [
                    {"role": "system", "content": f"Relevant context:\n{context}"}
                ] + messages
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating response from OpenAI: {str(e)}"

class AnthropicProvider(AIProvider):
    """Anthropic provider implementation"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize Anthropic: {e}")
    
    def generate_response(self, messages: List[Dict[str, str]], context: str = "") -> str:
        if not self.client:
            return "Anthropic is not configured. Please set ANTHROPIC_API_KEY."
        
        try:
            # Convert messages format and add context
            formatted_messages = []
            system_message = ""
            
            if context:
                system_message = f"Relevant context:\n{context}\n\n"
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message += msg["content"]
                else:
                    formatted_messages.append(msg)
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                system=system_message if system_message else None,
                messages=formatted_messages
            )
            
            return response.content[0].text
        except Exception as e:
            return f"Error generating response from Anthropic: {str(e)}"

class LLMAdapter:
    """Main adapter for managing multiple AI providers"""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider()
        }
        self.default_provider = os.getenv("DEFAULT_AI_PROVIDER", "openai")
    
    def get_response(
        self, 
        message: str, 
        context: str = "", 
        provider: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Get response from AI provider with context"""
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            return f"Provider '{provider_name}' not supported."
        
        # Build messages list
        messages = conversation_history or []
        messages.append({"role": "user", "content": message})
        
        return self.providers[provider_name].generate_response(messages, context)
    
    def is_available(self, provider: Optional[str] = None) -> bool:
        """Check if a provider is available"""
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            return False
        
        provider_obj = self.providers[provider_name]
        return provider_obj.client is not None

# Global instance
llm_adapter = LLMAdapter()
