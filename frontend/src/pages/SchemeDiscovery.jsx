import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  FunnelIcon, MagnifyingGlassIcon, MapPinIcon, BriefcaseIcon,
  CheckBadgeIcon, ArrowRightIcon, BookmarkIcon, StarIcon,
  SparklesIcon, XMarkIcon, ClockIcon, CurrencyRupeeIcon,
  ArrowTopRightOnSquareIcon, CheckCircleIcon, InformationCircleIcon,
  ChatBubbleLeftEllipsisIcon, PaperAirplaneIcon, DocumentCheckIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { BookmarkIcon as BookmarkSolid } from '@heroicons/react/24/solid';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { normalizeLanguageCode } from '../lib/languages';

const API_BASE = 'http://127.0.0.1:8001';
const ALL_SECTORS = 'All Sectors';
const ALL_STATES = 'All States';
const ALL_ENTITIES = 'All Entities';

const SECTORS = [
  ALL_SECTORS, 'Manufacturing', 'Services', 'Technology', 'Agriculture',
  'Healthcare', 'Education', 'Food Processing', 'Textiles & Garments',
  'FinTech', 'Renewable Energy', 'E-commerce',
];
const STATES_FILTER = [ALL_STATES, 'Central Government', 'Tamil Nadu', 'Maharashtra', 'Karnataka', 'Gujarat', 'Delhi'];
const ENTITY_FILTER = [ALL_ENTITIES, 'Proprietorship', 'Private Limited', 'LLP', 'Startup'];

function optionKey(value) {
  const normalized = String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
  return normalized || 'item';
}

function localizeOption(t, baseKey, value) {
  return t(`${baseKey}.${optionKey(value)}`, { defaultValue: value });
}

function localizeOptions(t, baseKey, values) {
  return values.map((value) => ({
    value,
    label: localizeOption(t, baseKey, value),
  }));
}

function buildFallbackSchemes(languageCode) {
  if (languageCode === 'ta') {
    return [
      { scheme_id: '1', scheme_name: 'PMEGP - பிரதம மந்திரி வேலைவாய்ப்பு உருவாக்கத் திட்டம்', sector: 'Manufacturing', state: 'All India', ai_confidence: 94, timeline_days: 90, description: 'மைக்ரோ நிறுவனங்களை தொடங்க கடன் இணைந்த நிதியுதவியை வழங்குகிறது. உற்பத்தித் துறைக்கு அதிகபட்ச திட்டச் செலவு ரூ.25 லட்சம்.', match_reasons: ['துறை: உற்பத்தி', 'இடம்: இந்தியா முழுவதும்'], eligibility: 'முதல் தலைமுறை தொழில்முனைவோர், 18+ வயது, உற்பத்திக்காக 8ஆம் வகுப்பு தேர்ச்சி.' },
      { scheme_id: '2', scheme_name: 'Stand-Up India திட்டம்', sector: 'Services', state: 'All India', ai_confidence: 88, timeline_days: 60, description: 'SC/ST மற்றும் பெண் தொழில்முனைவோருக்கான புதிய நிறுவனங்களுக்கு ரூ.10 லட்சம் முதல் ரூ.1 கோடி வரை ஒருங்கிணைந்த கடன்.', match_reasons: ['வகை: பெண் தொழில்முனைவோர்', 'இடம்: இந்தியா முழுவதும்'] },
      { scheme_id: '3', scheme_name: 'CLCSS - கடன் இணைந்த மூலதன நிதியுதவி திட்டம்', sector: 'Technology', state: 'All India', ai_confidence: 82, timeline_days: 120, description: 'சிறு தொழில்களுக்கான தொழில்நுட்ப மேம்பாட்டிற்கு நிறுவனம் பெறும் நிதிக்கு 15% மூலதன நிதியுதவி.', match_reasons: ['துறை: தொழில்நுட்பம்', 'நிறுவனம்: MSME'] },
      { scheme_id: '4', scheme_name: 'Startup India Seed Fund திட்டம்', sector: 'Any', state: 'All India', ai_confidence: 76, timeline_days: 45, description: 'கருத்துச் சான்று, முன்னோடி வடிவம் மற்றும் சந்தை நுழைவுக்காக ரூ.20 லட்சம் வரை மானியம் அல்லது ரூ.50 லட்சம் வரை கடன்.', match_reasons: ['நிலை: ஆரம்ப கட்டம்', 'இடம்: இந்தியா முழுவதும்'] },
      { scheme_id: '5', scheme_name: 'MUDRA - சிஷு கடன்', sector: 'Any', state: 'All India', ai_confidence: 72, timeline_days: 30, description: 'புதியதாக தொடங்கும் சிறு வணிகங்களுக்கு ரூ.50,000 வரை கடன் உதவி.', match_reasons: ['நிறுவனம்: தனிநபர் உரிமம்', 'இடம்: இந்தியா முழுவதும்'] },
      { scheme_id: '6', scheme_name: 'DEDS - பால் தொழில் முனைவோர் மேம்பாட்டு திட்டம்', sector: 'Agriculture', state: 'All India', ai_confidence: 65, timeline_days: 75, description: 'சிறிய பால்பண்ணைகள் மற்றும் துணை பிரிவுகளை அமைக்க பின்தங்கிய மூலதன நிதியுதவி.', match_reasons: ['துறை: வேளாண்மை', 'இடம்: இந்தியா முழுவதும்'] },
    ];
  }

  return [
    { scheme_id: '1', scheme_name: 'PMEGP - Prime Minister Employment Generation Programme', sector: 'Manufacturing', state: 'All India', ai_confidence: 94, timeline_days: 90, description: 'Provides credit-linked subsidy for setting up micro enterprises. Maximum project cost Rs 25L for manufacturing.', match_reasons: ['Sector: Manufacturing', 'Location: Pan India'], eligibility: 'First generation entrepreneur, 18+ years, 8th pass for manufacturing.' },
    { scheme_id: '2', scheme_name: 'Stand-Up India Scheme', sector: 'Services', state: 'All India', ai_confidence: 88, timeline_days: 60, description: 'Composite loan between Rs 10L and Rs 1Cr for SC/ST and women entrepreneurs to set up greenfield enterprises.', match_reasons: ['Category: Women Entrepreneur', 'Location: Pan India'] },
    { scheme_id: '3', scheme_name: 'CLCSS - Credit Linked Capital Subsidy Scheme', sector: 'Technology', state: 'All India', ai_confidence: 82, timeline_days: 120, description: '15% capital subsidy on institutional finance for technology up-gradation of Small Scale Industries.', match_reasons: ['Sector: Technology', 'Entity: MSME'] },
    { scheme_id: '4', scheme_name: 'Startup India Seed Fund Scheme', sector: 'Any', state: 'All India', ai_confidence: 76, timeline_days: 45, description: 'Up to Rs 20L as grant or Rs 50L as debt for proof of concept, prototype development, and market entry.', match_reasons: ['Stage: Early Stage', 'Location: Pan India'] },
    { scheme_id: '5', scheme_name: 'MUDRA - Shishu Loan', sector: 'Any', state: 'All India', ai_confidence: 72, timeline_days: 30, description: 'Loans up to Rs 50,000 for micro business activities that are just starting and need small capital support.', match_reasons: ['Entity: Proprietorship', 'Location: Pan India'] },
    { scheme_id: '6', scheme_name: 'Dairy Entrepreneurship Development Scheme (DEDS)', sector: 'Agriculture', state: 'All India', ai_confidence: 65, timeline_days: 75, description: 'Back-ended capital subsidy for setting up small dairy farms and ancillary units for clean milk production.', match_reasons: ['Sector: Agriculture', 'Location: Pan India'] },
  ];
}

