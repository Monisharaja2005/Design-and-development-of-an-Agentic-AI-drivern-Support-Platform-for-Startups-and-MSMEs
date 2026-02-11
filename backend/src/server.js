const app = require('./app');
const { PORT } = require('./config/constants');

app.listen(PORT, () => {
  console.log(`Backend running on http://localhost:${PORT}`);
});
