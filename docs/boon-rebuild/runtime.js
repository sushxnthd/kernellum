(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const out=t=>1-Math.pow(1-t,3);
const mobile=matchMedia('(max-width:58.749rem)');
const reduce=matchMedia('(prefers-reduced-motion:reduce)');

/* ---------- exact client-only header shape ---------- */
const header=$('#header');
if(header){
  header.innerHTML=`
    <div class="nav-bar">
      <a class="k-logo" href="#home" aria-label="Kernellum"><span>KERNELLUM</span></a>
      <button class="k-menu-btn" type="button" aria-expanded="false">
        <p>MENU</p>
        <b class="k-dot9" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></b>
      </button>
      <div class="k-menu-panel">
        <a href="#home">Home</a>
        <a href="#difference">What We Do</a>
        <a href="#research">Research</a>
        <a href="#insights">Insights</a>
        <a href="https://github.com/sushxnthd/kernellum">GitHub ↗</a>
      </div>
    </div>`;
  const btn=$('.k-menu-btn',header),label=$('p',btn);
  const scramble=text=>{
    if(reduce.matches){label.textContent=text;return}
    const chars='░▒▓■□',start=performance.now(),dur=300;
    const f=now=>{const p=clamp((now-start)/dur),fixed=Math.floor(text.length*p);label.textContent=[...text].map((c,i)=>i<fixed?c:chars[(Math.random()*chars.length)|0]).join('');if(p<1)requestAnimationFrame(f);else label.textContent=text};requestAnimationFrame(f)
  };
  btn.addEventListener('click',()=>{
    const open=!header.classList.contains('k-expanded');
    header.classList.toggle('k-expanded',open);btn.setAttribute('aria-expanded',String(open));scramble(open?'CLOSE':'MENU');
  });
  document.addEventListener('pointerdown',e=>{if(header.classList.contains('k-expanded')&&!header.contains(e.target)){header.classList.remove('k-expanded');btn.setAttribute('aria-expanded','false');scramble('MENU')}});
}

/* ---------- source-faithful content preparation ---------- */
const hero=$('section.page-header.home');
if(hero) hero.id='home';
const heroTitle=hero?$('.title',hero):null;
const heroWrappers=hero?$$('.images>.image-wrapper',hero):[];
const heroImgs=hero?$$('.images>.image-wrapper img',hero):[];
const heroSubtitle=hero?$('.subtitle',hero):null;
const heroScroll=hero?$('.scroll',hero):null;
if(heroTitle){
  const lines=heroTitle.textContent.trim().split(/\n+/).map(s=>s.trim()).filter(Boolean);
  heroTitle.innerHTML=lines.map(s=>`<span class="k-line"><span>${s}</span></span>`).join('');
  if(!reduce.matches){
    $$('.k-line>span',heroTitle).forEach((l,i)=>{l.style.opacity='0';l.style.transform='translateY(.6em)';l.style.transition=`opacity .9s cubic-bezier(.65,0,.35,1) ${180+i*80}ms,transform .9s cubic-bezier(.65,0,.35,1) ${180+i*80}ms`});
    heroImgs.forEach((im,i)=>{im.style.opacity='0';im.style.transition=`opacity .9s cubic-bezier(.5,.1,0,1) ${100+i*65}ms`});
    [heroSubtitle,heroScroll].filter(Boolean).forEach((el,i)=>{el.style.opacity='0';el.style.transform='translateY(16px)';el.style.transition=`opacity .6s ease ${1100+i*100}ms,transform .6s cubic-bezier(.5,.1,0,1) ${1100+i*100}ms`});
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      $$('.k-line>span',heroTitle).forEach(l=>{l.style.opacity='1';l.style.transform='translateY(0)'});
      heroImgs.forEach(im=>im.style.opacity='1');
      [heroSubtitle,heroScroll].filter(Boolean).forEach(el=>{el.style.opacity='1';el.style.transform='translateY(0)'});
    }));
  }else heroImgs.forEach(im=>im.style.opacity='1');
}

