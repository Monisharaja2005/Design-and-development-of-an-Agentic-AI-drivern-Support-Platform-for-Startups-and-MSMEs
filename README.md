# Full Stack Login and Registration

Project structure:
- `frontend` -> React + Vite app
- `backend` -> Node.js + Express API

Backend structure:
- `backend/src/server.js` -> bootstrap entry
- `backend/src/app.js` -> app + middleware wiring
- `backend/src/routes/` -> auth/business/schemes/chatbot/documents routes
- `backend/src/services/domainService.js` -> validation and recommendation logic
- `backend/src/middleware/` -> auth, upload, security
- `backend/src/data/store.js` -> in-memory data maps
- `backend/src/config/constants.js` -> app constants and catalogs

## Features
- Login page as the first screen
- Registration for new users using email + password
- Strong password validation in frontend and backend
- Responsive interactive UI (mobile + desktop)
- Frontend connected to backend auth APIs
- JWT-based login session
- Protected dashboard data endpoint
- Post-login Startup/MSME business profile onboarding
- Business profile validation (gender, PAN, mobile, GSTIN, duplicates)
- Multi-step profile wizard with completeness meter and live format checks
- Scheme recommendation engine based on profile signals
- Forgot password and reset-password flow (demo token based)
- Scheme dashboard API with chatbot-guided application assistance
- Document upload and rule-based validation feedback (verified/review/rejected)

## Run backend
```bash
cd backend
npm install
npm run dev
```

Backend runs at `http://localhost:5000`.

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## API endpoints
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me` (requires `Authorization: Bearer <token>`)
- `GET /api/business-profile` (requires `Authorization: Bearer <token>`)
- `POST /api/business-profile` (requires `Authorization: Bearer <token>`)
- `GET /api/business-profile/requirements`
- `GET /api/business-profile/recommendations` (requires `Authorization: Bearer <token>`)
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `GET /api/schemes` (requires `Authorization: Bearer <token>`)
- `POST /api/chatbot/scheme-assistant` (requires `Authorization: Bearer <token>`)
- `GET /api/documents` (requires `Authorization: Bearer <token>`)
- `POST /api/documents/upload` (requires `Authorization: Bearer <token>`, multipart)
- `POST /api/documents/revalidate/:id` (requires `Authorization: Bearer <token>`)
- `GET /api/health`

## Note
The backend uses in-memory storage right now, so users are reset when server restarts.
Set `JWT_SECRET` in your backend environment for production.
Install new backend dependencies after pulling latest code: `helmet`, `express-rate-limit`, `multer`.
Alert read/unread state is persisted in `backend/src/data/notification-reads.json`.
