import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.186.0/build/three.module.js';
import Lenis from 'https://cdn.jsdelivr.net/npm/lenis@1.3.26/+esm';
import { animate, stagger } from 'https://cdn.jsdelivr.net/npm/animejs@4.5.0/+esm';

const reduce = matchMedia('(prefers-reduced-motion: reduce)');
const mobile = matchMedia('(max-width: 58.75rem)');
const clamp = (v,a,b)=>Math.max(a,Math.min(b,v));
const mix = (a,b,t)=>a+(b-a)*t;
const easeInOutCubic = t => t < .5 ? 4*t*t*t : 1-Math.pow(-2*t+2,3)/2;

/* ---------- Header / smooth scroll ---------- */
const header = document.getElementById('header');
const menuToggle = document.getElementById('menu-toggle');
const menuLabel = document.getElementById('menu-label');
const navPanel = document.getElementById('nav-panel');
let expanded = false;
let lastToggleScroll = 0;
let direction = 0;

function scramble(el, text){
  if(reduce.matches){ el.textContent = text; return; }
  const chars = '░▒▓■□';
  const start = performance.now(), dur = 320;
  function tick(now){
    const p = clamp((now-start)/dur,0,1);
    const fixed = Math.floor(p*text.length);
    el.textContent = [...text].map((c,i)=> i<fixed ? c : chars[(Math.random()*chars.length)|0]).join('');
    if(p<1) requestAnimationFrame(tick); else el.textContent = text;
  }
  requestAnimationFrame(tick);
}
function setMenu(open){
  expanded = open;
  header.toggleAttribute('data-expanded', open);
  menuToggle.setAttribute('aria-expanded', String(open));
  scramble(menuLabel, open ? 'CLOSE' : 'MENU');
}
menuToggle.addEventListener('click',()=>setMenu(!expanded));
document.addEventListener('pointerdown',e=>{
  if(!expanded) return;
  if(header.contains(e.target)) return;
  setMenu(false);
});
document.addEventListener('keydown',e=>{ if(e.key==='Escape') setMenu(false); });
navPanel.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>setMenu(false)));

const lenis = new Lenis({
  smoothWheel: !reduce.matches,
  syncTouch: !reduce.matches,
  touchMultiplier: 1.5,
  anchors: true,
  autoRaf: false,
  lerp: .1
});
lenis.on('scroll', e=>{
  direction = e.direction || 0;
  const h = header.offsetHeight;
  if(e.scroll <= h){ header.dataset.visible='true'; lastToggleScroll=e.scroll; return; }
  if(Math.abs(e.scroll-lastToggleScroll)<50) return;
  lastToggleScroll=e.scroll;
  header.dataset.visible = direction > 0 ? 'false' : 'true';
});

/* ---------- Hero split + entrance / exit ---------- */
const hero = document.getElementById('hero');
const heroTitle = document.querySelector('[data-hero-title]');
const heroMeta = document.querySelector('.page-header__meta');
const heroMedia = document.querySelector('.page-header__media');
const heroContent = document.querySelector('.page-header__content');
const heroLayers = [...document.querySelectorAll('.hero-media')];

function composeHeroTitle(){
  heroTitle.innerHTML = '<span class="split-line">CLOSE THE</span><span class="split-line">LOOP</span>';
}
composeHeroTitle();
document.fonts?.ready?.then(()=>{
  if(reduce.matches) return;
  const lines=[...heroTitle.querySelectorAll('.split-line')];
  animate(lines,{opacity:[0,1],y:['.6em',0],duration:900,delay:stagger(80,{start:200}),ease:'inOutCubic'});
  animate(heroMedia,{opacity:[0,1],scale:[1.08,1],duration:1400,ease:'inOutCubic'});
  animate(heroMeta,{opacity:[0,1],y:[16,0],duration:600,delay:1500,ease:'inOutCubic'});
  animate('.page-header__cue svg',{y:[0,6],duration:1200,loop:true,alternate:true,ease:'inOutSine'});
});

/* ---------- DOM reveal helpers ---------- */
const revealIO = new IntersectionObserver(entries=>{
  entries.forEach(entry=>{
    if(!entry.isIntersecting || entry.target.dataset.revealed) return;
    entry.target.dataset.revealed='1';
    animate(entry.target,{opacity:[0,1],y:[60,0],duration:800,ease:'inOutCubic'});
  });
},{threshold:.15});
document.querySelectorAll('[data-reveal]').forEach(el=>revealIO.observe(el));