function MatchBadge({ score }) {
  const { t } = useTranslation();
  const isHigh = score >= 90;
  const color = score >= 85 ? 'text-emerald-700 bg-emerald-50 border-emerald-200 shadow-emerald-100/50' :
                score >= 70 ? 'text-blue-700 bg-blue-50 border-blue-200' :
                              'text-amber-700 bg-amber-50 border-amber-200';
  
  return (
    <div className="relative">
      {isHigh && (
        <span className="absolute inset-0 rounded-full bg-emerald-400/20 animate-ping opacity-75" />
      )}
      <span className={`relative inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-wider border transition-all ${color} ${isHigh ? 'shadow-glow-sm scale-105' : ''}`}>
        <StarIcon className={`w-3 h-3 ${isHigh ? 'animate-pulse' : ''}`} />
        {t('discovery.match_badge', { score, defaultValue: `${score}% Match` })}
      </span>
    </div>
  );
}

function SchemeCardSkeleton() {
  return (
    <div className="intelligence-card p-6 space-y-4">
      <div className="flex justify-between">
        <div className="space-y-2 flex-1">
          <div className="h-4 bg-slate-100 rounded animate-shimmer w-3/4" />
          <div className="h-3 bg-slate-100 rounded animate-shimmer w-1/2" />
        </div>
        <div className="h-6 w-20 bg-slate-100 rounded-full animate-shimmer" />
      </div>
      <div className="h-12 bg-slate-100 rounded-xl animate-shimmer" />
      <div className="flex gap-2">
        <div className="h-5 w-16 bg-slate-100 rounded-lg animate-shimmer" />
        <div className="h-5 w-20 bg-slate-100 rounded-lg animate-shimmer" />
      </div>
      <div className="pt-4 border-t border-slate-100 flex justify-between">
        <div className="h-4 w-24 bg-slate-100 rounded animate-shimmer" />
        <div className="h-8 w-28 bg-slate-100 rounded-xl animate-shimmer" />
      </div>
    </div>
  );
}

function getSchemeId(scheme) {
  return scheme?.scheme_id || scheme?.scheme_code || scheme?.id || '';
}

function matchesSelectedOption(selectedValue, allValue, schemeValue) {
  if (!selectedValue || selectedValue === allValue) {
    return true;
  }

  const selected = String(selectedValue || '').trim().toLowerCase();
  const candidate = String(schemeValue || '').trim().toLowerCase();
  if (!candidate) {
    return false;
  }

  return candidate.includes(selected) || selected.includes(candidate);
}

