// Exercise the delivered file:// artifact without a web server or network.
const {chromium}=require('./playwright-runtime.cjs');
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'mechanical/universal-mount-r01');
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--enable-unsafe-swiftshader']});
 try{
  const page=await browser.newPage({viewport:{width:1600,height:1120},deviceScaleFactor:1});
  const errors=[],external=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route(/^https?:/,route=>{external.push(route.request().url());return route.abort();});
  await page.goto('file://'+path.join(out,'viewer.html'),{waitUntil:'load'});
  await page.waitForFunction(()=>window.__CAD_READY__||window.__CAD_ERROR__,{timeout:30000});
  assert.equal(await page.evaluate(()=>window.__CAD_ERROR__),undefined);
  const captures=[];
  async function capture(name){await page.waitForTimeout(350);await page.screenshot({path:path.join(out,'view-'+name+'.png')});captures.push(name);}
  await capture('mounted');
  for(const view of ['exploded','underside','pcb','parts']){
   await page.locator('[data-view="'+view+'"]').click();
   assert.equal((await page.evaluate(()=>window.__CAD_STATE__)).view,view);
   await capture(view);
  }
  await page.locator('[data-view="underside"]').click();
  const cases=[];
  for(const option of ['narrow','standard','wide','rope_small','rope','rope_large']){
   await page.selectOption('#collar',option);
   const s=await page.evaluate(()=>window.__CAD_STATE__);
   assert(s.visible.includes(option+'_collar'));assert(s.visible.includes(option+'_installed_straps'));
   assert(s.visible.includes(option.startsWith('rope')?'round_pad':'flat_pad'));
   cases.push(option);
  }
  await page.selectOption('#collar','rope');await capture('round');
  await page.locator('[data-view="mounted"]').click();
  await page.selectOption('#collar','standard');await page.check('#ghost');await capture('inside');
  await page.uncheck('#ghost');
  await page.locator('#explode').fill('50');
  assert.equal((await page.evaluate(()=>window.__CAD_STATE__)).explode,.5);
  await page.locator('#reference').click();assert(await page.locator('#modal').isVisible());
  await page.keyboard.press('Escape');assert(!(await page.locator('#modal').isVisible()));
  await page.locator('[data-view="mounted"]').click();
  const canvas=page.locator('canvas'),box=await canvas.boundingBox();
  await page.mouse.move(box.x+500,box.y+400);await page.mouse.down();await page.mouse.move(box.x+560,box.y+425);await page.mouse.up();await page.mouse.wheel(0,-70);
  await page.setViewportSize({width:430,height:932});await page.waitForTimeout(250);
  const dimensions=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,viewport:innerWidth}));assert.equal(dimensions.scroll,dimensions.viewport);
  // Clean orthogonal outputs for the engineering overview, from the same scene.
  await page.setViewportSize({width:1100,height:900});
  await page.addStyleTag({content:'header,.panel,.views,.caption,.hint,.scale{display:none!important}main{display:block;height:100vh;min-height:0}#stage{height:100vh;min-height:0}'});
  for(const view of ['mounted','exploded','underside']){
   await page.evaluate(v=>document.querySelector('[data-view="'+v+'"]').click(),view);
   await page.waitForTimeout(350);await page.screenshot({path:path.join(out,'render-'+view+'.png')});
  }
  await page.evaluate(()=>{const el=document.querySelector('#collar');el.value='rope';el.dispatchEvent(new Event('change'));});await page.waitForTimeout(350);await page.screenshot({path:path.join(out,'render-round.png')});
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  const result={file_protocol:true,network_requests:external,uncaught_errors:errors,views:captures,collar_cases:cases,slider:true,ghost:true,reference_image:true,orbit_zoom:true,mobile_no_horizontal_overflow:true};
  fs.writeFileSync(path.join(out,'viewer-checks.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