const textIO = new IntersectionObserver(entries=>{
  entries.forEach(entry=>{
    if(!entry.isIntersecting || entry.target.dataset.textDone) return;
    entry.target.dataset.textDone='1';
    animate(entry.target,{opacity:[0,1],y:[25,0],duration:800,ease:'inOutCubic'});
  });
},{threshold:.25});
document.querySelectorAll('[data-text-reveal]').forEach(el=>{ el.style.opacity=0; textIO.observe(el); });

/* ---------- Theme ---------- */
const palettes = {
  dark:{
    base100:'#010001',base200:'#161210',base300:'#312c21',base400:'#010001',
    content100:'#eeeadc',content200:'#cdc9b5',content300:'#959180',
    border:'#312c21',borderCard:'#312c21',primary:'#ff9d00',secondary:'#e34608'
  },
  light:{
    base100:'#cdc9b5',base200:'#eeeadc',base300:'#cdc9b5',base400:'#eeeadc',
    content100:'#010001',content200:'#010001',content300:'#5e594a',
    border:'#959180',borderCard:'#cdc9b5',primary:'#e34608',secondary:'#ff9d00'
  }
};
let currentTheme='dark';
function applyTheme(name){
  if(name===currentTheme) return;
  currentTheme=name;
  const p=palettes[name],r=document.documentElement.style;
  r.setProperty('--clr-base-100',p.base100);r.setProperty('--clr-base-200',p.base200);
  r.setProperty('--clr-base-300',p.base300);r.setProperty('--clr-base-400',p.base400);
  r.setProperty('--clr-content-100',p.content100);r.setProperty('--clr-content-200',p.content200);
  r.setProperty('--clr-content-300',p.content300);r.setProperty('--clr-border',p.border);
  r.setProperty('--clr-border-card',p.borderCard);r.setProperty('--clr-primary',p.primary);
  r.setProperty('--clr-secondary',p.secondary);
  particleField?.setColors(p.border,p.secondary);
}

