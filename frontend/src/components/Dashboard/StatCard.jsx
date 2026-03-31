import React from 'react';
import { motion } from 'framer-motion';

export default function StatCard({ title, value, label, icon: Icon, color, bg, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      className="intelligence-card p-6 group hover:shadow-premium transition-all duration-300"
    >
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-2xl ${bg} ${color} flex items-center justify-center transition-transform group-hover:scale-110`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="badge-primary bg-slate-50 border-slate-100 text-slate-400">
          Live
        </div>
      </div>
      <div>
        <div className="text-2xl font-black text-slate-900 tracking-tight">{value}</div>
        <div className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-1">{title}</div>
      </div>
    </motion.div>
  );
}
