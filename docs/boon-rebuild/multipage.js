(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const base='/kernellum/boon-rebuild/';
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

const header=`<header id="header"><div class="nav-bar">
<a class="logo" href="${base}" aria-label="Kernellum"><span class="wordmark">KERNELLUM</span></a>
<button class="expand-btn" type="button" aria-expanded="false"><p>MENU</p><b class="dot9" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></b></button>
<div class="expand-menu" aria-hidden="true"><nav><ul>
<li><a href="${base}">Home</a></li>
<li><a href="${base}what-we-do/" ${route==='what-we-do'?'aria-current="page"':''}>What We Do</a></li>
<li><a href="${base}who-we-are/" ${route==='who-we-are'?'aria-current="page"':''}>Who We Are</a></li>
<li><a href="${base}careers/" ${route==='careers'?'aria-current="page"':''}>Careers</a></li>
<li><a href="${base}contact/" ${route==='contact'?'aria-current="page"':''}>Contact</a></li>
</ul></nav></div></div></header>`;

const footer=`<footer><div class="footer-shell">
<nav class="footer-nav">
<a href="${base}what-we-do/"><span>What We Do</span><span>↗</span></a>
<a href="${base}who-we-are/"><span>Who We Are</span><span>↗</span></a>
<a href="${base}contact/"><span>Contact</span><span>↗</span></a>
<a href="${base}careers/"><span>Careers</span><span>↗</span></a>
</nav>
<a class="footer-brand" href="${base}">KERNELLUM</a>
<nav class="footer-legal"><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">GitHub</a><span>Research-first</span><span>Public evidence</span></nav>
</div></footer>`;

const arrow=(label,href)=>`<a class="arrow-link" href="${href}">${label}</a>`;
const hero=`<section class="hero"><div class="hero-grid">
<div class="eyebrow reveal">${data.heroLabel}</div>
<h1 class="reveal">${data.hero}</h1>
<p class="hero-copy reveal">${data.intro}</p>
<div class="hero-cta reveal">${arrow(route==='contact'?'Open GitHub':'Explore the work', route==='contact'?'https://github.com/sushxnthd/kernellum':'#content')}</div>
</div></section>`;

function blockCards(){
 if(!data.blocks)return '';
 return `<section class="section" id="content"><div>
 <div class="section-label reveal">The Kernellum Difference</div>
 <h2 class="display wide reveal">${data.blocks[0][1]}</h2>
 <div class="cards">${data.blocks.map((b,i)=>`<article class="card reveal"><span class="card-index">0${i+1}</span><h3>${b[0]}</h3><p>${b[1]}</p></article>`).join('')}</div>
 </div></section>`;
}
function features(){
 if(!data.features)return '';
 return `<section class="section compact"><div>
 <div class="section-label reveal">${route==='careers'?'Where the work lives':'The Loop'}</div>
 <h2 class="display reveal">${route==='careers'?'Work across disciplines.':'From workload to routed evidence.'}</h2>
 <div class="feature-list">${data.features.map(f=>`<div class="feature reveal"><span class="n">${f[0]}</span><h3>${f[1]}</h3><p>${f[2]}</p></div>`).join('')}</div>
 </div></section>`;
}
function who(){
 return `<section class="section" id="content"><div class="split">
 <div class="left"><div class="section-label reveal">Our Vision</div><h2 class="display reveal">Design with physical reality in the loop.</h2></div>
 <div class="right body-copy reveal"><p class="lede">${data.vision}</p><div class="rule"></div><p>Kernellum's current evidence ladder runs from analytical architecture search through functional RTL, synthesis, final-route timing, and closed-loop acquisition. Physical-board latency, power, and energy remain future validation stages rather than assumed results.</p></div>
 </div></section>
 <section class="section compact"><div><div class="section-label reveal">Our Values</div><h2 class="display wide reveal">Stay true to the evidence and the mission.</h2>
 <div class="values">${data.values.map(v=>`<article class="value reveal"><span class="num">${v[0]}</span><div><h3>${v[1]}</h3><p>${v[2]}</p></div></article>`).join('')}</div></div></section>`;
}
function contact(){
 return `<section class="section" id="content"><div>
 <div class="section-label reveal">Contact</div><h2 class="display reveal">Research should be inspectable.</h2>
 <div class="contact-grid">
 <div class="contact-info reveal">
  <div class="contact-row"><small>Repository</small><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">github.com/sushxnthd/kernellum ↗</a></div>
  <div class="contact-row"><small>Technical discussion</small><a href="https://github.com/sushxnthd/kernellum/issues" target="_blank" rel="noopener">GitHub Issues ↗</a></div>
  <div class="contact-row"><small>Current stage</small><span>K2 board-ready; physical measurements not yet claimed</span></div>
 </div>
 <form class="contact-form form-stack reveal" id="contact-form">
  <div class="field"><input name="name" placeholder="Name *" required><input name="org" placeholder="Organisation"></div>
  <div class="field"><input name="email" type="email" placeholder="Email *" required><select name="reason"><option>Reason for contact</option><option>Research collaboration</option><option>Reproduction question</option><option>Technical feedback</option><option>Other</option></select></div>
  <div class="field full"><textarea name="message" placeholder="Message *" required></textarea></div>
  <button class="submit" type="submit">Continue via GitHub</button>
 </form>
 </div></div></section>`;
}
const closing=`<section class="closing"><div><div class="section-label reveal">Kernellum</div><h2 class="display reveal">${data.closing}</h2><div class="reveal">${arrow(route==='careers'?'View Repository':'Read the Research','https://github.com/sushxnthd/kernellum')}</div></div></section>`;

let content='';
if(route==='who-we-are')content=who();
else if(route==='contact')content=contact();
else content=blockCards()+features();

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
 for(const p of pts){if(!p.a)continue;const y=((p.y-sy)%h+h)%h;const d=Math.hypot(p.x-mx,y-my),hot=Math.pow(Math.max(0,1-d/(Math.min(w,h)*.75)),1.8);const pulse=.45+.55*Math.sin(now*.0016+p.r*6.28);const rad=.4+2.6*pulse*p.a;const rr=Math.round(62+(227-62)*hot),gg=Math.round(58+(70-58)*hot),bb=Math.round(44+(8-44)*hot);ctx.fillStyle='rgba('+rr+','+gg+','+bb+','+(0.18+p.a*.62)+')';ctx.beginPath();ctx.arc(p.x,y,rad,0,Math.PI*2);ctx.fill()}
 requestAnimationFrame(draw)
}
requestAnimationFrame(draw);
})();