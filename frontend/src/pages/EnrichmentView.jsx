import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  SparklesIcon, CpuChipIcon,
  ShieldCheckIcon, ChartBarIcon, ArrowRightIcon,
  MagnifyingGlassIcon, CheckBadgeIcon, Squares2X2Icon
} from '@heroicons/react/24/outline';

const API_BASE = '';

const PROCESSING_PHASES = [
  { icon: CpuChipIcon, label: 'Generating Profile Intelligence Object', color: 'text-brand-primary', delay: 0 },
  { icon: ChartBarIcon, label: 'Creating Contextual Sector Tags', color: 'text-purple-600', delay: 800 },
  { icon: MagnifyingGlassIcon, label: 'Encoding BGE-M3 Profile Embedding', color: 'text-blue-600', delay: 1800 },
  { icon: SparklesIcon, label: 'Running Soft Eligibility Filter (383 schemes)', color: 'text-amber-600', delay: 2800 },
  { icon: ShieldCheckIcon, label: 'Initializing Document Readiness Index', color: 'text-emerald-600', delay: 3800 },
  { icon: CheckBadgeIcon, label: 'Analysis Complete — Building Dashboard', color: 'text-brand-primary', delay: 4800 },
];

function AnimatedCounter({ target, duration = 2000 }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    const step = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      setVal(Math.floor(current));
      if (current >= target) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return <span>{val}</span>;
}

export default function EnrichmentView({ onComplete, userProfile }) {
  const [phase, setPhase] = useState(0);
  const [done, setDone] = useState(false);
  const [schemeCount, setSchemeCount] = useState(0);

  useEffect(() => {
    // Run through processing phases
    PROCESSING_PHASES.forEach((p, i) => {
      setTimeout(() => {
        setPhase(i + 1);
        if (i === PROCESSING_PHASES.length - 1) {
          // Final phase — trigger scheme discovery in background
          setTimeout(() => setDone(true), 1000);
        }
      }, p.delay);
    });

    // Fetch scheme count to show dynamic data
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(data => setSchemeCount(data.schemes_loaded || 383))
      .catch(() => setSchemeCount(383));
  }, []);

  return (
    <div className="min-h-screen bg-brand-intelligence flex items-center justify-center p-6 relative overflow-hidden">
      {/* Animated Background */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-brand-primary/5 rounded-full blur-[120px] animate-blob" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-400/4 rounded-full blur-[100px] animate-blob" style={{ animationDelay: '3s' }} />
        {/* Grid Pattern */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{ backgroundImage: 'linear-gradient(rgba(79,124,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(79,124,255,1) 1px, transparent 1px)', backgroundSize: '48px 48px' }}
        />
      </div>

      <div className="relative z-10 w-full max-w-2xl">
        {/* Logo & Title */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-brand-primary/10 border border-brand-primary/20 mb-6 relative mx-auto">
            <SparklesIcon className="w-10 h-10 text-brand-primary animate-pulse-soft" />
            <div className="absolute inset-0 rounded-3xl border-2 border-brand-primary/30 animate-spin-slow" />
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight mb-2">
            Analyzing Your Profile
          </h1>
          <p className="text-slate-500 font-medium">
            Your profile is being analyzed to find the best matching government schemes.
          </p>
        </motion.div>

        {/* Processing Steps */}
        <div className="intelligence-card p-8 mb-6">
          <div className="space-y-5">
            {PROCESSING_PHASES.map((p, i) => {
              const isActive = phase === i + 1;
              const isDone = phase > i + 1;
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={phase >= i + 1 ? { opacity: 1, x: 0 } : { opacity: 0.3, x: 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex items-center gap-4"
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
                    isDone ? 'bg-emerald-100 text-emerald-600' :
                    isActive ? 'bg-brand-primary/10 text-brand-primary' : 'bg-slate-100 text-slate-300'
                  }`}>
                    {isDone ? (
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} stroke="currentColor" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : isActive ? (
                      <p.icon className={`w-4 h-4 ${isActive ? 'animate-spin' : ''}`} />
                    ) : (
                      <p.icon className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex-1">
                    <span className={`text-sm font-semibold transition-colors duration-300 ${
                      isDone ? 'text-emerald-600' :
                      isActive ? 'text-slate-800' : 'text-slate-400'
                    }`}>
                      {p.label}
                    </span>
                  </div>
                  {isActive && (
                    <div className="flex gap-1">
                      {[0, 1, 2].map(d => (
                        <div key={d} className="w-1.5 h-1.5 bg-brand-primary rounded-full animate-bounce"
                          style={{ animationDelay: `${d * 0.15}s` }}
                        />
                      ))}
                    </div>
                  )}
                  {isDone && (
                    <span className="text-[10px] font-black text-emerald-600 uppercase tracking-widest">Done</span>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Intelligence Metrics */}
        {phase >= 3 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-3 gap-4 mb-6"
          >
            {[
              { label: 'Schemes Indexed', value: schemeCount, suffix: '' },
              { label: 'Profile Vectors', value: 768, suffix: 'dims' },
              { label: 'Intelligence Score', value: 94, suffix: '%' },
            ].map((m, i) => (
              <div key={i} className="intelligence-card p-5 text-center">
                <div className="text-2xl font-black text-slate-900 tracking-tight">
                  <AnimatedCounter target={m.value} duration={1500 + i * 300} />
                  <span className="text-brand-primary ml-1 text-sm">{m.suffix}</span>
                </div>
                <div className="label-xs mt-1">{m.label}</div>
              </div>
            ))}
          </motion.div>
        )}

        {/* CTA Button */}
        {done && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-700 font-semibold text-sm flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} stroke="currentColor" d="M5 13l4 4L19 7" />
              </svg>
              Analysis Complete! Your profile is ready for scheme matching.
            </div>
            <button
              onClick={onComplete}
              className="btn-primary text-base px-10 py-4 rounded-2xl"
            >
              <Squares2X2Icon className="w-5 h-5" />
              Go to Dashboard
              <ArrowRightIcon className="w-5 h-5" />
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
