const data=JSON.parse(document.querySelector('#cad-data').textContent);
const bytes=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const moduleURL=URL.createObjectURL(new Blob([bytes(data.three)],{type:'text/javascript'}));
try {
const T=await import(moduleURL); URL.revokeObjectURL(moduleURL);
const stage=document.querySelector('#stage'),scene=new T.Scene();
scene.background=new T.Color('#e9eeeb');
const renderer=new T.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=T.SRGBColorSpace;renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=1.35;
renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
stage.prepend(renderer.domElement);
const camera=new T.PerspectiveCamera(33,1,.1,1500);camera.up.set(0,0,1);
scene.add(new T.HemisphereLight(0xffffff,0x718275,2.1));
const key=new T.DirectionalLight(0xffffff,3.2);key.position.set(-65,-90,160);key.castShadow=true;
key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-150,right:150,top:150,bottom:-150,near:1,far:400});key.shadow.bias=-.0004;scene.add(key);
const fill=new T.DirectionalLight(0xe8f2ff,1.8);fill.position.set(80,30,90);scene.add(fill);
const floor=new T.Mesh(new T.PlaneGeometry(1000,1000),new T.ShadowMaterial({color:0x496555,opacity:.16}));floor.position.z=-25;floor.receiveShadow=true;scene.add(floor);
function geometry(b64){
 const raw=bytes(b64),v=new DataView(raw.buffer),n=v.getUint32(80,true),p=new Float32Array(n*9);
 for(let i=0;i<n;i++)for(let j=0;j<9;j++)p[i*9+j]=v.getFloat32(84+i*50+12+j*4,true);
 const g=new T.BufferGeometry();g.setAttribute('position',new T.BufferAttribute(p,3));g.computeVertexNormals();g.computeBoundingSphere();return g;
}
const palette={body:0xdce0d7,lid:0xe5e7df,boot:0x243e3d,flat_pad:0x287f71,round_pad:0x287f71,carrier:0x4e9290,retainer:0x4a5c59,battery:0x414c51,pcb_substrate:0x186243,pcb_components:0x333a3e,contacts:0xb79a4b,gasket:0x1c2724,antennas:0xbb904b,terminals:0xc0a657,charge_wires:0x763d35,fasteners:0xa5afb0,rf:0x343d3c,staking:0xc7b381,strap_short:0x287f71,strap_long:0x287f71};
const offsets={boot:-16,flat_pad:-22,round_pad:-22,body:0,carrier:8,battery:14,pcb_substrate:25,pcb_components:25,retainer:34,antennas:44,gasket:51,lid:56,fasteners:56};
const baseZ={boot:-5.5,flat_pad:-7.8,round_pad:-12};
const objects={};
for(const [name,source]of Object.entries(data.meshes)){
 const isCollar=name.endsWith('_collar'),isStrap=name.endsWith('_installed_straps');
 const color=isCollar?0xa16c41:isStrap?0x287f71:palette[name]??0x8e9a93;
 const metallic=['contacts','terminals','fasteners','antennas'].includes(name);
 const material=new T.MeshStandardMaterial({color,roughness:metallic?.38:.68,metalness:metallic?.55:0});
 const mesh=new T.Mesh(geometry(source),material);mesh.castShadow=true;mesh.receiveShadow=true;mesh.name=name;scene.add(mesh);objects[name]=mesh;
}
// Package envelopes use the native footprint positions. The detailed PCB image
// is kept separately instead of presenting box approximations as vendor models.
const state={view:'mounted',collar:'standard',explode:0,ghost:false};
const viewText={mounted:['Built around the collar.','Two independent wrap straps secure the removable outer holder. The gasketed housing stays intact.'],exploded:['Every layer, in place.','Rigid shell, retained battery and PCB, antenna envelopes, gasket and lid. Internal models follow the current assembly.'],underside:['Wrap. Adjust. Secure.','Two replaceable straps thread through the holder. A flat pad or V-groove pad supports the collar underneath.'],pcb:['The board inside.','40 × 32 mm. This interactive view uses component envelopes; open the actual KiCad render for package and copper detail.'],parts:['One holder. Two pad choices.','Print the flexible holder, choose a flat or V-groove pad, then fit two matching short or long straps.']};
let az=-.95,el=.62,distance=215,target=new T.Vector3(0,0,4);
function resetCamera(){
 az=-.95;el=state.view==='underside'?-.65:state.view==='parts'?.85:.62;
 distance=state.view==='pcb'?115:state.view==='parts'?375:state.explode?300:215;
 target.set(0,0,state.view==='pcb'?11:state.view==='parts'?1:state.explode?20:4);
}
function update(){
 const rope=state.collar.startsWith('rope'),amount=state.explode;
 for(const[name,mesh]of Object.entries(objects)){
  mesh.rotation.set(0,0,0);mesh.position.set(0,0,baseZ[name]||0);mesh.visible=true;
  mesh.material.opacity=1;mesh.material.transparent=false;mesh.material.depthWrite=true;
  if(name.endsWith('_collar')||name.endsWith('_installed_straps')){mesh.visible=name.startsWith(state.collar+'_')&&amount===0;}
  if(name==='flat_pad')mesh.visible=!rope;
  if(name==='round_pad')mesh.visible=rope;
  if(name==='strap_short'||name==='strap_long')mesh.visible=false;
  if(amount>0){mesh.position.z+=(offsets[name]||0)*amount;if(['charge_wires','rf','staking'].includes(name))mesh.visible=false;}
  if(state.ghost&&['body','lid','boot'].includes(name)){mesh.material.opacity=.18;mesh.material.transparent=true;mesh.material.depthWrite=false;}
  if(state.view==='pcb')mesh.visible=['pcb_substrate','pcb_components'].includes(name);
  if(state.view==='parts'){
   mesh.visible=['boot','flat_pad','round_pad','strap_short','strap_long'].includes(name);mesh.position.z=0;
   if(name==='boot')mesh.position.set(-35,-18,0);
   if(name==='flat_pad')mesh.position.set(17,-28,0);
   if(name==='round_pad')mesh.position.set(17,9,0);
   if(name==='strap_short'){mesh.rotation.z=-Math.PI/2;mesh.position.set(-65,-62,0);}
   if(name==='strap_long'){mesh.rotation.z=-Math.PI/2;mesh.position.set(-110,52,0);}
  }
 }
 floor.visible=state.view!=='underside'&&!state.ghost;floor.position.z=state.view==='parts'?-.1:amount>0?-39:-25;
 document.querySelector('#viewTitle').textContent=viewText[state.view][0];document.querySelector('#viewDescription').textContent=viewText[state.view][1];
 document.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('active',b.dataset.view===state.view));
 document.querySelector('#explode').value=Math.round(amount*100);document.querySelector('#explodeValue').textContent=Math.round(amount*100)+'%';
 document.querySelector('#collar').disabled=['pcb','parts'].includes(state.view);
 window.__CAD_STATE__={...state,visible:Object.values(objects).filter(o=>o.visible).map(o=>o.name)};
}
for(const button of document.querySelectorAll('[data-view]'))button.onclick=()=>{state.view=button.dataset.view;state.explode=state.view==='exploded'?1:0;update();resetCamera();};
document.querySelector('#collar').onchange=e=>{state.collar=e.target.value;update();};
document.querySelector('#explode').oninput=e=>{state.explode=+e.target.value/100;state.view=state.explode?'exploded':'mounted';update();resetCamera();};
document.querySelector('#ghost').onchange=e=>{state.ghost=e.target.checked;update();};
const modal=document.querySelector('#modal');document.querySelector('#reference').onclick=()=>modal.classList.add('open');document.querySelector('#closeModal').onclick=()=>modal.classList.remove('open');
addEventListener('keydown',e=>{if(e.key==='Escape')modal.classList.remove('open');});
let drag=null;
renderer.domElement.onpointerdown=e=>{drag=[e.clientX,e.clientY];renderer.domElement.setPointerCapture(e.pointerId);};
renderer.domElement.onpointermove=e=>{if(!drag)return;az-=(e.clientX-drag[0])*.007;el=Math.max(-1.4,Math.min(1.4,el+(e.clientY-drag[1])*.006));drag=[e.clientX,e.clientY];};
renderer.domElement.onpointerup=()=>drag=null;renderer.domElement.onpointercancel=()=>drag=null;
renderer.domElement.addEventListener('wheel',e=>{e.preventDefault();distance=Math.max(65,Math.min(650,distance*Math.exp(e.deltaY*.001)));},{passive:false});
renderer.domElement.ondblclick=resetCamera;
function resize(){const w=stage.clientWidth,h=stage.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(stage);
function frame(){camera.position.set(target.x+distance*Math.cos(el)*Math.cos(az),target.y+distance*Math.cos(el)*Math.sin(az),target.z+distance*Math.sin(el));camera.lookAt(target);renderer.render(scene,camera);requestAnimationFrame(frame);}
update();resetCamera();resize();frame();document.querySelector('#loading').remove();window.__CAD_READY__=true;
}catch(error){document.querySelector('#loading').textContent='3D could not start: '+error.message;console.error(error);window.__CAD_ERROR__=String(error);}