const centered=$$('section.centered-text');
centered.forEach((sec,i)=>{
  if(i===1)sec.id='difference';
  const main=$('.main-text',sec);if(!main)return;
  const lines=main.textContent.trim().split(/\n+/).map(s=>s.trim()).filter(Boolean);
  main.innerHTML=lines.map(s=>`<span class="k-line"><span>${s}</span></span>`).join('');
  sec._kLines=$$('.k-line>span',main);
  if(!reduce.matches)sec._kLines.forEach(l=>l.style.transform='translateY(101%)');
});
const roloSec=centered[1],roloEntries=roloSec?$$('.rolodex-entry',roloSec):[];
roloEntries.forEach((e,i)=>e.classList.toggle('k-active',i===0));
let roloIndex=0,roloTimer=0;
function runRolodex(on){
  if(reduce.matches||!roloEntries.length)return;
  if(on&&!roloTimer){roloTimer=setInterval(()=>{roloEntries[roloIndex].classList.remove('k-active');roloIndex=(roloIndex+1)%roloEntries.length;roloEntries[roloIndex].classList.add('k-active')},2000)}
  else if(!on&&roloTimer){clearInterval(roloTimer);roloTimer=0}
}

const cardGrid=$('section.card-grid.three-wide'); if(cardGrid) cardGrid.id='research';
const cardList=cardGrid?$('ul.cards',cardGrid):null;
if(cardList)cardList.classList.remove('pre-anim');
const cards=cardGrid?$('ul.cards>li.card',cardGrid):[];
cards.forEach((c,i)=>{if(!reduce.matches){c.style.opacity='0';c.style.transform=`translateY(${100+i*50}px)`}});

/* draw BOON-like animated orange marks into the existing lottie canvases */
$$('.card-grid .lottie-canvas canvas').forEach((cv,idx)=>{
  const ctx=cv.getContext('2d');let start=performance.now();
  const draw=now=>{
    const r=cv.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2),w=Math.max(1,Math.round(r.width*dpr)),h=Math.max(1,Math.round(r.height*dpr));
    if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h}ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,r.width,r.height);
    const cx=r.width/2,cy=r.height/2,R=Math.min(r.width,r.height)*.36,t=(now-start)*.001;
    ctx.strokeStyle=getComputedStyle(document.documentElement).getPropertyValue('--clr-primary').trim()||'#ff9d00';ctx.lineWidth=1;
    ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.stroke();
    ctx.setLineDash([1.5,4]);
    ctx.beginPath();ctx.arc(cx,cy,R*(idx===0?.58:idx===1?.7:.8),t*(idx+1)*.35,t*(idx+1)*.35+Math.PI*1.7);ctx.stroke();ctx.setLineDash([]);
    if(idx===1){ctx.beginPath();ctx.arc(cx,cy,R*.28,0,Math.PI*2);ctx.stroke()}
    if(idx===2){ctx.beginPath();ctx.moveTo(cx-R*.38,cy);ctx.lineTo(cx+R*.38,cy);ctx.stroke()}
    requestAnimationFrame(draw)
  };requestAnimationFrame(draw)
});

/* sock images are client-populated on BOON; restore the same production assets */
const sock=$('section.sock'); if(sock)sock.id='insights';
const sockImgs=sock?$$('.images .image-wrapper img',sock):[];
const sockUrls=[
 'https://cdn.sanity.io/images/cktal3h7/production/be4c39906759d893e768c4a568249eb5d45d9f2d-1344x896.png?w=1920&q=80&auto=format',
 'https://cdn.sanity.io/images/cktal3h7/production/5801762dd7fa3dc8bee609598fcda57777814cff-1232x928.png?w=1920&q=80&auto=format',
 'https://cdn.sanity.io/images/cktal3h7/production/901002228d737f8cef110aab22ad5d49bd3bf3cf-5567x3542.jpg?w=1920&q=80&auto=format',
 'https://cdn.sanity.io/images/cktal3h7/production/a5fac863effd309796bd824f9d3bda53d56872c7-2464x1856.png?w=1920&q=80&auto=format'
];
sockImgs.forEach((im,i)=>{if(sockUrls[i]){im.src=sockUrls[i];im.style.opacity='1'}});
const sockH=sock?$('h2',sock):null;
if(sockH){sockH.innerHTML=`<span class="k-line"><span>${sockH.textContent.trim()}</span></span>`}

/* minimal visible brand substitutions, no geometry changes */
document.title='Kernellum';
$$('.text-label').forEach(el=>{if(/boon difference/i.test(el.textContent))el.textContent='The Kernellum Difference'});
$$('p,h1,h2,h3,h4,h5,span').forEach(el=>{if(el.children.length===0&&/\bBOON\b/.test(el.textContent))el.textContent=el.textContent.replace(/\bBOON\b/g,'KERNELLUM')});

