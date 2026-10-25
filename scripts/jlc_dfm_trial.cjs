// Upload manufacturing layers only to the requested JLCDFM checker.
// No orders, messages, rule changes, or user browser credentials.
const {chromium}=require('./playwright-runtime.cjs');
const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const root=path.resolve(__dirname,'..');
const [zipArg,tag]=process.argv.slice(2);
if (!zipArg || !/^[a-z0-9-]+$/.test(tag)) throw Error('usage: zip trial-tag');
const zip=path.resolve(zipArg);
const zipSha=crypto.createHash('sha256').update(fs.readFileSync(zip)).digest('hex');
const out=path.join(root,'evidence/zero-warning-r033',tag);
fs.mkdirSync(out,{recursive:true});
(async()=>{
 const ctx=await chromium.launchPersistentContext(path.join(root,'evidence/zero-warning-r033/browser-profile'),{headless:true,viewport:{width:1440,height:1000},serviceWorkers:'block'});
 const pending=[];let serial=0,uploadId=null,uploadRequested=false;
 ctx.on('request',r=>{if(new URL(r.url()).pathname.endsWith('/pcbDfm/uploadGerber'))uploadRequested=true;});
 await ctx.route('**/*',r=>/datacollect|onlineVisitor\/save/.test(r.request().url())?r.abort():r.continue());
 ctx.on('response',r=>{
  const u=new URL(r.url());
  if (!/\/pcbDfm\/(uploadGerber|getParseStatus|getDfmFile|getDfmConfigFile)$|\/file\/downloadByFileAccessId$/.test(u.pathname)) return;
  const n=++serial;
  pending.push((async()=>{
   try {
    const b=await r.body();const endpoint=u.pathname.split('/').pop();
    if(endpoint==='uploadGerber'){
     const response=JSON.parse(b.toString());
     if(response.code===200){
      uploadId=String(response.data||response.message);
      fs.writeFileSync(path.join(out,'upload-receipt.json'),JSON.stringify({zip,zip_sha256:zipSha,record_id:uploadId},null,2));
     }
    }
    const name=String(n).padStart(3,'0')+'-'+endpoint;
    fs.writeFileSync(path.join(out,name+'.bin'),b);
    fs.writeFileSync(path.join(out,name+'.meta.json'),JSON.stringify({url:r.url(),status:r.status(),bytes:b.length},null,2));
    console.log(endpoint,r.status(),b.length);
   }catch(e){console.log('capture failed',u.pathname,e.message.slice(0,120));}
  })());
 });
 try {
  let p=await ctx.newPage();
  await p.goto('https://jlcdfm.com',{waitUntil:'domcontentloaded',timeout:30000});
  // SSR exposes the file input before Vue/auth have hydrated; early selections
  // can be discarded without an upload request. Wait for the logged-in header.
  await p.getByText('My Account',{exact:true}).first().waitFor({state:'attached',timeout:45000});
  if(await p.getByText('Reject All',{exact:true}).isVisible())await p.getByText('Reject All',{exact:true}).click();
  await p.waitForLoadState('networkidle',{timeout:10000}).catch(()=>{});
  await p.locator('input[type=file]').first().setInputFiles(zip);
  console.log('Selected',path.basename(zip));
  let analysisTriggered=false,stableRows='',stablePasses=0;
  for (let i=0;i<30;i++) {
   await p.waitForTimeout(4000);
   if(i===2 && !uploadRequested){
    // Retry only if no upload request was sent; never duplicate an in-flight upload.
    console.log('Retrying file selection after hydration; no upload request was issued');
    await p.locator('input[type=file]').first().setInputFiles([]);
    await p.locator('input[type=file]').first().setInputFiles(zip);
   }
   p=ctx.pages().find(q=>uploadId && new URL(q.url()).searchParams.get('pcbUploadFileId')===uploadId) || p;
   const body=await p.locator('body').innerText();
   fs.writeFileSync(path.join(out,'latest.txt'),body);
   const u=new URL(p.url());
   const safeUrl=u.hostname==='passport.jlcpcb.com'?u.origin+u.pathname:p.url();
   fs.writeFileSync(path.join(out,'url.txt'),safeUrl);
   if(u.hostname==='passport.jlcpcb.com'){console.log('LOGIN_REQUIRED');break;}
   if(i%3===0) console.log('state',i,safeUrl,body.slice(0,500).replace(/\n/g,' | '));
   if(/Upload failed|upload failed/.test(body)){console.log(body.slice(-4000));break;}
   if(p.url().includes('/viewer') && /Pad spacing\tUnanalyzed/.test(body) && !analysisTriggered){
    await p.getByText('DFM check',{exact:true}).first().evaluate(el=>el.click());analysisTriggered=true;
   }
   const rows=(body.match(/[^\n]+\t\d+,\s*\d+,\s*\d+\tDetails/g)||[]).join('\n');
   if(analysisTriggered && rows.split('\n').length===29 && !/Unanalyzed|Performing DFM/.test(body)){
    stablePasses=rows===stableRows?stablePasses+1:1;stableRows=rows;
    if(stablePasses>=2)break;
   }
  }
  await p.screenshot({path:path.join(out,'screen.png'),fullPage:true});
  fs.writeFileSync(path.join(out,'page.html'),await p.content());
  console.log((await p.locator('body').innerText()).slice(0,9000));
  if(/Pad spacing\t\d+,/.test(await p.locator('body').innerText())){
   if(stablePasses<2 || new URL(p.url()).searchParams.get('pcbUploadFileId')!==uploadId)throw Error('Incomplete or wrong-record analysis');
   if(crypto.createHash('sha256').update(fs.readFileSync(zip)).digest('hex')!==zipSha)throw Error('Upload input changed');
   const downloadPromise=p.waitForEvent('download',{timeout:45000});
   await p.locator('[title="Export analysis report"]').evaluate(el=>el.click());
   const download=await downloadPromise;await download.saveAs(path.join(out,download.suggestedFilename()));
   console.log('PDF saved',download.suggestedFilename());
  } else throw Error('No complete analyzed record; this run is not a DFM result');
 } finally {await Promise.allSettled(pending);await ctx.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
