(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const out=t=>1-Math.pow(1-t,3);
const reduce=matchMedia('(prefers-reduced-motion: reduce)');
const mobile=matchMedia('(max-width:58.75rem)');
const still=new URLSearchParams(location.search).has('still');

addEventListener('load',()=>requestAnimationFrame(()=>document.body.classList.add('ready')),{once:true});
if(still) document.body.classList.add('ready');

const header=$('#header'), menuToggle=$('#menuToggle'), menuPanel=$('#menuPanel'), menuLabel=$('#menuLabel');
let expanded=false,lastScroll=scrollY,lastToggle=0,direction=0;
function scramble(text){
  if(still||reduce.matches){menuLabel.textContent=text;return}
  const chars='░▒▓■□',start=performance.now(),dur=280;
  const f=now=>{const p=clamp((now-start)/dur),fixed=Math.floor(text.length*p);menuLabel.textContent=[...text].map((c,i)=>i<fixed?c:chars[(Math.random()*chars.length)|0]).join('');if(p<1)requestAnimationFrame(f);else menuLabel.textContent=text};requestAnimationFrame(f);
}
function setMenu(v){expanded=v;header.classList.toggle('expanded',v);menuToggle.setAttribute('aria-expanded',String(v));scramble(v?'CLOSE':'MENU')}
menuToggle.addEventListener('click',()=>setMenu(!expanded));
document.addEventListener('pointerdown',e=>{if(expanded&&!header.contains(e.target))setMenu(false)});
document.addEventListener('keydown',e=>{if(e.key==='Escape')setMenu(false)});
$$('a',menuPanel).forEach(a=>a.addEventListener('click',()=>setMenu(false)));

const hero=$('#hero'),title=$('.title',hero),heroWrappers=$$('.image-wrapper',hero),heroImgs=$$('img',hero),subtitle=$('.subtitle',hero),scrollCue=$('.scroll',hero);
const titleText=title.textContent.trim().split('\n').map(x=>x.trim()).filter(Boolean);
title.innerHTML=titleText.map(x=>'<span class="line"><span>'+x+'</span></span>').join('');
const heroLines=$$('.line>span',title);
if(!still&&!reduce.matches){
  heroLines.forEach((l,i)=>{l.style.opacity='0';l.style.transform='translateY(.55em)';l.style.transition='opacity .9s cubic-bezier(.65,0,.35,1) '+(180+i*80)+'ms,transform .9s cubic-bezier(.65,0,.35,1) '+(180+i*80)+'ms'});
  heroImgs.forEach((im,i)=>{im.style.opacity='0';im.style.transition='opacity .9s cubic-bezier(.5,.1,0,1) '+(100+i*60)+'ms'});
  [subtitle,scrollCue].forEach((el,i)=>{el.style.opacity='0';el.style.transform='translateY(16px)';el.style.transition='opacity .6s ease '+(1000+i*100)+'ms,transform .6s cubic-bezier(.5,.1,0,1) '+(1000+i*100)+'ms'});
  requestAnimationFrame(()=>requestAnimationFrame(()=>{heroLines.forEach(l=>{l.style.opacity='1';l.style.transform='translateY(0)'});heroImgs.forEach(im=>im.style.opacity='1');[subtitle,scrollCue].forEach(el=>{el.style.opacity='1';el.style.transform='translateY(0)'})}));
}

const centered=$$('section.centered-text');
centered.forEach(sec=>{
  const main=$('.main-text',sec); if(!main) return;
  const lines=main.textContent.trim().split('\n').map(x=>x.trim()).filter(Boolean);
  main.innerHTML=lines.map(x=>'<span class="line"><span>'+x+'</span></span>').join('');
  sec._lines=$$('.line>span',main);
  if(!still&&!reduce.matches) sec._lines.forEach(l=>l.style.transform='translateY(101%)');
});
const rolo=$('.centered-2'),entries=rolo?$$('.rolodex-entry',rolo):[];let ri=0,rt=0;
function runRolodex(on){if(still||reduce.matches)return;if(on&&!rt&&entries.length){rt=setInterval(()=>{entries[ri].classList.remove('active');ri=(ri+1)%entries.length;entries[ri].classList.add('active')},2000)}else if(!on&&rt){clearInterval(rt);rt=0}}

const cardSec=$('.difference-grid'), cards=$$('.card',cardSec);
if(!still&&!reduce.matches) cards.forEach((c,i)=>{c.style.opacity='0';c.style.transform='translateY('+(100+i*50)+'px)'}); else cards.forEach(c=>c.style.opacity='1');

class Particles{
  constructor(canvas){
    this.canvas=canvas;this.ctx=canvas.getContext('2d');this.shape='none';this.target='none';this.theme='dark';this.startT=0;this.dur=1500;this.morph=false;this.mx=innerWidth/2;this.my=innerHeight/2;this.tx=this.mx;this.ty=this.my;
    addEventListener('pointermove',e=>{this.tx=e.clientX;this.ty=e.clientY},{passive:true});addEventListener('resize',()=>this.resize(),{passive:true});this.resize();this.set('none',true);
  }
  resize(){const dpr=Math.min(devicePixelRatio||1,1.5);this.w=innerWidth;this.h=innerHeight;this.canvas.width=Math.floor(this.w*dpr);this.canvas.height=Math.floor(this.h*dpr);this.ctx.setTransform(dpr,0,0,dpr,0,0);this.n=Math.min((mobile.matches?2200:5000),Math.ceil(this.w/14)*Math.ceil(this.h/14));this.cur=new Float32Array(this.n*3);this.from=new Float32Array(this.n*3);this.to=new Float32Array(this.n*3);this.rand=new Float32Array(this.n);for(let i=0;i<this.n;i++)this.rand[i]=Math.random();this.build(this.shape,this.cur);this.to.set(this.cur)}
  write(a,i,x,y,s){const j=i*3;a[j]=x;a[j+1]=y;a[j+2]=s}
  build(shape,a){
    const cols=Math.ceil(Math.sqrt(this.n*this.w/this.h)),rows=Math.ceil(this.n/cols),gx=this.w/(cols-1||1),gy=this.h/(rows-1||1);
    if(shape==='none'||shape==='grid'){for(let i=0;i<this.n;i++){const c=i%cols,r=(i/cols)|0,s=shape==='none'?0:(this.rand[i]>.46?.35+this.rand[(i*7+3)%this.n]*.65:0);this.write(a,i,c*gx,r*gy,s)}return}
    if(shape==='image'){const cx=this.w/2,cy=this.h/2,ww=Math.min(this.w*.68,920),hh=ww*.55;for(let i=0;i<this.n;i++){const u=this.rand[i],v=this.rand[(i*17+13)%this.n],x=cx+(u-.5)*ww,y=cy+(v-.5)*hh,ell=Math.pow((x-cx)/(ww*.5),2)+Math.pow((y-cy)/(hh*.5),2),bars=Math.sin((x-cx)*.045)*Math.sin((y-cy)*.05)>.05;this.write(a,i,x,y,ell<1&&bars?.4+this.rand[i]*.6:0)}return}
    const horizontal=shape==='rings-horizontal',rings=horizontal?10:6,per=Math.ceil(this.n/rings),cx=this.w/2,cy=this.h/2,r0=Math.min(this.w,this.h)*(horizontal?.33:.42);for(let i=0;i<this.n;i++){const ring=(i/per)|0,t=(i%per)/per*Math.PI*2,r=Math.max(20,r0-ring*(horizontal?.7:32));const x=horizontal?cx+Math.cos(t)*r:cx+Math.cos(t)*r*.45,y=horizontal?cy-ring*4+Math.sin(t)*r*.55:cy+Math.sin(t)*r;this.write(a,i,x,y,1)}
  }
  set(shape,instant=false){if(shape===this.target&&!instant)return;this.target=shape;this.from.set(this.cur);this.build(shape,this.to);this.startT=performance.now();this.morph=!instant&&!still&&!reduce.matches;if(instant||still||reduce.matches){this.cur.set(this.to);this.shape=shape;this.morph=false}}
  setTheme(name){this.theme=name}
  draw(now,dt){
    const c=this.ctx;c.clearRect(0,0,this.w,this.h);this.mx=lerp(this.mx,this.tx,1-Math.exp(-7*dt));this.my=lerp(this.my,this.ty,1-Math.exp(-7*dt));const p=this.morph?clamp((now-this.startT)/this.dur):1,e=ease(p),arc=Math.sin(p*Math.PI);const dark=this.theme==='dark',base=dark?[49,44,33]:[149,145,128],hi=dark?[227,70,8]:[255,157,0];
    for(let i=0;i<this.n;i++){const j=i*3,r=this.rand[i],r2=this.rand[(i*23+9)%this.n];let x=this.morph?lerp(this.from[j],this.to[j],e):this.cur[j],y=this.morph?lerp(this.from[j+1],this.to[j+1],e):this.cur[j+1],s=this.morph?lerp(this.from[j+2],this.to[j+2],e):this.cur[j+2];if(this.morph){x+=(r-.5)*200*arc;y+=(r2-.5)*200*arc}if(s<.02)continue;const d=Math.hypot(x-this.mx,y-this.my),h=clamp(1-d/Math.min(this.w,this.h)*.42),rr=Math.round(lerp(base[0],hi[0],h)),gg=Math.round(lerp(base[1],hi[1],h)),bb=Math.round(lerp(base[2],hi[2],h)),pulse=.55+.45*Math.sin(now*.002+r*6.28)*.5+.225,rad=(.7+pulse)*s;c.fillStyle='rgba('+rr+','+gg+','+bb+','+(.22+.68*s)+')';c.beginPath();c.arc(x,y,rad,0,Math.PI*2);c.fill()}
    if(this.morph&&p>=1){this.cur.set(this.to);this.shape=this.target;this.morph=false}
  }
}
const particles=new Particles($('#particle-field'));

const focusEls=$$('[data-theme],[data-particles]');let winner=null;
function chooseFocus(){const vh=innerHeight,line=vh*(direction>0?.4:direction<0?.6:.5);let best=null,score=-1;focusEls.forEach(el=>{const r=el.getBoundingClientRect(),vis=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));if(vis<vh*.05)return;const ratio=vis/Math.min(vh,r.height),d=(r.top<=line&&r.bottom>=line)?0:Math.min(Math.abs(r.top-line),Math.abs(r.bottom-line)),center=1-Math.min(1,d/vh),s=ratio*.6+center*.4;if(s>score){score=s;best=el}});if(best&&best!==winner){winner=best;const theme=best.dataset.theme||'dark';document.body.classList.toggle('light',theme==='light');particles.setTheme(theme);particles.set(best.dataset.particles||'none')}}

