import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  RotateCcw, 
  Sparkles, 
  Server, 
  Database, 
  Zap, 
  AlertTriangle, 
  Sliders, 
  CheckCircle2, 
  Layers,
  Clock,
  Coins
} from 'lucide-react';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

function generateSessionId() {
  return `s-${Math.random().toString(36).substring(2, 8)}`;
}

export default function App() {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful and concise AI assistant.');
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Failure simulation hook selection
  const [simulateFailure, setSimulateFailure] = useState('none');
  const [customSimulate, setCustomSimulate] = useState('');
  const [healthInfo, setHealthInfo] = useState(null);

  const messagesEndRef = useRef(null);

  // Initialize fresh session on page load
  useEffect(() => {
    const newId = generateSessionId();
    setSessionId(newId);
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (res.ok) {
        const data = await res.json();
        setHealthInfo(data);
      } else {
        setHealthInfo({ status: 'unreachable' });
      }
    } catch {
      setHealthInfo({ status: 'unreachable' });
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleNewSession = () => {
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([]);
    checkHealth();
  };

  const sendMessage = async (e) => {
    if (e) e.preventDefault();
    const trimmed = inputMessage.trim();
    if (!trimmed || isLoading) return;

    // Add user message to UI immediately
    const userMsg = { role: 'user', content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsLoading(true);

    // Prepare headers for failure simulation test hook
    const headers = { 'Content-Type': 'application/json' };
    if (simulateFailure === 'custom' && customSimulate.trim()) {
      headers['X-Simulate-Failure'] = customSimulate.trim();
    } else if (simulateFailure !== 'none') {
      headers['X-Simulate-Failure'] = simulateFailure;
    }

    try {
      const payload = {
        session_id: sessionId,
        message: trimmed,
      };
      if (systemPrompt.trim()) {
        payload.system_prompt = systemPrompt.trim();
      }

      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        let errorDetail = 'Unknown error';
        try {
          const errData = await res.json();
          errorDetail = typeof errData.detail === 'string' 
            ? errData.detail 
            : JSON.stringify(errData.detail);
        } catch {
          errorDetail = `Server returned HTTP ${res.status}`;
        }

        // Display error gracefully as a message in the chat (never a blank screen)
        setMessages((prev) => [
          ...prev,
          {
            role: 'error',
            status: res.status,
            content: `Error ${res.status}: ${errorDetail}`,
          },
        ]);
      } else {
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: data.reply,
            metadata: data.metadata,
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'error',
          status: 0,
          content: `Network Connection Error: Could not reach backend at ${BACKEND_URL}. Check if backend is running.`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-3 flex items-center justify-between shrink-0 shadow-md">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-sky-600 flex items-center justify-center shadow-lg shadow-sky-600/30">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-semibold text-lg text-white">Lyftr AI Gateway</h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-medium">
                LiteLLM Resilient
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-2">
              <span>Session: <code className="text-slate-300 font-mono">{sessionId || 'initializing...'}</code></span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Database className="w-3 h-3 text-emerald-400" />
                SQLite Volume
              </span>
            </p>
          </div>
        </div>

        {/* Status badges & controls */}
        <div className="flex items-center gap-3">
          {healthInfo && (
            <div className="hidden sm:flex items-center gap-2 text-xs bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
              <span className={`inline-block w-2 h-2 rounded-full ${healthInfo.status === 'ok' ? 'bg-emerald-400' : 'bg-rose-500'} animate-pulse`} />
              <span className="text-slate-300 font-medium">
                {healthInfo.status === 'ok' 
                  ? `Backend Healthy (${healthInfo.keys_configured} Keys, Cache ON)` 
                  : 'Backend Disconnected'}
              </span>
            </div>
          )}

          <button
            onClick={() => setShowSystemPrompt(!showSystemPrompt)}
            className="flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg border border-slate-700 transition"
            title="Configure System Prompt"
          >
            <Sliders className="w-3.5 h-3.5 text-sky-400" />
            <span>System Prompt</span>
          </button>

          <button
            onClick={handleNewSession}
            className="flex items-center gap-1.5 text-xs bg-sky-600 hover:bg-sky-500 text-white font-medium px-3 py-1.5 rounded-lg shadow transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
        </div>
      </header>

      {/* Test Hook Simulator Bar */}
      <div className="bg-slate-900 border-b border-slate-800/80 px-6 py-2 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-slate-300">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
          <span className="font-semibold text-slate-200">X-Simulate-Failure Hook:</span>
          <span className="text-slate-400 hidden md:inline">Test key failover on demand</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <label className="flex items-center gap-1 text-slate-300 cursor-pointer">
            <input 
              type="radio" 
              name="simFail" 
              checked={simulateFailure === 'none'} 
              onChange={() => setSimulateFailure('none')}
              className="accent-sky-500" 
            />
            <span>None (Normal)</span>
          </label>
          <label className="flex items-center gap-1 text-slate-300 cursor-pointer">
            <input 
              type="radio" 
              name="simFail" 
              checked={simulateFailure === 'key_1=429'} 
              onChange={() => setSimulateFailure('key_1=429')}
              className="accent-sky-500" 
            />
            <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-amber-300">key_1=429</span>
          </label>
          <label className="flex items-center gap-1 text-slate-300 cursor-pointer">
            <input 
              type="radio" 
              name="simFail" 
              checked={simulateFailure === 'key_1=500'} 
              onChange={() => setSimulateFailure('key_1=500')}
              className="accent-sky-500" 
            />
            <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-amber-300">key_1=500</span>
          </label>
          <label className="flex items-center gap-1 text-slate-300 cursor-pointer">
            <input 
              type="radio" 
              name="simFail" 
              checked={simulateFailure === '*=429'} 
              onChange={() => setSimulateFailure('*=429')}
              className="accent-sky-500" 
            />
            <span className="font-mono bg-slate-800 px-1.5 py-0.5 rounded text-rose-300">*=429 (503)</span>
          </label>
        </div>
      </div>

      {/* System Prompt Drawer (Optional Feature) */}
      {showSystemPrompt && (
        <div className="bg-slate-900/90 border-b border-slate-800 px-6 py-3 transition-all animate-in slide-in-from-top-2">
          <label className="block text-xs font-medium text-slate-300 mb-1">
            System Prompt for this session (optional):
          </label>
          <input
            data-testid="system-prompt-input"
            type="text"
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            placeholder="e.g. You are a helpful AI assistant."
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
          />
        </div>
      )}

      {/* Main Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <div className="h-14 w-14 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-4 text-sky-400 shadow-inner">
              <Zap className="w-7 h-7" />
            </div>
            <h3 className="text-slate-200 font-medium text-base mb-1">LiteLLM Chat Gateway</h3>
            <p className="text-sm max-w-md text-slate-400 mb-4">
              Send messages to test response caching, automatic key fallback, and token tracking.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-lg">
              <button
                onClick={() => setInputMessage('What is the capital of France?')}
                className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-3 py-1.5 rounded-lg transition"
              >
                "What is the capital of France?" (Cache test)
              </button>
              <button
                onClick={() => setInputMessage('Explain quantum computing in two sentences.')}
                className="text-xs bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 px-3 py-1.5 rounded-lg transition"
              >
                "Explain quantum computing in two sentences."
              </button>
            </div>
          </div>
        ) : (
          messages.map((msg, index) => {
            if (msg.role === 'user') {
              return (
                <div key={index} className="flex justify-end">
                  <div className="max-w-xl bg-sky-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </div>
                </div>
              );
            }

            if (msg.role === 'error') {
              return (
                <div key={index} className="flex justify-start">
                  <div className="max-w-xl bg-rose-950/60 border border-rose-800/80 text-rose-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow text-sm">
                    <div className="flex items-center gap-2 font-semibold text-rose-400 mb-1">
                      <AlertTriangle className="w-4 h-4 shrink-0" />
                      <span>Request Error</span>
                    </div>
                    <p className="font-mono text-xs text-rose-300">{msg.content}</p>
                  </div>
                </div>
              );
            }

            // Assistant reply with exact data-testid attributes
            const isCache = msg.metadata?.resolution_source === 'LLM_CACHE';
            return (
              <div key={index} className="flex justify-start">
                <div 
                  data-testid="assistant-message"
                  className="max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm p-4 shadow-lg space-y-3"
                >
                  {/* Reply text */}
                  <div className="text-slate-100 text-sm leading-relaxed whitespace-pre-wrap">
                    {msg.content}
                  </div>

                  {/* Metadata container */}
                  {msg.metadata && (
                    <div className="pt-2.5 border-t border-slate-800/80 flex flex-wrap items-center gap-2 text-xs">
                      {/* Resolution Source */}
                      <span 
                        data-testid="meta-source"
                        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-semibold ${
                          isCache 
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' 
                            : 'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                        }`}
                      >
                        {isCache ? <Zap className="w-3 h-3" /> : <Sparkles className="w-3 h-3" />}
                        {msg.metadata.resolution_source}
                      </span>

                      {/* Model Used */}
                      <span 
                        data-testid="meta-model"
                        className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700/60 font-mono text-[11px]"
                      >
                        {msg.metadata.model}
                      </span>

                      {/* Latency */}
                      <span 
                        data-testid="meta-latency"
                        className="inline-flex items-center gap-1 text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded"
                      >
                        <Clock className="w-3 h-3 text-amber-400" />
                        {msg.metadata.latency_ms} ms
                      </span>

                      {/* Tokens info */}
                      <span className="inline-flex items-center gap-1.5 text-slate-400 bg-slate-800/60 px-2 py-0.5 rounded">
                        <Coins className="w-3 h-3 text-sky-400" />
                        <span>In: <strong data-testid="meta-input-tokens" className="text-slate-200">{msg.metadata.input_tokens}</strong></span>
                        <span>•</span>
                        <span>Out: <strong data-testid="meta-output-tokens" className="text-slate-200">{msg.metadata.output_tokens}</strong></span>
                      </span>

                      {/* Key ID badge */}
                      {msg.metadata.key_id && (
                        <span className="bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700/50 font-mono text-[11px]">
                          Key: {msg.metadata.key_id}
                        </span>
                      )}

                      {/* Fallback attempts if any */}
                      {msg.metadata.fallback_attempts > 0 && (
                        <span className="bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded text-[11px] font-medium">
                          Fallbacks: {msg.metadata.fallback_attempts}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 shadow flex items-center gap-3 text-slate-400 text-sm">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-sky-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2 h-2 bg-sky-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2 h-2 bg-sky-400 rounded-full animate-bounce"></div>
              </div>
              <span className="text-xs">Generating response & routing...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Footer */}
      <footer className="border-t border-slate-800 bg-slate-900/90 p-4 shrink-0">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex items-center gap-3">
          <input
            data-testid="chat-input"
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send)"
            disabled={isLoading}
            className="flex-1 bg-slate-950 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition shadow-inner disabled:opacity-50"
          />
          <button
            data-testid="send-button"
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 disabled:hover:bg-sky-600 text-white font-medium px-5 py-3 rounded-xl shadow-lg shadow-sky-600/30 transition flex items-center justify-center shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </footer>
    </div>
  );
}
