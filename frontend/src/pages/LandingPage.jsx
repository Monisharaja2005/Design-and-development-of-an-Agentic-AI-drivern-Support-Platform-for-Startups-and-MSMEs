import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRightIcon, ShieldCheckIcon, SparklesIcon,
  CheckCircleIcon, GlobeAltIcon, CurrencyRupeeIcon, ChartBarIcon,
  UserGroupIcon, DocumentCheckIcon, StarIcon, BuildingOfficeIcon,
  MagnifyingGlassIcon, ClockIcon
} from '@heroicons/react/24/outline';

const features = [
  {
    icon: SparklesIcon,
    title: 'AI Scheme Discovery',
    desc: 'Semantic search across government schemes using advanced embeddings.',
    color: 'text-brand-primary',
    bg: 'bg-brand-primary/8',
  },
  {
    icon: ChartBarIcon,
    title: 'Semantic Scheme Discovery',
    desc: 'Government schemes indexed with BGE-M3 dense embeddings. Get matches based on meaning, not just keywords.',
    color: 'text-purple-600',
    bg: 'bg-purple-50',
  },
  {
    icon: DocumentCheckIcon,
    title: 'Document Validation',
    desc: 'AI-powered OCR validation checks your documents against exact scheme requirements — before you apply.',
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
  },
  {
    icon: CurrencyRupeeIcon,
    title: 'Multi-Factor Ranking',
    desc: 'Schemes ranked by eligibility confidence, subsidy %, funding size, urgency, and your personalization signals.',
    color: 'text-amber-600',
    bg: 'bg-amber-50',
  },
  {
    icon: GlobeAltIcon,
    title: 'RAG-Powered Chat Advisor',
    desc: 'Ask anything about schemes, eligibility, or application strategy. Grounded answers from the Knowledge Base.',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
  },
  {
    icon: UserGroupIcon,
    title: 'Multi-Language Support',
    desc: 'Platform available in 16 Indian languages with localized scheme names and guidance for every region.',
    color: 'text-rose-600',
    bg: 'bg-rose-50',
  },
];

const stats = [
  { value: 'AI', label: 'Eligibility Matching', icon: '🎯' },
  { value: 'Smart', label: 'Document Verification', icon: '📄' },
  { value: 'All', label: 'India Coverage', icon: '🌏' },
];

const testimonials = [
  {
    name: 'Meena Agarwal',
    role: 'Founder, TextilePro MSME',
  text: 'The platform found 8 schemes I never knew existed and pre-validated all my documents. Got PMEGP approval in 3 weeks.',
    avatar: 'M',
    rating: 5,
  },
  {
    name: 'Rajesh Kumar',
    role: 'CEO, AgriTech Startup',
    text: 'The AI chat advisor explained every eligibility criterion in Hindi. Made the entire government funding process clear.',
    avatar: 'R',
    rating: 5,
  },
  {
    name: 'Ananya Krishnan',
    role: 'Director, EduTech Pvt Ltd',
    text: 'Multi-factor ranking put Startup India Seed Fund as #1 for us. Score was 96% match. We applied the same week.',
    avatar: 'A',
    rating: 5,
  },
];

