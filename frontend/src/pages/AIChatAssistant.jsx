import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PaperAirplaneIcon, XMarkIcon,
  UserCircleIcon, ChevronDownIcon, DocumentTextIcon,
  BookmarkIcon, LightBulbIcon, ClipboardDocumentListIcon,
  ArrowPathIcon, SparklesIcon
} from '@heroicons/react/24/outline';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { normalizeLanguageCode } from '../lib/languages';

const API_BASE = '';

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-xl bg-brand-primary/10 flex items-center justify-center flex-shrink-0">
        <SparklesIcon className="w-4 h-4 text-brand-primary animate-pulse" />
      </div>
      <div className="px-4 py-3 bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-none">
        <div className="flex gap-1.5">
          {[0, 1, 2].map(i => (
            <div key={i} className="w-2 h-2 bg-brand-primary/40 rounded-full animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  const { t } = useTranslation();
  const isUser = msg.role === 'user';
  const [reasoningOpen, setReasoningOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-slate-800 text-white' : 'bg-brand-primary/10 text-brand-primary'
      }`}>
        {isUser ? <UserCircleIcon className="w-5 h-5" /> : <SparklesIcon className="w-4 h-4" />}
      </div>

      <div className={`space-y-2 max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`px-4 py-3 rounded-2xl text-sm font-medium leading-relaxed prose prose-sm max-w-none ${
          isUser
            ? 'bg-slate-800 text-white rounded-tr-none'
            : 'bg-white border border-slate-100 text-slate-800 rounded-tl-none shadow-sm'
        }`}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              h3: ({node, ...props}) => <h3 className="text-brand-primary font-black mt-4 mb-2 first:mt-0" {...props} />,
              h4: ({node, ...props}) => <h4 className="text-slate-900 font-extrabold mt-3 mb-1" {...props} />,
              p: ({node, ...props}) => <p className="mb-2 last:mb-0" {...props} />,
              ul: ({node, ...props}) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
              li: ({node, ...props}) => <li className="text-slate-600" {...props} />,
              a: ({node, ...props}) => <a className="text-brand-primary font-bold underline hover:no-underline" target="_blank" rel="noopener noreferrer" {...props} />,
              blockquote: ({node, ...props}) => (
                <div className="my-4 border-l-4 border-brand-primary/30 pl-4 py-1 bg-brand-primary/5 rounded-r-xl italic text-slate-500" {...props} />
              )
            }}
          >
            {msg.text}
          </ReactMarkdown>
        </div>

        {/* AI Reasoning */}
        {msg.reasoning && (
          <button
            onClick={() => setReasoningOpen(v => !v)}
            className="flex items-center gap-1.5 text-[10px] font-black text-brand-primary uppercase tracking-widest hover:opacity-80 transition-opacity"
          >
            <ChevronDownIcon className={`w-3 h-3 transition-transform ${reasoningOpen ? 'rotate-180' : ''}`} />
            {t('assistant.reasoning', 'Intelligence Reasoning')}
          </button>
        )}
        {reasoningOpen && msg.reasoning && (
          <div className="reasoning-box w-full text-[11px]">
            <span className="font-bold text-brand-primary block mb-1">
              {t('assistant.source', 'Source')}: AI Local Engine
            </span>
            {msg.reasoning}
          </div>
        )}

        {!isUser && msg.timestamp && (
          <span className="text-[9px] text-slate-400 font-medium">{msg.timestamp}</span>
        )}
      </div>
    </motion.div>
  );
}

