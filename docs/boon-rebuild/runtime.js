(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const out=t=>1-Math.pow(1-t,3);
const mobile=matchMedia('(max-width:58.749rem)');
const reduce=matchMedia('(prefers-reduced-motion:reduce)');

/* ---------- source-geometry header reconstruction ---------- */
const header=$('#header');
if(header){
  const dot9='<div class="dot-icon" aria-hidden="true" style="--v812fb6d2:var(--clr-content-100);--v1c2e9760:1">'+
    Array.from({length:9},(_,i)=>'<div class="dot" style="grid-column-start:'+((i%3)+1)+';grid-row-start:'+(((i/3)|0)+1)+'"></div>').join('')+
    '</div>';
  header.innerHTML=`
    <div class="nav-bar">
      <a class="logo" href="#home" aria-label="Kernellum">
        <svg viewBox="0 0 142 24" role="img" aria-label="Kernellum">
          <text x="0" y="18" fill="currentColor" font-family="Suisse Int'l, Arial, sans-serif" font-size="18" font-weight="600" letter-spacing=".8">KERNELLUM</text>
        </svg>
      </a>
      <button class="expand-btn" type="button" aria-expanded="false">
        <p>MENU</p>${dot9}
      </button>
      <div class="expand-menu" aria-hidden="true">
        <nav aria-label="Primary">
          <ul>
            <li><a href="#home">Home</a></li>
            <li><a href="#difference">What We Do</a></li>
            <li><a href="#research">Research</a></li>
            <li><a href="#insights">Insights</a></li>
            <li><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener noreferrer">GitHub ↗</a></li>
          </ul>
        </nav>
      </div>
    </div>`;
  const btn=$('.expand-btn',header),label=$('p',btn),panel=$('.expand-menu',header);
  const scramble=text=>{
    if(reduce.matches){label.textContent=text;return}
    const chars='░▒▓■□',start=performance.now(),dur=300;
    const f=now=>{const p=clamp((now-start)/dur),fixed=Math.floor(text.length*p);label.textContent=[...text].map((c,i)=>i<fixed?c:chars[(Math.random()*chars.length)|0]).join('');if(p<1)requestAnimationFrame(f);else label.textContent=text};requestAnimationFrame(f)
  };
  const setOpen=open=>{
    header.classList.toggle('k-expanded',open);
    btn.setAttribute('aria-expanded',String(open));
    panel.setAttribute('aria-hidden',String(!open));
    panel.style.maxHeight=open?(panel.scrollHeight+32)+'px':'0px';
    scramble(open?'CLOSE':'MENU');
  };
  btn.addEventListener('click',()=>setOpen(!header.classList.contains('k-expanded')));
  $$('.expand-menu a',header).forEach(a=>a.addEventListener('click',()=>setOpen(false)));
  document.addEventListener('pointerdown',e=>{if(header.classList.contains('k-expanded')&&!header.contains(e.target))setOpen(false)});
  addEventListener('resize',()=>{if(header.classList.contains('k-expanded'))panel.style.maxHeight=(panel.scrollHeight+32)+'px'},{passive:true});
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
const cards=cardGrid?$$('ul.cards>li.card',cardGrid):[];
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
 'https://cdn.sanity.io/images/cktal3h7/production/0cd1b737f485d70df84c6fc1f95e3585f7e5db6d-1232x928.png?w=1920&q=80&auto=format',
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
    this.canvas=canvas;
    this.ctx=canvas.getContext('2d',{alpha:true});
    this.shape='none';this.target='none';this.theme='dark';
    this.start=0;this.duration=1500;this.morphing=false;
    this.mx=innerWidth/2;this.my=innerHeight/2;this.tx=this.mx;this.ty=this.my;
    this.image=null;this.imageReady=false;
    addEventListener('pointermove',e=>{this.tx=e.clientX;this.ty=e.clientY},{passive:true});
    addEventListener('resize',()=>this.resize(),{passive:true});
    this.loadImage();this.resize();this.set('none',true);
    window.__kernellumParticles=this;
  }
  loadImage(){
    const im=new Image();
    im.src='/kernellum/boon-rebuild/assets/particle-image.png?v=2';
    im.onload=()=>{
      this.image=im;this.imageReady=true;
      if(this.target==='image'){
        this.from.set(this.cur);
        this.build('image',this.to);
        this.start=performance.now();
        this.morphing=!reduce.matches;
      }
    };
  }
  resize(){
    const dpr=Math.min(devicePixelRatio||1,1.5);
    this.w=innerWidth;this.h=innerHeight;
    this.canvas.width=Math.floor(this.w*dpr);this.canvas.height=Math.floor(this.h*dpr);
    this.canvas.style.width=this.w+'px';this.canvas.style.height=this.h+'px';
    this.ctx.setTransform(dpr,0,0,dpr,0,0);
    this.gap=13.5;
    this.cols=Math.ceil(this.w/this.gap)+1;
    this.rows=Math.ceil(this.h/this.gap)+1;
    this.n=this.cols*this.rows;
    this.x0=(this.w-(this.cols-1)*this.gap)/2;
    this.y0=(this.h-(this.rows-1)*this.gap)/2;
    this.cur=new Float32Array(this.n*3);
    this.from=new Float32Array(this.n*3);
    this.to=new Float32Array(this.n*3);
    this.rand=new Float32Array(this.n);
    for(let i=0;i<this.n;i++)this.rand[i]=Math.random();
    this.build(this.shape,this.cur);this.to.set(this.cur);
  }
  write(a,i,x,y,s){const j=i*3;a[j]=x;a[j+1]=y;a[j+2]=s}
  cell(i){
    const c=i%this.cols,r=(i/this.cols)|0;
    return [this.x0+c*this.gap,this.y0+r*this.gap,c,r];
  }
  heavy(i){
    const q=this.rand[(i*7+3)%this.n];
    return .10+Math.pow(q,2.8)*.98;
  }
  capsule(px,py,ax,ay,bx,by,r){
    const abx=bx-ax,aby=by-ay,apx=px-ax,apy=py-ay;
    const t=clamp((apx*abx+apy*aby)/(abx*abx+aby*aby||1));
    const dx=px-(ax+abx*t),dy=py-(ay+aby*t);
    return clamp(1-Math.hypot(dx,dy)/r);
  }
  build(shape,a){
    if(shape==='none'||shape==='grid'){
      for(let i=0;i<this.n;i++){
        const [x,y]=this.cell(i);
        let sc=0;
        if(shape==='grid'&&this.rand[i]>.34)sc=this.heavy(i);
        this.write(a,i,x,y,sc);
      }
      return;
    }

    if(shape==='image'){
      let data=null;
      if(this.imageReady&&this.image){
        const oc=document.createElement('canvas');
        oc.width=this.cols;oc.height=this.rows;
        const ox=oc.getContext('2d',{willReadFrequently:true});
        const sc=Math.max(this.cols/this.image.width,this.rows/this.image.height);
        const dw=this.image.width*sc,dh=this.image.height*sc;
        ox.clearRect(0,0,this.cols,this.rows);
        ox.drawImage(this.image,(this.cols-dw)/2,(this.rows-dh)/2,dw,dh);
        data=ox.getImageData(0,0,this.cols,this.rows).data;
      }
      for(let i=0;i<this.n;i++){
        const [x,y,c,r]=this.cell(i);
        const bg=this.rand[i]>.52 ? (.035+Math.pow(this.rand[(i*11+5)%this.n],3)*.20) : 0;
        let sc=bg;
        if(data){
          const p=(r*this.cols+c)*4;
          const lum=(.2126*data[p]+.7152*data[p+1]+.0722*data[p+2])/255;
          const alpha=data[p+3]/255;
          const m=clamp((lum-.035)/.68)*alpha;
          if(m>.035)sc=Math.max(sc,.12+Math.pow(m,.82)*1.04);
        }else{
          // Fallback silhouette derived from the live point-cloud composition.
          const nx=(x-this.w*.5)/this.w,ny=(y-this.h*.5)/this.h;
          const torso=clamp(1-(nx*nx/(.115*.115)+(ny+.08)*(ny+.08)/(.30*.30)));
          const head=clamp(1-(nx-.035)*(nx-.035)/(.09*.09)-(ny+.31)*(ny+.31)/(.13*.13));
          const left=this.capsule(nx,ny,-.02,-.03,-.36,.18,.075);
          const right=this.capsule(nx,ny,.05,-.15,.36,.02,.075);
          const lower=this.capsule(nx,ny,.015,.13,-.05,.43,.09);
          const m=Math.max(torso,head,left,right,lower);
          if(m>.02)sc=Math.max(sc,.12+m*.98);
        }
        this.write(a,i,x,y,sc);
      }
      return;
    }

    if(shape==='rings-horizontal'){
      const rings=9,cx=this.w/2,cy=this.h*.50;
      const outerX=Math.min(this.w*.414,596),outerY=Math.min(this.h*.255,255);
      let idx=0;
      for(let ring=0;ring<rings;ring++){
        const rx=outerX*(1-ring*.068),ry=outerY*(1-ring*.075);
        const circ=2*Math.PI*Math.sqrt((rx*rx+ry*ry)/2);
        const pts=Math.max(50,Math.floor(circ/13.5));
        for(let k=0;k<pts&&idx<this.n;k++,idx++){
          const t=k/pts*Math.PI*2;
          const jitter=(this.rand[idx]-.5)*2.2;
          this.write(a,idx,cx+Math.cos(t)*(rx+jitter),cy+Math.sin(t)*(ry+jitter),this.heavy(idx)*1.02);
        }
      }
      for(;idx<this.n;idx++)this.write(a,idx,cx,cy,0);
      return;
    }

    if(shape==='rings-vertical'){
      const rings=8,cx=this.w/2,cy=this.h*.50;
      const outerX=Math.min(this.w*.225,325),outerY=Math.min(this.h*.355,355);
      let idx=0;
      for(let ring=0;ring<rings;ring++){
        const rx=outerX*(1-ring*.10),ry=outerY*(1-ring*.095);
        const circ=2*Math.PI*Math.sqrt((rx*rx+ry*ry)/2);
        const pts=Math.max(48,Math.floor(circ/13.5));
        for(let k=0;k<pts&&idx<this.n;k++,idx++){
          const t=k/pts*Math.PI*2;
          const jitter=(this.rand[idx]-.5)*2;
          this.write(a,idx,cx+Math.cos(t)*(rx+jitter),cy+Math.sin(t)*(ry+jitter),this.heavy(idx)*1.05);
        }
      }
      for(;idx<this.n;idx++)this.write(a,idx,cx,cy,0);
      return;
    }
  }
  set(shape,instant=false){
    if(shape===this.target&&!instant)return;
    this.target=shape;this.from.set(this.cur);this.build(shape,this.to);
    this.start=performance.now();this.morphing=!instant&&!reduce.matches;
    if(instant||reduce.matches){this.cur.set(this.to);this.shape=shape;this.morphing=false}
  }
  draw(now,dt){
    const c=this.ctx;c.clearRect(0,0,this.w,this.h);
    this.mx=lerp(this.mx,this.tx,1-Math.exp(-6*dt));
    this.my=lerp(this.my,this.ty,1-Math.exp(-6*dt));
    const p=this.morphing?clamp((now-this.start)/this.duration):1,e=ease(p),arc=Math.sin(p*Math.PI);
    const base=[62,58,44],hi=[227,70,8];
    for(let i=0;i<this.n;i++){
      const j=i*3,r=this.rand[i],r2=this.rand[(i*23+9)%this.n];
      let x=this.morphing?lerp(this.from[j],this.to[j],e):this.cur[j];
      let y=this.morphing?lerp(this.from[j+1],this.to[j+1],e):this.cur[j+1];
      let s=this.morphing?lerp(this.from[j+2],this.to[j+2],e):this.cur[j+2];
      if(this.morphing){x+=(r-.5)*230*arc;y+=(r2-.5)*230*arc}
      if(s<.018)continue;
      const d=Math.hypot(x-this.mx,y-this.my);
      const h=Math.pow(clamp(1-d/(Math.min(this.w,this.h)*.72)),1.7);
      const rr=Math.round(lerp(base[0],hi[0],h)),gg=Math.round(lerp(base[1],hi[1],h)),bb=Math.round(lerp(base[2],hi[2],h));
      const pulse=.5+.5*Math.sin(now*.0018+r*6.283);
      const rad=(.55+3.9*pulse)*Math.pow(Math.min(s,1.2),1.12)*(.55+.72*r);
      c.fillStyle='rgba('+rr+','+gg+','+bb+','+Math.min(.94,.28+.62*Math.min(s,1))+')';
      c.beginPath();c.arc(x,y,Math.max(.45,rad),0,Math.PI*2);c.fill();
    }
    if(this.morphing&&p>=1){this.cur.set(this.to);this.shape=this.target;this.morphing=false}
  }
}

