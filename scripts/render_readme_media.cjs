// Render documentation media from the preserved CAD viewer. No CAD is changed.
const {chromium}=require('./playwright-runtime.cjs');
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {spawnSync}=require('child_process');
const root=path.resolve(__dirname,'..');
const source=path.join(root,'mechanical/universal-mount-r01/viewer.html');
const out=path.join(root,'docs/media'),run=path.join(root,'.runtime/readme-media');
fs.mkdirSync(out,{recursive:true});fs.mkdirSync(run,{recursive:true});
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const sourceHash=sha(source);
const hook=`
window.__README_FRAME__=(kind,t)=>{
 const smooth=v=>v*v*(3-2*v);
 if(kind==='assembly'){
  const q=t<.15?0:t<.40?smooth((t-.15)/.25):t<.60?1:t<.85?1-smooth((t-.60)/.25):0;
  Object.assign(state,{view:q?'exploded':'mounted',explode:q,collar:'standard',ghost:false});update();
  for(const[n,o]of Object.entries(objects))if(n.endsWith('_collar')||n.endsWith('_installed_straps'))o.visible=false;
  az=-.95+.14*Math.sin(2*Math.PI*t);el=.58;distance=205+85*q;target.set(0,0,4+16*q);
  floor.position.z=-39;floor.visible=true;
  document.querySelector('#phase').textContent=q>.9?'PCB · BATTERY · ANTENNAS · GASKET':q<.1?'ENCLOSURE + REMOVABLE HOLDER':'ASSEMBLY LAYERS';
 }else{
  const cases=['standard','narrow','wide','rope'];const names=['FLAT 25 × 3 MM','FLAT 8 × 1 MM','FLAT 60 × 8 MM','ROUND Ø8 MM'];
  const index=Math.min(3,Math.floor(t*4));Object.assign(state,{view:'underside',explode:0,collar:cases[index],ghost:false});update();
  az=-.95+.14*Math.sin(t*8*Math.PI);el=-.62;distance=235;target.set(0,0,-3);floor.visible=false;
  document.querySelector('#phase').textContent=names[index];
 }
 frame();return {view:state.view,collar:state.collar,explode:state.explode};
};
`;
let html=fs.readFileSync(source,'utf8');
const needle="update();resetCamera();resize();frame();document.querySelector('#loading').remove();window.__CAD_READY__=true;";
if(!html.includes(needle))throw Error('Pinned viewer initialization changed');
html=html.replace(needle,hook+needle).replace('requestAnimationFrame(frame);','/* Deterministic documentation frame. */');
const pagePath=path.join(run,'capture.html');fs.writeFileSync(pagePath,html);
function command(exe,args){const r=spawnSync(exe,args,{cwd:root,encoding:'utf8',maxBuffer:2*1024*1024});if(r.status!==0)throw Error(exe+': '+r.stderr.slice(-2000));}
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--enable-unsafe-swiftshader']});
 const errors=[],requests=[],records=[];
 try{
  const page=await browser.newPage({viewport:{width:960,height:600},deviceScaleFactor:1});
  page.on('pageerror',e=>errors.push(e.message));
  await page.route(/^https?:/,r=>{requests.push(r.request().url());return r.abort();});
  await page.goto('file://'+pagePath);
  await page.waitForFunction(()=>window.__CAD_READY__||window.__CAD_ERROR__);
  if(await page.evaluate(()=>window.__CAD_ERROR__))throw Error(await page.evaluate(()=>window.__CAD_ERROR__));
  await page.addStyleTag({content:'header,.panel,.views,.caption,.hint,.scale{display:none!important}main{display:block;height:100vh;min-height:0}#stage{height:100vh;min-height:0}.readme-label{position:absolute;z-index:5;left:26px;right:26px;pointer-events:none;font-family:Arial,sans-serif}.readme-top{top:24px;font-size:12px;font-weight:700;letter-spacing:2px;color:#426553}.readme-bottom{bottom:22px;display:flex;justify-content:space-between;gap:20px;font-size:11px;letter-spacing:1px;color:#527361}#phase{color:#203e31;font-weight:700}'});
  await page.evaluate(()=>{
   document.querySelector('#stage').insertAdjacentHTML('beforeend','<div class="readme-label readme-top" id="mediaTitle"></div><div class="readme-label readme-bottom"><span id="phase"></span><span id="mediaNote"></span></div>');
  });
  // Let ResizeObserver settle before the first manual render; a resize clears
  // the WebGL drawing buffer and would otherwise leave an empty first frame.
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  for(const [kind,count,fps] of [['assembly',96,12],['mount',96,12]]){
   const dir=path.join(run,kind);fs.mkdirSync(dir,{recursive:true});
   await page.evaluate(k=>{document.querySelector('#mediaTitle').textContent=k==='assembly'?'COLLAR TRACKER / FROM SHELL TO PCB':'ONE HOLDER / DIFFERENT COLLARS';document.querySelector('#mediaNote').textContent=k==='assembly'?'PARAMETRIC CAD · PROTOTYPE':'NOMINAL FIT EXAMPLES · ROUTING ENVELOPES';},kind);
   for(let i=0;i<count;i++){
    const state=await page.evaluate(({kind,t})=>window.__README_FRAME__(kind,t),{kind,t:i/(count-1)});
    await page.screenshot({path:path.join(dir,String(i).padStart(3,'0')+'.png')});
    if([0,Math.floor(count/2)].includes(i))records.push({kind,frame:i,...state});
   }
   command('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate',String(fps),'-i',path.join(dir,'%03d.png'),'-filter_complex','[0:v]split[a][b];[a]palettegen=max_colors=128:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle','-loop','0',path.join(out,kind+'.gif')]);
   fs.copyFileSync(path.join(dir,'000.png'),path.join(out,kind+'-poster.png'));
   const crop=spawnSync('magick',[path.join(out,kind+'-poster.png'),'-crop','600x400+180+100','+repage','-format','%[fx:standard_deviation]','info:'],{encoding:'utf8'});
   if(crop.status!==0||Number(crop.stdout)<.04)throw Error(kind+': empty or failed poster render');
   console.log(kind+'.gif',fs.statSync(path.join(out,kind+'.gif')).size,'bytes',count,'frames');
  }
 }finally{await browser.close();}
 if(errors.length||requests.length)throw Error(JSON.stringify({errors,requests}));
 if(sha(source)!==sourceHash)throw Error('Preserved viewer changed');
 command('magick',[path.join(root,'mechanical/universal-mount-r01/pcb-top.png'),'-resize','960x','-quality','86',path.join(out,'pcb.webp')]);
 const files=['assembly.gif','mount.gif','assembly-poster.png','mount-poster.png','pcb.webp'];
 const diagram=path.join(out,'architecture.svg');
 fs.writeFileSync(path.join(out,'provenance.json'),JSON.stringify({source:path.relative(root,source),source_sha256:sourceHash,method:'Deterministic camera and separation poses of the existing CAD scene; no mesh or native PCB changes.',render:'Playwright / Three.js',encoding:'FFmpeg, 960x600, 12 fps, 96 frames, 128-color palette',limits:'Component envelopes and installed strap routing are simplified; this is not a physical prototype demonstration.',network_requests:requests,uncaught_errors:errors,sampled_states:records,outputs:Object.fromEntries(files.map(f=>[f,{sha256:sha(path.join(out,f)),bytes:fs.statSync(path.join(out,f)).size}])),diagram:{source:path.relative(root,diagram),sha256:sha(diagram),basis:['firmware/tracker/README.md','firmware/tracker-r02/README.md','firmware/tracker-r03/README.md','firmware/receiver/README.md']}},null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
