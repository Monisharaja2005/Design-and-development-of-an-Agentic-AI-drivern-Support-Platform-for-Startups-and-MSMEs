const express = require('express');
const cors = require('cors');
const { applySecurity } = require('./middleware/security');
const authRoutes = require('./routes/authRoutes');
const businessRoutes = require('./routes/businessRoutes');
const schemeRoutes = require('./routes/schemeRoutes');
const chatbotRoutes = require('./routes/chatbotRoutes');
const documentRoutes = require('./routes/documentRoutes');
const notificationRoutes = require('./routes/notificationRoutes');

const app = express();

app.use(cors());
applySecurity(app);
app.use(express.json());

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, message: 'Backend is running' });
});

app.use('/api/auth', authRoutes);
app.use('/api/business-profile', businessRoutes);
app.use('/api/schemes', schemeRoutes);
app.use('/api/chatbot', chatbotRoutes);
app.use('/api/documents', documentRoutes);
app.use('/api/notifications', notificationRoutes);

app.use((err, _req, res, next) => {
  if (err && err.name === 'MulterError') return res.status(400).json({ message: err.message });
  if (err && err.message && err.message.includes('Only PDF, PNG, and JPG')) {
    return res.status(400).json({ message: err.message });
  }
  return next(err);
});

module.exports = app;