const bgCanvas=$('.three-canvas');
if(bgCanvas){
  const stage=bgCanvas.closest('.three-canvas-container')?.parentElement;
  if(stage){stage.style.zIndex='0';stage.style.pointerEvents='none'}
  const wrapper=$('.page-wrapper');
  if(wrapper){wrapper.style.position='relative';wrapper.style.zIndex='1'}
}
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
  if(header)header.classList.add('visible')
  const hp=clamp(smoothY/vh);
  if(hero&&!reduce.matches){
    if(heroWrappers[1])heroWrappers[1].style.transform=`translateY(${25*hp}%)`;if(heroImgs[1])heroImgs[1].style.transform=`translateY(${-12.5*hp}%)`;
    if(heroWrappers[2])heroWrappers[2].style.transform=`translateX(${-25*hp}%)`;if(heroImgs[2])heroImgs[2].style.transform=`translateX(${12.5*hp}%)`;
    if(heroWrappers[3])heroWrappers[3].style.transform=`translateX(${25*hp}%)`;if(heroImgs[3])heroImgs[3].style.transform=`translateX(${-12.5*hp}%)`;
    if(heroImgs[0])heroImgs[0].style.transform=`scale(${1+.15*hp})`;
    if(!mobile.matches){const ls=$$('.title>.k-line',hero);if(ls[0])ls[0].style.transform=`translateX(${-50*hp}vw)`;if(ls[1])ls[1].style.transform=`translateX(${50*hp}vw)`;if(heroSubtitle)heroSubtitle.style.transform=`translateX(${-5*hp}vw)`;if(heroScroll)heroScroll.style.transform=`translateX(${5*hp}vw)`}
    if(heroSubtitle)heroSubtitle.style.opacity=String(hp>.64?0:clamp(1-hp/.56));if(heroScroll)heroScroll.style.opacity=String(hp>.64?0:clamp(1-hp/.56));
  }
  centered.forEach(sec=>{const r=sec.getBoundingClientRect(),p=clamp(-r.top/(vh*.34));(sec._kLines||[]).forEach(l=>l.style.transform=`translateY(${101*(1-p)}%)`);if(sec===roloSec)runRolodex(p>=.96)});
  if(cardGrid&&!reduce.matches){const r=cardGrid.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height*.5));cards.forEach((c,i)=>{const lp=clamp((p-i*.06)/.7),e=out(lp);c.style.opacity=String(e);c.style.transform=`translateY(${(100+i*50)*(1-e)}px)`})}
  if(sock&&!reduce.matches){const r=sock.getBoundingClientRect(),p=clamp((vh-r.top)/(vh+r.height)),wrap=$$('.images>.image-wrapper',sock);if(sockImgs[0])sockImgs[0].style.transform=`scale(${1.15-.15*p})`;if(wrap[1])wrap[1].style.transform=`translateX(${-10*(1-p)}%)`;if(sockImgs[1])sockImgs[1].style.transform=`translateX(${5*(1-p)}%)`;if(wrap[2])wrap[2].style.transform=`translateY(${50*(1-p)}%)`;if(sockImgs[2])sockImgs[2].style.transform=`translateY(${-25*(1-p)}%)`;if(wrap[3])wrap[3].style.transform=`translateY(${-50*(1-p)}%)`;if(sockImgs[3])sockImgs[3].style.transform=`translateY(${25*(1-p)}%)`;const line=$('.k-line>span',sock);if(line)line.style.transform='translateY(0)'}
  chooseFocus();if(particles)particles.draw(now,dt);lastY=y;requestAnimationFrame(frame)
}
setTheme();
requestAnimationFrame(frame);

addEventListener('load',()=>setTimeout(()=>{const l=$('#loader');if(l)l.classList.add('kernellum-loaded')},180),{once:true});
setTimeout(()=>{const l=$('#loader');if(l)l.classList.add('kernellum-loaded')},1200);
})();