/* ---------- persistent BOON-style particle field ---------- */
class ParticleField{
  constructor(canvas){
    this.canvas=canvas;this.ctx=canvas.getContext('2d');this.shape='none';this.target='none';this.theme='dark';this.start=0;this.duration=1500;this.morphing=false;this.mx=innerWidth/2;this.my=innerHeight/2;this.tx=this.mx;this.ty=this.my;
    addEventListener('pointermove',e=>{this.tx=e.clientX;this.ty=e.clientY},{passive:true});addEventListener('resize',()=>this.resize(),{passive:true});this.image=null;this.imageReady=false;this.loadImage();this.resize();this.set('none',true)
  }
  loadImage(){const im=new Image();im.crossOrigin='anonymous';im.src='https://cdn.sanity.io/images/cktal3h7/production/6e6c3150c4aee4b572782ae46c37e742f19fb173-1600x1066.png?w=1800&q=85&auto=format';im.onload=()=>{this.image=im;this.imageReady=true;if(this.target==='image'){this.from.set(this.cur);this.build('image',this.to);this.start=performance.now();this.morphing=!reduce.matches}}}
  resize(){const dpr=Math.min(devicePixelRatio||1,1.5);this.w=innerWidth;this.h=innerHeight;this.canvas.width=Math.floor(this.w*dpr);this.canvas.height=Math.floor(this.h*dpr);this.canvas.style.width=this.w+'px';this.canvas.style.height=this.h+'px';this.ctx.setTransform(dpr,0,0,dpr,0,0);this.n=Math.min(mobile.matches?1350:2300,Math.ceil(this.w/13.5)*Math.ceil(this.h/13.5));this.cur=new Float32Array(this.n*3);this.from=new Float32Array(this.n*3);this.to=new Float32Array(this.n*3);this.rand=new Float32Array(this.n);for(let i=0;i<this.n;i++)this.rand[i]=Math.random();this.build(this.shape,this.cur);this.to.set(this.cur)}
  write(a,i,x,y,s){const j=i*3;a[j]=x;a[j+1]=y;a[j+2]=s}
  build(shape,a){
    const cols=Math.ceil(Math.sqrt(this.n*this.w/this.h)),rows=Math.ceil(this.n/cols),gx=this.w/(cols-1||1),gy=this.h/(rows-1||1);
    if(shape==='none'||shape==='grid'){for(let i=0;i<this.n;i++){const c=i%cols,r=(i/cols)|0,s=shape==='none'?0:(this.rand[i]>.43?.55+this.rand[(i*7+3)%this.n]*1.05:0);this.write(a,i,c*gx,r*gy,s)}return}
    if(shape==='image'){
      if(this.imageReady&&this.image){
        const oc=document.createElement('canvas');oc.width=cols;oc.height=rows;const ox=oc.getContext('2d',{willReadFrequently:true});
        const sc=Math.max(cols/this.image.width,rows/this.image.height),dw=this.image.width*sc,dh=this.image.height*sc;
        ox.drawImage(this.image,(cols-dw)/2,(rows-dh)/2,dw,dh);
        const data=ox.getImageData(0,0,cols,rows).data;
        for(let i=0;i<this.n;i++){const c=i%cols,r=(i/cols)|0,p=(r*cols+c)*4,lum=Math.max(data[p],data[p+1],data[p+2])/255,s=data[p+3]>40&&lum>.08?(.45+lum*1.15):0;this.write(a,i,c*gx,r*gy,s)}
      }else{
        const cx=this.w/2,cy=this.h/2,ww=this.w*1.15,hh=this.h*1.08;
        for(let i=0;i<this.n;i++){const u=this.rand[i],v=this.rand[(i*17+13)%this.n],x=cx+(u-.5)*ww,y=cy+(v-.5)*hh,ell=Math.pow((x-cx)/(ww*.5),2)+Math.pow((y-cy)/(hh*.5),2),mask=Math.sin((x-cx)*.032)*Math.sin((y-cy)*.038)>.0;this.write(a,i,x,y,ell<1&&mask?.5+this.rand[i]*1.05:0)}
      }
      return}
    const horiz=shape==='rings-horizontal',rings=horiz?10:6,per=Math.ceil(this.n/rings),cx=this.w/2,cy=this.h/2,r0=Math.min(this.w,this.h)*(horiz?.33:.42);
    for(let i=0;i<this.n;i++){const ring=(i/per)|0,t=(i%per)/per*Math.PI*2,r=Math.max(18,r0-ring*(horiz?.8:32)),x=horiz?cx+Math.cos(t)*r:cx+Math.cos(t)*r*.44,y=horiz?cy-ring*4+Math.sin(t)*r*.55:cy+Math.sin(t)*r;this.write(a,i,x,y,1)}
  }
  set(shape,instant=false){if(shape===this.target&&!instant)return;this.target=shape;this.from.set(this.cur);this.build(shape,this.to);this.start=performance.now();this.morphing=!instant&&!reduce.matches;if(instant||reduce.matches){this.cur.set(this.to);this.shape=shape;this.morphing=false}}
  draw(now,dt){
    const c=this.ctx;c.clearRect(0,0,this.w,this.h);this.mx=lerp(this.mx,this.tx,1-Math.exp(-6*dt));this.my=lerp(this.my,this.ty,1-Math.exp(-6*dt));const p=this.morphing?clamp((now-this.start)/this.duration):1,e=ease(p),arc=Math.sin(p*Math.PI),dark=this.theme==='dark',base=dark?[49,44,33]:[149,145,128],hi=dark?[227,70,8]:[255,157,0];
    for(let i=0;i<this.n;i++){const j=i*3,r=this.rand[i],r2=this.rand[(i*23+9)%this.n];let x=this.morphing?lerp(this.from[j],this.to[j],e):this.cur[j],y=this.morphing?lerp(this.from[j+1],this.to[j+1],e):this.cur[j+1],s=this.morphing?lerp(this.from[j+2],this.to[j+2],e):this.cur[j+2];if(this.morphing){x+=(r-.5)*230*arc;y+=(r2-.5)*230*arc}if(s<.02)continue;const d=Math.hypot(x-this.mx,y-this.my),h=clamp(1-d/Math.min(this.w,this.h)*.42),rr=Math.round(lerp(base[0],hi[0],h)),gg=Math.round(lerp(base[1],hi[1],h)),bb=Math.round(lerp(base[2],hi[2],h)),pulse=.62+.38*Math.sin(now*.002+r*6.28),rad=(2.25+3.1*pulse)*s;c.fillStyle=`rgba(${rr},${gg},${bb},${.25+.68*s})`;c.beginPath();c.arc(x,y,rad,0,Math.PI*2);c.fill()}
    if(this.morphing&&p>=1){this.cur.set(this.to);this.shape=this.target;this.morphing=false}
  }
}
const bgCanvas=$('.three-canvas');
const particles=bgCanvas?new ParticleField(bgCanvas):null;

