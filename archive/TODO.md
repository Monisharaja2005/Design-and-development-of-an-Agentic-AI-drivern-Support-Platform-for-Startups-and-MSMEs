# Fix Saved Schemes Disappear Bug - Backend Persistence
====================

## Current Status
✅ **Plan approved by user**  
🔄 **Step 1: Create TODO.md** (current)  

## Implementation Steps

### Step 1: Create API Helpers [lib/userWorkspace.js]
```
✅ Added saveUserSchemes(email, schemeIds): POST /v1/schemes/save {email, schemes: []}
✅ Added loadUserSchemes(email): GET /v1/schemes/saved → schemes array
✅ Preserved existing exports (workspace functions)
```
**Status**: ✅ Complete

### Step 2: Fix SchemesStep.jsx Toggle Save
```
✅ Import helpers + savingSchemeId state
✅ toggleSelect async: email check → saveUserSchemes → local update → parent notify  
✅ Error handling + saving prop to SchemeCard (spinner per button)
✅ Alert fallback (TODO: toast polish)
```
**Status**: ✅ Complete

### Step 3: Fix ShortlistStep.jsx Load Saved
```
✅ useEffect: loadUserSchemes(email) on mount  
✅ Loading state + fallback to props
✅ onSchemesLoad(savedIds) → parent sync
✅ displaySchemes prioritizes backend data
```
**Status**: ✅ Complete

### Step 4: Parent Integration Check
```
- Read KariosApp.jsx/ProfileStep.jsx → see onSave prop source
- Chain API call if parent handles persistence
```
**Status**: Pending

### Step 5: Test End-to-End
```
- Login → Schemes → Toggle save → Network: /v1/schemes/save 200
- Refresh → Shortlist → Shows saved schemes from /v1/schemes/saved
- sqlite3 users.db "SELECT saved_schemes FROM users LIMIT 1" → verify JSON array
```
**Status**: Pending

### Step 6: Polish
```
- Add offline fallback (localStorage)
- Error toasts (use react-hot-toast or similar)
- Loading spinner on save button
```
**Status**: Pending

## Completion Criteria
- [ ] Save persists across refresh
- [ ] Shortlist shows backend-saved schemes  
- [ ] Network calls succeed (no 404/500)
- [ ] DB entry verified
- [ ] attempt_completion

**Next action**: Edit lib/userWorkspace.js helpers → Update TODO with ✅

