const {defineConfig, devices} = require('@playwright/test');
// 1.63 avoids WebKit's native-select CSP regression in 1.64.x:
// https://github.com/microsoft/playwright/issues/43497
module.exports = defineConfig({
  testDir: '.',
  testMatch: '*.spec.js',
  timeout: 90000,
  expect: {timeout: 10000},
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 2,
  reporter: [['list'], ['json', {outputFile: '../.local/web-e2e/results.json'}]],
  outputDir: '../.local/web-e2e/artifacts',
  use: {
    baseURL: process.env.WORKSHOP_BASE_URL || 'http://127.0.0.1:8765/agentic-transformation-workshop-latam/',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure'
  },
  projects: [
    {name: 'chromium', use: {...devices['Desktop Chrome']}},
    {name: 'webkit', use: {...devices['Desktop Safari']}},
    {name: 'mobile', use: {...devices['Pixel 7']}}
  ],
  webServer: process.env.WORKSHOP_BASE_URL ? undefined : {
    command: 'python3 ../scripts/build_site.py --output ../.local/web-test/agentic-transformation-workshop-latam && python3 -m http.server 8765 --bind 127.0.0.1 --directory ../.local/web-test',
    url: 'http://127.0.0.1:8765/agentic-transformation-workshop-latam/practica/',
    reuseExistingServer: false,
    stdout: 'ignore', stderr: 'ignore'
  }
});
