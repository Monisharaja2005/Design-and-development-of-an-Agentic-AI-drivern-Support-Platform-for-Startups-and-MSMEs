const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { JWT_SECRET, ALLOWED_USER_TYPES } = require('../config/constants');
const { authMiddleware } = require('../middleware/auth');
const { usersByEmail, resetTokensByEmail, persistStore } = require('../data/store');
const { validateEmail, getPasswordErrors, signToken } = require('../services/domainService');

const router = express.Router();

router.post('/register', async (req, res) => {
  try {
    const { email, password, phone, userType } = req.body;
    if (!email || !password || !phone || !userType) {
      return res.status(400).json({ message: 'Email, password, phone, and user type are required.' });
    }

    const normalizedEmail = email.trim().toLowerCase();
    if (!validateEmail(normalizedEmail)) return res.status(400).json({ message: 'Please provide a valid email.' });
    if (!/^\d{10}$/.test(String(phone).trim())) return res.status(400).json({ message: 'Phone must be a 10-digit number.' });
    if (!ALLOWED_USER_TYPES.includes(String(userType).trim().toLowerCase())) {
      return res.status(400).json({ message: 'User type must be Individual or Business.' });
    }

    const passwordErrors = getPasswordErrors(password);
    if (passwordErrors.length) return res.status(400).json({ message: 'Password is not strong enough.', errors: passwordErrors });
    if (usersByEmail.has(normalizedEmail)) return res.status(409).json({ message: 'Email is already registered.' });

    const passwordHash = await bcrypt.hash(password, 10);
    usersByEmail.set(normalizedEmail, {
      email: normalizedEmail,
      phone: String(phone).trim(),
      userType: String(userType).trim().toLowerCase(),
      passwordHash,
      createdAt: new Date().toISOString(),
    });
    if (!persistStore()) return res.status(500).json({ message: 'Registration failed while saving data.' });

    return res.status(201).json({
      message: 'Registration successful.',
      user: { email: normalizedEmail },
      token: signToken(normalizedEmail),
    });
  } catch (_error) {
    return res.status(500).json({ message: 'Registration failed due to server error.' });
  }
});

router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;
    if (!email || !password) return res.status(400).json({ message: 'Email and password are required.' });

    const normalizedEmail = email.trim().toLowerCase();
    const user = usersByEmail.get(normalizedEmail);
    if (!user) return res.status(401).json({ message: 'Invalid email or password.' });

    const match = await bcrypt.compare(password, user.passwordHash);
    if (!match) return res.status(401).json({ message: 'Invalid email or password.' });

    return res.status(200).json({
      message: 'Login successful.',
      user: { email: user.email },
      token: signToken(user.email),
    });
  } catch (_error) {
    return res.status(500).json({ message: 'Login failed due to server error.' });
  }
});

router.post('/forgot-password', (req, res) => {
  const email = String(req.body?.email || '').trim().toLowerCase();
  if (!email || !validateEmail(email)) return res.status(400).json({ message: 'Valid email is required.' });

  const user = usersByEmail.get(email);
  if (!user) return res.status(200).json({ message: 'If this email exists, reset instructions were sent.' });

  const resetToken = jwt.sign({ email, action: 'password_reset' }, JWT_SECRET, { expiresIn: '20m' });
  resetTokensByEmail.set(email, resetToken);
  if (!persistStore()) return res.status(500).json({ message: 'Unable to generate reset token right now.' });
  return res.status(200).json({ message: 'Password reset token generated for demo usage.', resetToken });
});

router.post('/reset-password', async (req, res) => {
  const email = String(req.body?.email || '').trim().toLowerCase();
  const resetToken = String(req.body?.resetToken || '');
  const newPassword = String(req.body?.newPassword || '');
  if (!email || !resetToken || !newPassword) {
    return res.status(400).json({ message: 'Email, reset token, and new password are required.' });
  }

  const tokenFromStore = resetTokensByEmail.get(email);
  if (!tokenFromStore || tokenFromStore !== resetToken) {
    return res.status(400).json({ message: 'Invalid or expired reset token.' });
  }

  const passwordErrors = getPasswordErrors(newPassword);
  if (passwordErrors.length > 0) return res.status(400).json({ message: 'Password is not strong enough.', errors: passwordErrors });

  try {
    const payload = jwt.verify(resetToken, JWT_SECRET);
    if (payload.action !== 'password_reset' || payload.email !== email) {
      return res.status(400).json({ message: 'Invalid reset token payload.' });
    }
    const user = usersByEmail.get(email);
    if (!user) return res.status(404).json({ message: 'User not found.' });

    const passwordHash = await bcrypt.hash(newPassword, 10);
    usersByEmail.set(email, { ...user, passwordHash });
    resetTokensByEmail.delete(email);
    if (!persistStore()) return res.status(500).json({ message: 'Password reset failed while saving data.' });
    return res.status(200).json({ message: 'Password reset successful.' });
  } catch (_error) {
    return res.status(400).json({ message: 'Invalid or expired reset token.' });
  }
});

router.get('/me', authMiddleware, (req, res) => {
  const normalizedEmail = String(req.user.email || '').toLowerCase();
  const user = usersByEmail.get(normalizedEmail);
  if (!user) return res.status(404).json({ message: 'User not found.' });

  return res.status(200).json({
    user: {
      email: user.email,
      phone: user.phone || '',
      userType: user.userType || 'individual',
      createdAt: user.createdAt,
    },
  });
});

module.exports = router;
