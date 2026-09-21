import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.186.0/build/three.module.js';
import Lenis from 'https://cdn.jsdelivr.net/npm/lenis@1.3.26/+esm';
import { animate, stagger } from 'https://cdn.jsdelivr.net/npm/animejs@4.5.0/+esm';

const reduce=matchMedia('(prefers-reduced-motion: reduce)');
const mobile=matchMedia('(max-width:58.75rem)');
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const outCubic=t=>1-Math.pow(1-t,3);
const map=(v,a,b,c,d)=>c+(d-c)*clamp((v-a)/(b-a));
let direction=0;

/* Header: 50px dead-zone + scramble label, matching the production behavior. */
const header=document.getElementById('header'),toggle=document.getElementById('menu-toggle'),menu=document.getElementById('expand-menu'),label=document.getElementById('menu-label');
let expanded=false,lastHeaderScroll=0;
function scramble(text){
  if(reduce.matches){label.textContent=text;return}
  const chars='░▒▓■□';const start=performance.now(),dur=320;
  function step(now){const p=clamp((now-start)/dur),locked=Math.floor(text.length*p);label.textContent=[...text].map((c,i)=>i<locked?c:chars[Math.floor(Math.random()*chars.length)]).join('');if(p<1)requestAnimationFrame(step);else label.textContent=text}requestAnimationFrame(step);
}
function setMenu(v){expanded=v;header.classList.toggle('expanded',v);toggle.setAttribute('aria-expanded',String(v));scramble(v?'CLOSE':'MENU')}
toggle.addEventListener('click',()=>setMenu(!expanded));
document.addEventListener('pointerdown',e=>{if(expanded&&!header.contains(e.target))setMenu(false)});
document.addEventListener('keydown',e=>{if(e.key==='Escape')setMenu(false)});
menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>setMenu(false)));

const lenis=new Lenis({smoothWheel:!reduce.matches,syncTouch:!reduce.matches,touchMultiplier:1.5,anchors:true,autoRaf:false,lerp:.1});
lenis.on('scroll',e=>{
  direction=e.direction||0;
  const h=header.offsetHeight;
  if(e.scroll<=h){header.classList.add('visible');lastHeaderScroll=e.scroll;return}
  if(Math.abs(e.scroll-lastHeaderScroll)<50)return;
  lastHeaderScroll=e.scroll;
  header.classList.toggle('visible',direction<0);
});

/* Hero text split and entrance. */
const hero=document.querySelector('.page-header.home'),heroTitle=hero.querySelector('.title'),heroWrappers=[...hero.querySelectorAll('.image-wrapper')],heroImgs=[...hero.querySelectorAll('.image-wrapper img')],heroSubtitle=hero.querySelector('.subtitle'),heroScroll=hero.querySelector('.scroll');
const heroLines=heroTitle.textContent.trim().split('\n').map(s=>s.trim()).filter(Boolean);
heroTitle.innerHTML=heroLines.map(s=>`<span class="line">${s}</span>`).join('');
const titleLines=[...heroTitle.querySelectorAll('.line')];
heroImgs.forEach(i=>{i.style.opacity='0'});
document.fonts?.ready?.then(()=>{
  if(reduce.matches){heroImgs.forEach(i=>i.style.opacity='1');return}
  animate(titleLines,{opacity:[0,1],y:['.6em',0],duration:900,delay:stagger(80,{start:200}),ease:'inOutCubic'});
  animate(heroImgs,{opacity:[0,1],duration:900,delay:stagger(70,{start:120}),ease:'inOutCubic'});
  animate(heroSubtitle,{opacity:[0,1],y:[16,0],duration:600,delay:1100,ease:'inOutCubic'});
  animate(heroScroll,{opacity:[0,1],y:[16,0],duration:600,delay:1200,ease:'inOutCubic'});
});

/* Centered text: the original animates line wrappers from y:101% to 0. */
const centered=[...document.querySelectorAll('section.centered-text')];
centered.forEach(sec=>{
  const main=sec.querySelector('.main-text');if(!main)return;
  const lines=main.textContent.split('\n').map(x=>x.trim()).filter(Boolean);
  main.innerHTML=lines.map(x=>`<span class="line"><span>${x}</span></span>`).join('');
  sec._lineInners=[...main.querySelectorAll('.line>span')];
  sec._lineInners.forEach(x=>x.style.transform='translateY(101%)');
});
const roloSec=document.querySelector('.centered-text-two'),roloEntries=roloSec?[...roloSec.querySelectorAll('.rolodex-entry')]:[];
let roloIndex=0,roloTimer=null;
function startRolodex(on){
  if(on&&!roloTimer){roloTimer=setInterval(()=>{const old=roloEntries[roloIndex];roloIndex=(roloIndex+1)%roloEntries.length;const next=roloEntries[roloIndex];old.classList.remove('active');next.classList.add('active')},2000)}
  if(!on&&roloTimer){clearInterval(roloTimer);roloTimer=null}
}

