// Development-site integration check. Creates a uniquely named audit request and registered correspondence.
const assert = require('node:assert/strict');
const { chromium } = require(process.env.DIWAN_PLAYWRIGHT || 'playwright-core');
(async () => {
 const browser = await chromium.connectOverCDP(process.env.DIWAN_UI_CDP);
 const page = await browser.contexts()[0].newPage();
 const base = process.env.DIWAN_UI_URL;
 const errors = [];
 page.on('pageerror', e => errors.push(e.message));
 try {
  const routes = ['/diwan/requests', '/diwan/requests?tab=submit', '/diwan/queue', ...['tray','delivery_sheets','envelopes','audit_log'].map(t=>'/diwan/queue?tab='+t)];
  for (const lang of ['en','ar']) for (const width of [360,768,1440]) {
   await page.setViewportSize({width,height:1000});
   for (const route of routes) {
    const response = await page.goto(base+route+(route.includes('?')?'&':'?')+'_lang='+lang,{waitUntil:'networkidle'});
    assert.equal(response.status(),200,route);
    assert.equal(await page.locator('.diwan-app').getAttribute('dir'),lang==='ar'?'rtl':'ltr');
    assert.ok(await page.locator('h1').innerText());
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,route+' '+lang+' '+width);
    const languageLink = await page.locator('.diwan-navbar__lang a').first().getAttribute('href');
    assert.equal(new URL(languageLink,base).searchParams.get('tab'),new URL(route,base).searchParams.get('tab'));
   }
  }
  console.log('PASS: seven tab views × two languages × three widths; tab-preserving language links.');
  await page.goto(base+'/diwan/requests?tab=submit&_lang=en',{waitUntil:'networkidle'});
  await page.locator('#field-subject').fill('UI audit - upstream rebase '+Date.now());
  await page.locator('#field-draft-text').fill('Approval and registration are separate steps.');
  await page.locator('#save-draft-btn').click();
  await page.waitForFunction(()=>document.querySelector('#form-message').innerText.includes('Saved as draft.'));
  const name = new URL(page.url()).searchParams.get('name');
  assert.ok(name);
  await page.goto(base+'/diwan/submit?name='+encodeURIComponent(name)+'&_lang=en',{waitUntil:'networkidle'});
  assert.equal(new URL(page.url()).searchParams.get('tab'),'submit');
  assert.equal(new URL(page.url()).searchParams.get('name'),name);
  assert.match(await page.locator('#field-subject').inputValue(),/upstream rebase/);
  await page.locator('#submit-btn').click();
  await page.waitForURL('**/diwan/requests?name=*');
  await page.waitForFunction(()=>document.querySelector('#status-pill')?.textContent==='Pending Review');
  await page.goto(base+'/diwan/queue?name='+encodeURIComponent(name)+'&_lang=en',{waitUntil:'networkidle'});
  await page.locator('#start-review-btn').click();
  await page.waitForSelector('#approve-btn');
  assert.equal(await page.locator('#field-correspondence-type').count(),0);
  await page.locator('#approve-btn').click();
  await page.waitForSelector('#register-btn');
  assert.match(await page.locator('#status-pill').innerText(),/^Approved$/);
  await page.locator('#register-btn').click();
  assert.match(await page.locator('#decision-message').innerText(),/before registering/);
  assert.equal(await page.evaluate(()=>document.activeElement.id),'field-correspondence-type');
  const type=await page.locator('#field-correspondence-type option').evaluateAll(os=>os.find(o=>o.value)?.value);
  assert.ok(type);
  await page.locator('#field-correspondence-type').selectOption(type);
  await page.locator('#register-btn').click();
  await page.waitForFunction(()=>document.querySelector('#status-pill')?.textContent==='Approved & Numbered');
  const doc=await page.evaluate(async name=>(await frappe.call({method:'frappe.client.get',args:{doctype:'Correspondence Request',name}})).message,name);
  assert.equal(doc.status,'Approved & Numbered');assert.ok(doc.resulting_correspondence);
  await page.goto(base+'/diwan/requests?name='+encodeURIComponent(name)+'&_lang=en',{waitUntil:'networkidle'});
  assert.equal(await page.locator('.diwan-stepper__step').count(),5);
  console.log('PASS: legacy draft redirect → same-request submission → review → approval without type → registration with type → stored reference and five-stage requester timeline.');
  console.log(JSON.stringify({request:name,correspondence:doc.resulting_correspondence}));
  await page.screenshot({path:'/tmp/diwan-rebase-outcome.png',fullPage:true});
  assert.deepEqual(errors,[]);
 } catch (error) { console.error("Failed at",page.url(),(await page.locator("body").innerText()).slice(-2000)); throw error; } finally { await page.close();await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