/* ---------- Particle engine ---------- */
const canvas=document.getElementById('particle-canvas');
class ParticleField{
  constructor(canvas){
    this.canvas=canvas;
    this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
    this.renderer.setClearAlpha(0);
    this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
    this.scene=new THREE.Scene();
    this.camera=new THREE.OrthographicCamera();
    this.camera.position.z=1000;
    this.clock=new THREE.Clock();
    this.pointer=new THREE.Vector2();
    this.mouse=new THREE.Vector2();
    this.transition=1;
    this.morphStart=0;
    this.morphDuration=1500;
    this.currentShape='none';
    this.targetShape='none';
    this.active=false;
    this.baseColor=new THREE.Color('#312c21');
    this.highlightColor=new THREE.Color('#e34608');
    this.targetBase=this.baseColor.clone();
    this.targetHighlight=this.highlightColor.clone();
    this.onPointer=e=>{
      if(reduce.matches) return;
      this.pointer.set((e.clientX/innerWidth)*2-1,-((e.clientY/innerHeight)*2-1));
    };
    this.onLeave=()=>this.pointer.set(0,0);
    addEventListener('pointermove',this.onPointer,{passive:true});
    document.addEventListener('mouseleave',this.onLeave);
    this.resize();
    this.build();
    new ResizeObserver(()=>this.resize()).observe(document.documentElement);
  }
  resize(){
    this.w=innerWidth; this.h=innerHeight;
    this.renderer.setSize(this.w,this.h,false);
    this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
    this.camera.left=-this.w/2;this.camera.right=this.w/2;this.camera.top=this.h/2;this.camera.bottom=-this.h/2;
    this.camera.updateProjectionMatrix();
    if(this.points) this.rebuildGeometry();
  }
  gridSpec(){
    const gap=13.5,cols=Math.ceil(this.w/gap)+1,rows=Math.ceil(this.h/gap)+1;
    return{gap,cols,rows,count:cols*rows,startX:-cols*gap/2+gap/2,startY:-rows*gap/2+gap/2,width:this.w,height:this.h};
  }
  shuffled(count){
    const a=Uint32Array.from({length:count},(_,i)=>i);
    for(let i=count-1;i>0;i--){const j=(Math.random()*(i+1))|0;const t=a[i];a[i]=a[j];a[j]=t;}
    return a;
  }
  build(){
    this.rebuildGeometry(true);
    const uniforms={
      uBaseSize:{value:18*Math.min(devicePixelRatio||1,2)},
      uTime:{value:0},
      uViewport:{value:new THREE.Vector2(this.w,this.h)},
      uMouse:{value:this.mouse},
      uParallaxStrength:{value:0},
      uTransition:{value:0},
      uBaseColor:{value:this.baseColor},
      uHighlightColor:{value:this.highlightColor}
    };
    this.uniforms=uniforms;
    const vertex=`
      uniform float uBaseSize; uniform float uTime; uniform vec2 uViewport; uniform vec2 uMouse;
      uniform float uParallaxStrength; uniform float uTransition;
      attribute vec3 aTargetPosition; attribute float aScale; attribute float aTargetScale; attribute float aRandom;
      varying float vScale; varying float vIntensity;
      void main(){
        vec3 finalPos=mix(position,aTargetPosition,uTransition);
        float pathArc=sin(uTransition*3.141592653589793);
        float rand1=aRandom; float rand2=fract(aRandom*123.456);
        finalPos.x+=(rand1-.5)*250.0*pathArc;
        finalPos.y+=(rand2-.5)*250.0*pathArc;
        finalPos.xy+=uMouse*finalPos.z*4.0*uParallaxStrength;
        vec4 mvPosition=modelViewMatrix*vec4(finalPos,1.0); gl_Position=projectionMatrix*mvPosition;
        float finalScale=mix(aScale,aTargetScale,uTransition); vScale=finalScale;
        float pulse=sin(uTime*2.0+(rand1*6.28318530718))*.5+.5;
        float oscillationScale=mix(.35,.9,pulse);
        gl_PointSize=uBaseSize*oscillationScale*finalScale;
        vec2 mouseWorld=uMouse*uViewport*.5; float distToMouse=distance(finalPos.xy,mouseWorld);
        float outerRadius=min(uViewport.x,uViewport.y)*.65;
        vIntensity=smoothstep(outerRadius,0.0,distToMouse);
      }`;
    const fragment=`
      uniform vec3 uBaseColor; uniform vec3 uHighlightColor; varying float vScale; varying float vIntensity;
      void main(){
        if(vScale<.001) discard;
        vec2 p=gl_PointCoord-.5; float dist=length(p); float aa=fwidth(dist);
        if(dist>.5+aa) discard;
        float alpha=1.0-smoothstep(.5-aa,.5+aa,dist);
        vec3 finalColor=mix(uBaseColor,uHighlightColor,vIntensity);
        gl_FragColor=vec4(finalColor,alpha);
        #include <colorspace_fragment>
      }`;
    this.material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms,vertexShader:vertex,fragmentShader:fragment});
    this.points=new THREE.Points(this.geometry,this.material);
    this.scene.add(this.points);
    this.morph('none',{instant:true});
  }
  rebuildGeometry(first=false){
    const spec=this.gridSpec();this.spec=spec;this.order=this.shuffled(spec.count);
    const pos=new Float32Array(spec.count*3),target=new Float32Array(spec.count*3),scale=new Float32Array(spec.count),targetScale=new Float32Array(spec.count),random=new Float32Array(spec.count);
    random.forEach((_,i)=>random[i]=Math.random());
    this.buffers={pos,target,scale,targetScale,random};
    const data=this.shapeData(this.currentShape||'none');
    pos.set(data.positions);target.set(data.positions);scale.set(data.scales);targetScale.set(data.scales);
    const g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.BufferAttribute(pos,3));
    g.setAttribute('aTargetPosition',new THREE.BufferAttribute(target,3));
    g.setAttribute('aScale',new THREE.BufferAttribute(scale,1));
    g.setAttribute('aTargetScale',new THREE.BufferAttribute(targetScale,1));
    g.setAttribute('aRandom',new THREE.BufferAttribute(random,1));
    if(this.geometry) this.geometry.dispose();
    this.geometry=g;if(this.points)this.points.geometry=g;
    if(this.uniforms){this.uniforms.uBaseSize.value=18*Math.min(devicePixelRatio||1,2);this.uniforms.uViewport.value.set(this.w,this.h);}
  }
  cell(i){const s=this.spec;return[s.startX+(i%s.cols)*s.gap,s.startY+Math.floor(i/s.cols)*s.gap];}
  grid(){
    const s=this.spec,p=new Float32Array(s.count*3),sc=new Float32Array(s.count);
    for(let i=0;i<s.count;i++){const [x,y]=this.cell(i),idx=this.order[i],j=idx*3;p[j]=x;p[j+1]=y;p[j+2]=(x*x+y*y)/400000;sc[idx]=Math.random()>.46?(.45+Math.random()*.55):0;}
    return{positions:p,scales:sc};
  }
  ringsHorizontal(){
    const s=this.spec,p=new Float32Array(s.count*3),sc=new Float32Array(s.count).fill(1),rings=10,per=Math.max(1,Math.ceil(s.count/rings)),r0=Math.max(Math.min(s.width,s.height)*.25,150);
    for(let i=0;i<s.count;i++){const ring=Math.floor(i/per),a=((i%per)/per)*Math.PI*2,r=r0-ring*.3,idx=this.order[i],j=idx*3;p[j]=Math.cos(a)*r;p[j+1]=-ring*5;p[j+2]=Math.sin(a)*r;}return{positions:p,scales:sc};
  }
  ringsVertical(){
    const s=this.spec,p=new Float32Array(s.count*3),sc=new Float32Array(s.count).fill(1),rings=6,per=Math.max(1,Math.ceil(s.count/rings)),r0=Math.max(Math.min(s.width,s.height)*.35,250);
    for(let i=0;i<s.count;i++){const ring=Math.floor(i/per),a=((i%per)/per)*Math.PI*2,r=r0-ring*40,idx=this.order[i],j=idx*3;p[j]=Math.cos(a)*r;p[j+1]=Math.sin(a)*r;p[j+2]=-ring*15;}return{positions:p,scales:sc};
  }
  chip(){
    const s=this.spec,base=this.grid(),p=base.positions,sc=new Float32Array(s.count);
    const oc=document.createElement('canvas');oc.width=s.cols;oc.height=s.rows;const c=oc.getContext('2d');
    c.fillStyle='#000';c.fillRect(0,0,oc.width,oc.height);
    c.fillStyle='#fff';const w=oc.width*.46,h=oc.height*.46,x=(oc.width-w)/2,y=(oc.height-h)/2;c.fillRect(x,y,w,h);
    c.fillStyle='#000';for(let r=0;r<4;r++)for(let q=0;q<4;q++)c.fillRect(x+w*(.1+q*.22),y+h*(.1+r*.22),w*.1,h*.1);
    c.fillStyle='#fff';for(let i=0;i<8;i++){c.fillRect(x-oc.width*.045,y+h*(.06+i*.115),oc.width*.05,h*.035);c.fillRect(x+w-oc.width*.005,y+h*(.06+i*.115),oc.width*.05,h*.035);}
    const d=c.getImageData(0,0,oc.width,oc.height).data;
    for(let row=0;row<s.rows;row++)for(let col=0;col<s.cols;col++){const pp=(row*s.cols+col)*4,lum=d[pp]/255,t=Math.max(0,(lum-.33)/.67),idx=this.order[row*s.cols+col];sc[idx]=t;}
    return{positions:p,scales:sc};
  }
  shapeData(shape){
    if(shape==='none'){const g=this.grid();return{positions:g.positions,scales:new Float32Array(this.spec.count)};}
    if(shape==='grid')return this.grid();
    if(shape==='rings-horizontal')return this.ringsHorizontal();
    if(shape==='rings-vertical')return this.ringsVertical();
    if(shape==='image')return this.chip();
    return this.grid();
  }
  morph(shape,{instant=false}={}){
    if(shape===this.targetShape&&!instant)return;
    const data=this.shapeData(shape);this.buffers.target.set(data.positions);this.buffers.targetScale.set(data.scales);
    this.geometry.attributes.aTargetPosition.needsUpdate=true;this.geometry.attributes.aTargetScale.needsUpdate=true;
    this.targetShape=shape;this.morphStart=performance.now();this.active=!instant&&!reduce.matches;
    if(instant||reduce.matches){this.buffers.pos.set(data.positions);this.buffers.scale.set(data.scales);this.geometry.attributes.position.needsUpdate=true;this.geometry.attributes.aScale.needsUpdate=true;this.currentShape=shape;this.active=false;if(this.uniforms){this.uniforms.uTransition.value=0;this.uniforms.uParallaxStrength.value=this.is3D(shape)?1:0;}}
    else{this.uniforms.uTransition.value=0;}
  }
  is3D(s){return s==='grid'||s==='rings-horizontal'||s==='rings-vertical';}
  setColors(base,highlight){this.targetBase.set(base);this.targetHighlight.set(highlight);}
  update(now,delta){
    if(!this.uniforms)return;
    this.uniforms.uTime.value=now/1000;this.uniforms.uViewport.value.set(this.w,this.h);
    const damp=1-Math.exp(-5*delta);this.mouse.lerp(this.pointer,damp);
    this.baseColor.lerp(this.targetBase,1-Math.exp(-3*delta));this.highlightColor.lerp(this.targetHighlight,1-Math.exp(-3*delta));
    if(this.active){const p=clamp((now-this.morphStart)/this.morphDuration,0,1),e=easeInOutCubic(p);this.uniforms.uTransition.value=e;this.uniforms.uParallaxStrength.value=mix(this.uniforms.uParallaxStrength.value,this.is3D(this.targetShape)?1:0,e);if(p>=1){this.buffers.pos.set(this.buffers.target);this.buffers.scale.set(this.buffers.targetScale);this.geometry.attributes.position.needsUpdate=true;this.geometry.attributes.aScale.needsUpdate=true;this.uniforms.uTransition.value=0;this.currentShape=this.targetShape;this.active=false;}}
    this.renderer.render(this.scene,this.camera);
  }
}
const particleField=new ParticleField(canvas);

