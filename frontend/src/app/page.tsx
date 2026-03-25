"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  PlusCircle,
  MessageSquare,
  Trash2,
  Menu,
  X,
  AlertCircle,
  CheckCircle,
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ---------------------------------------------------------------------------
// Toast notification system
// ---------------------------------------------------------------------------

interface Toast {
  id: string;
  message: string;
  type: "error" | "success";
}

function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: Toast[];
  onDismiss: (id: string) => void;
}) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={cn(
            "flex items-center gap-2 px-4 py-3 rounded-lg shadow-lg text-sm pointer-events-auto",
            t.type === "error"
              ? "bg-red-900/90 border border-red-700 text-red-100"
              : "bg-emerald-900/90 border border-emerald-700 text-emerald-100",
          )}
        >
          {t.type === "error" ? (
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
          ) : (
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
          )}
          <span>{t.message}</span>
          <button
            onClick={() => onDismiss(t.id)}
            className="ml-2 opacity-60 hover:opacity-100 transition-opacity"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const WELCOME_MESSAGE =
  "Hello! I'm your personal AI assistant. I can help you with analysis, coding, or just have a chat. How can I help you today?";

const WELCOME_MESSAGE_ITEM = (id = "init"): Message => ({
  id,
  role: "ai",
  content: WELCOME_MESSAGE,
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** A single message bubble in the active chat view. */
interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
}

/** Summary of a stored session returned by GET /sessions. */
interface SessionSummary {
  session_id: string;
  title: string;
  preview: string;
  message_count: number;
  last_message_at: string;
}

/** A message returned by GET /session/{id}/history. */
interface HistoryMessage {
  id: string;
  role: "user" | "ai";
  content: string;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function generateUUID(): string {
  return crypto.randomUUID();
}

function getOrCreateSessionId(): string {
  if (typeof window === "undefined") return "ssr-session";
  const stored = localStorage.getItem("chat_session_id");
  if (stored) return stored;
  const id = generateUUID();
  localStorage.setItem("chat_session_id", id);
  return id;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);
  if (diffDays === 0)
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return d.toLocaleDateString([], { weekday: "short" });
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

// ---------------------------------------------------------------------------
// Sidebar: list of past sessions
// ---------------------------------------------------------------------------

interface SidebarProps {
  sessions: SessionSummary[];
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  loading: boolean;
}

function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  loading,
}: SidebarProps) {
  return (
    <aside className="flex flex-col h-full bg-neutral-950 border-r border-neutral-800 w-full">
      {/* New Chat button */}
      <div className="p-3 border-b border-neutral-800">
        <button
          onClick={onNewChat}
          className="flex items-center gap-2 w-full px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium transition-colors"
        >
          <PlusCircle className="w-4 h-4 flex-shrink-0" />
          New Chat
        </button>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto py-2">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-neutral-500" />
          </div>
        )}
        {!loading && sessions.length === 0 && (
          <p className="text-xs text-neutral-500 text-center py-8 px-4">
            No conversations yet.
            <br />
            Start a new chat!
          </p>
        )}
        {!loading &&
          sessions.map((s) => (
            <div
              key={s.session_id}
              onClick={() => onSelectSession(s.session_id)}
              className={cn(
                "group relative flex items-start gap-3 px-3 py-2.5 mx-1 rounded-lg cursor-pointer transition-colors",
                s.session_id === activeSessionId
                  ? "bg-neutral-800"
                  : "hover:bg-neutral-900",
              )}
            >
              <MessageSquare className="w-4 h-4 flex-shrink-0 mt-0.5 text-neutral-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-neutral-100 truncate leading-tight">
                  {s.title}
                </p>
                <p className="text-xs text-neutral-500 truncate mt-0.5">
                  {s.preview}
                </p>
              </div>
              <div className="flex flex-col items-end gap-1 flex-shrink-0">
                <span className="text-[10px] text-neutral-600 whitespace-nowrap">
                  {formatDate(s.last_message_at)}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(s.session_id);
                  }}
                  title="Delete conversation"
                  className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:text-red-400 text-neutral-500 transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
      </div>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

/**
 * Main chat interface page.
 *
 * Implements an ai-webui–style layout with:
 * - A collapsible left sidebar listing all persisted chat sessions.
 * - A main chat area that loads the full history of the active session.
 * - A "New Chat" button to start a fresh session.
 * - Per-session delete support.
 */
export default function Home() {
  // ---- session management ----
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  // ---- active conversation ----
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);

  // ---- sidebar visibility (mobile) ----
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // ---- toast notifications ----
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback(
    (message: string, type: Toast["type"] = "error") => {
      const id = Date.now().toString();
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(
        () => setToasts((prev) => prev.filter((t) => t.id !== id)),
        4000,
      );
    },
    [],
  );

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ---- initialize session on first render ----
  useEffect(() => {
    const id = getOrCreateSessionId();
    setActiveSessionId(id);
  }, []);

  // ---- scroll to bottom when messages change ----
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // ---- fetch sessions list ----
  const fetchSessions = useCallback(async () => {
    setSessionsLoading(true);
    try {
      const res = await axios.get<SessionSummary[]>(`${API_URL}/sessions`, {
        timeout: 10000,
      });
      setSessions(res.data);
    } catch {
      showToast("Could not load conversations. Is the backend running?");
    } finally {
      setSessionsLoading(false);
    }
  }, []);

  // ---- load full history for a session ----
  const loadSessionHistory = useCallback(async (sessionId: string) => {
    setHistoryLoading(true);
    setMessages([]);
    try {
      const res = await axios.get<HistoryMessage[]>(
        `${API_URL}/session/${sessionId}/history`,
        { timeout: 10000 },
      );
      const loaded: Message[] = res.data.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
      }));
      if (loaded.length === 0) {
        setMessages([WELCOME_MESSAGE_ITEM()]);
      } else {
        setMessages(loaded);
      }
    } catch {
      showToast("Could not load chat history.");
      setMessages([WELCOME_MESSAGE_ITEM()]);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // ---- fetch sessions on mount ----
  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // ---- load history whenever active session changes ----
  useEffect(() => {
    if (!activeSessionId || activeSessionId === "ssr-session") return;
    loadSessionHistory(activeSessionId);
  }, [activeSessionId, loadSessionHistory]);

  // ---- handlers ----

  const handleNewChat = () => {
    const id = generateUUID();
    localStorage.setItem("chat_session_id", id);
    setActiveSessionId(id);
    // Close sidebar on mobile after selecting
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  const handleSelectSession = (id: string) => {
    localStorage.setItem("chat_session_id", id);
    setActiveSessionId(id);
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  const handleDeleteSession = async (id: string) => {
    try {
      await axios.delete(`${API_URL}/session/${id}`, { timeout: 10000 });
      showToast("Conversation deleted.", "success");
    } catch {
      showToast("Failed to delete conversation. Please try again.");
      return;
    }
    setSessions((prev) => prev.filter((s) => s.session_id !== id));
    // If we deleted the active session, start a new one
    if (id === activeSessionId) {
      handleNewChat();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    try {
      const res = await axios.post<{ reply: string }>(
        `${API_URL}/chat`,
        { message: userMsg.content, session_id: activeSessionId },
        { timeout: 30000 },
      );

      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content: res.data.reply,
        },
      ]);

      // Refresh sidebar sessions after a successful exchange
      fetchSessions();
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content:
            "Sorry, I encountered an error connecting to the server. Please ensure the backend is running.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="flex h-screen bg-neutral-900 text-neutral-100 font-sans selection:bg-blue-500/30 overflow-hidden">
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
      {/* ------------------------------------------------------------------ */}
      {/* Sidebar                                                              */}
      {/* ------------------------------------------------------------------ */}
      <div
        className={cn(
          "flex-shrink-0 transition-all duration-300 overflow-hidden",
          sidebarOpen ? "w-72" : "w-0",
        )}
      >
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={handleSelectSession}
          onNewChat={handleNewChat}
          onDeleteSession={handleDeleteSession}
          loading={sessionsLoading}
        />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Main chat panel                                                      */}
      {/* ------------------------------------------------------------------ */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="flex items-center gap-3 px-4 py-3 bg-neutral-900/80 backdrop-blur-md border-b border-neutral-800 sticky top-0 z-10">
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            className="p-1.5 rounded-lg hover:bg-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors"
            title="Toggle sidebar"
          >
            {sidebarOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
          <div className="flex items-center gap-2 flex-1">
            <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-900/20">
              <Sparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <h1 className="text-lg font-semibold tracking-tight">
              AI Assistant
            </h1>
          </div>
          <div className="text-xs text-neutral-500 font-medium px-3 py-1 bg-neutral-800 rounded-full border border-neutral-700/50">
            v1.0.0
          </div>
        </header>

        {/* Chat area */}
        <main className="flex-1 overflow-y-auto w-full max-w-4xl mx-auto p-4 md:p-6 space-y-5">
          {historyLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-6 h-6 animate-spin text-neutral-500" />
            </div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex w-full gap-3 max-w-3xl",
                  msg.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto",
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
                    msg.role === "user" ? "bg-indigo-600" : "bg-emerald-600",
                  )}
                >
                  {msg.role === "user" ? (
                    <User className="w-4 h-4 text-white" />
                  ) : (
                    <Bot className="w-4 h-4 text-white" />
                  )}
                </div>

                {/* Bubble */}
                <div
                  className={cn(
                    "p-4 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed",
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : "bg-neutral-800 text-neutral-100 rounded-bl-none border border-neutral-700/50",
                  )}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))
          )}

          {/* Typing indicator */}
          {isSending && (
            <div className="flex w-full gap-3 max-w-3xl mr-auto">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-neutral-800 p-4 rounded-2xl rounded-bl-none border border-neutral-700/50 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-neutral-400" />
                <span className="text-sm text-neutral-400">Thinking…</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </main>

        {/* Input area */}
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
                placeholder="Ask me anything…"
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
            <p className="text-center text-xs text-neutral-500 mt-3">
              AI can make mistakes. Please verify important information.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
