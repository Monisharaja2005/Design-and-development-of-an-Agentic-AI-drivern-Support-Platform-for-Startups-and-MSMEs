const multer = require('multer');

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    const allowed = ['application/pdf', 'image/png', 'image/jpeg'];
    if (!allowed.includes(file.mimetype)) {
      return cb(new Error('Only PDF, PNG, and JPG files are allowed.'));
    }
    return cb(null, true);
  },
});

module.exports = { upload };