const themeDark={base:'#010001',base2:'#161210',base3:'#312c21',content:'#eeeadc',content2:'#cdc9b5',muted:'#959180',border:'#312c21',primary:'#ff9d00',secondary:'#e34608'};
const themeLight={base:'#cdc9b5',base2:'#eeeadc',base3:'#cdc9b5',content:'#010001',content2:'#010001',muted:'#5e594a',border:'#959180',primary:'#e34608',secondary:'#ff9d00'};
function setTheme(){
  const t=themeDark,r=document.documentElement.style;
  r.setProperty('--clr-base-100',t.base);r.setProperty('--clr-base-200',t.base2);r.setProperty('--clr-base-300',t.base3);r.setProperty('--clr-base-400',t.base);
  r.setProperty('--clr-content-100',t.content);r.setProperty('--clr-content-200',t.content2);r.setProperty('--clr-content-300',t.muted);r.setProperty('--clr-border',t.border);r.setProperty('--clr-border-card',t.border);r.setProperty('--clr-primary',t.primary);r.setProperty('--clr-secondary',t.secondary);
  if(particles)particles.theme='dark';
}
const large=$('section.large-text');
const focus=[
  [hero,'dark','none'],
  [centered[0],'dark','grid'],
  [centered[1],'dark','image'],
  [cardGrid,'dark','rings-horizontal'],
  [large,'dark','rings-vertical'],
  [sock,'dark','none']
].filter(x=>x[0]);
let focusEl=null;
function chooseFocus(){
  const vh=innerHeight,line=vh*(scrollY>lastY?.4:scrollY<lastY?.6:.5);let best=null,score=-1;
  focus.forEach(item=>{const r=item[0].getBoundingClientRect(),vis=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));if(vis<vh*.05)return;const ratio=vis/Math.min(vh,r.height),d=(r.top<=line&&r.bottom>=line)?0:Math.min(Math.abs(r.top-line),Math.abs(r.bottom-line)),center=1-Math.min(1,d/vh),s=ratio*.6+center*.4;if(s>score){score=s;best=item}});
  if(best&&best[0]!==focusEl){focusEl=best[0];setTheme();if(particles)particles.set(best[2])}
}

