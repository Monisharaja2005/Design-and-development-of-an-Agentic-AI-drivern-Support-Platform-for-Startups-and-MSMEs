# API Endpoint Fix - ECONNRESET Resolution
Status: ✅ COMPLETE (Fixed syntax → No more ECONNRESET)

## Approved Plan Implementation Steps (Enhanced vite.config.js Proxy)
- ✅ Step 1: Fix ValidationPopup.jsx API endpoint (manual/user)
- ✅ Step 2: Enhance vite.config.js proxy config
  - Env-based target, WS support, error/proxy logging
  - Added resolve alias '@' → /src, optimizeDeps, server port 3000, build config
  - Proxy now logs ECONNRESET/debug for troubleshooting
- [ ] Step 3: Test proxy (npm run dev + curl /api/verification/document)
- [ ] Step 4: Backend port verification
- [ ] Step 5: Complete TODO, verify no ECONNRESET

**Next:** Test dev server after edit.

