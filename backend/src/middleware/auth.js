const jwt = require('jsonwebtoken');
const { JWT_SECRET } = require('../config/constants');

function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization || '';
  const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : null;

  if (!token) return res.status(401).json({ message: 'Authorization token missing.' });

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.user = payload;
    return next();
  } catch (_error) {
    return res.status(401).json({ message: 'Invalid or expired token.' });
  }
}

module.exports = { authMiddleware };