/* Glow cursors on glass targets. */
document.querySelectorAll('.glow-target').forEach(el=>el.addEventListener('pointermove',e=>{const r=el.getBoundingClientRect();el.style.setProperty('--gx',`${e.clientX-r.left}px`);el.style.setProperty('--gy',`${e.clientY-r.top}px`)}));

/* One persistent Points field, following BOON's five-shape model. */
class ParticleField{
  constructor(canvas){
    this.canvas=canvas;this.renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});this.renderer.setClearAlpha(0);this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
    this.scene=new THREE.Scene();this.camera=new THREE.OrthographicCamera();this.camera.position.z=1000;
    this.pointer=new THREE.Vector2();this.mouse=new THREE.Vector2();this.base=new THREE.Color('#312c21');this.highlight=new THREE.Color('#e34608');this.targetBase=this.base.clone();this.targetHighlight=this.highlight.clone();
    this.shape='none';this.targetShape='none';this.imageUrl='';this.transitioning=false;this.morphStart=0;this.morphDuration=1500;this.decodeToken=0;
    addEventListener('pointermove',e=>{if(!reduce.matches)this.pointer.set(e.clientX/innerWidth*2-1,-(e.clientY/innerHeight*2-1))},{passive:true});document.addEventListener('mouseleave',()=>this.pointer.set(0,0));
    this.resize();this.build();new ResizeObserver(()=>this.resize()).observe(document.documentElement);
  }
  spec(){const gap=13.5,cols=Math.ceil(this.w/gap)+1,rows=Math.ceil(this.h/gap)+1;return{gap,cols,rows,count:cols*rows,startX:-cols*gap/2+gap/2,startY:-rows*gap/2+gap/2,width:this.w,height:this.h}}
  order(n){const a=Uint32Array.from({length:n},(_,i)=>i);for(let i=n-1;i>0;i--){const j=Math.floor(Math.random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t}return a}
  resize(){this.w=innerWidth;this.h=innerHeight;this.renderer.setSize(this.w,this.h,false);this.renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));this.camera.left=-this.w/2;this.camera.right=this.w/2;this.camera.top=this.h/2;this.camera.bottom=-this.h/2;this.camera.updateProjectionMatrix();if(this.points)this.rebuild()}
  build(){
    this.rebuild(true);
    this.uniforms={uBaseSize:{value:18*Math.min(devicePixelRatio||1,2)},uTime:{value:0},uViewport:{value:new THREE.Vector2(this.w,this.h)},uMouse:{value:this.mouse},uParallaxStrength:{value:0},uTransition:{value:0},uBaseColor:{value:this.base},uHighlightColor:{value:this.highlight}};
    const vertex=`
uniform float uBaseSize,uTime,uParallaxStrength,uTransition;uniform vec2 uViewport,uMouse;attribute vec3 aTargetPosition;attribute float aScale,aTargetScale,aRandom;varying float vScale,vIntensity;
void main(){vec3 finalPos=mix(position,aTargetPosition,uTransition);float pathArc=sin(uTransition*3.141592653589793);float rand1=aRandom;float rand2=fract(aRandom*123.456);finalPos.x+=(rand1-.5)*250.0*pathArc;finalPos.y+=(rand2-.5)*250.0*pathArc;finalPos.xy+=uMouse*finalPos.z*4.0*uParallaxStrength;vec4 mvPosition=modelViewMatrix*vec4(finalPos,1.0);gl_Position=projectionMatrix*mvPosition;float finalScale=mix(aScale,aTargetScale,uTransition);vScale=finalScale;float pulse=sin(uTime*2.0+rand1*6.2831853)*.5+.5;float oscillationScale=mix(.35,.9,pulse);gl_PointSize=uBaseSize*oscillationScale*finalScale;vec2 mouseWorld=uMouse*uViewport*.5;float d=distance(finalPos.xy,mouseWorld);vIntensity=smoothstep(min(uViewport.x,uViewport.y)*.65,0.0,d);}`;
    const fragment=`uniform vec3 uBaseColor,uHighlightColor;varying float vScale,vIntensity;void main(){if(vScale<.001)discard;vec2 p=gl_PointCoord-.5;float dist=length(p);float aa=fwidth(dist);if(dist>.5+aa)discard;float alpha=1.0-smoothstep(.5-aa,.5+aa,dist);gl_FragColor=vec4(mix(uBaseColor,uHighlightColor,vIntensity),alpha);#include <colorspace_fragment>}`;
    this.material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:this.uniforms,vertexShader:vertex,fragmentShader:fragment});this.points=new THREE.Points(this.geometry,this.material);this.scene.add(this.points);this.morph('none',{instant:true});
  }
  rebuild(){const s=this.spec();this.s=s;this.ord=this.order(s.count);const pos=new Float32Array(s.count*3),tar=new Float32Array(s.count*3),sc=new Float32Array(s.count),ts=new Float32Array(s.count),rnd=new Float32Array(s.count);for(let i=0;i<s.count;i++)rnd[i]=Math.random();this.buf={pos,tar,sc,ts,rnd};const data=this.gridShape();pos.set(data.positions);tar.set(data.positions);sc.set(data.scales);ts.set(data.scales);const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('aTargetPosition',new THREE.BufferAttribute(tar,3));g.setAttribute('aScale',new THREE.BufferAttribute(sc,1));g.setAttribute('aTargetScale',new THREE.BufferAttribute(ts,1));g.setAttribute('aRandom',new THREE.BufferAttribute(rnd,1));if(this.geometry)this.geometry.dispose();this.geometry=g;if(this.points)this.points.geometry=g;if(this.uniforms){this.uniforms.uViewport.value.set(this.w,this.h);this.uniforms.uBaseSize.value=18*Math.min(devicePixelRatio||1,2)}}
  cell(i){return[this.s.startX+(i%this.s.cols)*this.s.gap,this.s.startY+Math.floor(i/this.s.cols)*this.s.gap]}
  write(p,idx,x,y,z){let j=idx*3;p[j]=x;p[j+1]=y;p[j+2]=z}
  gridShape(){const s=this.s,p=new Float32Array(s.count*3),sc=new Float32Array(s.count);for(let i=0;i<s.count;i++){const[x,y]=this.cell(i),idx=this.ord[i];this.write(p,idx,x,y,(x*x+y*y)/400000);sc[idx]=Math.random()>.5?(.35+Math.random()*.65):0}return{positions:p,scales:sc}}
  noneShape(){const g=this.gridShape();return{positions:g.positions,scales:new Float32Array(this.s.count)}}
  ringsHorizontal(){const s=this.s,p=new Float32Array(s.count*3),sc=new Float32Array(s.count).fill(1),rings=10,per=Math.ceil(s.count/rings),r0=Math.max(Math.min(s.width,s.height)*.25,150);for(let i=0;i<s.count;i++){const ring=Math.floor(i/per),a=((i%per)/per)*Math.PI*2,r=r0-ring*.3,idx=this.ord[i];this.write(p,idx,Math.cos(a)*r,-ring*5,Math.sin(a)*r)}return{positions:p,scales:sc}}
  ringsVertical(){const s=this.s,p=new Float32Array(s.count*3),sc=new Float32Array(s.count).fill(1),rings=6,per=Math.ceil(s.count/rings),r0=Math.max(Math.min(s.width,s.height)*.35,250);for(let i=0;i<s.count;i++){const ring=Math.floor(i/per),a=((i%per)/per)*Math.PI*2,r=r0-ring*40,idx=this.ord[i];this.write(p,idx,Math.cos(a)*r,Math.sin(a)*r,-ring*15)}return{positions:p,scales:sc}}
  async imageShape(url,token){const img=new Image();img.crossOrigin='anonymous';img.src=url;await img.decode();if(token!==this.decodeToken)return null;const base=this.gridShape(),p=base.positions,sc=new Float32Array(this.s.count),c=document.createElement('canvas');c.width=this.s.cols;c.height=this.s.rows;const ctx=c.getContext('2d',{willReadFrequently:true}),scale=Math.max(c.width/img.width,c.height/img.height),dw=img.width*scale,dh=img.height*scale;ctx.drawImage(img,(c.width-dw)/2,(c.height-dh)/2,dw,dh);const d=ctx.getImageData(0,0,c.width,c.height).data;for(let row=0;row<this.s.rows;row++)for(let col=0;col<this.s.cols;col++){const pp=(row*this.s.cols+col)*4;if(d[pp+3]<=128)continue;const lum=(.299*d[pp]+.587*d[pp+1]+.114*d[pp+2])/255,t=Math.max(0,(1-lum-.33)/.67),idx=this.ord[row*this.s.cols+col];sc[idx]=t}return{positions:p,scales:sc}}
  data(shape){if(shape==='none')return this.noneShape();if(shape==='grid')return this.gridShape();if(shape==='rings-horizontal')return this.ringsHorizontal();if(shape==='rings-vertical')return this.ringsVertical();return this.noneShape()}
  async morph(shape,{image,instant=false}={}){if(shape===this.targetShape&&image===this.imageUrl&&!instant)return;this.targetShape=shape;this.imageUrl=image||'';const token=++this.decodeToken;let data=shape==='image'&&image?await this.imageShape(image,token):this.data(shape);if(!data||token!==this.decodeToken)return;this.buf.tar.set(data.positions);this.buf.ts.set(data.scales);this.geometry.attributes.aTargetPosition.needsUpdate=true;this.geometry.attributes.aTargetScale.needsUpdate=true;this.uniforms.uTransition.value=0;this.morphStart=performance.now();this.transitioning=!instant&&!reduce.matches;if(instant||reduce.matches)this.snap()}
  snap(){this.buf.pos.set(this.buf.tar);this.buf.sc.set(this.buf.ts);this.geometry.attributes.position.needsUpdate=true;this.geometry.attributes.aScale.needsUpdate=true;this.uniforms.uTransition.value=0;this.uniforms.uParallaxStrength.value=this.is3D(this.targetShape)?1:0;this.shape=this.targetShape;this.transitioning=false}
  is3D(s){return s==='grid'||s==='rings-horizontal'||s==='rings-vertical'}
  setColors(a,b){this.targetBase.set(a);this.targetHighlight.set(b)}
  frame(now,dt){this.uniforms.uTime.value=now/1000;this.uniforms.uViewport.value.set(this.w,this.h);this.mouse.lerp(this.pointer,1-Math.exp(-5*dt));this.base.lerp(this.targetBase,1-Math.exp(-4*dt));this.highlight.lerp(this.targetHighlight,1-Math.exp(-4*dt));if(this.transitioning){const p=clamp((now-this.morphStart)/1500),e=p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2;this.uniforms.uTransition.value=e;this.uniforms.uParallaxStrength.value=this.is3D(this.targetShape)?e:1-e;if(p>=1)this.snap()}this.renderer.render(this.scene,this.camera)}
}
const particles=new ParticleField(document.getElementById('particle-canvas'));