export default function LandingPage({ onStart }) {
  const [hoveredFeature, setHoveredFeature] = useState(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-emerald-50 overflow-x-hidden">
      {/* Ambient Background */}

      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] bg-brand-primary/5 rounded-full blur-[120px] animate-blob" />
        <div className="absolute top-[20%] right-[-10%] w-[50%] h-[50%] bg-purple-400/4 rounded-full blur-[100px] animate-blob" style={{ animationDelay: '3s' }} />
        <div className="absolute bottom-[-20%] left-[30%] w-[50%] h-[50%] bg-emerald-400/4 rounded-full blur-[120px] animate-blob" style={{ animationDelay: '6s' }} />
      </div>

      {/* Top Nav */}
      <header className="relative z-10 flex items-center justify-between px-8 md:px-16 py-6">
        <div className="flex items-center gap-3">
          <span className="font-plus font-black text-xl text-slate-900 tracking-tight">AI Scheme Discovery Platform</span>
          <span className="hidden md:inline-block px-2.5 py-1 bg-slate-100 text-slate-700 text-[9px] font-black uppercase tracking-wider rounded-full border border-slate-200">Platform</span>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={onStart}
            className="hidden md:inline-flex text-sm font-semibold text-slate-600 hover:text-slate-900 transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={onStart}
            className="btn-primary text-sm px-5 py-2.5"
          >
            Get Started Free
            <ArrowRightIcon className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 pt-16 pb-24 px-8 md:px-16 max-w-7xl mx-auto">
        <div className="text-center max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 border border-slate-200 rounded-full text-xs font-bold text-slate-700 shadow-sm mb-8">
              <span className="glow-dot" />
              AI Scheme Discovery + Document Validation + Multi-Language Support
            </div>

            <h1 className="text-5xl md:text-7xl font-black text-slate-900 leading-[1.05] tracking-tight mb-6">
              India's Most Advanced{' '}
              <span className="gradient-text">Funding Advisor</span>{' '}
              for MSMEs
            </h1>

            <p className="text-lg md:text-xl text-slate-500 font-medium leading-relaxed mb-10 max-w-2xl mx-auto">
              This platform intelligently analyzes business profiles and automatically identifies relevant government schemes, grants, and subsidies available for MSMEs across India. Using advanced AI-driven analysis and data matching, the system evaluates eligibility criteria, sector alignment, funding opportunities, and regional policies to recommend the most suitable schemes for businesses.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={onStart}
                className="btn-primary text-base px-8 py-4 rounded-2xl"
              >
                <MagnifyingGlassIcon className="w-5 h-5" />
                Start Discovery
                <ArrowRightIcon className="w-5 h-5" />
              </motion.button>
              <button
                onClick={onStart}
                className="btn-secondary text-base px-8 py-4 rounded-2xl"
              >
                <BuildingOfficeIcon className="w-5 h-5" />
                Explore Schemes
              </button>
            </div>

            {/* Trust Signals */}
            <div className="flex items-center justify-center gap-8 text-slate-400 text-xs font-bold">
              <span className="flex items-center gap-2">
                <ShieldCheckIcon className="w-4 h-4 text-emerald-500" />
                256-bit Encrypted
              </span>
              <span className="flex items-center gap-2">
                <GlobeAltIcon className="w-4 h-4 text-purple-500" />
                All India Coverage
              </span>
            </div>
          </motion.div>
        </div>

        {/* Stats Row */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-20 max-w-4xl mx-auto"
        >
          {stats.map((stat, i) => (
            <div key={i} className="intelligence-card p-6 text-center">
              <div className="text-3xl mb-2">{stat.icon}</div>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{stat.value}</div>
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mt-1">{stat.label}</div>
            </div>
          ))}
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="relative z-10 py-20 px-8 md:px-16 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight mb-4">
            Built for the Entire Funding Journey
          </h2>
          <p className="text-slate-500 font-medium max-w-xl mx-auto leading-relaxed">
            From your first profile input to final application submission — AI Scheme Discovery Platform handles every intelligence layer autonomously.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.5 }}
              onHoverStart={() => setHoveredFeature(i)}
              onHoverEnd={() => setHoveredFeature(null)}
              className={`intelligence-card p-7 cursor-default transition-all duration-300 ${hoveredFeature === i ? 'shadow-premium -translate-y-1' : ''}`}
            >
              <div className={`w-12 h-12 rounded-2xl ${feat.bg} ${feat.color} flex items-center justify-center mb-5`}>
                <feat.icon className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-slate-900 mb-2 text-lg">{feat.title}</h3>
              <p className="text-sm text-slate-500 font-medium leading-relaxed">{feat.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section className="relative z-10 py-20 px-8 md:px-16 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-black text-slate-900 tracking-tight mb-4">
            Trusted by Indian Businesses
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map((t, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="intelligence-card p-7"
            >
              <div className="flex mb-4">
                {[...Array(t.rating)].map((_, s) => (
                  <StarIcon key={s} className="w-4 h-4 text-amber-400 fill-amber-400" />
                ))}
              </div>
              <p className="text-sm text-slate-600 font-medium leading-relaxed mb-6 italic">
                "{t.text}"
              </p>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-brand-primary/10 text-brand-primary font-black flex items-center justify-center">
                  {t.avatar}
                </div>
                <div>
                  <div className="font-bold text-slate-900 text-sm">{t.name}</div>
                  <div className="text-xs text-slate-400 font-medium">{t.role}</div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-20 px-8 md:px-16 max-w-5xl mx-auto">
        <div className="rounded-3xl bg-gradient-to-br from-brand-primary via-blue-600 to-purple-600 p-12 md:p-16 text-center relative overflow-hidden">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-white blur-[60px]" />
            <div className="absolute bottom-0 left-0 w-64 h-64 rounded-full bg-white blur-[60px]" />
          </div>
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 border border-white/30 rounded-full text-xs font-bold text-white mb-6">
              <ClockIcon className="w-4 h-4" />
              Free to get started — No credit card required
            </div>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight mb-4">
              Your Government Funding<br />Intelligence Awaits
            </h2>
            <p className="text-blue-100 font-medium mb-10 text-lg max-w-xl mx-auto">
              Join thousands of MSMEs and startups who discovered funding opportunities with AI Scheme Discovery Platform.
            </p>
            <button
              onClick={onStart}
              className="inline-flex items-center gap-3 px-10 py-5 bg-white text-brand-primary font-black rounded-2xl hover:bg-blue-50 transition-all duration-200 hover:-translate-y-0.5 text-lg shadow-xl"
            >
              <MagnifyingGlassIcon className="w-6 h-6" />
              Get Started Now
              <ArrowRightIcon className="w-6 h-6" />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-10 px-8 md:px-16 border-t border-slate-100">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-black text-slate-800">AI Scheme Discovery Platform</span>
          </div>
          <p className="text-sm text-slate-400 font-medium">
            © 2026 AI Scheme Discovery Platform. Agentic Decision Support for India's Growth Engine.
          </p>
          <div className="flex items-center gap-2 text-slate-400 text-xs font-medium">
            <ShieldCheckIcon className="w-4 h-4 text-emerald-500" />
            MeitY Recognized Platform
          </div>
        </div>
      </footer>
    </div>
  );
}
