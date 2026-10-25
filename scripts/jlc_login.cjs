const {chromium}=require('./playwright-runtime.cjs');
const path=require('path');
(async()=>{
 const c=await chromium.launchPersistentContext(path.resolve('evidence/zero-warning-r033/browser-profile'),{headless:false,viewport:{width:1440,height:1000},serviceWorkers:'block'});
 const p=await c.newPage();await p.goto('https://jlcdfm.com',{waitUntil:'domcontentloaded'});
 await p.waitForTimeout(3000);
 await p.getByText('Sign In',{exact:true}).first().evaluate(el=>el.click());
 console.log('Login window open. No credentials are read or logged.');
 const timeout=Date.now()+30*60*1000;
 while(Date.now()<timeout){
  await new Promise(r=>setTimeout(r,5000));
  if(p.isClosed()) break;
  if(new URL(p.url()).hostname==='jlcdfm.com'){
   await p.waitForTimeout(3000);
   if(await p.getByText('Sign In',{exact:true}).count()===0){console.log('LOGIN_RETURNED');break;}
  }
 }
 await c.close();
})().catch(e=>{console.error(e.message);process.exitCode=1});