/* ---------- Section focus picker ---------- */
const focusEls=[...document.querySelectorAll('[data-theme],[data-particles]')];
const focusState=new Map();let focusWinner=null;
const thresholds=Array.from({length:11},(_,i)=>i/10);
const focusIO=new IntersectionObserver(entries=>{
  entries.forEach(e=>focusState.set(e.target,e.intersectionRatio));
  chooseFocus();
},{threshold:thresholds});
focusEls.forEach(el=>focusIO.observe(el));
function chooseFocus(){
  const vh=innerHeight,focusLine=vh*(direction>0?.4:direction<0?.6:.5);
  let best=null,bestScore=-1;
  for(const el of focusEls){
    const rect=el.getBoundingClientRect(),visible=Math.max(0,Math.min(rect.bottom,vh)-Math.max(rect.top,0));
    if(visible<vh*.05)continue;
    const ratio=focusState.get(el)||0;
    const d=(rect.top<=focusLine&&rect.bottom>=focusLine)?0:Math.min(Math.abs(rect.top-focusLine),Math.abs(rect.bottom-focusLine));
    const center=1-Math.min(1,d/vh),score=ratio*.6+center*.4;
    if(score>bestScore){bestScore=score;best=el;}
  }
  if(best&&best!==focusWinner){focusWinner=best;applyTheme(best.dataset.theme||'dark');particleField.morph(best.dataset.particles||'none');}
}

