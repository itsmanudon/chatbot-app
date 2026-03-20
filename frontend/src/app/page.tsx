'use client';

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, Bot, User, Loader2, Sparkles } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Message {
  role: 'user' | 'ai';
  content: string;
  id: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'ai',
      content: "Hello! I'm your personal AI assistant. I can help you with analysis, coding, or just have a chat. How can I help you today?",
      id: 'init-1'
    }
  ]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const sessionId = useRef<string>(
    typeof window !== 'undefined'
      ? (localStorage.getItem('chat_session_id') ?? (() => {
          const id = crypto.randomUUID();
          localStorage.setItem('chat_session_id', id);
          return id;
        })())
      : 'ssr-session'
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      id: Date.now().toString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      // Create a temporary ID for the AI response
      const aiTempId = (Date.now() + 1).toString();

      const res = await axios.post(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/chat`, {
        message: userMessage.content,
        session_id: sessionId.current
      });

      const aiReply = res.data.reply;

      setMessages(prev => [
        ...prev,
        { role: 'ai', content: aiReply, id: aiTempId }
      ]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [
        ...prev,
        {
          role: 'ai',
          content: 'Sorry, I encountered an error connecting to the server. Please ensure the backend is running.',
          id: Date.now().toString()
        }
      ]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-neutral-900 text-neutral-100 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-neutral-900/80 backdrop-blur-md border-b border-neutral-800 sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/20">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">AI Assistant</h1>
        </div>
        <div className="text-xs text-neutral-500 font-medium px-3 py-1 bg-neutral-800 rounded-full border border-neutral-700/50">
          v1.0.0
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto w-full max-w-5xl mx-auto p-4 md:p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex w-full gap-4 max-w-3xl",
              msg.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
            )}
          >
            {/* Avatar */}
            <div className={cn(
              "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
              msg.role === 'user' ? "bg-indigo-600" : "bg-emerald-600"
            )}>
              {msg.role === 'user' ? (
                <User className="w-5 h-5 text-white" />
              ) : (
                <Bot className="w-5 h-5 text-white" />
              )}
            </div>

            {/* Message Bubble */}
            <div className={cn(
              "flex flex-col gap-1 min-w-0 p-4 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed",
              msg.role === 'user'
                ? "bg-indigo-600 text-white rounded-br-none"
                : "bg-neutral-800 text-neutral-100 rounded-bl-none border border-neutral-700/50"
            )}>
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
        {isSending && (
          <div className="flex w-full gap-4 max-w-3xl mr-auto">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-neutral-800 p-4 rounded-2xl rounded-bl-none border border-neutral-700/50 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-neutral-400" />
              <span className="text-sm text-neutral-400">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <div className="p-4 bg-transparent">
        <div className="max-w-3xl mx-auto">
          <form
            onSubmit={handleSubmit}
            className="relative flex items-center gap-2 bg-neutral-800/50 p-2 rounded-xl border border-neutral-700 focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/50 transition-all shadow-lg"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything..."
              className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder-neutral-400 px-4 py-3 h-12"
              disabled={isSending}
            />
            <button
              type="submit"
              disabled={!input.trim() || isSending}
              className="p-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
            >
              {isSending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </form>
          <div className="text-center mt-3">
            <p className="text-xs text-neutral-500">AI can make mistakes. Please verify important information.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
