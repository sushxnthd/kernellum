(() => {
'use strict';

const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const reduce=matchMedia('(prefers-reduced-motion: reduce)');
const mobile=matchMedia('(max-width:58.75rem)');

document.addEventListener('DOMContentLoaded',()=>requestAnimationFrame(()=>document.body.classList.add('ready')));

/* Exact-font detection: keep BOON's font names first; calibrate fallback if cross-origin font loading fails. */
if(document.fonts){
  Promise.allSettled([
    document.fonts.load('500 32px MSCHN'),
    document.fonts.load("450 16px \"Suisse Int'l\"")
  ]).then(()=>{
    const ok=document.fonts.check('500 32px MSCHN')&&document.fonts.check("450 16px \"Suisse Int'l\"");
    document.documentElement.classList.toggle('font-fallback',!ok);
  }).catch(()=>document.documentElement.classList.add('font-fallback'));
}else document.documentElement.classList.add('font-fallback');

/* Header / menu */
const header=$('#header'),toggle=$('#menu-toggle'),menu=$('#expand-menu'),menuLabel=$('#menu-label');
let expanded=false,lastHeaderScroll=0,lastScrollY=scrollY,direction=0;
function scramble(text){
  if(reduce.matches){menuLabel.textContent=text;return}
  const chars='░▒▓■□',start=performance.now(),dur=320;
  const step=now=>{
    const p=clamp((now-start)/dur),fixed=Math.floor(text.length*p);
    menuLabel.textContent=[...text].map((c,i)=>i<fixed?c:chars[(Math.random()*chars.length)|0]).join('');
    if(p<1)requestAnimationFrame(step);else menuLabel.textContent=text;
  };
  requestAnimationFrame(step);
}
function setMenu(v){expanded=v;header.classList.toggle('expanded',v);toggle?.setAttribute('aria-expanded',String(v));scramble(v?'CLOSE':'MENU')}
toggle?.addEventListener('click',()=>setMenu(!expanded));
document.addEventListener('pointerdown',e=>{if(expanded&&!header.contains(e.target))setMenu(false)});
document.addEventListener('keydown',e=>{if(e.key==='Escape')setMenu(false)});
$$('a',menu).forEach(a=>a.addEventListener('click',()=>setMenu(false)));

/* Cursor glow */
$$('.glow-target').forEach(el=>{
  el.addEventListener('pointermove',e=>{
    const r=el.getBoundingClientRect();
    el.style.setProperty('--gx',(e.clientX-r.left)+'px');
    el.style.setProperty('--gy',(e.clientY-r.top)+'px');
  });
});

/* Hero composition */
const hero=$('section.page-header.home');
const heroTitle=$('.title',hero),heroWrappers=$$('.image-wrapper',hero),heroImgs=$$('.image-wrapper img',hero);
const heroSubtitle=$('.subtitle',hero),heroScroll=$('.scroll',hero);
const rawLines=heroTitle.textContent.trim().split('\n').map(x=>x.trim()).filter(Boolean);
heroTitle.innerHTML=rawLines.map(x=>'<span class="line"><span>'+x+'</span></span>').join('');
const heroLines=$$('.title>.line>span',hero);
heroLines.forEach((l,i)=>{l.style.opacity='0';l.style.transform='translateY(.55em)';l.style.transition='opacity .9s cubic-bezier(.65,0,.35,1) '+(180+i*80)+'ms,transform .9s cubic-bezier(.65,0,.35,1) '+(180+i*80)+'ms'});
heroImgs.forEach((img,i)=>{img.style.opacity='0';img.style.transition='opacity .9s cubic-bezier(.5,.1,0,1) '+(100+i*70)+'ms'});
[heroSubtitle,heroScroll].forEach((el,i)=>{el.style.opacity='0';el.style.transition='opacity .6s ease '+(1050+i*100)+'ms,transform .6s cubic-bezier(.5,.1,0,1) '+(1050+i*100)+'ms';el.style.transform='translateY(16px)'});
requestAnimationFrame(()=>requestAnimationFrame(()=>{
  heroLines.forEach(l=>{l.style.opacity='1';l.style.transform='translateY(0)'});
  heroImgs.forEach(i=>i.style.opacity='1');
  [heroSubtitle,heroScroll].forEach(el=>{el.style.opacity='1';el.style.transform='translateY(0)'});
}));

/* Centered text line wrappers */
const centered=$$('section.centered-text');
centered.forEach(sec=>{
  const main=$('.main-text',sec);if(!main)return;
  const lines=main.textContent.split('\n').map(x=>x.trim()).filter(Boolean);
  main.innerHTML=lines.map(x=>'<span class="line"><span>'+x+'</span></span>').join('');
  sec._lines=$$('.line>span',main);
  sec._lines.forEach(l=>l.style.transform='translateY(101%)');
});
const roloSec=$('.centered-text-two'),roloEntries=roloSec?$$('.rolodex-entry',roloSec):[];
let roloIndex=0,roloTimer=0;
function rolodex(on){
  if(on&&!roloTimer&&roloEntries.length){
    roloTimer=setInterval(()=>{
      roloEntries[roloIndex].classList.remove('active');
      roloIndex=(roloIndex+1)%roloEntries.length;
      roloEntries[roloIndex].classList.add('active');
    },2000);
  }else if(!on&&roloTimer){clearInterval(roloTimer);roloTimer=0}
}

/* Card and statement preparation */
const cards=$$('ul.cards li.card'),cardGrid=$('.card-grid');
cards.forEach((c,i)=>{c.style.opacity='0';c.style.transform='translateY('+(100+i*50)+'px)'});
const large=$('.large-text'),largeH=$('h2',large);
if(largeH){
  const html=largeH.innerHTML;
  const m=html.match(/^(.*?)(<mark>.*<\/mark>)$/i);
  if(m)largeH.innerHTML='<span class="large-line"><span>'+m[1].trim()+'</span></span><span class="large-line"><span>'+m[2]+'</span></span>';
  $$('.large-line',largeH).forEach(l=>{l.style.display='block';l.style.overflow='hidden';l.firstElementChild.style.display='block';l.firstElementChild.style.transform='translateY(100%)'});
}
const sock=$('.sock'),sockWrap=sock?$$('.image-wrapper',sock):[],sockImgs=sock?$$('.image-wrapper img',sock):[];
const sockH=sock?$('h2',sock):null;
if(sockH){sockH.innerHTML='<span class="sock-line"><span>'+sockH.textContent.trim()+'</span></span>';const s=$('.sock-line',sockH);s.style.display='block';s.style.overflow='hidden';s.firstElementChild.style.display='block';s.firstElementChild.style.transform='translateY(100%)'}

/* ---------- Runtime-safe canvas particle engine ---------- */
class ParticleField{
  constructor(canvas){
    this.canvas=canvas;this.ctx=canvas.getContext('2d',{alpha:true});
    this.pointer={x:innerWidth/2,y:innerHeight/2,tx:innerWidth/2,ty:innerHeight/2};
    this.base=[49,44,33];this.hi=[227,70,8];this.targetBase=[49,44,33];this.targetHi=[227,70,8];
    this.shape='none';this.targetShape='none';this.morphStart=0;this.morphDuration=1500;this.morphing=false;this.imageToken=0;
    addEventListener('pointermove',e=>{this.pointer.tx=e.clientX;this.pointer.ty=e.clientY},{passive:true});
    addEventListener('resize',()=>this.resize(),{passive:true});
    this.resize();this.setShape('none',null,true);
  }
  resize(){
    const dpr=Math.min(devicePixelRatio||1,1.6);
    this.w=innerWidth;this.h=innerHeight;this.canvas.width=Math.floor(this.w*dpr);this.canvas.height=Math.floor(this.h*dpr);this.canvas.style.width=this.w+'px';this.canvas.style.height=this.h+'px';this.ctx.setTransform(dpr,0,0,dpr,0,0);
    const desired=Math.ceil(this.w/13.5)*Math.ceil(this.h/13.5),cap=mobile.matches?3000:6500;
    this.n=Math.min(desired,cap);
    this.cur=new Float32Array(this.n*3);this.tar=new Float32Array(this.n*3);this.start=new Float32Array(this.n*3);this.rand=new Float32Array(this.n);
    for(let i=0;i<this.n;i++)this.rand[i]=Math.random();
    this.build(this.shape,this.cur);this.tar.set(this.cur);this.start.set(this.cur);
  }
  color(name){return name==='light'?[[149,145,128],[255,157,0]]:[[49,44,33],[227,70,8]]}
  setTheme(name){const [a,b]=this.color(name);this.targetBase=a;this.targetHi=b}
  write(arr,i,x,y,s){const j=i*3;arr[j]=x;arr[j+1]=y;arr[j+2]=s}
  build(shape,out){
    if(!out)return;
    const cols=Math.ceil(Math.sqrt(this.n*this.w/this.h)),rows=Math.ceil(this.n/cols),gx=this.w/(cols-1||1),gy=this.h/(rows-1||1);
    if(shape==='grid'||shape==='none'){
      for(let i=0;i<this.n;i++){const c=i%cols,r=(i/cols)|0,x=c*gx,y=r*gy,s=shape==='none'?0:(Math.random()>.46?.42+Math.random()*.58:0);this.write(out,i,x,y,s)}
      return;
    }
    if(shape==='rings-horizontal'){
      const rings=10,per=Math.ceil(this.n/rings),cx=this.w/2,cy=this.h/2,r0=Math.min(this.w,this.h)*.34;
      for(let i=0;i<this.n;i++){const ring=(i/per)|0,a=(i%per)/per*Math.PI*2,r=r0-ring*.9;this.write(out,i,cx+Math.cos(a)*r,cy-ring*4+Math.sin(a)*r*.55,1)}
      return;
    }
    if(shape==='rings-vertical'){
      const rings=6,per=Math.ceil(this.n/rings),cx=this.w/2,cy=this.h/2,r0=Math.min(this.w,this.h)*.43;
      for(let i=0;i<this.n;i++){const ring=(i/per)|0,a=(i%per)/per*Math.PI*2,r=Math.max(20,r0-ring*32);this.write(out,i,cx+Math.cos(a)*r*.45,cy+Math.sin(a)*r,1)}
      return;
    }
    if(shape==='image'){
      const cx=this.w/2,cy=this.h/2,ww=Math.min(this.w*.58,760),hh=ww*.55;
      for(let i=0;i<this.n;i++){
        const u=this.rand[i],v=(this.rand[(i*17+13)%this.n]||.5);
        const x=cx+(u-.5)*ww,y=cy+(v-.5)*hh;
        const edge=Math.pow((x-cx)/(ww*.5),2)+Math.pow((y-cy)/(hh*.5),2);
        const bars=(Math.sin((x-cx)*.055)*Math.sin((y-cy)*.06)>.15);
        this.write(out,i,x,y,edge<1&&bars?(.45+this.rand[i]*.55):0);
      }
      return;
    }
    this.build('grid',out);
  }
  async setShape(shape,image,instant=false){
    if(shape===this.targetShape&&!instant)return;
    this.targetShape=shape;this.start.set(this.cur);this.build(shape,this.tar);this.morphStart=performance.now();this.morphing=!instant&&!reduce.matches;
    if(instant){this.cur.set(this.tar);this.shape=shape;this.morphing=false}
    if(shape==='image'&&image){ // Optional: upgrade synthetic point cloud to real image luminance when CORS permits.
      const token=++this.imageToken,img=new Image();img.crossOrigin='anonymous';img.src=image;
      try{
        await img.decode();if(token!==this.imageToken)return;
        const cols=Math.ceil(Math.sqrt(this.n*this.w/this.h)),rows=Math.ceil(this.n/cols),oc=document.createElement('canvas');oc.width=cols;oc.height=rows;const c=oc.getContext('2d',{willReadFrequently:true});
        const sc=Math.max(cols/img.width,rows/img.height),dw=img.width*sc,dh=img.height*sc;c.drawImage(img,(cols-dw)/2,(rows-dh)/2,dw,dh);const d=c.getImageData(0,0,cols,rows).data;
        const gx=this.w/(cols-1||1),gy=this.h/(rows-1||1);
        for(let i=0;i<this.n;i++){const col=i%cols,row=(i/cols)|0,p=(row*cols+col)*4,lum=(.299*d[p]+.587*d[p+1]+.114*d[p+2])/255,s=d[p+3]>120?clamp((1-lum-.22)/.65):0;this.write(this.tar,i,col*gx,row*gy,s)}
        this.start.set(this.cur);this.morphStart=performance.now();this.morphing=!reduce.matches;
      }catch(_){}
    }
  }
  frame(now,dt){
    const c=this.ctx;c.clearRect(0,0,this.w,this.h);
    this.pointer.x=lerp(this.pointer.x,this.pointer.tx,1-Math.exp(-7*dt));this.pointer.y=lerp(this.pointer.y,this.pointer.ty,1-Math.exp(-7*dt));
    for(let k=0;k<3;k++){this.base[k]=lerp(this.base[k],this.targetBase[k],1-Math.exp(-4*dt));this.hi[k]=lerp(this.hi[k],this.targetHi[k],1-Math.exp(-4*dt))}
    let p=this.morphing?clamp((now-this.morphStart)/this.morphDuration):1,e=ease(p),arc=Math.sin(p*Math.PI);
    for(let i=0;i<this.n;i++){
      const j=i*3,r=this.rand[i],r2=this.rand[(i*31+7)%this.n];
      let x=this.morphing?lerp(this.start[j],this.tar[j],e):this.cur[j],y=this.morphing?lerp(this.start[j+1],this.tar[j+1],e):this.cur[j+1],s=this.morphing?lerp(this.start[j+2],this.tar[j+2],e):this.cur[j+2];
      if(this.morphing){x+=(r-.5)*180*arc;y+=(r2-.5)*180*arc}
      if(s<.02)continue;
      const dx=x-this.pointer.x,dy=y-this.pointer.y,d=Math.hypot(dx,dy),hi=clamp(1-d/Math.min(this.w,this.h)*.4);
      const rr=Math.round(lerp(this.base[0],this.hi[0],hi)),gg=Math.round(lerp(this.base[1],this.hi[1],hi)),bb=Math.round(lerp(this.base[2],this.hi[2],hi));
      const pulse=.45+.5*(.5+.5*Math.sin(now*.002+r*6.28)),rad=(.75+1.05*pulse)*s;
      c.fillStyle='rgba('+rr+','+gg+','+bb+','+(.25+.7*s)+')';c.beginPath();c.arc(x,y,rad,0,Math.PI*2);c.fill();
      if(this.morphing&&p>=1){this.cur[j]=this.tar[j];this.cur[j+1]=this.tar[j+1];this.cur[j+2]=this.tar[j+2]}
    }
    if(this.morphing&&p>=1){this.cur.set(this.tar);this.shape=this.targetShape;this.morphing=false}
  }
}
const particles=new ParticleField($('#particle-canvas'));

/* Section focus picker */
const focusEls=$$('[data-theme],[data-particles]');let winner=null;
function pickFocus(){
  const vh=innerHeight,line=vh*(direction>0?.4:direction<0?.6:.5);let best=null,score=-1;
  focusEls.forEach(el=>{
    const r=el.getBoundingClientRect(),visible=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));if(visible<vh*.05)return;
    const ratio=visible/Math.min(vh,r.height),d=(r.top<=line&&r.bottom>=line)?0:Math.min(Math.abs(r.top-line),Math.abs(r.bottom-line)),center=1-Math.min(1,d/vh),s=ratio*.6+center*.4;
    if(s>score){score=s;best=el}
  });
  if(best&&best!==winner){
    winner=best;const theme=best.dataset.theme||'dark';document.body.classList.toggle('light',theme==='light');particles.setTheme(theme);particles.setShape(best.dataset.particles||'none',best.dataset.image);
  }
}