function SchemeDetailModal({ scheme, onClose, onSave, isSaved }) {
  const { t, i18n } = useTranslation();
  if (!scheme) return null;
  const name = t(`schemes.${scheme.scheme_id}.name`, { defaultValue: scheme.scheme_name || scheme.Scheme_Name || 'Scheme' });
  const desc = t(`schemes.${scheme.scheme_id}.description`, {
    defaultValue: scheme.detailed_description || scheme.description || scheme.Scheme_Description || t('discovery.no_description', 'No description available.'),
  });
  const elig = t(`schemes.${scheme.scheme_id}.eligibility`, {
    defaultValue: scheme.eligibility || scheme.Eligibility_Criteria || '',
  });
  const website = scheme.official_link || scheme.Website_URL || scheme.website_url || '';
  const docs = scheme.required_documents || scheme.ai_required_documents || [];
  const steps = scheme.application_steps || scheme.ai_application_steps || [];
  const reasons = scheme.match_reasons || [];

  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const chatEndRef = useRef(null);

  // Auto-scroll to bottom whenever messages or streaming text update
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'auto', block: 'end' });
  }, [messages, streamingText]);

  // Generate contextual follow-up chips based on the AI reply content
  const generateFollowUps = (aiText) => {
    const lc = aiText.toLowerCase();
    if (lc.includes('eligib') || lc.includes('who can'))
      return ['What documents do I need?', 'How much subsidy can I get?', 'How do I apply?'];
    if (lc.includes('document') || lc.includes('required'))
      return ['How long does it take?', 'What is the subsidy amount?', 'Where do I apply online?'];
    if (lc.includes('apply') || lc.includes('step') || lc.includes('process'))
      return ['What is the processing timeline?', 'Am I eligible?', 'What documents are needed?'];
    if (lc.includes('subsidy') || lc.includes('amount') || lc.includes('crore') || lc.includes('lakh'))
      return ['Am I eligible for this?', 'How do I apply?', 'How long does approval take?'];
    if (lc.includes('timeline') || lc.includes('days') || lc.includes('weeks'))
      return ['What documents are required?', 'What is the subsidy amount?', 'Can I track my application?'];
    // default follow-ups
    return ['Am I eligible?', 'What documents do I need?', 'How do I apply?'];
  };

  // Welcome message when modal opens (Guard against firing twice)
  useEffect(() => {
    if (!scheme || messages.length > 0) return;
    setMessages([]);
    setStreamingText('');
    setTimeout(() => {
      streamReply(`Welcome the user to ${name} and offer help.`, []);
    }, 400);
  }, [scheme?.scheme_id]);

  const streamReply = async (msg, history) => {
    setChatLoading(true);
    setStreamingText('');
    let accumulated = '';

    try {
      const res = await fetch(`${API_BASE}/v1/chat/scheme/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scheme_id: scheme.scheme_id || scheme.scheme_code || '',
          message: msg,
          language: i18n.language,
          history: history.slice(-6),
        }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        accumulated += chunk;
        
        // Strip [DONE] and clean robot emojis for a premium feel
        const display = accumulated.replace(/\[DONE\]/g, '').replace(/🤖/g, '').trim();
        setStreamingText(display);
      }
    } catch (err) {
      accumulated = t('assistant.error_sync') || 'I encountered an error. Please try again.';
      setStreamingText(accumulated);
    } finally {
      const finalText = accumulated.trim().replace(/🤖/g, '');
      const followUps = generateFollowUps(finalText);
      setMessages(prev => [...prev, { role: 'ai', content: finalText, suggestions: followUps }]);
      setStreamingText('');
      setChatLoading(false);
    }
  };

  const handleSendMessage = async (customMsg = null) => {
    const msg = customMsg || chatInput;
    if (!msg.trim() || chatLoading) return;
    
    // Guard against identical rapid-fire messages (debouncing)
    if (messages.length > 0 && messages[messages.length - 1].content === msg && messages[messages.length - 1].role === 'user') {
      return;
    }

    setChatInput('');
    // Remove suggestions from all prior messages when user sends new one
    const newMessages = [...messages.map(m => ({ ...m, suggestions: [] })), { role: 'user', content: msg }];
    setMessages(newMessages);
    await streamReply(msg, newMessages);
  };

  const QUICK_CHIPS = [
    { label: t('modal.quick_chips.eligibility') || 'Am I eligible?', icon: CheckCircleIcon, color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: t('modal.quick_chips.documents') || 'Documents needed', icon: DocumentCheckIcon, color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: t('modal.quick_chips.apply') || 'How to apply', icon: ArrowRightIcon, color: 'text-brand-primary', bg: 'bg-brand-primary/5' },
    { label: 'Key benefits', icon: StarIcon, color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Timeline', icon: ClockIcon, color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Subsidy amount', icon: CurrencyRupeeIcon, color: 'text-rose-600', bg: 'bg-rose-50' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 24 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 24 }}
        className="bg-white rounded-[2rem] shadow-premium max-w-4xl w-full max-h-[92vh] overflow-hidden flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="bg-white border-b border-slate-100 p-8 flex items-start justify-between gap-6">
          <div className="min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 bg-brand-primary/10 rounded-xl flex items-center justify-center border border-brand-primary/20">
                <CheckBadgeIcon className="w-6 h-6 text-brand-primary" />
              </div>
              <h2 className="font-black text-slate-900 text-xl tracking-tight leading-tight">{name}</h2>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {scheme.sector && <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{localizeOption(t, 'discovery.filter_options.sectors', scheme.sector)}</span>}
              <span className="text-slate-200">·</span>
              {scheme.state && <span className="text-[10px] font-bold text-brand-primary uppercase tracking-widest">{localizeOption(t, 'discovery.filter_options.states', scheme.state)}</span>}
              <span className="ml-2 flex items-center gap-1 px-1.5 py-0.5 bg-emerald-50 text-emerald-600 text-[8px] font-black rounded border border-emerald-100 uppercase tracking-tighter">
                <DocumentCheckIcon className="w-2.5 h-2.5" />
                DPIIT Verified Match
              </span>
            </div>
          </div>
          <button onClick={onClose} className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-400 hover:text-slate-600 rounded-full transition-colors">
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-8 pt-2 space-y-8 scroll-smooth">
          {/* AI Intelligence Box — Premium Karios Theme (White/Blue Glassmorphism) */}
          <div className="relative rounded-[2rem] overflow-hidden p-8 border border-white/60 shadow-premium bg-white/40 backdrop-blur-2xl group">
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-brand-primary/10 rounded-full blur-[100px] animate-pulse" />
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-brand-gold/5 rounded-full blur-[100px]" />
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-brand-primary to-blue-600 rounded-2xl flex items-center justify-center shadow-glow-sm transform group-hover:scale-110 transition-transform duration-500">
                    <SparklesIcon className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <h3 className="font-black text-lg uppercase tracking-tight text-slate-800 flex items-center gap-2">
                      {t('modal.intel_advisor')}
                      <span className="px-2 py-0.5 bg-brand-primary/10 text-brand-primary text-[10px] rounded-full border border-brand-primary/20">AGENTIC</span>
                    </h3>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                      <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-widest">{t('modal.grounded_tag')}</span>
                    </div>
                  </div>
                </div>
                <div className="px-3 py-1 bg-white/40 border border-white/60 rounded-lg backdrop-blur-sm shadow-inner group-hover:border-brand-primary/20 transition-colors">
                  <span className="text-[9px] font-black text-brand-primary uppercase tracking-[0.2em] animate-pulse">Live Reasoning</span>
                </div>
              </div>

              {/* Quick Chips */}
              <div className="flex flex-wrap gap-2 mb-8">
                {QUICK_CHIPS.map((chip, ci) => (
                  <button
                    key={ci}
                    onClick={() => handleSendMessage(t('modal.show_more_about', {
                      topic: chip.label,
                      defaultValue: `Show more about ${chip.label}`,
                    }))}
                    className={`flex items-center gap-2 px-3 py-2 ${chip.bg} border border-transparent rounded-xl hover:bg-white hover:border-brand-primary/20 hover:shadow-premium-sm transition-all text-[11px] font-bold ${chip.color} group`}
                  >
                    <chip.icon className="w-3.5 h-3.5" />
                    {chip.label}
                  </button>
                ))}
              </div>

              {/* Chat Thread */}
              <div className="space-y-4 mb-6 max-h-[360px] overflow-y-auto pr-2 custom-scrollbar">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`p-4 rounded-2xl text-[13px] font-medium leading-relaxed max-w-[92%] whitespace-pre-wrap transition-all ${
                      m.role === 'user' 
                        ? 'bg-gradient-to-br from-brand-primary to-blue-600 text-white rounded-tr-none shadow-premium border border-white/20' 
                        : 'bg-white/80 text-slate-700 rounded-tl-none border border-slate-200 backdrop-blur-sm shadow-sm'
                    }`}>
                      {/* Removed redundant small badge for cleaner UI */}
                      {m.role === 'ai' ? (
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            h3: ({ node, ...props }) => <h3 className="text-slate-800 font-black text-[14px] m-0 mb-2 flex items-center gap-2 bg-slate-50 p-2 rounded-lg border border-slate-100" {...props} />,
                            h4: ({ node, ...props }) => <h4 className="text-brand-primary font-bold text-[10px] m-0 mt-3 mb-1 uppercase tracking-widest flex items-center gap-1 bg-brand-primary/5 px-2 py-1 rounded border border-brand-primary/10 w-fit" {...props} />,
                            p: ({ node, ...props }) => <p className="m-0 mb-2 last:mb-0 leading-relaxed text-slate-600 text-[12.5px] font-medium" {...props} />,
                            ul: ({ node, ...props }) => <ul className="m-0 mb-2 pl-4 list-disc space-y-1" {...props} />,
                            ol: ({ node, ...props }) => <ol className="m-0 mb-2 pl-4 list-decimal space-y-1 text-[12.5px]" {...props} />,
                            li: ({ node, ...props }) => <li className="m-0 p-0 leading-relaxed marker:text-brand-primary text-slate-600 text-[12.5px] font-medium" {...props} />,
                            a: ({ node, ...props }) => (
                              <a className="text-brand-primary font-bold underline hover:text-brand-secondary" target="_blank" rel="noopener noreferrer" {...props} />
                            ),
                            strong: ({ node, ...props }) => <strong className="font-extrabold text-slate-900 underline decoration-brand-primary/30 underline-offset-2" {...props} />,
                            code: ({ node, inline, className, children, ...props }) => (
                              inline
                                ? <code className="px-1.5 py-0.5 rounded bg-slate-100 text-brand-primary font-bold border border-slate-200" {...props}>{children}</code>
                                : <pre className="bg-slate-900 text-white p-3 rounded-xl my-2 overflow-x-auto text-[11px]"><code className={className} {...props}>{children}</code></pre>
                            ),
                          }}
                        >
                          {m.content}
                        </ReactMarkdown>
                      ) : (
                        m.content
                      )}
                    </div>
                    {/* Follow-up suggestion chips */}
                    {m.role === 'ai' && m.suggestions?.length > 0 && !chatLoading && (
                      <div className="flex flex-wrap gap-2 mt-3 ml-1">
                        {m.suggestions.map((s, si) => (
                          <button
                            key={si}
                            onClick={() => handleSendMessage(s)}
                            className="text-[10px] font-bold px-4 py-2 rounded-xl bg-brand-primary/10 border border-brand-primary/20 text-brand-primary hover:bg-brand-primary hover:text-white transition-all shadow-sm backdrop-blur-sm"
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}

                {/* Live streaming bubble */}
                {streamingText && (
                  <div className="flex justify-start">
                    <div className="bg-white/90 text-slate-700 rounded-2xl rounded-tl-none border border-slate-200 backdrop-blur-md shadow-lg p-4 max-w-[92%]">
                      <div className="flex items-center gap-2 mb-2 bg-brand-primary/5 w-fit px-2 py-0.5 rounded-md border border-brand-primary/10">
                        <div className="w-1 h-3 bg-brand-primary rounded-full animate-bounce" />
                        <span className="text-[9px] font-black text-brand-primary uppercase tracking-widest">Karios Thinking…</span>
                      </div>
                      <p className="text-[13px] font-medium leading-relaxed text-slate-700 whitespace-pre-wrap m-0">
                        {streamingText}
                        <span className="inline-block w-1.5 h-4 bg-brand-primary ml-1 animate-pulse align-middle rounded-sm" />
                      </p>
                    </div>
                  </div>
                )}

                {/* Typing dots (before streaming starts) */}
                {chatLoading && !streamingText && (
                  <div className="flex justify-start">
                    <div className="bg-slate-50 p-4 rounded-2xl rounded-tl-none border border-slate-100 shadow-sm">
                      <div className="flex gap-1.5">
                        <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-pulse" />
                        <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-pulse [animation-delay:0.2s]" />
                        <div className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-pulse [animation-delay:0.4s]" />
                      </div>
                    </div>
                  </div>
                )}
                {/* Auto-scroll sentinel */}
                <div ref={chatEndRef} />
              </div>


              {/* Input Area */}
              <div className="relative group/input">
                <input
                  type="text"
                  placeholder={t('modal.chat_placeholder', { defaultValue: 'Ask about steps, documents, or eligibility...' })}
                  className="w-full bg-slate-100/50 border border-slate-200 rounded-2xl px-6 py-4 pr-16 text-sm font-bold placeholder:text-slate-400 outline-none focus:bg-white focus:border-brand-primary/50 focus:shadow-glow-sm transition-all text-slate-800"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSendMessage(); }}
                />
                <button 
                  onClick={() => handleSendMessage()}
                  disabled={chatLoading}
                  className="absolute right-2 top-1/2 -translate-y-1/2 w-11 h-11 bg-brand-primary text-white rounded-xl flex items-center justify-center hover:bg-brand-secondary hover:scale-105 active:scale-95 transition-all disabled:opacity-50 shadow-glow-sm"
                >
                  <PaperAirplaneIcon className="w-5 h-5 -rotate-45 mb-0.5 ml-0.5" />
                </button>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
            {/* Overview Section */}
            <div className="space-y-3">
              <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">{t('modal.overview')}</h4>
              <p className="text-sm text-slate-600 font-medium leading-relaxed">{desc}</p>
            </div>

            {/* Eligibility Section */}
            {elig && (
              <div className="space-y-3">
                <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">{t('modal.eligibility')}</h4>
                <div className="p-4 bg-slate-50 rounded-[1.25rem] border border-slate-100 italic text-slate-600 text-[13px] leading-relaxed">
                  "{elig}"
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-8 bg-white border-t border-slate-100 flex gap-4">
          <button
            onClick={() => onSave(scheme)}
            className={`flex-[0.4] py-4 rounded-2xl font-black text-sm uppercase tracking-widest transition-all flex items-center justify-center gap-2 border-2 ${
              isSaved ? 'bg-emerald-50 border-emerald-500 text-emerald-600' : 'bg-slate-50 border-slate-100 text-slate-400 hover:bg-slate-100'
            }`}
          >
            {isSaved ? <BookmarkSolid className="w-5 h-5" /> : <BookmarkIcon className="w-5 h-5" />}
            {isSaved ? t('common.shortlisted') : t('common.shortlist')}
          </button>
          <a
            href={website || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 bg-brand-primary text-white py-4 rounded-2xl font-black text-sm uppercase tracking-widest shadow-glow hover:shadow-glow-sm hover:-translate-y-0.5 transition-all flex items-center justify-center gap-3"
          >
            {t('modal.official_portal')}
            <ArrowTopRightOnSquareIcon className="w-5 h-5" />
          </a>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default function SchemeDiscovery({
  userProfile,
  userEmail = '',
  savedSchemes = [],
  lastSelectedSchemeId = '',
  onSavedSchemesChange,
  onLastSelectedSchemeChange,
}) {
  const { t, i18n } = useTranslation();
  const languageCode = normalizeLanguageCode(i18n.language);
  const [schemes, setSchemes] = useState([]);
  const [aiSummary, setAiSummary] = useState('');
  const [totalSchemes, setTotalSchemes] = useState(383);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState(ALL_SECTORS);
  const [state, setState] = useState(ALL_STATES);
  const [entity, setEntity] = useState(ALL_ENTITIES);
  const [sortBy, setSortBy] = useState('match');
  const [selectedScheme, setSelectedScheme] = useState(null);
  const [filterOpen, setFilterOpen] = useState(true);
  const [translating, setTranslating] = useState(false);
  // ── NEW: Server Status & API Error States ────────────────────────────────
  const [serverStatus, setServerStatus] = useState('checking');
  const [apiError, setApiError] = useState(null);

  // Track changes to avoid redundant full-reloads
  const prevLangRef = useRef(i18n.language);
  const prevProfileRef = useRef(JSON.stringify(userProfile));

  // ── Toast feedback ────────────────────────────────────────────────────────
  const [toast, setToast] = useState(null);
  const toastTimer = useRef(null);
  const schemesRef = useRef([]);
  const showToast = useCallback((message, type = 'success') => {
    clearTimeout(toastTimer.current);
    setToast({ message, type });
    toastTimer.current = setTimeout(() => setToast(null), 3000);
  }, []);

  // ── Persist saved schemes to backend DB ───────────────────────────────────
  const persistSchemes = useCallback(async (updatedSchemes) => {
    const email = userEmail || userProfile?.email;
    if (!email) return;
    try {
      const res = await fetch(`${API_BASE}/v1/schemes/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, schemes: updatedSchemes }),
      });
      if (!res.ok) throw new Error(`Save failed: ${res.status}`);
    } catch (err) {
      console.warn('Could not persist schemes:', err);
      showToast('Could not save to server. Check your connection.', 'error');
    }
  }, [userEmail, userProfile?.email, showToast]);

  const sectorOptions = useMemo(() => localizeOptions(t, 'discovery.filter_options.sectors', SECTORS), [languageCode, t]);
  const stateOptions = useMemo(() => localizeOptions(t, 'discovery.filter_options.states', STATES_FILTER), [languageCode, t]);
  const entityOptions = useMemo(() => localizeOptions(t, 'discovery.filter_options.entities', ENTITY_FILTER), [languageCode, t]);

  const resetFilters = useCallback(() => {
    setSearch('');
    setSector(ALL_SECTORS);
    setState(ALL_STATES);
    setEntity(ALL_ENTITIES);
  }, []);

  const fetchSchemes = useCallback(async (isForceFull = false) => {
    const isLangChangeOnly = !isForceFull && 
                             schemes.length > 0 && 
                             prevLangRef.current !== i18n.language && 
                             prevProfileRef.current === JSON.stringify(userProfile);

    if (isLangChangeOnly) {
      setTranslating(true);
      try {
        const res = await fetch(`${API_BASE}/v1/translate_schemes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: AbortSignal.timeout(120000),
          body: JSON.stringify({
            schemes: schemes,
            language: i18n.language,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          setSchemes(data.schemes || []);
          prevLangRef.current = i18n.language;
          return;
        }
      } catch (err) {
        console.warn('Translate-only failed, falling back to full fetch', err);
      } finally {
        setTranslating(false);
      }
    }

    setLoading(true);
    try {
      const profile = userProfile || {};
      // Build a meaningful query even when profile fields are empty
      const isEmptyProfile = Object.keys(profile).length === 0;
      const fallbackDescription = isEmptyProfile 
        ? 'new small business startup general enterprise entrepreneur India MSME'
        : [
            profile.sector ? `${profile.sector} business` : '',
            profile.entityType || '',
            profile.state ? `located in ${profile.state}` : '',
            profile.turnover ? `with turnover ${profile.turnover}` : '',
          ].filter(Boolean).join(', ') || 'general business India';

      console.log("🚀 CALLING /v1/recommend:", { 
        profile: userProfile || {}, 
        timestamp: new Date().toISOString(),
        hasProfile: !!userProfile 
      });
      
      console.log("🚀 CALLING /v1/recommend with profile:", {
        isEmpty: Object.keys(profile).length === 0,
        profile,
        timestamp: new Date().toISOString()
      });
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 12000);
      
      const requestBody = {
        sector: profile.sector || '',
        state: profile.state || '',
        entityType: profile.entityType || '',
        turnover: profile.turnover || '',
        businessDescription: profile.businessDescription || fallbackDescription,
        language: i18n.language,
      };
      
      const res = await fetch(`${API_BASE}/v1/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify(requestBody),
      });
      
      console.log(`📡 Response status: ${res.status} ${res.statusText}`);
      if (!res.ok) {
        const errText = await res.text();
        console.error('❌ API ERROR details:', { status: res.status, errText });
        throw new Error(`HTTP ${res.status}: ${errText}`);
      }
      
      const data = await res.json();
      console.log("✅ API SUCCESS:", {
        schemeCount: data.schemes?.length || 0,
        summary: data.summary,
        profileUsed: requestBody
      });
      setSchemes(data.schemes || []);
      schemesRef.current = data.schemes || [];
      setAiSummary(data.summary || '');
      setTotalSchemes(data.total_count || data.totalSchemes || 383);
      prevLangRef.current = i18n.language;
      prevProfileRef.current = JSON.stringify(userProfile);
    } catch (err) {
      console.error('[SchemeDiscovery] fetchSchemes FAILED:', err);
      
      // Server down → fallback + error state
      setApiError(`Failed to load schemes: ${err.message}`);
      console.log("⚠️ LOADING FALLBACK SCHEMES");
      const fallbackData = buildFallbackSchemes(languageCode);
      setSchemes(fallbackData);
      setTotalSchemes(fallbackData.length);
      setAiSummary('🔌 Server offline - using demo schemes. Run `python ai_scheme_server.py`');
    } finally {
      setLoading(false);
    }
  }, [languageCode, userProfile, i18n.language]);

  // ── Enhanced Server health check with verbose logging ─────────────────────
  useEffect(() => {
    const testServer = async () => {
      try {
        console.log('🩺 Testing server health at', API_BASE);
        const res = await fetch(`${API_BASE}/health`, { 
          signal: AbortSignal.timeout(5000),
          cache: 'no-store'
        });
        console.log('🩺 Health response:', res.status, await res.text());
        const status = res.ok ? 'live' : 'error';
        setServerStatus(status);
      } catch (err) {
        console.error('🩺 Server health FAILED:', err.name, err.message);
        setServerStatus('down');
      }
    };
    testServer();
  }, []);

  useEffect(() => {
    console.log("🔥 PAGE LOADED - Profile state:", {
      hasProfile: !!userProfile,
      profileKeys: userProfile ? Object.keys(userProfile) : [],
      userProfile
    });
    fetchSchemes(true);
  }, []);

  const filteredSchemes = schemes
    .filter(s => {
      const name = (s.scheme_name || s.Scheme_Name || '').toLowerCase();
      const description = (s.description || s.Scheme_Description || '').toLowerCase();
      const entityValue = s.entity_type || s.entityType || s.legal_entity_type || s.entity || '';
      const searchValue = search.toLowerCase();
      const secMatch = matchesSelectedOption(sector, ALL_SECTORS, s.sector);
      const stateMatch = matchesSelectedOption(state, ALL_STATES, s.state);
      const entityMatch = matchesSelectedOption(entity, ALL_ENTITIES, entityValue);
      const searchMatch = !searchValue || name.includes(searchValue) || description.includes(searchValue);
      return secMatch && stateMatch && entityMatch && searchMatch;
    })
    .sort((a, b) => {
      if (sortBy === 'match') return (b.final_rank_score || b.ai_confidence || 0) - (a.final_rank_score || a.ai_confidence || 0);
      if (sortBy === 'deadline') return (a.timeline_days || 999) - (b.timeline_days || 999);
      return 0;
    });

  const toggleSave = useCallback(async (scheme) => {
    const id = getSchemeId(scheme);
    const isCurrentlySaved = savedSchemes.some((item) => getSchemeId(item) === id);
    const updated = isCurrentlySaved
      ? savedSchemes.filter((item) => getSchemeId(item) !== id)
      : [...savedSchemes, scheme];
    const preferred = updated.find((item) => getSchemeId(item) === id) || updated[0];
    const nextSelectedSchemeId = preferred ? getSchemeId(preferred) : '';

    // 1. Show toast immediately
    const name = scheme.scheme_name || scheme.Scheme_Name || 'Scheme';
    showToast(
      isCurrentlySaved ? `Removed "${name}" from shortlist` : `"${name}" saved to shortlist`,
      isCurrentlySaved ? 'info' : 'success'
    );

    // 2. Update parent state (triggers persistWorkspaceState in App.jsx which saves to backend)
    // Do NOT also call persistSchemes — that causes two concurrent saves that race each other
    // and the second one reverts the first optimistic update.
    onSavedSchemesChange?.(updated, nextSelectedSchemeId);
  }, [savedSchemes, onSavedSchemesChange, showToast]);

  const isSaved = useCallback(
    (scheme) => savedSchemes.some((item) => getSchemeId(item) === getSchemeId(scheme)),
    [savedSchemes]
  );

  return (
    <div className="space-y-6">

      {/* ── Save Toast ─────────────────────────────────────────── */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className={`fixed bottom-6 right-6 z-[200] flex items-center gap-3 px-5 py-3 rounded-2xl shadow-xl text-sm font-bold border backdrop-blur-md ${
              toast.type === 'success'
                ? 'bg-emerald-900/90 border-emerald-500/30 text-emerald-300'
                : toast.type === 'error'
                ? 'bg-red-900/90 border-red-500/30 text-red-300'
                : 'bg-slate-800/90 border-white/10 text-slate-300'
            }`}
          >
            {toast.type === 'success' && <BookmarkSolid className="w-4 h-4 text-emerald-400 flex-shrink-0" />}
            {toast.message}
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── ADVANCED HEADING SECTION ─────────────────────────────── */}
      <div className="relative rounded-3xl overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8 shadow-xl border border-white/5">
        {/* Decorative glows */}
        <div className="absolute -top-16 -right-16 w-64 h-64 bg-brand-primary/20 rounded-full blur-[80px] pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-blue-500/10 rounded-full blur-[60px] pointer-events-none" />

        <div className="relative z-10 flex flex-col gap-6">
          {/* Title row */}
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                <span className="text-[10px] font-black text-emerald-400 uppercase tracking-[0.2em]">{t('discovery.ai_matching_badge')}</span>
              </div>
              <h2 className="text-2xl font-black text-white tracking-tight leading-tight">
                {t('discovery.hero_title')}
              </h2>
              <p className="text-slate-400 text-sm font-medium mt-1">
                {t('discovery.hero_subtitle_start')}<span className="text-brand-primary font-bold">{totalSchemes}+ schemes</span>{t('discovery.hero_subtitle_end')}
              </p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-[11px] font-bold text-white">
                <SparklesIcon className="w-3.5 h-3.5 text-brand-primary" />
                {t('common.matches_count', { count: filteredSchemes.length })}
              </span>
              <button
                onClick={() => { resetFilters(); fetchSchemes(true); }}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-[11px] font-bold transition-all ${
                  translating ? 'bg-slate-700 border-slate-600 text-slate-400 cursor-wait' : 'bg-brand-primary/10 border-brand-primary/20 text-brand-primary hover:bg-brand-primary/20'
                }`}
                disabled={translating}
              >
                <ArrowPathIcon className={`w-3.5 h-3.5 ${translating ? 'animate-spin' : ''}`} />
                {translating ? t('common.translating') || 'Translating...' : t('common.re_run') || 'Re-run AI'}
              </button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-12 py-3.5 text-sm text-white placeholder-slate-500 font-medium focus:outline-none focus:border-brand-primary/50 focus:bg-white/8 transition-all"
              placeholder={t('discovery.search_placeholder') || 'Search schemes, sectors or keywords...'}
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors">
                <XMarkIcon className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Inline Filter Chips Row */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex items-center gap-1.5 text-[10px] font-black text-slate-500 uppercase tracking-widest">
              <FunnelIcon className="w-3.5 h-3.5" /> {t('common.filter')}
            </span>

            {/* Sector */}
            <div className="relative">
              <select
                className="appearance-none pl-3 pr-8 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 hover:border-white/20 focus:outline-none focus:border-brand-primary/50 transition-all cursor-pointer"
                value={sector}
                onChange={e => setSector(e.target.value)}
              >
                {sectorOptions.map(o => (
                  <option key={o.value} value={o.value} className="bg-slate-800 text-white">{o.label}</option>
                ))}
              </select>
              <BriefcaseIcon className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400" />
            </div>

            {/* State */}
            <div className="relative">
              <select
                className="appearance-none pl-3 pr-8 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 hover:border-white/20 focus:outline-none focus:border-brand-primary/50 transition-all cursor-pointer"
                value={state}
                onChange={e => setState(e.target.value)}
              >
                {stateOptions.map(o => (
                  <option key={o.value} value={o.value} className="bg-slate-800 text-white">{o.label}</option>
                ))}
              </select>
              <MapPinIcon className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400" />
            </div>

            {/* Entity */}
            <div className="relative">
              <select
                className="appearance-none pl-3 pr-8 py-2 rounded-xl bg-white/5 border border-white/10 text-xs font-bold text-white hover:bg-white/10 hover:border-white/20 focus:outline-none focus:border-brand-primary/50 transition-all cursor-pointer"
                value={entity}
                onChange={e => setEntity(e.target.value)}
              >
                {entityOptions.map(o => (
                  <option key={o.value} value={o.value} className="bg-slate-800 text-white">{o.label}</option>
                ))}
              </select>
              <CheckBadgeIcon className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-slate-400" />
            </div>

            {/* Apply button */}
            <button
              onClick={fetchSchemes}
              className="px-4 py-2 rounded-xl bg-brand-primary text-white text-xs font-black hover:bg-brand-primary/90 transition-all shadow-sm"
            >
              {t('common.apply')}
            </button>

            {/* Active filter tags */}
            {sector !== ALL_SECTORS && (
              <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-500/15 border border-blue-400/20 text-[11px] font-bold text-blue-300">
                {sector}
                <button onClick={() => setSector(ALL_SECTORS)} className="hover:text-white"><XMarkIcon className="w-3 h-3" /></button>
              </span>
            )}
            {state !== ALL_STATES && (
              <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/15 border border-emerald-400/20 text-[11px] font-bold text-emerald-300">
                {state}
                <button onClick={() => setState(ALL_STATES)} className="hover:text-white"><XMarkIcon className="w-3 h-3" /></button>
              </span>
            )}
            {entity !== ALL_ENTITIES && (
              <span className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-purple-500/15 border border-purple-400/20 text-[11px] font-bold text-purple-300">
                {entity}
                <button onClick={() => setEntity(ALL_ENTITIES)} className="hover:text-white"><XMarkIcon className="w-3 h-3" /></button>
              </span>
            )}

            {/* Saved count pill */}
            {savedSchemes.length > 0 && (
              <span className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 border border-emerald-400/20 text-[11px] font-bold text-emerald-400">
                <BookmarkSolid className="w-3.5 h-3.5" />
                {savedSchemes.length} {t('common.shortlisted')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── RESULTS ──────────────────────────────────────────────── */}
      <div className="space-y-5">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              {serverStatus === 'live' && (
                <span className="px-2 py-1 bg-emerald-100 text-emerald-700 text-xs font-bold rounded-full">
                  🟢 Live
                </span>
              )}
              {serverStatus === 'down' && (
                <span className="px-2 py-1 bg-orange-100 text-orange-700 text-xs font-bold rounded-full animate-pulse">
                  🟡 Offline - Demo Mode
                </span>
              )}
              <p className="text-slate-500 font-semibold text-sm">
                {loading ? t('discovery.analyzing') : t('discovery.showing_full', { count: filteredSchemes.length, total: totalSchemes })}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="label-xs">{t('common.sort')}:</span>
              <select
                className="text-sm font-bold text-slate-700 bg-transparent outline-none cursor-pointer border border-slate-200 rounded-lg px-3 py-1.5"
                value={sortBy}
                onChange={e => setSortBy(e.target.value)}
              >
                <option value="match">{t('discovery.best_match') || 'Best Match'}</option>
                <option value="deadline">{t('discovery.deadline') || 'Deadline'}</option>
              </select>
            </div>
          </div>
          
          {/* AI Strategic Analyst Box - 'Perfect Sooper' Upgrade */}
          <AnimatePresence>
            {aiSummary && !loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="relative overflow-hidden p-6 rounded-3xl bg-white border border-brand-primary/10 shadow-premium-sm group"
              >
                <div className="absolute top-0 right-0 w-32 h-32 bg-brand-primary/5 rounded-full -mr-16 -mt-16 blur-3xl" />
                <div className="flex items-center gap-5">
                  <div className="w-12 h-12 bg-gradient-to-br from-brand-primary to-blue-600 rounded-2xl flex items-center justify-center shadow-glow-sm">
                    <SparklesIcon className="w-7 h-7 text-white animate-pulse" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-[10px] font-black text-brand-primary uppercase tracking-[0.2em] mb-1">Karios Strategic Analyst</h3>
                    <p className="text-sm text-slate-700 font-bold leading-relaxed">{aiSummary}</p>
                  </div>
                  <div className="px-3 py-1 bg-emerald-50 text-emerald-600 text-[10px] font-black rounded-lg border border-emerald-100 uppercase tracking-widest whitespace-nowrap">
                    Live Engine
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {translating && (
              <motion.div 
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-4 p-3 bg-brand-primary/10 border border-brand-primary/20 rounded-xl flex items-center justify-center gap-3 text-brand-primary font-bold text-sm"
              >
                <ArrowPathIcon className="w-4 h-4 animate-spin" />
                {t('discovery.translating_status', 'Translating scheme details...')}
              </motion.div>
            )}
          </AnimatePresence>

          {loading ? (
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
              {[...Array(6)].map((_, i) => <SchemeCardSkeleton key={i} />)}
            </div>
          ) : (
            <div className={`grid grid-cols-1 xl:grid-cols-2 gap-5 transition-opacity duration-300 ${translating ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
              <AnimatePresence>
                {filteredSchemes.map((scheme, i) => {
                  const name = t(`schemes.${scheme.scheme_id}.name`, {
                    defaultValue: scheme.scheme_name || scheme.Scheme_Name || t('discovery.unknown_scheme', { defaultValue: 'Unknown Scheme' }),
                  });
                  const desc = t(`schemes.${scheme.scheme_id}.description`, {
                    defaultValue: scheme.description || scheme.Scheme_Description || t('discovery.no_description', 'No description available.'),
                  });
                  const saved = isSaved(scheme);

                  return (
                    <motion.div
                      key={scheme.scheme_id || i}
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ delay: i * 0.04, duration: 0.3 }}
                      className={`scheme-card ${saved ? 'scheme-card-selected' : ''}`}
                      onClick={() => {
                        setSelectedScheme(scheme);
                        onLastSelectedSchemeChange?.(getSchemeId(scheme));
                      }}
                    >
                      <div className="flex justify-between items-start gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-start gap-2 mb-2">
                            <CheckBadgeIcon className="w-5 h-5 text-brand-primary flex-shrink-0 mt-0.5" />
                            <h4 className="font-extrabold text-slate-900 text-sm leading-tight group-hover:text-brand-primary transition-colors line-clamp-2">{name}</h4>
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            {scheme.sector && (
                              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                                <BriefcaseIcon className="w-3 h-3" /> {localizeOption(t, 'discovery.filter_options.sectors', scheme.sector)}
                              </span>
                            )}
                            {scheme.state && (
                              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1">
                                <MapPinIcon className="w-3 h-3" /> {localizeOption(t, 'discovery.filter_options.states', scheme.state)}
                              </span>
                            )}
                          </div>
                        </div>
                        {scheme.ai_confidence && <MatchBadge score={scheme.ai_confidence} />}
                      </div>

                      {desc && (
                        <p className="text-xs text-slate-500 font-medium leading-relaxed line-clamp-2">{desc}</p>
                      )}

                      {/* Match Reasons Tags */}
                      {scheme.match_reasons?.length > 0 && (
                        <div className="flex flex-wrap gap-2 pt-2">
                          {scheme.match_reasons.map((r, ri) => (
                            <span key={ri} className="flex items-center gap-1.5 px-3 py-1 bg-slate-50 text-slate-500 text-[10px] font-black rounded-lg border border-slate-100 uppercase tracking-widest shadow-sm">
                              <div className="w-1 h-1 bg-brand-primary rounded-full" />
                              {r}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {scheme.timeline_days && (
                            <span className="flex items-center gap-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                              <ClockIcon className="w-3.5 h-3.5" />
                              {t('discovery.processing_days', {
                                days: scheme.timeline_days,
                                defaultValue: `~${scheme.timeline_days}d processing`,
                              })}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={e => { e.stopPropagation(); toggleSave(scheme); }}
                            className={`p-2 rounded-xl transition-all ${saved ? 'text-emerald-600 bg-emerald-50' : 'text-slate-400 hover:text-brand-primary hover:bg-brand-primary/5'}`}
                          >
                            {saved ? <BookmarkSolid className="w-4 h-4" /> : <BookmarkIcon className="w-4 h-4" />}
                          </button>
                          <button className="btn-primary text-xs px-4 py-2" onClick={e => { e.stopPropagation(); setSelectedScheme(scheme); }}>
                            {t('common.view_details')} <ArrowRightIcon className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}

          {!loading && filteredSchemes.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <MagnifyingGlassIcon className="w-12 h-12 text-slate-300 mb-4" />
              <h3 className="font-bold text-slate-600 mb-2">{t('discovery.no_matches')}</h3>
              <p className="text-sm text-slate-400 font-medium">{t('discovery.search_hint', 'Try clearing filters or adjusting your search query.')}</p>
              <button onClick={resetFilters} className="btn-secondary mt-4">
                {t('common.clear_all') || 'Clear All Filters'}
              </button>
            </div>
          )}
        </div>

      {/* Scheme Detail Modal */}
      <AnimatePresence>
        {selectedScheme && (
          <SchemeDetailModal
            scheme={selectedScheme}
            onClose={() => setSelectedScheme(null)}
            onSave={toggleSave}
            isSaved={isSaved(selectedScheme)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
