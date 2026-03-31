import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// ── Inline icon replacements (no @heroicons dependency needed) ────────────────
function EyeIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function EyeSlashIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
    </svg>
  );
}

function CheckCircleIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ExclamationCircleIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function ArrowRightIcon({ className }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = 'http://127.0.0.1:8001';

function getPasswordStrength(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

// Simple translation map (replaces useTranslation for now)
const STRINGS = {
  'login.create_account': 'Create Account',
  'login.welcome_back': 'Welcome Back',
  'login.journey_subtitle': 'Start your scheme discovery journey',
  'login.signin_subtitle': 'Sign in to your account',
  'login.tabs.signin': 'Sign In',
  'login.tabs.signup': 'Sign Up',
  'login.fields.full_name': 'Full Name',
  'login.fields.full_name_placeholder': 'Enter your full name',
  'login.fields.business_email': 'Business Email',
  'login.fields.business_email_placeholder': 'yourbusiness@example.com',
  'login.fields.password': 'Password',
  'login.fields.confirm_password': 'Confirm Password',
  'login.fields.confirm_password_placeholder': 'Confirm your password',
  'login.forgot_password': 'Forgot Password?',
  'login.errors.enter_email': 'Please enter your email',
  'login.errors.valid_email': 'Please enter a valid email',
  'login.errors.password_required': 'Password is required',
  'login.errors.password_length': 'Password must be at least 8 characters',
  'login.errors.full_name_required': 'Full name is required',
  'login.errors.passwords_mismatch': 'Passwords do not match',
  'login.errors.auth_failed': 'Authentication failed',
  'login.errors.server_unavailable': 'Server unavailable. Try again.',
  'login.submitting.signup': 'Creating account...',
  'login.submitting.signin': 'Signing in...',
  'login.actions.signup': 'Sign Up',
  'login.actions.signin': 'Sign In',
  'login.password_strength.label': 'Strength',
  'login.password_strength.empty': 'Empty',
  'login.password_strength.weak': 'Weak',
  'login.password_strength.fair': 'Fair',
  'login.password_strength.good': 'Good',
  'login.password_strength.strong': 'Strong',
  'login.hero_title_top': 'Discover Every',
  'login.hero_title_middle': 'Scheme You Deserve',
  'login.hero_subtitle': 'AI-powered scheme discovery and document verification for Indian entrepreneurs.',
};
const t = (key) => STRINGS[key] || key;

// ─────────────────────────────────────────────────────────────────────────────

export default function LoginPage({ onLogin }) {
  const [isSignUp, setIsSignUp]       = useState(false);
  const [showPass, setShowPass]       = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState('');
  const [form, setForm] = useState({ email: '', password: '', confirm: '', fullName: '' });

  const strengthMap = {
    0: { label: t('login.password_strength.empty'),  color: 'bg-slate-200',   textColor: 'text-slate-400',   width: '0%'   },
    1: { label: t('login.password_strength.weak'),   color: 'bg-red-400',     textColor: 'text-red-500',     width: '25%'  },
    2: { label: t('login.password_strength.fair'),   color: 'bg-orange-400',  textColor: 'text-orange-500',  width: '50%'  },
    3: { label: t('login.password_strength.good'),   color: 'bg-yellow-400',  textColor: 'text-yellow-600',  width: '75%'  },
    4: { label: t('login.password_strength.strong'), color: 'bg-emerald-500', textColor: 'text-emerald-600', width: '100%' },
  };

  const strength     = getPasswordStrength(form.password);
  const strengthInfo = strengthMap[strength];

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const validate = () => {
    if (!form.email.trim())                           return t('login.errors.enter_email');
    if (!/\S+@\S+\.\S+/.test(form.email))            return t('login.errors.valid_email');
    if (!form.password)                               return t('login.errors.password_required');
    if (form.password.length < 8)                     return t('login.errors.password_length');
    if (isSignUp && !form.fullName.trim())            return t('login.errors.full_name_required');
    if (isSignUp && form.password !== form.confirm)   return t('login.errors.passwords_mismatch');
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const err = validate();
    if (err) { setError(err); return; }
    setLoading(true);
    try {
      const endpoint = isSignUp ? '/v1/auth/signup' : '/v1/auth/login';
      const body = isSignUp
        ? { email: form.email.trim().toLowerCase(), password: form.password, full_name: form.fullName.trim() }
        : { email: form.email.trim().toLowerCase(), password: form.password };
      const res  = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(60000),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t('login.errors.auth_failed'));
      sessionStorage.setItem('karios_user',   JSON.stringify(data.user || { email: form.email }));
      sessionStorage.setItem('scheme_token',  data.access_token || '');
      onLogin(data.user || { email: form.email });
    } catch (ex) {
      setError(ex.message || t('login.errors.server_unavailable'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-gradient-to-br from-slate-50 to-slate-100">

      {/* ── Left panel ──────────────────────────────────────────────────── */}
      <div className="hidden lg:flex w-[48%] bg-gradient-to-br from-slate-900 via-blue-900 to-blue-700 flex-col justify-between p-12 relative overflow-hidden">
        {/* Decorative blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-[-20%] right-[-20%] w-[70%] h-[70%] bg-white/5 rounded-full blur-[80px]" />
          <div className="absolute bottom-[-20%] left-[-20%] w-[60%] h-[60%] bg-blue-400/10 rounded-full blur-[80px]" />
          <div
            className="absolute inset-0 opacity-[0.04]"
            style={{
              backgroundImage:
                'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
              backgroundSize: '40px 40px',
            }}
          />
        </div>

        <div className="relative z-10">
          <h2 className="text-4xl font-black text-white leading-tight mb-4 tracking-tight">
            {t('login.hero_title_top')}<br />
            <span className="text-blue-300">{t('login.hero_title_middle')}</span>
          </h2>
          <p className="text-blue-200 font-medium leading-relaxed mb-12 max-w-sm">
            {t('login.hero_subtitle')}
          </p>
        </div>

        <div className="relative z-10 flex gap-8" />
      </div>

      {/* ── Right form panel ─────────────────────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center p-8 md:p-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-[420px]"
        >
          {/* Header */}
          <div className="mb-10">
            <h2 className="text-3xl font-black text-slate-900 tracking-tight mb-2">
              {isSignUp ? t('login.create_account') : t('login.welcome_back')}
            </h2>
            <p className="text-slate-500 font-medium">
              {isSignUp ? t('login.journey_subtitle') : t('login.signin_subtitle')}
            </p>
          </div>

          {/* Tab toggle */}
          <div className="flex bg-slate-100 rounded-xl p-1 mb-8">
            {[t('login.tabs.signin'), t('login.tabs.signup')].map((tab, i) => (
              <button
                key={i}
                onClick={() => { setIsSignUp(i === 1); setError(''); }}
                className={`flex-1 py-2.5 rounded-lg text-sm font-bold transition-all duration-200 ${
                  (i === 1) === isSignUp
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Full name — sign-up only */}
            <AnimatePresence mode="popLayout">
              {isSignUp && (
                <motion.div
                  key="fullname"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  style={{ overflow: 'hidden' }}
                >
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                    {t('login.fields.full_name')}
                  </label>
                  <input
                    type="text"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    placeholder={t('login.fields.full_name_placeholder')}
                    value={form.fullName}
                    onChange={(e) => update('fullName', e.target.value)}
                  />
                </motion.div>
              )}
            </AnimatePresence>

            {/* Email */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                {t('login.fields.business_email')}
              </label>
              <input
                type="email"
                className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                placeholder={t('login.fields.business_email_placeholder')}
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                {t('login.fields.password')}
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) => update('password', e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPass
                    ? <EyeSlashIcon className="w-5 h-5" />
                    : <EyeIcon className="w-5 h-5" />}
                </button>
              </div>

              {/* Password strength bar */}
              {isSignUp && form.password && (
                <div className="mt-2 space-y-1">
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full rounded-full ${strengthInfo.color}`}
                      initial={{ width: 0 }}
                      animate={{ width: strengthInfo.width }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <span className={`text-[10px] font-bold ${strengthInfo.textColor}`}>
                    {t('login.password_strength.label')}: {strengthInfo.label}
                  </span>
                </div>
              )}
            </div>

            {/* Confirm password — sign-up only */}
            <AnimatePresence mode="popLayout">
              {isSignUp && (
                <motion.div
                  key="confirm"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.2 }}
                  style={{ overflow: 'hidden' }}
                >
                  <label className="block text-sm font-semibold text-slate-700 mb-1.5">
                    {t('login.fields.confirm_password')}
                  </label>
                  <div className="relative">
                    <input
                      type={showConfirm ? 'text' : 'password'}
                      className="w-full px-4 py-3 pr-12 rounded-xl border border-slate-200 bg-white text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                      placeholder={t('login.fields.confirm_password_placeholder')}
                      value={form.confirm}
                      onChange={(e) => update('confirm', e.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm(!showConfirm)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showConfirm
                        ? <EyeSlashIcon className="w-5 h-5" />
                        : <EyeIcon className="w-5 h-5" />}
                    </button>
                    {form.confirm && form.password === form.confirm && (
                      <CheckCircleIcon className="absolute right-10 top-1/2 -translate-y-1/2 w-5 h-5 text-emerald-500" />
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Forgot password */}
            {!isSignUp && (
              <div className="flex justify-end">
                <button
                  type="button"
                  className="text-sm text-blue-600 hover:underline font-semibold"
                >
                  {t('login.forgot_password')}
                </button>
              </div>
            )}

            {/* Error message */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl text-red-600 text-sm font-medium"
                >
                  <ExclamationCircleIcon className="w-5 h-5 flex-shrink-0" />
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Submit button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-4 px-6 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-base rounded-xl transition-colors duration-200"
            >
              {loading ? (
                <>
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {isSignUp ? t('login.submitting.signup') : t('login.submitting.signin')}
                </>
              ) : (
                <>
                  {isSignUp ? t('login.actions.signup') : t('login.actions.signin')}
                  <ArrowRightIcon className="w-5 h-5" />
                </>
              )}
            </button>

          </form>
        </motion.div>
      </div>
    </div>
  );
}