/* Section focus picker: same 60/40 visibility/centre score and direction bias. */
const focusEls=[...document.querySelectorAll('[data-particles],[data-theme]')],ratios=new Map();let winner=null;
const io=new IntersectionObserver(es=>{es.forEach(e=>ratios.set(e.target,e.intersectionRatio));pick()},{threshold:Array.from({length:11},(_,i)=>i/10)});focusEls.forEach(e=>io.observe(e));
const palettes={dark:['#312c21','#e34608'],light:['#959180','#ff9d00']};
function pick(){const vh=innerHeight,line=vh*(direction>0?.4:direction<0?.6:.5);let best=null,score=-1;for(const el of focusEls){const r=el.getBoundingClientRect(),vis=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));if(vis<vh*.05)continue;const ratio=ratios.get(el)||0,d=(r.top<=line&&r.bottom>=line)?0:Math.min(Math.abs(r.top-line),Math.abs(r.bottom-line)),cp=1-Math.min(1,d/vh),s=ratio*.6+cp*.4;if(s>score){score=s;best=el}}if(best&&best!==winner){winner=best;const theme=best.dataset.theme||'dark';document.body.classList.toggle('light',theme==='light');particles.setColors(...palettes[theme]);particles.morph(best.dataset.particles||'none',{image:best.dataset.image})}}

