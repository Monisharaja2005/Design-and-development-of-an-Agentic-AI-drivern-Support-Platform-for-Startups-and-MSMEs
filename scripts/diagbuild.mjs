import { execSync } from 'child_process';
try {
  execSync('npm run build', { cwd: 'd:/Main_project1/final/frontend', stdio: 'inherit' });
} catch(e) {
  console.error('Build failed');
}
