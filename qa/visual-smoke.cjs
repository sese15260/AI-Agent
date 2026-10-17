// Local UI check with a mocked API. Screenshots are previews, not submission evidence.
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..');
const csv = fs.readFileSync(path.join(root, 'backend', 'data', 'samsung_005930_daily.csv'), 'utf8').trim().split(/\r?\n/);
const rows = csv.slice(1).map(line => {
  const [date, value] = line.split(',');
  return {id: date, date, value: Number(value), memo: '삼성전자 일별 종가'};
});
const values = rows.map(row => row.value);
const mean = items => items.reduce((a, b) => a + b, 0) / items.length;
const high = rows.reduce((a, b) => a.value > b.value ? a : b);
const low = rows.reduce((a, b) => a.value < b.value ? a : b);
const summary = {
  symbol:'005930', name:'삼성전자', unit:'KRW',
  period:{start:rows[0].date,end:rows.at(-1).date}, count:rows.length,
  metrics:{average:mean(values), max:high.value, max_date:high.date, min:low.value, min_date:low.date,
    latest:rows.at(-1).value, latest_date:rows.at(-1).date, first:rows[0].value,
    total_change_percent:0, recent_change_percent:0}, trend:'최근 20거래일 보합 (0.00%)',
};

(async () => {
  const browser = await chromium.launch({executablePath:process.env.CHROME_PATH,headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:950}});
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('http://localhost:8000/**', async route => {
    const pathname = new URL(route.request().url()).pathname;
    const body = pathname === '/api/data' ? rows : pathname === '/api/data/summary' ? summary
      : pathname === '/api/conversations' ? [] : pathname === '/api/chat'
        ? {answer:`${rows.at(-1).date} 종가는 ${rows.at(-1).value.toLocaleString('ko-KR')}원입니다.`,conversation_id:'preview',summary}
        : {status:'ok'};
    await route.fulfill({status:200,contentType:'application/json',headers:{
      'access-control-allow-origin':'*',
      'access-control-allow-headers':'content-type,x-access-key',
      'access-control-allow-methods':'GET,POST,PUT,DELETE,OPTIONS',
    },body:JSON.stringify(body)});
  });
  const url = pathToFileURL(path.join(root,'frontend','index.html')).href + '#access=preview-token';
  await page.goto(url,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(() => document.querySelector('#status')?.textContent === 'API 연결됨');
  if (await page.locator('#data-rows tr').count() !== 20) throw new Error('The recent 20 data rows were not rendered');
  await page.locator('#filter-date').fill(rows[0].date);
  if (await page.locator('#data-rows tr').count() !== 1 ||
      !await page.locator('#data-rows tr').innerText().then(text => text.includes(rows[0].date))) {
    throw new Error('Older rows are not searchable for editing');
  }
  await page.locator('#filter-date').fill('');
  if (await page.locator('#price-chart polyline').count() !== 1) throw new Error('Chart was not rendered');
  await page.locator('#theme-toggle').click();
  if (!await page.locator('body').evaluate(node => node.classList.contains('light'))) throw new Error('Light theme failed');
  const downloadPromise = page.waitForEvent('download');
  await page.locator('#export-data').click();
  const download = await downloadPromise;
  if (download.suggestedFilename() !== 'samsung_005930_close.csv') throw new Error('CSV export failed');
  await page.locator('#chat-input').fill('최근 종가는?');
  await page.locator('#chat-form button').click();
  await page.locator('.bubble.assistant').waitFor();
  if (errors.length) throw new Error(errors.join('; '));
  await page.screenshot({path:path.join(root,'.qa-desktop.png')});
  await page.setViewportSize({width:390,height:844});
  await page.screenshot({path:path.join(root,'.qa-mobile.png'),fullPage:true});
  console.log('UI smoke passed: 250 source rows, recent 20 visible rows, chart, theme, CSV export, chat, desktop/mobile previews');
  await Promise.race([browser.close(), new Promise(resolve => setTimeout(resolve, 3000))]);
  process.exit(0);
})().catch(error => {console.error(error);process.exit(1);});