export default function AIChatAssistant({ userProfile, appLanguage, savedSchemes = [] }) {
  const { t, i18n } = useTranslation();
  const languageCode = normalizeLanguageCode(appLanguage || i18n.resolvedLanguage || i18n.language);
  const suggestionItems = useMemo(() => ([
    { text: t('assistant.quick_questions_items.subsidy'), tag: t('assistant.quick_question_tags.subsidy') },
    { text: t('assistant.quick_questions_items.application'), tag: t('assistant.quick_question_tags.application') },
    { text: t('assistant.quick_questions_items.documents'), tag: t('assistant.quick_question_tags.documents') },
    { text: t('assistant.quick_questions_items.eligibility'), tag: t('assistant.quick_question_tags.eligibility') },
  ]), [languageCode, t]);

  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      text: t('assistant.welcome') || "Hello! I'm AI Local Advisor. How can I assist you today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }
  ]);

  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, isTyping]);

  const sendMessage = useCallback(async (text) => {
    const val = (text || input).trim();
    if (!val || isTyping) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      text: val,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    const assistantMsgId = Date.now() + 1;

    try {
      const profile = userProfile || JSON.parse(sessionStorage.getItem('karios_user') || '{}');
      const response = await fetch(`${API_BASE}/v1/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: val,
          profile: { sector: profile.sector || '', state: profile.state || '' },
          schemes: savedSchemes.slice(0, 1),
          language: languageCode,
        }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let streamedText = '';


      while (true) {
        const { done, value } = await reader.read();
        const chunk = decoder.decode(value || new Uint8Array(), { stream: !done });
        streamedText += chunk;
        
        // Robust split by ### or #### section headers
        const parts = streamedText.split(/(?=###?# )/g)
          .map(p => p.trim())
          .filter(p => p && !p.includes('[DONE]'));

        setMessages(prev => {
          // Identify indices for user messages and old assistant messages
          const others = prev.filter(m => m.id < assistantMsgId);
          
          // Generate new cards for each section found in the raw stream
          const cards = parts.map((p, idx) => ({
            id: assistantMsgId + idx,
            role: 'assistant',
            text: p,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          }));
          
          return [...others, ...cards];
        });

        if (done) break;
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        id: Date.now() + 999,
        role: 'assistant',
        text: "I encountered an error. Please ensure the local server is running on port 8001.",
      }]);
    } finally { setIsTyping(false); }
  }, [input, isTyping, languageCode, savedSchemes, t, userProfile]);

  const clearChat = () => {
    setMessages([{
      id: Date.now(),
      role: 'assistant',
      text: "Hello! I'm AI Local Advisor.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }]);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="page-title">{t('assistant.title', 'AI Local Advisor')}</h2>
      </div>

      <div className="intelligence-card overflow-hidden flex flex-col" style={{ height: 'calc(100vh - 16rem)' }}>
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-brand-primary rounded-xl flex items-center justify-center shadow-glow-sm">
              <SparklesIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 tracking-tight">AI Advisor Strategy Room</h3>
              <div className="flex items-center gap-1.5">
                <span className="glow-dot" />
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Local Mode Active</span>
              </div>
            </div>
          </div>
          <button onClick={clearChat} className="btn-ghost p-2"><ArrowPathIcon className="w-4 h-4" /></button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map(msg => ( <MessageBubble key={msg.id} msg={msg} /> ))}
          {isTyping && <TypingIndicator />}
          <div ref={scrollRef} />
        </div>

        <div className="px-5 py-3 border-t border-slate-50 flex gap-2">
          {suggestionItems.map((s, i) => (
            <button key={i} onClick={() => sendMessage(s.text)} className="px-3 py-1.5 bg-white border border-slate-200 hover:border-brand-primary rounded-full text-[10px] font-bold text-slate-600 transition-all shadow-sm">
              {s.text}
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-slate-100 bg-white">
          <div className="flex gap-3 items-center bg-slate-50 p-2 pr-2 pl-4 rounded-2xl border border-slate-200">
            <DocumentTextIcon className="w-5 h-5 text-slate-300 flex-shrink-0" />
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder="Ask for 'Eligibility', 'Documents', or 'Summarize'..."
              className="flex-1 py-2 text-sm font-medium outline-none bg-transparent"
              disabled={isTyping}
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || isTyping}
              className="w-10 h-10 bg-brand-primary text-white rounded-xl flex items-center justify-center disabled:opacity-50 shadow-glow-sm"
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