/* Card-grid entrance, exact 100 + index*50 Y stagger. */
const cards=[...document.querySelectorAll('ul.cards li.card')],cardGrid=document.querySelector('.card-grid');cards.forEach((c,i)=>c.style.transform=`translateY(${100+i*50}px)`);
let cardsStarted=false;

/* Sock lines + images */
const sock=document.querySelector('.sock'),sockWrap=[...sock.querySelectorAll('.image-wrapper')],sockImgs=[...sock.querySelectorAll('img')],sockH=sock.querySelector('h2');sockH.innerHTML=`<span class="line"><span>${sockH.textContent.trim()}</span></span>`;const sockText=sockH.querySelector('.line>span');sockText.style.display='block';sockText.style.transform='translateY(100%)';sockH.querySelector('.line').style.overflow='hidden';sockH.querySelector('.line').style.display='block';

/* Large text reveal */
const large=document.querySelector('.large-text'),largeH=large.querySelector('h2');largeH.innerHTML=largeH.innerHTML.replace('Physical reality is part of the search, ','<span class="large-line"><span>Physical reality is part of the search,</span></span>').replace('<mark>','<span class="large-line"><span><mark>').replace('</mark>','</mark></span></span>');[...largeH.querySelectorAll('.large-line')].forEach(l=>{l.style.display='block';l.style.overflow='hidden';l.firstElementChild.style.display='block';l.firstElementChild.style.transform='translateY(100%)'});

