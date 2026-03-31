import fs from 'fs';

const sfCss = `

/* =======================================================================
   SCHEME FEED — Premium Design System (sf-*)
   ======================================================================= */

.sf-root {
  position: fixed;
  inset: 0;
  background: #0b0f1a;
  display: flex;
  flex-direction: column;
  z-index: 999;
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.sf-topbar {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 20px;
  background: linear-gradient(to bottom, rgba(11,15,26,0.95), transparent);
  z-index: 100;
}
.sf-topbar-logo { display: flex; align-items: baseline; }
.sf-topbar-k    { font-size: 1.5rem; font-weight: 900; color: #4f7cff; letter-spacing: -1px; }
.sf-topbar-arios{ font-size: 1rem; font-weight: 700; color: white; letter-spacing: -0.5px; }
.sf-topbar-meta { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.sf-topbar-count{ font-size: 12px; color: rgba(255,255,255,0.5); font-weight: 500; }
.sf-topbar-chip {
  padding: 3px 10px;
  background: rgba(79,124,255,0.15);
  border: 1px solid rgba(79,124,255,0.3);
  color: #a5b4fc;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 700;
}
.sf-topbar-hint {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; color: rgba(255,255,255,0.3);
  animation: sf-bob 2.5s ease-in-out infinite;
}
@keyframes sf-bob {
  0%,100% { transform: translateY(0); }
  50%      { transform: translateY(3px); }
}

.sf-scroll-track {
  flex: 1;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
  scrollbar-width: none;
}
.sf-scroll-track::-webkit-scrollbar { display: none; }

.sf-scroll-slide {
  height: 100vh;
  scroll-snap-align: start;
  scroll-snap-stop: always;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 72px 24px 32px;
  position: relative;
}

.sf-counter {
  position: absolute;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: rgba(255,255,255,0.4);
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  padding: 4px 12px;
  border-radius: 99px;
  font-weight: 600;
  backdrop-filter: blur(8px);
}

.sf-card-wrapper {
  width: 100%;
  max-width: 520px;
}

.sf-card {
  background: white;
  border-radius: 28px;
  overflow: hidden;
  box-shadow: 0 40px 80px -20px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 110px);
}

.sf-card-banner {
  padding: 28px 28px 24px;
  position: relative;
  overflow: hidden;
  flex-shrink: 0;
}
.sf-card-banner-noise {
  position: absolute;
  inset: 0;
  opacity: 0.35;
  pointer-events: none;
  background: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwBAMAAAClLOS0AAAAG1BMVEUhISEmJiYmJiYmJiYmJiYmJiYmJiYmJiZG/u5AAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAIUlEQVQ4jWNgYGBg/P//PxQzMTAwMDENCQoK/v8HABhKBBhCdIiuAAAAAElFTkSuQmCC") repeat;
}
.sf-card-banner-content { position: relative; z-index: 2; padding-right: 64px; }
.sf-badge-cat {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 99px;
  font-size: 10px; font-weight: 800; color: white;
  text-transform: uppercase; letter-spacing: 0.08em;
  margin-bottom: 10px;
  backdrop-filter: blur(4px);
}
.sf-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: white;
  line-height: 1.3;
  letter-spacing: -0.02em;
}
.sf-ministry {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255,255,255,0.65);
  font-weight: 500;
}

.sf-confidence-ring {
  position: absolute;
  top: 20px; right: 20px;
  width: 56px; height: 56px;
  display: flex; align-items: center; justify-content: center;
  z-index: 2;
}
.sf-ring-svg {
  width: 56px; height: 56px;
  transform: rotate(-90deg);
  position: absolute;
}
.sf-ring-label {
  font-size: 11px; font-weight: 900; color: white;
  position: relative; z-index: 2; text-align: center;
}

.sf-card-body {
  padding: 20px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  flex: 1;
}
.sf-card-body::-webkit-scrollbar { width: 3px; }
.sf-card-body::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 99px; }

.sf-match-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.sf-match-dot {
  width: 8px; height: 8px; min-width: 8px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 8px rgba(22,163,74,0.6);
  margin-top: 4px;
}
.sf-match-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.sf-match-tag {
  padding: 4px 10px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #15803d;
  border-radius: 8px;
  font-size: 11px; font-weight: 700;
}

.sf-desc {
  font-size: 13.5px;
  line-height: 1.65;
  color: #475569;
  font-weight: 500;
}

.sf-meta-row { display: flex; flex-wrap: wrap; gap: 6px; }
.sf-meta-pill {
  padding: 4px 10px; border-radius: 8px;
  font-size: 11px; font-weight: 700;
}
.sf-meta-blue   { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.sf-meta-green  { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.sf-meta-purple { background: #faf5ff; color: #7e22ce; border: 1px solid #e9d5ff; }

.sf-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.sf-btn-save {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 16px; border-radius: 12px;
  font-size: 12px; font-weight: 700;
  border: 1.5px solid #e2e8f0;
  background: white; color: #475569;
  cursor: pointer; transition: all 0.18s ease;
}
.sf-btn-save:hover { background: #f8fafc; border-color: #cbd5e1; }
.sf-btn-save--saved { background: #f0fdf4; border-color: #86efac; color: #15803d; }

.sf-btn-apply {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 16px; border-radius: 12px;
  font-size: 12px; font-weight: 700;
  background: #4f7cff; color: white;
  text-decoration: none; transition: all 0.18s ease;
  box-shadow: 0 4px 12px -4px rgba(79,124,255,0.5);
}
.sf-btn-apply:hover {
  background: #3b68ff;
  box-shadow: 0 6px 16px -4px rgba(79,124,255,0.6);
  transform: translateY(-1px);
}

.sf-btn-chat {
  margin-left: auto;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 9px 14px; border-radius: 12px;
  font-size: 12px; font-weight: 700;
  border: 1.5px solid #e2e8f0;
  background: white; color: #64748b;
  cursor: pointer; transition: all 0.18s ease;
}
.sf-btn-chat:hover { background: #f1f5ff; border-color: #4f7cff; color: #4f7cff; }
.sf-btn-chat--active { background: #eff6ff; border-color: #4f7cff; color: #4f7cff; }

.sf-chat { border-top: 1px solid #f1f5f9; overflow: hidden; }
.sf-chat-history {
  padding: 14px 0 8px;
  display: flex; flex-direction: column; gap: 10px;
  max-height: 200px; overflow-y: auto;
}
.sf-chat-hint { font-size: 12px; color: #94a3b8; text-align: center; font-style: italic; padding: 12px 0; }
.sf-chat-msg {
  padding: 10px 14px; border-radius: 14px;
  font-size: 12px; line-height: 1.55; font-weight: 500;
  max-width: 88%;
}
.sf-chat-msg--user {
  background: #4f7cff; color: white;
  border-radius: 14px 14px 4px 14px;
  align-self: flex-end;
}
.sf-chat-msg--assistant {
  background: #f8fafc; color: #334155;
  border: 1px solid #e2e8f0;
  border-radius: 14px 14px 14px 4px;
  align-self: flex-start;
}
.sf-chat-typing { display: flex; align-items: center; gap: 6px; padding: 12px 16px; }
.sf-chat-typing span {
  width: 6px; height: 6px; border-radius: 50%; background: #94a3b8;
  animation: sf-bounce 1.2s ease-in-out infinite;
}
.sf-chat-typing span:nth-child(2) { animation-delay: 0.2s; }
.sf-chat-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes sf-bounce {
  0%,60%,100% { transform: translateY(0); }
  30%          { transform: translateY(-6px); }
}

.sf-chat-input-row { display: flex; gap: 8px; padding: 10px 0 0; }
.sf-chat-input {
  flex: 1; padding: 10px 14px;
  background: #f8fafc; border: 1.5px solid #e2e8f0;
  border-radius: 12px; font-size: 12px; color: #1e293b;
  outline: none; transition: border-color 0.15s;
  font-family: inherit;
}
.sf-chat-input:focus { border-color: #4f7cff; background: white; }
.sf-chat-send {
  width: 38px; height: 38px; flex-shrink: 0;
  background: #4f7cff; color: white;
  border-radius: 10px; border: none;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; transition: all 0.18s ease;
}
.sf-chat-send:hover { background: #3b68ff; transform: scale(1.05); }
.sf-chat-send:disabled { background: #cbd5e1; cursor: not-allowed; transform: none; }

.sf-loader {
  position: fixed; inset: 0; background: #0b0f1a;
  display: flex; align-items: center; justify-content: center; z-index: 999;
}
.sf-loader-inner {
  display: flex; flex-direction: column;
  align-items: center; gap: 20px; text-align: center;
}
.sf-loader-label { font-size: 1.1rem; font-weight: 800; color: white; letter-spacing: -0.02em; }
.sf-loader-sub   { font-size: 13px; color: rgba(255,255,255,0.4); font-weight: 500; }

.sf-loader-ring { width: 56px; height: 56px; position: relative; }
.sf-loader-ring div {
  box-sizing: border-box; display: block; position: absolute;
  width: 44px; height: 44px; margin: 6px;
  border: 4px solid transparent; border-top-color: #4f7cff;
  border-radius: 50%;
  animation: sf-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
}
.sf-loader-ring div:nth-child(1) { animation-delay: -0.45s; }
.sf-loader-ring div:nth-child(2) { animation-delay: -0.3s;  border-top-color: #8b9cff; }
.sf-loader-ring div:nth-child(3) { animation-delay: -0.15s; border-top-color: #6ee7b7; }
@keyframes sf-ring {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
`;

const cssPath = 'd:/Main_project1/final/frontend/src/App.css';
let existing = fs.readFileSync(cssPath, 'utf-8');
// Remove old sf-* section if exists
const sfStart = existing.indexOf('/* =======================================================================\n   SCHEME FEED — Premium Design System (sf-*)');
if (sfStart !== -1) {
  existing = existing.slice(0, sfStart);
}
fs.writeFileSync(cssPath, existing + sfCss);
console.log('sf-* CSS injected successfully. Total chars:', (existing + sfCss).length);
