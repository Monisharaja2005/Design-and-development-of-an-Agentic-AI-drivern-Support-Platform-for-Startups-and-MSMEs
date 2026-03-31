import fs from 'fs';

const cssPath = 'd:/Main_project1/final/frontend/src/App.css';
let css = fs.readFileSync(cssPath, 'utf-8');

const anchor = '.scheme-reel-title {';
const idx = css.indexOf(anchor);

if (idx !== -1) {
  const newCss = css.substring(0, idx) + `.scheme-reel-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: #1e293b;
  line-height: 1.2;
}

.scheme-reel-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scheme-tag {
  background: #f1f5f9;
  color: #64748b;
  padding: 4px 12px;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.scheme-reel-desc {
  color: #475569;
  font-size: 1rem;
  line-height: 1.6;
  overflow-y: auto;
  padding-right: 8px;
}

.scheme-reel-desc::-webkit-scrollbar {
  width: 4px;
}
.scheme-reel-desc::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}

/* 3. Actions in Reel */
.scheme-reel-actions {
  position: absolute;
  right: 24px;
  bottom: 120px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  z-index: 50;
}

.action-btn-circle {
  width: 56px;
  height: 56px;
  border-radius: 28px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  color: #64748b;
}

.action-btn-circle:hover {
  transform: scale(1.1);
  color: #4f46e5;
}

.action-btn-circle.active {
  color: #ef4444;
}

/* 4. Navigation Hint */
.reel-nav-hint {
  position: absolute;
  bottom: 40px;
  left: 50%;
  transform: translateX(-50%);
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.6;
  animation: bounce 2s infinite;
  z-index: 50;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {transform: translateX(-50%) translateY(0);}
  40% {transform: translateX(-50%) translateY(-10px);}
  60% {transform: translateX(-50%) translateY(-5px);}
}

/* 5. Professional Login Adjustments */
.login-wrap {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 0;
  border-radius: 24px;
  overflow: hidden;
  background: white;
  box-shadow: 0 50px 100px -20px rgba(0,0,0,0.15);
}

.login-hero {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: white;
  padding: 60px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-form-card {
  padding: 60px;
}

/* 6. Corner Profile */
.user-profile-corner {
  animation: slideInRight 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes slideInRight {
  from { transform: translateX(50px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* Spinner */
.spinner {
  width: 50px;
  height: 50px;
  border: 5px solid rgba(255,255,255,0.2);
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
`;
  
  fs.writeFileSync(cssPath, newCss);
  console.log("CSS fixed successfully.");
} else {
  console.log("Could not find anchor.");
}