/* ---------- scroll choreography ---------- */
let smoothY=scrollY,lastY=scrollY,lastToggle=0,lastTime=performance.now();
function frame(now){
  const dt=Math.min(.05,(now-lastTime)/1000);lastTime=now;
  const y=scrollY,dir=Math.sign(y-lastY),vh=innerHeight;smoothY=lerp(smoothY,y,1-Math.exp(-8*dt));
  if(header){if(y<=vh*1.05){header.classList.add('visible');lastToggle=y}else if(Math.abs(y-lastToggle)>80){header.classList.toggle('visible',dir<0);lastToggle=y}}
  const hp=clamp(smoothY/vh);
  if(hero&&!reduce.matches){
    if(heroWrappers[1])heroWrappers[1].style.transform=`translateY(${25*hp}%)`;if(heroImgs[1])heroImgs[1].style.transform=`translateY(${-12.5*hp}%)`;
    if(heroWrappers[2])heroWrappers[2].style.transform=`translateX(${-25*hp}%)`;if(heroImgs[2])heroImgs[2].style.transform=`translateX(${12.5*hp}%)`;
    if(heroWrappers[3])heroWrappers[3].style.transform=`translateX(${25*hp}%)`;if(heroImgs[3])heroImgs[3].style.transform=`translateX(${-12.5*hp}%)`;
    if(heroImgs[0])heroImgs[0].style.transform=`scale(${1+.15*hp})`;
    if(!mobile.matches){const ls=$$('.title>.k-line',hero);if(ls[0])ls[0].style.transform=`translateX(${-50*hp}vw)`;if(ls[1])ls[1].style.transform=`translateX(${50*hp}vw)`;if(heroSubtitle)heroSubtitle.style.transform=`translateX(${-5*hp}vw)`;if(heroScroll)heroScroll.style.transform=`translateX(${5*hp}vw)`}
    if(heroSubtitle)heroSubtitle.style.opacity=String(clamp(1-hp/.68));if(heroScroll)heroScroll.style.opacity=String(clamp(1-hp/.68));
  }
  centered.forEach(sec=>{const r=sec.getBoundingClientRect(),p=clamp(-r.top/(vh*.5));(sec._kLines||[]).forEach(l=>l.style.transform=`translateY(${101*(1-p)}%)`);if(sec===roloSec)runRolodex(p>=.995)});
  if(cardGrid&&!reduce.matches){const r=cardGrid.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height*.5));cards.forEach((c,i)=>{const lp=clamp((p-i*.06)/.7),e=out(lp);c.style.opacity=String(e);c.style.transform=`translateY(${(100+i*50)*(1-e)}px)`})}
  if(sock&&!reduce.matches){const r=sock.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height)),wrap=$$('.images>.image-wrapper',sock);if(sockImgs[0])sockImgs[0].style.transform=`scale(${1.15-.15*p})`;if(wrap[1])wrap[1].style.transform=`translateX(${-10*(1-p)}%)`;if(sockImgs[1])sockImgs[1].style.transform=`translateX(${5*(1-p)}%)`;if(wrap[2])wrap[2].style.transform=`translateY(${50*(1-p)}%)`;if(sockImgs[2])sockImgs[2].style.transform=`translateY(${-25*(1-p)}%)`;if(wrap[3])wrap[3].style.transform=`translateY(${-50*(1-p)}%)`;if(sockImgs[3])sockImgs[3].style.transform=`translateY(${25*(1-p)}%)`;const line=$('.k-line>span',sock);if(line)line.style.transform='translateY(0)'}
  chooseFocus();if(particles)particles.draw(now,dt);lastY=y;requestAnimationFrame(frame)
}
setTheme();
requestAnimationFrame(frame);

addEventListener('load',()=>setTimeout(()=>{const l=$('#loader');if(l)l.classList.add('kernellum-loaded')},180),{once:true});
setTimeout(()=>{const l=$('#loader');if(l)l.classList.add('kernellum-loaded')},1200);
})();