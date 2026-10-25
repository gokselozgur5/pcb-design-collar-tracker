const {chromium}=require('./playwright-runtime.cjs');
const fs=require('fs'),path=require('path'),readline=require('readline');
const root=path.resolve(__dirname,'..');
const [id,tag]=process.argv.slice(2);
if(!/^\d+$/.test(id)||!/^[a-z0-9-]+$/.test(tag))throw Error('record-id tag required');
const out=path.join(root,'evidence/zero-warning-r033',tag);fs.mkdirSync(out,{recursive:true});
(async()=>{
 const c=await chromium.launchPersistentContext(path.join(root,'evidence/zero-warning-r033/browser-profile'),{headless:true,viewport:{width:1600,height:1200},serviceWorkers:'block',acceptDownloads:true});
 await c.route('**/*',r=>/datacollect|onlineVisitor\/save/.test(r.request().url())?r.abort():r.continue());
 let serial=0;const pending=[];
 c.on('response',r=>{
  const u=new URL(r.url());if(!/\/pcbDfm\/|\/file\/downloadByFileAccessId$/.test(u.pathname))return;
  const n=String(++serial).padStart(3,'0')+'-'+u.pathname.split('/').pop();
  pending.push((async()=>{try{const b=await r.body();fs.writeFileSync(path.join(out,n+'.bin'),b);fs.writeFileSync(path.join(out,n+'.meta.json'),JSON.stringify({url:r.url(),status:r.status(),bytes:b.length},null,2));console.log('CAPTURE',n,r.status(),b.length)}catch(e){console.log('CAPTURE_ERROR',n)}})());
 });
 const p=await c.newPage();
 p.on('download',d=>{pending.push(d.saveAs(path.join(out,d.suggestedFilename())).then(()=>console.log('DOWNLOAD',d.suggestedFilename())))});
 await p.goto('https://jlcdfm.com/viewer?pcbUploadFileId='+id,{waitUntil:'domcontentloaded'});
 console.log('READY');
 let queue=Promise.resolve();
 const rl=readline.createInterface({input:process.stdin,terminal:false});
 rl.on('line',line=>{queue=queue.then(async()=>{try{
  const a=JSON.parse(line);
  if(a.op==='text'){const t=await p.locator('body').innerText();fs.writeFileSync(path.join(out,'latest.txt'),t);console.log(t.slice(0,a.limit||9000))}
  else if(a.op==='click') await p.getByText(a.text,{exact:true}).first().evaluate(el=>el.click());
  else if(a.op==='button')await p.getByRole('button',{name:a.text,exact:true}).click();
  else if(a.op==='eval')console.log(JSON.stringify(await p.evaluate(a.code)));
  else if(a.op==='screenshot')await p.screenshot({path:path.join(out,a.name||'screen.png'),fullPage:true});
  else if(a.op==='exit'){await Promise.allSettled(pending);await c.close();rl.close();process.exit(0)}
  else throw Error('unknown operation');
  console.log('DONE',a.op);
 }catch(e){console.log('ERROR',e.message)}})});
})().catch(e=>{console.error(e.message);process.exitCode=1});