let smoothY=scrollY,last=performance.now();
function update(now){
  const dt=Math.min(.05,(now-last)/1000);last=now;const y=scrollY;direction=Math.sign(y-lastScroll);lastScroll=y;smoothY=lerp(smoothY,y,1-Math.exp(-8*dt));
  if(y<=header.offsetHeight){header.classList.add('visible');lastToggle=y}else if(Math.abs(y-lastToggle)>50){header.classList.toggle('visible',direction<0);lastToggle=y}
  const vh=innerHeight,hp=clamp(smoothY/vh);
  if(!still&&!reduce.matches){
    if(heroWrappers[1])heroWrappers[1].style.transform='translateY('+(25*hp)+'%)';if(heroImgs[1])heroImgs[1].style.transform='translateY('+(-12.5*hp)+'%)';
    if(heroWrappers[2])heroWrappers[2].style.transform='translateX('+(-25*hp)+'%)';if(heroImgs[2])heroImgs[2].style.transform='translateX('+(12.5*hp)+'%)';
    if(heroWrappers[3])heroWrappers[3].style.transform='translateX('+(25*hp)+'%)';if(heroImgs[3])heroImgs[3].style.transform='translateX('+(-12.5*hp)+'%)';
    if(heroImgs[0])heroImgs[0].style.transform='scale('+(1+.15*hp)+')';
    if(!mobile.matches){const ls=$$('.title>.line',hero);if(ls[0])ls[0].style.transform='translateX('+(-50*hp)+'vw)';if(ls[1])ls[1].style.transform='translateX('+(50*hp)+'vw)';subtitle.style.transform='translateX('+(-5*hp)+'vw)';scrollCue.style.transform='translateX('+(5*hp)+'vw)'}
    subtitle.style.opacity=String(clamp(1-.5*hp));scrollCue.style.opacity=String(clamp(1-.5*hp));
  }
  centered.forEach(sec=>{const r=sec.getBoundingClientRect(),p=clamp(-r.top/(vh*.5));(sec._lines||[]).forEach(l=>l.style.transform='translateY('+(101*(1-p))+'%)');if(sec===rolo)runRolodex(p>=.999)});
  if(cardSec){const r=cardSec.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height*.5));cards.forEach((c,i)=>{const local=clamp((p-i*.06)/.7),e=out(local),extra=i===1?40:i===2?80:0;c.style.opacity=String(e);c.style.transform='translateY('+(extra+(100+i*50)*(1-e))+'px)'})}
  const ins=$('.insights-scene');if(ins){const r=ins.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height));const bg=$('.insights-bg',ins);bg.style.transform='translateY('+((p-.5)*-42)+'px) scale(1.08) rotate(-2deg)'}
  const sock=$('.sock');if(sock){const r=sock.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height)),w=$$('.image-wrapper',sock),im=$$('img',sock);if(im[0])im[0].style.transform='scale('+(1.15-.15*p)+')';if(w[1])w[1].style.transform='translateX('+(-10*(1-p))+'%)';if(im[1])im[1].style.transform='translateX('+(5*(1-p))+'%)';if(w[2])w[2].style.transform='translateY('+(50*(1-p))+'%)';if(im[2])im[2].style.transform='translateY('+(-25*(1-p))+'%)';if(w[3])w[3].style.transform='translateY('+(-50*(1-p))+'%)';if(im[3])im[3].style.transform='translateY('+(25*(1-p))+'%)'}
  chooseFocus();particles.draw(now,dt);requestAnimationFrame(update)
}
if(still){chooseFocus();particles.draw(performance.now(),.016)}else requestAnimationFrame(update);
})();