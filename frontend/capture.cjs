const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const outDir = 'C:\\Users\\91915\\.gemini\\antigravity\\brain\\554c6934-1cb8-47f1-a90b-cf1388ad8c72';

(async () => {
  console.log("Launching Chrome...");
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    defaultViewport: { width: 1440, height: 900 },
    headless: "new"
  });
  
  const page = await browser.newPage();
  console.log("Navigating to app...");
  await page.goto("http://localhost:5176/", { waitUntil: 'networkidle0' });
  
  // Wait for React and Framer Motion
  await new Promise(r => setTimeout(r, 2000));
  
  console.log("Taking login screenshot...");
  await page.screenshot({ path: path.join(outDir, 'karios_new_login.png') });
  
  console.log("Entering credentials...");
  await page.type('input[type="email"]', 'founder@company.in');
  await page.type('input[type="password"]', 'Password123!');
  
  console.log("Clicking sign in...");
  // Click the "Continue" or "Sign In" button directly by selecting the button inside .actions
  await page.click('.actions button.btn.primary');
  
  console.log("Waiting for schemes to load...");
  // Wait for the feed container or at least 5 seconds for the API call to resolve
  await new Promise(r => setTimeout(r, 6000));
  
  console.log("Taking feed screenshot...");
  await page.screenshot({ path: path.join(outDir, 'karios_new_feed.png') });
  
  console.log("Clicking corner profile...");
  try {
    await page.click('.user-profile-corner');
    await new Promise(r => setTimeout(r, 1000));
    console.log("Taking profile modal screenshot...");
    await page.screenshot({ path: path.join(outDir, 'karios_new_profile_modal.png') });
  } catch(e) {
    console.log("Profile corner not found or failed to click.");
  }

  await browser.close();
  console.log("Done.");
})();