/* Scroll-linked choreography */
let smoothY=scrollY,last=performance.now(),cardsVisible=false;
function frame(now){
  const dt=Math.min(.05,(now-last)/1000);last=now;
  const y=scrollY;direction=Math.sign(y-lastScrollY);lastScrollY=y;smoothY=lerp(smoothY,y,1-Math.exp(-8*dt));

  if(y<=header.offsetHeight){header.classList.add('visible');lastHeaderScroll=y}
  else if(Math.abs(y-lastHeaderScroll)>50){header.classList.toggle('visible',direction<0);lastHeaderScroll=y}

  const vh=innerHeight;
  const hp=clamp(smoothY/vh);
  if(!reduce.matches){
    if(heroWrappers[1])heroWrappers[1].style.transform='translate3d(0,'+(25*hp)+'%,0)';
    if(heroImgs[1])heroImgs[1].style.transform='translate3d(0,'+(-12.5*hp)+'%,0)';
    if(heroWrappers[2])heroWrappers[2].style.transform='translate3d('+(-25*hp)+'%,0,0)';
    if(heroImgs[2])heroImgs[2].style.transform='translate3d('+(12.5*hp)+'%,0,0)';
    if(heroWrappers[3])heroWrappers[3].style.transform='translate3d('+(25*hp)+'%,0,0)';
    if(heroImgs[3])heroImgs[3].style.transform='translate3d('+(-12.5*hp)+'%,0,0)';
    if(heroImgs[0])heroImgs[0].style.transform='scale('+(1+.15*hp)+')';
    if(!mobile.matches){
      if(heroLines[0])heroLines[0].parentElement.style.transform='translate3d('+(-50*hp)+'vw,0,0)';
      if(heroLines[1])heroLines[1].parentElement.style.transform='translate3d('+(50*hp)+'vw,0,0)';
      heroSubtitle.style.transform='translate3d('+(-5*hp)+'vw,0,0)';
      heroScroll.style.transform='translate3d('+(5*hp)+'vw,0,0)';
    }
    heroSubtitle.style.opacity=String(clamp(1-.5*hp));heroScroll.style.opacity=String(clamp(1-.5*hp));
  }

  centered.forEach(sec=>{
    const r=sec.getBoundingClientRect(),p=clamp(-r.top/(vh*.5));
    (sec._lines||[]).forEach(l=>l.style.transform='translateY('+(101*(1-p))+'%)');
    if(sec===roloSec)rolodex(p>=.995);
  });

  if(cardGrid){
    const r=cardGrid.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height*.45));
    if(p>0&&!cardsVisible){cardsVisible=true;$('.cards',cardGrid)?.classList.remove('pre-anim')}
    cards.forEach((c,i)=>{const local=clamp((p-i*.06)/.72),e=outCubic(local);c.style.opacity=String(e);c.style.transform='translateY('+((100+i*50)*(1-e))+'px)'});
  }

  if(large){
    const r=large.getBoundingClientRect(),p=clamp((vh*.55-r.top)/(vh*.55));
    $$('.large-line>span',large).forEach(s=>s.style.transform='translateY('+(100*(1-p))+'%)');
  }

  const insights=$('.insights-scene');
  if(insights){
    const r=insights.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height));
    const bg=$('.insights-backdrop',insights);if(bg)bg.style.transform='translate3d(0,'+((p-.5)*-42)+'px,0) scale(1.08) rotate(-2deg)';
  }

  if(sock){
    const r=sock.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height));
    if(sockImgs[0])sockImgs[0].style.transform='scale('+(1.15-.15*p)+')';
    if(sockWrap[1])sockWrap[1].style.transform='translate3d('+(-10*(1-p))+'%,0,0)';
    if(sockImgs[1])sockImgs[1].style.transform='translate3d('+(5*(1-p))+'%,0,0)';
    if(sockWrap[2])sockWrap[2].style.transform='translate3d(0,'+(50*(1-p))+'%,0)';
    if(sockImgs[2])sockImgs[2].style.transform='translate3d(0,'+(-25*(1-p))+'%,0)';
    if(sockWrap[3])sockWrap[3].style.transform='translate3d(0,'+(-50*(1-p))+'%,0)';
    if(sockImgs[3])sockImgs[3].style.transform='translate3d(0,'+(25*(1-p))+'%,0)';
    const sl=$('.sock-line>span',sock);if(sl)sl.style.transform='translateY('+(100*(1-clamp((p-.38)/.55)))+'%)';
  }

  pickFocus();particles.frame(now,dt);requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

reduce.addEventListener?.('change',()=>location.reload());
})();