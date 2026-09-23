(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const base='/kernellum/';
const route=location.pathname.replace(base,'').replace(/\/+$/,'')||'home';
const pages={
'what-we-do':{
 title:'What We Do • Kernellum',
 heroLabel:'What We Do',
 hero:'A New Hardware Design Paradigm',
 intro:'Kernellum explores AI-native hardware/software co-design: choosing accelerator architectures for real workloads, generating implementations, and feeding physical-design results back into the search.',
 blocks:[
  ['The Kernellum Difference','Architectures are not judged only by analytical estimates. The research loop is built to test whether predicted advantages survive synthesis and place-and-route.'],
  ['Closed-loop physical feedback','K1 routes candidate architectures on ECP5, learns from final-routed timing, and uses that evidence to guide the next acquisition rather than treating physical design as a final afterthought.'],
  ['Workload-specific search','The current system evaluates tiled INT8 GEMM architectures against Transformer workloads and deployment constraints, with explicit controls and frozen validation sets.']
 ],
 features:[
  ['01','Model the workload','Translate workload shapes and constraints into architecture-level objectives and predicted latency.'],
  ['02','Search architecture space','Explore parameterized accelerator candidates instead of hand-picking a single design.'],
  ['03','Generate and verify RTL','Produce synthesizable implementations and test functional behavior before physical evaluation.'],
  ['04','Synthesize and route','Use Yosys and nextpnr to obtain final-routed implementation evidence on the target family.'],
  ['05','Learn from physical feedback','Update the timing surrogate from routed observations and acquire the next candidates.'],
  ['06','Preserve scientific boundaries','Keep analytical, routed, and future board-measured claims separate rather than collapsing them into one headline metric.']
 ],
 closing:'Design the architecture. Route the evidence. Close the loop.'
},
'who-we-are':{
 title:'Who We Are • Kernellum',
 heroLabel:'Who We Are',
 hero:'Built for architectures that survive reality.',
 intro:'Kernellum is a research-first effort around one question: can automated systems design AI accelerators whose predicted advantages persist through physical implementation?',
 vision:'The long-term direction is an AI-native co-design system that moves from model and deployment constraints to workload-specific accelerator architecture, RTL, verification, FPGA implementation, and eventually licensable silicon IP.',
 values:[
  ['01','Scientific discipline','Claims are separated by evidence level: analytical estimates, synthesis, routed timing, and future board measurements.'],
  ['02','Physical feedback','Implementation effects are treated as part of the search problem, not noise to hide after architecture selection.'],
  ['03','Reproducibility','Experiments, scripts, frozen result files, and reports live alongside the code in the public repository.'],
  ['04','Iteration','Negative results and target-specific effects are used to improve the model and the next experiment.']
 ],
 closing:'Research, architecture, RTL, and physical design in one loop.'
},
'careers':{
 title:'Careers • Kernellum',
 heroLabel:'Careers',
 hero:'Build systems that shape real hardware outcomes.',
 intro:'Kernellum is currently research-first. The work spans architecture search, hardware generation, verification, FPGA tooling, physical-design modelling, and rigorous experimental evaluation.',
 blocks:[
  ['Research that touches implementation','The interesting problems sit between machine learning, computer architecture, EDA, and experimental science.'],
  ['Small systems, high ownership','Contributions can cut across modelling, RTL, tooling, experiments, documentation, and reproducibility rather than living inside narrow silos.'],
  ['Evidence over demos','The standard is not whether a concept looks convincing in a notebook. It is whether the result survives independent checks and increasingly physical validation.']
 ],
 features:[
  ['01','Architecture + ML','Search, surrogate modelling, workload characterization, acquisition strategies.'],
  ['02','RTL + verification','Parameterized datapaths, controllers, functional simulation, regression testing.'],
  ['03','Physical design','Synthesis, place-and-route, timing analysis, constraints, target-aware modelling.'],
  ['04','Research engineering','Experiment automation, data integrity, reproducibility, reports, visualization.']
 ],
 closing:'Interested in contributing? Start with the repository.'
},
'contact':{
 title:'Contact • Kernellum',
 heroLabel:'Contact',
 hero:'Get in touch with Kernellum.',
 intro:'For research discussion, collaboration, reproducibility questions, or technical feedback, use the public repository so the conversation can stay connected to the work.',
 closing:'The fastest route into the work is through the evidence.'
}};
const data=pages[route]||pages['what-we-do'];
document.title=data.title;

const arrowSvg='<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M3 13 13 3M6 3h7v7" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter"/></svg>';
const arrow=(label,href)=>'<a class="arrow-link" href="'+href+'"><span>'+label+'</span><span class="btn-arrow-stack" aria-hidden="true"><span class="arr one">'+arrowSvg+'</span><span class="arr two">'+arrowSvg+'</span></span></a>';
const navPips=()=>'<span class="k-nav-pips" aria-hidden="true"><i></i><i></i></span>';
const menuDots=()=>'<b class="dotgrid" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></b>';
const footerArrowDots=()=>'<span class="footer-dot-icon arrow" aria-hidden="true">'+[[1,3],[2,3],[3,3],[4,3],[5,3],[6,3],[4,1],[4,5],[5,2],[5,4]].map(([c,r])=>'<i style="grid-column:'+c+';grid-row:'+r+'"></i>').join('')+'</span>';
const footerPips=()=>'<span class="footer-dot-icon pips" aria-hidden="true"><i></i><i></i></span>';
const footerCorner=()=>'<span class="footer-corner" aria-hidden="true">'+Array.from({length:9},()=>'<i></i>').join('')+'</span>';

const header=`<header id="header" class="visible"><div class="nav-bar">
<a class="logo" href="${base}" aria-label="Kernellum"><span class="wordmark">KERNELLUM</span></a>
<button class="expand-btn" type="button" aria-expanded="false"><p>MENU</p>${menuDots()}</button>
<div class="expand-menu" aria-hidden="true"><nav aria-label="Main Navigation"><ul>
<li><a href="${base}">${navPips()}<span>Home</span>${navPips()}</a></li>
<li><a href="${base}what-we-do/" ${route==='what-we-do'?'aria-current="page"':''}>${navPips()}<span>What We Do</span>${navPips()}</a></li>
<li><a href="${base}who-we-are/" ${route==='who-we-are'?'aria-current="page"':''}>${navPips()}<span>Who We Are</span>${navPips()}</a></li>
<li><a href="${base}careers/" ${route==='careers'?'aria-current="page"':''}>${navPips()}<span>Careers</span>${navPips()}</a></li>
<li><a href="${base}contact/" ${route==='contact'?'aria-current="page"':''}>${navPips()}<span>Contact</span>${navPips()}</a></li>
</ul></nav></div></div></header>`;

const footer=`<footer class="k-footer">
<div class="footer-dot-wrapper">${footerCorner()}${footerCorner()}${footerCorner()}${footerCorner()}</div>
<div class="k-footer-container">
<nav class="k-footer-primary" aria-label="Primary Footer Nav">
<a href="${base}what-we-do/"><span>What We Do</span>${footerArrowDots()}</a>
<a href="${base}who-we-are/"><span>Who We Are</span>${footerArrowDots()}</a>
<a href="${base}contact/"><span>Research</span>${footerArrowDots()}</a>
<a href="${base}careers/"><span>Careers</span>${footerArrowDots()}</a>
</nav>
<div class="k-footer-cta">${arrow('Contact',base+'contact/')}</div>
<nav class="k-footer-secondary" aria-label="Secondary Footer Nav">
<a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">${footerPips()}<span>GitHub</span>${footerPips()}</a>
<a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">${footerPips()}<span>Repository</span>${footerPips()}</a>
<a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">${footerPips()}<span>Public Evidence</span>${footerPips()}</a>
</nav>
<a class="k-footer-brand" href="${base}">KERNELLUM</a>
</div></footer>`;

const heroType=route==='what-we-do'?'left':'center';
const hero=`<section class="route-page-header ${heroType}" data-particles="none">
<div class="route-images" aria-hidden="true">
  <figure class="route-image"><div class="route-viz viz-base"></div></figure>
  <figure class="route-image"><div class="route-viz viz-a"></div></figure>
  <figure class="route-image"><div class="route-viz viz-b"></div></figure>
</div>
<div class="route-content">
  <div class="route-title-wrap"><div class="route-label">${data.heroLabel}</div><h1 class="route-title">${data.hero}</h1></div>
  <div class="route-bottom"><p class="route-subtitle">${data.intro}</p><div class="route-cta">${arrow(route==='contact'?'Open GitHub':'Explore the work',route==='contact'?'https://github.com/sushxnthd/kernellum':'#content')}</div></div>
</div>
</section>`;

function blockCards(){
 if(!data.blocks)return '';
 return `<section class="section card-section" id="content" data-particles="rings-horizontal"><div>
 <div class="section-label">The Kernellum Difference</div>
 <h2 class="display wide">${data.blocks[0][1]}</h2>
 <div class="cards">${data.blocks.map((b,i)=>`<article class="card"><span class="card-index">0${i+1}</span><h3>${b[0]}</h3><p>${b[1]}</p></article>`).join('')}</div>
 </div></section>`;
}
function features(){
 if(!data.features)return '';
 return `<section class="section compact feature-section" data-particles="grid"><div>
 <div class="section-label">${route==='careers'?'Where the work lives':'The Loop'}</div>
 <h2 class="display">${route==='careers'?'Work across disciplines.':'From workload to routed evidence.'}</h2>
 <div class="feature-list">${data.features.map(f=>`<div class="feature"><span class="n">${f[0]}</span><h3>${f[1]}</h3><p>${f[2]}</p></div>`).join('')}</div>
 </div></section>`;
}
function who(){
 return `<section class="section intro-section" id="content" data-particles="grid"><div class="split">
 <div class="left"><div class="section-label">Our Vision</div><h2 class="display">Design with physical reality in the loop.</h2></div>
 <div class="right body-copy"><p class="lede">${data.vision}</p><div class="rule"></div><p>Kernellum's current evidence ladder runs from analytical architecture search through functional RTL, synthesis, final-route timing, and closed-loop acquisition. Physical-board latency, power, and energy remain future validation stages rather than assumed results.</p></div>
 </div></section>
 <section class="section compact values-section" data-particles="rings-horizontal"><div><div class="section-label">Our Values</div><h2 class="display wide">Stay true to the evidence and the mission.</h2>
 <div class="values">${data.values.map(v=>`<article class="value"><span class="num">${v[0]}</span><div><h3>${v[1]}</h3><p>${v[2]}</p></div></article>`).join('')}</div></div></section>`;
}
function contact(){
 return `<section class="section contact-section" id="content" data-particles="image"><div>
 <div class="section-label">Contact</div><h2 class="display">Research should be inspectable.</h2>
 <div class="contact-grid">
 <div class="contact-info">
  <div class="contact-row"><small>Repository</small><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">github.com/sushxnthd/kernellum <span class="k-arrow-icon" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><path d="M3 13 13 3M6 3h7v7" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter"/></svg></span></a></div>
  <div class="contact-row"><small>Technical discussion</small><a href="https://github.com/sushxnthd/kernellum/issues" target="_blank" rel="noopener">GitHub Issues <span class="k-arrow-icon" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><path d="M3 13 13 3M6 3h7v7" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter"/></svg></span></a></div>
  <div class="contact-row"><small>Current stage</small><span>K2 board-ready; physical measurements not yet claimed</span></div>
 </div>
 <form class="contact-form form-stack" id="contact-form">
  <div class="field"><input name="name" placeholder="Name *" required><input name="org" placeholder="Organisation"></div>
  <div class="field"><input name="email" type="email" placeholder="Email *" required><select name="reason"><option>Reason for contact</option><option>Research collaboration</option><option>Reproduction question</option><option>Technical feedback</option><option>Other</option></select></div>
  <div class="field full"><textarea name="message" placeholder="Message *" required></textarea></div>
  <button class="submit" type="submit">Continue via GitHub</button>
 </form>
 </div></div></section>`;
}
const statementMap={
  'what-we-do':'Architecture search matters only if its advantages survive implementation.',
  'careers':'The hardware does not respect org charts.'
};
function largeStatement(){
  const text=statementMap[route];if(!text)return '';
  return `<section class="large-statement" data-particles="grid"><h2>${text}</h2></section>`;
}
const closing=`<section class="closing" data-particles="rings-vertical"><div><div class="section-label">Kernellum</div><h2 class="display">${data.closing}</h2><div>${arrow(route==='careers'?'View Repository':'Read the Research','https://github.com/sushxnthd/kernellum')}</div></div></section>`;

let content='';
if(route==='who-we-are')content=who();
else if(route==='contact')content=contact();
else content=largeStatement()+blockCards()+features();

document.body.innerHTML=`<div id="particle-stage"><canvas></canvas></div><div class="site">${header}<main>${hero}${content}${closing}</main>${footer}</div>`;

const btn=$('.expand-btn'),menu=$('.expand-menu'),label=$('.expand-btn p');
function menuOpen(open){btn.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-hidden',String(!open));menu.style.maxHeight=open?(menu.scrollHeight+32)+'px':'0px';label.textContent=open?'CLOSE':'MENU'}
btn.addEventListener('click',()=>menuOpen(btn.getAttribute('aria-expanded')!=='true'));
document.addEventListener('pointerdown',e=>{if(!$('#header').contains(e.target))menuOpen(false)});

if(route==='contact'){
 const form=$('#contact-form');
 form.addEventListener('submit',e=>{
  e.preventDefault();
  const fd=new FormData(form);
  const title='Kernellum contact: '+(fd.get('reason')||'Research discussion');
  const body=['Name: '+fd.get('name'),'Organisation: '+(fd.get('org')||''),'Email: '+fd.get('email'),'','Message:',''+fd.get('message')].join('\n');
  location.href='https://github.com/sushxnthd/kernellum/issues/new?title='+encodeURIComponent(title)+'&body='+encodeURIComponent(body);
 });
}

const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')}),{threshold:.12});
$$('.reveal').forEach(el=>io.observe(el));

const cv=$('#particle-stage canvas'),ctx=cv.getContext('2d');
let w=0,h=0,dpr=1,pts=[],mx=innerWidth/2,my=innerHeight/2,tx=mx,ty=my;
function resize(){
 dpr=Math.min(devicePixelRatio||1,1.5);w=innerWidth;h=innerHeight;cv.width=w*dpr;cv.height=h*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);
 pts=[];const gap=w<700?18:14;const cols=Math.ceil(w/gap)+1,rows=Math.ceil(h/gap)+1;
 const x0=(w-(cols-1)*gap)/2,y0=(h-(rows-1)*gap)/2;
 for(let y=0;y<rows;y++)for(let x=0;x<cols;x++){const r=Math.random();pts.push({x:x0+x*gap,y:y0+y*gap,a:r>.48?(.08+Math.pow(r,3)*.6):0,r:Math.random()})}
}
addEventListener('resize',resize,{passive:true});addEventListener('pointermove',e=>{tx=e.clientX;ty=e.clientY},{passive:true});resize();
let last=performance.now();
function draw(now){
 const dt=Math.min(.05,(now-last)/1000);last=now;mx+=(tx-mx)*(1-Math.exp(-5*dt));my+=(ty-my)*(1-Math.exp(-5*dt));ctx.clearRect(0,0,w,h);
 const sy=scrollY*.035;
 for(const p of pts){if(!p.a)continue;const y=((p.y-sy)%h+h)%h;const d=Math.hypot(p.x-mx,y-my),hot=Math.pow(Math.max(0,1-d/(Math.min(w,h)*.75)),1.8);const pulse=.45+.55*Math.sin(now*.0016+p.r*6.28);const rad=.4+2.6*pulse*p.a;const rr=Math.round(36+(185-36)*hot),gg=Math.round(107+(243-107)*hot),bb=Math.round(73+(93-73)*hot);ctx.fillStyle='rgba('+rr+','+gg+','+bb+','+(0.18+p.a*.62)+')';ctx.beginPath();ctx.arc(p.x,y,rad,0,Math.PI*2);ctx.fill()}
 requestAnimationFrame(draw)
}
requestAnimationFrame(draw);

/* === KERNELLUM SOURCE-MATCH MOTION === */
const boonReduce=matchMedia('(prefers-reduced-motion: reduce)');
const boonClamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const boonOutCubic=t=>1-Math.pow(1-t,3);

function boonSplitHeading(el){
  if(!el||el.dataset.boonSplit||el.children.length)return [];
  el.dataset.boonSplit='chars';
  const words=el.textContent.trim().split(/\s+/);
  el.textContent='';
  const chars=[];
  words.forEach((word,wi)=>{
    const ws=document.createElement('span');
    ws.style.display='inline-block';
    ws.style.whiteSpace='nowrap';
    [...word].forEach(ch=>{
      const c=document.createElement('span');
      c.className='boon-char';
      c.textContent=ch;
      ws.appendChild(c); chars.push(c);
    });
    el.appendChild(ws);
    if(wi<words.length-1)el.appendChild(document.createTextNode(' '));
  });
  return chars;
}
function boonSplitLines(el){
  if(!el||el.dataset.boonSplit||el.children.length)return [];
  el.dataset.boonSplit='lines';
  const words=el.textContent.trim().split(/\s+/);
  el.textContent='';
  const probes=[];
  words.forEach((word,wi)=>{
    const w=document.createElement('span');
    w.textContent=word;
    w.style.whiteSpace='nowrap';
    el.appendChild(w); probes.push(w);
    if(wi<words.length-1)el.appendChild(document.createTextNode(' '));
  });
  const rows=[]; let lastTop=null,current=[];
  probes.forEach(w=>{
    const top=Math.round(w.offsetTop);
    if(lastTop===null||Math.abs(top-lastTop)<=1){current.push(w.textContent)}
    else{rows.push(current);current=[w.textContent]}
    lastTop=top;
  });
  if(current.length)rows.push(current);
  el.textContent='';
  const lines=rows.map(wordsInLine=>{
    const clip=document.createElement('span');clip.className='boon-line-clip';
    const line=document.createElement('span');line.className='boon-line';line.textContent=wordsInLine.join(' ');
    clip.appendChild(line);el.appendChild(clip);return line;
  });
  return lines;
}
function boonRevealScope(scope){
  if(!scope||scope.dataset.boonReveal)return;
  scope.dataset.boonReveal='1';
  const headings=$$('h1,h2,h3,h4,h5,h6',scope);
  const paragraphs=$$('p',scope).filter(p=>!p.closest('form'));
  const labels=$$('.section-label,.eyebrow,.card-index,.n,.num',scope);
  const chars=headings.flatMap(boonSplitHeading);
  const lines=paragraphs.flatMap(boonSplitLines);
  if(boonReduce.matches)return;
  chars.forEach(c=>{c.style.opacity='0'});
  lines.forEach(l=>{l.style.opacity='0';l.style.transform='translateY(50%)'});
  labels.forEach(l=>{l.style.opacity='0';l.style.transform='translateY(20px)'});
  const io=new IntersectionObserver(entries=>{
    entries.forEach(entry=>{
      if(!entry.isIntersecting)return;
      io.disconnect();
      let lineDelay=0;
      lines.forEach(line=>{
        line.animate([{opacity:0,transform:'translateY(50%)'},{opacity:1,transform:'translateY(0%)'}],
          {duration:850,delay:(lineDelay+=25),easing:'cubic-bezier(.165,.84,.44,1)',fill:'forwards'});
      });
      chars.forEach((char,i)=>char.animate([{opacity:0},{opacity:1}],
        {duration:650,delay:i*10,easing:'cubic-bezier(.25,.46,.45,.94)',fill:'forwards'}));
      labels.forEach((label,i)=>label.animate([{opacity:0,transform:'translateY(20px)'},{opacity:1,transform:'translateY(0px)'}],
        {duration:850,delay:50+i*25,easing:'cubic-bezier(.645,.045,.355,1)',fill:'forwards'}));
    });
  },{root:null,rootMargin:'0px 0px -20% 0px',threshold:0});
  io.observe(scope);
}

function boonPageEnter(){
  if(boonReduce.matches)return;
  const main=$('main');
  if(!main)return;
  main.classList.add('boon-page-enter');
  const anim=main.animate([
    {clipPath:'inset(50% 25% 50% 25%)',transform:'scale(.5)',filter:'blur(8px)'},
    {clipPath:'inset(0% 0% 0% 0%)',transform:'scale(1)',filter:'blur(0px)'}
  ],{duration:1000,easing:'cubic-bezier(.25,.46,.45,.94)',fill:'both'});
  anim.finished.finally(()=>{main.style.clipPath='';main.style.transform='';main.style.filter=''});
}
boonPageEnter();
$$('.hero,.section,.closing').forEach(boonRevealScope);

const boonCards=$$('.cards>.card');
if(boonCards.length&&!boonReduce.matches){
  boonCards.forEach((card,i)=>{card.style.transform=`translateY(${100+i*50}px)`});
  const updateBoonCards=()=>{
    const wrap=$('.cards'); if(!wrap)return;
    const r=wrap.getBoundingClientRect();
    const p=boonClamp((innerHeight-r.top)/(innerHeight*.65));
    boonCards.forEach((card,i)=>{
      const delayed=boonClamp((p-i*(150/800)*.35)/(1-i*.035));
      const e=boonOutCubic(delayed);
      card.style.transform=`translateY(${(100+i*50)*(1-e)}px)`;
    });
  };
  addEventListener('scroll',updateBoonCards,{passive:true});addEventListener('resize',updateBoonCards,{passive:true});updateBoonCards();
}

/* Lenis-equivalent source settings: root, syncTouch=true, touchMultiplier=1.5, default lerp≈0.1 */
if(!boonReduce.matches){
  let boonTarget=scrollY,boonCurrent=scrollY,boonDriving=false,boonTouchY=0;
  const maxScroll=()=>Math.max(0,document.documentElement.scrollHeight-innerHeight);
  addEventListener('wheel',e=>{
    if(e.ctrlKey||e.metaKey)return;
    const target=e.target;
    if(target instanceof Element&&target.closest('input,textarea,select,[contenteditable="true"]'))return;
    e.preventDefault();boonDriving=true;boonTarget=boonClamp(boonTarget+e.deltaY,0,maxScroll());
  },{passive:false});
  addEventListener('touchstart',e=>{if(e.touches[0])boonTouchY=e.touches[0].clientY},{passive:true});
  addEventListener('touchmove',e=>{
    if(!e.touches[0])return;
    const y=e.touches[0].clientY,dy=(boonTouchY-y)*1.5;boonTouchY=y;
    boonDriving=true;boonTarget=boonClamp(boonTarget+dy,0,maxScroll());
  },{passive:true});
  addEventListener('keydown',e=>{
    const amount=e.key==='PageDown'?innerHeight*.9:e.key==='PageUp'?-innerHeight*.9:e.key==='ArrowDown'?40:e.key==='ArrowUp'?-40:0;
    if(amount){e.preventDefault();boonDriving=true;boonTarget=boonClamp(boonTarget+amount,0,maxScroll())}
  });
  const boonLenisRaf=()=>{
    if(boonDriving){
      boonCurrent+=(boonTarget-boonCurrent)*.1;
      if(Math.abs(boonTarget-boonCurrent)<.2){boonCurrent=boonTarget;boonDriving=false}
      scrollTo(0,boonCurrent);
    }else{boonCurrent=scrollY;boonTarget=scrollY}
    requestAnimationFrame(boonLenisRaf);
  };
  requestAnimationFrame(boonLenisRaf);
  $$('a[href^="#"]').forEach(a=>a.addEventListener('click',e=>{
    const id=a.getAttribute('href');const target=id&&$(id);if(!target)return;e.preventDefault();
    boonTarget=boonClamp(scrollY+target.getBoundingClientRect().top,0,maxScroll());boonCurrent=scrollY;boonDriving=true;
  }));
}

})();