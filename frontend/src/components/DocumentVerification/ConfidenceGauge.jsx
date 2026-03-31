import React, { useEffect, useRef } from 'react';

const ConfidenceGauge = ({ confidence = 0 }) => {
  const canvasRef = useRef(null);
  const centerRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const center = canvas.width / 2;
    const radius = 120;
    const lineWidth = 20;
    
    // Clear
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Background circle
    ctx.beginPath();
    ctx.arc(center, center, radius, 0, 2 * Math.PI);
    ctx.lineWidth = lineWidth;
    ctx.strokeStyle = '#e5e7eb';
    ctx.stroke();
    
    // Progress arc
    const percentage = Math.min(Math.max(confidence, 0), 100) / 100;
    const angle = percentage * 2 * Math.PI - Math.PI / 2;  // Start from top
    
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#10b981');
    gradient.addColorStop(0.5, '#059669');
    gradient.addColorStop(1, '#047857');
    
    ctx.beginPath();
    ctx.arc(center, center, radius, -Math.PI / 2, angle);
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.strokeStyle = gradient;
    ctx.stroke();
    
    // Update center text
    if (centerRef.current) {
      centerRef.current.innerHTML = `
        <div class="text-3xl font-black text-gray-900">${Math.round(confidence)}<span class="text-lg font-normal text-gray-500">%</span></div>
        <div class="text-sm font-medium text-gray-600 mt-1 tracking-wide uppercase">Confidence</div>
      `;
    }
  }, [confidence]);

  const getStatus = () => {
    if (confidence >= 90) return { text: 'Excellent', color: 'text-green-600' };
    if (confidence >= 70) return { text: 'Good', color: 'text-yellow-600' };
    if (confidence >= 50) return { text: 'Fair', color: 'text-orange-600' };
    return { text: 'Poor', color: 'text-red-600' };
  };

  return (
    <div className="relative">
      <canvas 
        ref={canvasRef}
        width={320}
        height={320}
        className="mx-auto block"
      />
      <div 
        ref={centerRef}
        className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
      />
      <p className={`text-center mt-4 font-semibold ${getStatus().color}`}>
        {getStatus().text} Match
      </p>
      <div className="text-center text-xs text-gray-500 mt-1 space-y-px">
        <div>🟢 ≥90% Auto-approved</div>
        <div>🟡 70-89% Review</div>
        <div>🔴 70% Rejected</div>
      </div>
    </div>
  );
};

export default ConfidenceGauge;