/* ---------- Scroll-linked text highlight and parallax ---------- */
const highlightSection=document.querySelector('[data-highlight]')?.closest('.centered-text');
const marks=[...document.querySelectorAll('[data-highlight] mark')];
const parallaxMedia=[...document.querySelectorAll('[data-media-progress]')];
const sock=document.querySelector('.sock'),sockArts=[...document.querySelectorAll('.sock-art')];
let last=performance.now();

function updateScrollEffects(){
  const heroRect=hero.getBoundingClientRect(),hp=clamp(-heroRect.top/innerHeight,0,1);
  const lines=[...heroTitle.querySelectorAll('.split-line')];
  if(!mobile.matches&&!reduce.matches){
    lines.forEach((l,i)=>l.style.transform=`translate3d(${i===0?-50*hp:50*hp}vw,0,0)`);
    heroMeta.style.transform=`translate3d(5vw,0,0)`;
    heroMeta.style.opacity=String(1-hp);
    heroMedia.style.transform=`translate3d(0,${-12.5*hp}%,0)`;
  }else{
    lines.forEach(l=>l.style.transform='none');heroMeta.style.transform='none';heroMeta.style.opacity='1';heroMedia.style.transform='none';
  }
  parallaxMedia.forEach(media=>{const r=media.getBoundingClientRect(),p=clamp((innerHeight-r.top)/(innerHeight+r.height),0,1);media.querySelectorAll('[data-rate]').forEach(layer=>{const rate=+layer.dataset.rate||0;layer.style.transform=`translate3d(0,${(p-.5)*rate}%,0) scale(1.12)`;});});
  if(highlightSection){const r=highlightSection.getBoundingClientRect(),p=clamp((-r.top)/(r.height-innerHeight),0,1);marks.forEach((m,i)=>{const local=clamp((p-i*.18)/.42,0,1);m.style.color=`color-mix(in srgb,var(--clr-primary) ${Math.round(local*100)}%,var(--clr-content-300))`;});}
  if(sock){const r=sock.getBoundingClientRect(),p=clamp((innerHeight-r.top)/(innerHeight+r.height),0,1);sockArts.forEach((a,i)=>{if(mobile.matches&&i>0)return;const x=i===1?mix(-8,0,p):0,y=i===2?mix(20,0,p):i===3?mix(-20,0,p):0,s=i===0?mix(1.16,1.08,p):1.1;a.style.transform=`translate3d(${x}%,${y}%,0) scale(${s})`;});}
  chooseFocus();
}

function frame(now){
  const delta=Math.min(.05,(now-last)/1000);last=now;
  if(!reduce.matches)lenis.raf(now);
  updateScrollEffects();
  particleField.update(now,delta);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

/* live reduced-motion changes */
reduce.addEventListener('change',()=>location.reload());
