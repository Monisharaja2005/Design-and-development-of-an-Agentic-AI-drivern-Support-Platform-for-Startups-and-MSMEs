import fs from 'fs';

const cssPath = 'd:/Main_project1/final/frontend/src/App.css';
let css = fs.readFileSync(cssPath, 'utf-8');

// Replace aspect ratio with max height for the card
css = css.replace(
  '  aspect-ratio: 9/16;',
  '  height: 85%;\n  max-height: 800px;'
);

// Replace absolute action button layout to make it responsive
css = css.replace(
  '  right: 24px;\n  bottom: 120px;',
  '  left: 50%;\n  margin-left: 260px;\n  bottom: 120px;'
);

fs.writeFileSync(cssPath, css);
console.log("CSS fixed successfully.");
