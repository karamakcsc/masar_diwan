// Set DIWAN_ENVELOPE_TARGET to an existing, readable development envelope name.
const assert=require('node:assert/strict');
const {chromium}=require(process.env.DIWAN_PLAYWRIGHT || 'playwright-core');
(async()=>{
 const browser=await chromium.connectOverCDP(process.env.DIWAN_UI_CDP);
 const page=await browser.contexts()[0].newPage();const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 try {
  const name=process.env.DIWAN_ENVELOPE_TARGET;assert.ok(name);
  await page.goto(process.env.DIWAN_UI_URL+'/desk/correspondence-track?_lang=en',{waitUntil:'networkidle'});
  const search=page.locator('input[data-fieldname="search_text"]');
  await search.fill(name);await search.press('Enter');
  const result=page.locator('.correspondence-track-results').nth(1);
  await result.locator('.track-row-link').filter({hasText:name}).click();
  await page.waitForFunction(()=>document.querySelector('.correspondence-track-detail')?.textContent.includes('Open'));
  assert.match(await page.locator('.correspondence-track-detail').innerText(),new RegExp(name));
  assert.equal(await result.locator('th[scope="col"]').count(),4);
  assert.equal(await result.locator('[role="region"][tabindex="0"]').count(),1);
  await page.setViewportSize({width:360,height:900});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.screenshot({path:'/tmp/diwan-rebase-envelope-desk.png',fullPage:true});
  assert.deepEqual(errors,[]);
  console.log('PASS: real Desk envelope search → tracking detail; accessible results and mobile overflow.');
 } finally {await page.close();await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