let last=performance.now();
function tick(now){
  const dt=Math.min(.05,(now-last)/1000);last=now;if(!reduce.matches)lenis.raf(now);
  const vh=innerHeight;

  /* hero production exit */
  const hr=hero.getBoundingClientRect(),hp=clamp(-hr.top/vh);
  if(!reduce.matches){
    if(heroWrappers[1])heroWrappers[1].style.transform=`translate3d(0,${25*hp}%,0)`;if(heroImgs[1])heroImgs[1].style.transform=`translate3d(0,${-12.5*hp}%,0)`;
    if(heroWrappers[2])heroWrappers[2].style.transform=`translate3d(${-25*hp}%,0,0)`;if(heroImgs[2])heroImgs[2].style.transform=`translate3d(${12.5*hp}%,0,0)`;
    if(heroWrappers[3])heroWrappers[3].style.transform=`translate3d(${25*hp}%,0,0)`;if(heroImgs[3])heroImgs[3].style.transform=`translate3d(${-12.5*hp}%,0,0)`;
    if(heroImgs[0])heroImgs[0].style.transform=`scale(${1+.15*hp})`;
    if(!mobile.matches){if(titleLines[0])titleLines[0].style.transform=`translate3d(${-50*hp}vw,0,0)`;if(titleLines[1])titleLines[1].style.transform=`translate3d(${50*hp}vw,0,0)`;heroSubtitle.style.transform=`translate3d(${-5*hp}vw,0,0)`;heroScroll.style.transform=`translate3d(${5*hp}vw,0,0)`;}
    heroSubtitle.style.opacity=String(clamp(1-.5*hp));heroScroll.style.opacity=String(clamp(1-.5*hp));
  }

  /* centered text scroll reveal: top top -> top -= 50% top */
  centered.forEach(sec=>{const r=sec.getBoundingClientRect(),p=clamp(-r.top/(vh*.5));(sec._lineInners||[]).forEach(line=>line.style.transform=`translateY(${101*(1-p)}%)`);if(sec===roloSec)startRolodex(p>=.999)});

  /* card grid: enter bottom/top, leave center/top, sync */
  const cr=cardGrid.getBoundingClientRect(),cp=clamp((vh-cr.top)/(vh+cr.height*.5));
  if(cp>0&&!cardsStarted){cardsStarted=true;cardGrid.querySelector('.cards').classList.remove('pre-anim')}
  cards.forEach((c,i)=>{const local=clamp((cp-i*.06)/.72),e=outCubic(local);c.style.transform=`translateY(${(100+i*50)*(1-e)}px)`});

  /* large text source reveal */
  const lr=large.getBoundingClientRect(),lp=clamp((vh*.5-lr.top)/(vh*.5));
  [...largeH.querySelectorAll('.large-line>span')].forEach(x=>x.style.transform=`translateY(${100*(1-lp)}%)`);

  /* sock source choreography */
  const sr=sock.getBoundingClientRect(),sp=clamp((vh-sr.top)/(vh+sr.height));
  if(sockImgs[0])sockImgs[0].style.transform=`scale(${1.15-.15*sp})`;
  if(sockWrap[1])sockWrap[1].style.transform=`translate3d(${-10*(1-sp)}%,0,0)`;if(sockImgs[1])sockImgs[1].style.transform=`translate3d(${5*(1-sp)}%,0,0)`;
  if(sockWrap[2])sockWrap[2].style.transform=`translate3d(0,${50*(1-sp)}%,0)`;if(sockImgs[2])sockImgs[2].style.transform=`translate3d(0,${-25*(1-sp)}%,0)`;
  if(sockWrap[3])sockWrap[3].style.transform=`translate3d(0,${-50*(1-sp)}%,0)`;if(sockImgs[3])sockImgs[3].style.transform=`translate3d(0,${25*(1-sp)}%,0)`;
  sockText.style.transform=`translateY(${100*(1-clamp((sp-.4)/.6))}%)`;

  pick();particles.frame(now,dt);requestAnimationFrame(tick)
}
requestAnimationFrame(tick);
