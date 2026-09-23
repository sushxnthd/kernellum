(() => {
'use strict';
const BASE='/kernellum/';
const raw=location.pathname.replace(BASE,'').replace(/^\/+|\/+$/g,'');
const route=raw||'home';
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const pages={
home:{title:'Kernellum | Architecture search grounded in physical evidence',kicker:'Architecture Search / Physical Design',hero:'Search the Machine',intro:'From workload to architecture, RTL, and routed evidence. A design loop that learns what physical implementation changes.'},
'what-we-do':{title:'What We Do | Kernellum',kicker:'What We Do',hero:'Design for the Workload',intro:'Kernellum is building a loop from AI workload to accelerator architecture, verified RTL, and routed evidence. Physical results inform the next candidate.'},
'who-we-are':{title:'Who We Are | Kernellum',kicker:'Who We Are',hero:'Build for Physical Reality',intro:'Kernellum is a research-stage effort to automate the path from AI workload to implementable accelerator design. Every claim is tied to the evidence that supports it.'},
careers:{title:'Careers | Kernellum',kicker:'Careers / Contribute',hero:'Build the Next Design Loop',intro:'The work crosses architecture search, RTL, verification, FPGA tooling, and physical design. Explore the open research and the problems still to solve.'},
contact:{title:'Contact | Kernellum',kicker:'Contact',hero:'Shape the Next Experiment',intro:'Investors, research collaborators, and hardware builders can start with the public evidence, then open a focused discussion around what should be tested next.'}
};
const data=pages[route]||pages.home;
document.title=data.title;
const nav=[['Home',BASE,'home'],['What We Do',BASE+'what-we-do/','what-we-do'],['Who We Are',BASE+'who-we-are/','who-we-are'],['Careers',BASE+'careers/','careers'],['Contact',BASE+'contact/','contact']];
const pip='<span class="pips" aria-hidden="true"></span>';
const menuDots='<span class="menu-icon" aria-hidden="true">'+('<i></i>'.repeat(12))+'</span>';
const header='<header class="site-header" aria-label="Site header">'+
'<a class="brand glass-card" href="'+BASE+'" aria-label="Kernellum home">KERNELLUM</a>'+
'<button class="menu-button" type="button" aria-expanded="false" aria-controls="site-menu"><span>Menu</span>'+menuDots+'</button>'+
'<div class="menu-panel glass-card" id="site-menu"><nav aria-label="Main navigation">'+
nav.map(function(n){return '<a href="'+n[1]+'" '+(route===n[2]?'aria-current="page"':'')+'>'+pip+'<span>'+n[0]+'</span>'+pip+'</a>';}).join('')+
'</nav></div></header>';
const imageSet={
home:['study-die.webp','study-wafer.webp','study-researcher.webp','study-wafer.webp'],
'what-we-do':['study-researcher.webp','study-die.webp','study-wafer.webp','architecture-die.svg'],
'who-we-are':['study-researcher.webp','study-researcher.webp','study-researcher.webp','route-topology.svg'],
careers:['study-researcher.webp','study-wafer.webp','study-die.webp','study-researcher.webp']
};
function heroVisual(){
if(route==='contact')return '<div class="hero-visual" aria-hidden="true"><div class="contact-field"></div><div class="contact-grid-lines"></div><div class="contact-orbit"></div><div class="contact-scan"></div></div>';
const imgs=imageSet[route]||imageSet.home;
return '<div class="hero-visual" aria-hidden="true">'+imgs.map(function(img,i){return '<div class="hero-slice slice-'+(i+1)+' '+(i===3?'blur-clone':'')+'"><img src="'+BASE+'assets/'+img+'" alt=""></div>';}).join('')+'</div>';
}
function hero(){
const cls=route==='what-we-do'?'what':route;
return '<section class="hero '+cls+'">'+heroVisual()+'<div class="hero-copy"><div class="hero-center" data-reveal><div class="hero-kicker">'+data.kicker+'</div><h1>'+data.hero+'</h1></div><div class="hero-bottom" data-reveal data-reveal-delay="1"><p class="hero-subtitle">'+data.intro+'</p><div class="scroll-cue">Scroll for more</div></div></div></section>';
}
function button(label,href,secondary){
return '<a class="button '+(secondary?'secondary':'')+'" href="'+href+'" '+(href.indexOf('http')===0?'target="_blank" rel="noopener noreferrer"':'')+'><span>'+label+'</span><span aria-hidden="true">↗</span></a>';
}
function metrics(){
return '<div class="metric-strip"><div class="metrics" data-reveal>'+
'<div class="metric"><strong>9 / 9</strong><span>Held-out K1 architectures routed successfully in the reported campaign.</span></div>'+
'<div class="metric"><strong>0.944</strong><span>Mean Spearman correlation for final-routed ordering in the K1 evaluation.</span></div>'+
'<div class="metric"><strong>0.583%</strong><span>Gap between the selected K1 architecture and the final-routed oracle.</span></div>'+
'</div><p class="metric-note">Routed implementation evidence, not board-measured latency, power, or energy. See the public experiment ledger and K1 reports for scope and methods.</p></div>';
}
function home(){
return '<section class="section intro-statement green-wash"><div class="section-inner centered">'+
'<div class="eyebrow" data-reveal>Closed-loop architecture search</div>'+
'<h2 class="display" data-reveal data-reveal-delay="1">Search continuously, route the candidates, and let <mark>physical evidence</mark> reshape what gets built next.</h2>'+
'<p class="support" data-reveal data-reveal-delay="2">Kernellum connects architecture search, verifiable RTL, and implementation feedback instead of treating physical design as an afterthought.</p>'+
'</div></section>'+metrics()+
'<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>The Kernellum Difference</div><h2 class="display small" data-reveal>From fast search to routed truth.</h2><div class="cards">'+
'<article class="card" data-reveal><span class="card-index">01</span><h3>Physical feedback</h3><p>K1 uses final-routed timing as part of the search loop, so implementation effects can change what the system chooses next.</p></article>'+
'<article class="card" data-reveal data-reveal-delay="1"><span class="card-index">02</span><h3>Closed-loop search</h3><p>The active campaign reached 6.475% final-route-Fmax surrogate MAPE and found 16.74 ms best latency versus 19.44 ms for the random baseline.</p></article>'+
'<article class="card" data-reveal data-reveal-delay="2"><span class="card-index">03</span><h3>Implementation-aware scaling</h3><p>Across 96 routed designs, the corrected interconnect model reached 0.3039 ns held-out tax MAE with 0.8921 correlation.</p></article>'+
'</div></div></section>'+
'<section class="large-quote"><h2 data-reveal>A breakthrough is only real <em>when its evidence survives</em> physical implementation.</h2></section>'+
'<section class="visual-band"><div class="band-image"><img src="'+BASE+'assets/route-topology.svg" alt="Routed interconnect study"></div><div class="band-fragments"></div><div class="band-copy"><h2 class="display" data-reveal>Follow the evidence.</h2><div data-reveal data-reveal-delay="1"><p>Plans, scripts, frozen result files, routed reports, and the experiment ledger live alongside the code.</p><div class="cta-row">'+button('What We Do',BASE+'what-we-do/',false)+button('Public Repository','https://github.com/sushxnthd/kernellum',true)+'</div></div></div></section>';
}
function whatWeDo(){
const f=[
['01','Model the workload','Translate workload shapes and constraints into architecture-level objectives and predicted latency.'],
['02','Search architecture space','Explore parameterized accelerator candidates instead of hand-picking a single design.'],
['03','Generate and verify RTL','Produce synthesizable implementations and test functional behavior before physical evaluation.'],
['04','Synthesize and route','Use synthesis and place-and-route to obtain implementation evidence on the target family.'],
['05','Learn from physical feedback','Update the timing surrogate from routed observations and acquire the next candidates.'],
['06','Preserve scientific boundaries','Keep analytical, routed, and future board-measured claims separate.']
];
return '<section class="section green-wash"><div class="section-inner split"><div><div class="eyebrow" data-reveal>The design gap</div><h2 class="display small" data-reveal data-reveal-delay="1">Fast estimates can change once a design is routed.</h2></div><div class="split-copy" data-reveal data-reveal-delay="2"><p>AI workloads evolve faster than fixed accelerator designs. Kernellum treats implementation effects as part of the search problem instead of hiding them after architecture selection.</p><div class="hairline"></div><p class="muted">The current research wedge evaluates tiled INT8 GEMM candidates against Transformer workloads and uses routed timing on ECP5 to guide the next search step.</p></div></div></section>'+
'<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>The Loop</div><h2 class="display small" data-reveal>From workload to routed evidence.</h2><div class="feature-list">'+
f.map(function(x,i){return '<div class="feature" data-reveal data-reveal-delay="'+Math.min(i,3)+'"><span class="n">'+x[0]+'</span><h3>'+x[1]+'</h3><p>'+x[2]+'</p></div>';}).join('')+
'</div></div></section>'+metrics()+
'<section class="large-quote"><h2 data-reveal>Architecture search matters only if its advantages <em>survive implementation.</em></h2></section>'+
'<section class="visual-band"><div class="band-image"><img src="'+BASE+'assets/study-die.webp" alt="Semiconductor die study"></div><div class="band-fragments"></div><div class="band-copy"><h2 class="display" data-reveal>Route. Measure. Search again.</h2><div data-reveal data-reveal-delay="1"><p>The next validation stage moves toward physical-board measurements without promoting modeled or routed estimates into claims they do not support.</p><div class="cta-row">'+button('Read K1 Report','https://github.com/sushxnthd/kernellum/blob/main/docs/K1_CLOSED_LOOP_REPORT.md',false)+button('Experiment Ledger','https://github.com/sushxnthd/kernellum/blob/main/docs/EXPERIMENT_LEDGER.md',true)+'</div></div></div></section>';
}
function whoWeAre(){
const v=[
['01','Scientific discipline','Claims are separated by evidence level: analytical estimates, synthesis, routed timing, and future board measurements.'],
['02','Physical feedback','Implementation effects are treated as part of the search problem, not noise to hide after architecture selection.'],
['03','Reproducibility','Experiments, scripts, frozen result files, and reports live alongside the code in the public repository.'],
['04','Iteration','Negative results and target-specific effects are used to improve the model and the next experiment.']
];
return '<section class="section green-wash"><div class="section-inner split"><div><div class="eyebrow" data-reveal>Our direction</div><h2 class="display small" data-reveal data-reveal-delay="1">Design with physical reality in the loop.</h2></div><div class="split-copy" data-reveal data-reveal-delay="2"><p>The long-term direction is an AI-native co-design system that moves from model and deployment constraints to workload-specific accelerator architecture, RTL, verification, FPGA implementation, and eventually licensable silicon IP.</p><div class="hairline"></div><p class="muted">The current evidence ladder runs from analytical architecture search through functional RTL, synthesis, final-route timing, and closed-loop acquisition.</p></div></div></section>'+
'<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>Research principles</div><h2 class="display small" data-reveal>Evidence before narrative.</h2><div class="values">'+
v.map(function(x,i){return '<article class="value-row" data-reveal data-reveal-delay="'+Math.min(i,3)+'"><span class="num">'+x[0]+'</span><h3>'+x[1]+'</h3><p>'+x[2]+'</p></article>';}).join('')+
'</div></div></section>'+
'<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>The evidence ladder</div><h2 class="display small" data-reveal>Know what each result means.</h2><div class="evidence-ladder">'+
'<div class="evidence-step" data-reveal><span>01</span><strong>Analytical</strong><p>Architecture-level estimates and search objectives.</p></div>'+
'<div class="evidence-step" data-reveal data-reveal-delay="1"><span>02</span><strong>RTL</strong><p>Functional implementation and regression evidence.</p></div>'+
'<div class="evidence-step" data-reveal data-reveal-delay="2"><span>03</span><strong>Routed</strong><p>Target-aware synthesis, placement, routing, and timing.</p></div>'+
'<div class="evidence-step" data-reveal data-reveal-delay="3"><span>04</span><strong>Physical</strong><p>Board measurements are the next validation stage, not an assumed result.</p></div>'+
'</div></div></section>'+
'<section class="visual-band"><div class="band-image"><img src="'+BASE+'assets/study-researcher.webp" alt="Researcher and semiconductor study"></div><div class="band-fragments"></div><div class="band-copy"><h2 class="display" data-reveal>Research, architecture, RTL, and physical design in one loop.</h2><div class="cta-row" data-reveal data-reveal-delay="1">'+button('View Repository','https://github.com/sushxnthd/kernellum',false)+button('What We Do',BASE+'what-we-do/',true)+'</div></div></section>';
}
function careers(){
const a=[
['01','Architecture + ML','Search, surrogate modelling, workload characterization, and acquisition strategies.'],
['02','RTL + verification','Parameterized datapaths, controllers, functional simulation, and regression testing.'],
['03','Physical design','Synthesis, place-and-route, timing analysis, constraints, and target-aware modelling.'],
['04','Research engineering','Experiment automation, data integrity, reproducibility, reports, and visualization.']
];
return '<section class="section green-wash"><div class="section-inner"><div class="eyebrow" data-reveal>Open research</div><h2 class="display small" data-reveal>Work across the whole stack.</h2><div class="cards">'+
'<article class="card" data-reveal><span class="card-index">01</span><h3>Implementation matters</h3><p>The interesting problems sit between machine learning, computer architecture, EDA, and experimental science.</p></article>'+
'<article class="card" data-reveal data-reveal-delay="1"><span class="card-index">02</span><h3>High ownership</h3><p>Contributions can cut across modelling, RTL, tooling, experiments, documentation, and reproducibility.</p></article>'+
'<article class="card" data-reveal data-reveal-delay="2"><span class="card-index">03</span><h3>Evidence over demos</h3><p>The standard is whether a result survives independent checks and increasingly physical validation.</p></article>'+
'</div></div></section>'+
'<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>Where the work lives</div><h2 class="display small" data-reveal>Work across disciplines.</h2><div class="feature-list">'+
a.map(function(x,i){return '<div class="feature" data-reveal data-reveal-delay="'+Math.min(i,3)+'"><span class="n">'+x[0]+'</span><h3>'+x[1]+'</h3><p>'+x[2]+'</p></div>';}).join('')+
'</div></div></section>'+
'<section class="large-quote"><h2 data-reveal>The hardware does not respect <em>org charts.</em></h2></section>'+
'<section class="visual-band"><div class="band-image"><img src="'+BASE+'assets/study-wafer.webp" alt="Wafer study"></div><div class="band-fragments"></div><div class="band-copy"><h2 class="display" data-reveal>Interested in contributing?</h2><div data-reveal data-reveal-delay="1"><p>Start with the repository, reproduce a result, open an issue, or propose a focused experiment that makes the evidence stronger.</p><div class="cta-row">'+button('View Repository','https://github.com/sushxnthd/kernellum',false)+button('Open Issues','https://github.com/sushxnthd/kernellum/issues',true)+'</div></div></div></section>';
}
function contact(){
return '<section class="section green-wash"><div class="section-inner split"><div><div class="eyebrow" data-reveal>Start with the evidence</div><h2 class="display small" data-reveal data-reveal-delay="1">Research should be inspectable.</h2></div><div class="split-copy" data-reveal data-reveal-delay="2"><p>The public repository is the fastest route into the work. Reproduce a result, challenge a claim, propose an experiment, or open a focused discussion around collaboration.</p><div class="hairline"></div><p class="muted">Kernellum is currently at a routed, board-ready research stage. Board-measured latency, power, and energy are not yet claimed.</p></div></div></section>'+
'<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>Contact routes</div><h2 class="display small" data-reveal>Pick the shortest path.</h2><div class="contact-list">'+
'<div class="contact-item" data-reveal><small>Repository</small><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener noreferrer">github.com/sushxnthd/kernellum</a><span class="arrow">↗</span></div>'+
'<div class="contact-item" data-reveal data-reveal-delay="1"><small>Technical discussion</small><a href="https://github.com/sushxnthd/kernellum/issues" target="_blank" rel="noopener noreferrer">GitHub Issues</a><span class="arrow">↗</span></div>'+
'<div class="contact-item" data-reveal data-reveal-delay="2"><small>Experiment ledger</small><a href="https://github.com/sushxnthd/kernellum/blob/main/docs/EXPERIMENT_LEDGER.md" target="_blank" rel="noopener noreferrer">Public evidence record</a><span class="arrow">↗</span></div>'+
'<div class="contact-item" data-reveal data-reveal-delay="3"><small>Current stage</small><span>K2 board-ready, physical measurements next</span><span></span></div>'+
'</div></div></section>'+
'<section class="large-quote"><h2 data-reveal>Make the next claim <em>harder to break.</em></h2></section>';
}
function footer(){
return '<footer class="site-footer"><div class="footer-inner"><div class="footer-top">'+
'<h2 data-reveal>Build what <span>survives</span> the route.</h2>'+
'<div class="footer-nav" data-reveal data-reveal-delay="1"><div class="footer-col"><span>Explore</span><a href="'+BASE+'what-we-do/">What We Do</a><a href="'+BASE+'who-we-are/">Who We Are</a><a href="'+BASE+'careers/">Careers</a><a href="'+BASE+'contact/">Contact</a></div>'+
'<div class="footer-col"><span>Evidence</span><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener noreferrer">Repository ↗</a><a href="https://github.com/sushxnthd/kernellum/blob/main/docs/EXPERIMENT_LEDGER.md" target="_blank" rel="noopener noreferrer">Experiment Ledger ↗</a><a href="https://github.com/sushxnthd/kernellum/blob/main/docs/K2_BOARD_READY_REPORT.md" target="_blank" rel="noopener noreferrer">Current Stage ↗</a></div></div></div>'+
'<div class="footer-wordmark">KERNELLUM</div><div class="footer-meta"><span>Research / Architecture / Physical Design</span><span>Public evidence, current to 2026</span></div></div></footer>';
}
const builders={home:home,'what-we-do':whatWeDo,'who-we-are':whoWeAre,careers:careers,contact:contact};
document.body.innerHTML='<div class="noise" aria-hidden="true"></div>'+header+'<main>'+hero()+(builders[route]||home)()+'</main>'+footer();

const menuButton=$('.menu-button'),panel=$('.menu-panel');
if(menuButton&&panel){
menuButton.addEventListener('click',function(){const open=!panel.classList.contains('open');panel.classList.toggle('open',open);menuButton.setAttribute('aria-expanded',String(open));document.body.classList.toggle('menu-open',open);});
panel.addEventListener('click',function(e){if(e.target.closest('a')){panel.classList.remove('open');menuButton.setAttribute('aria-expanded','false');document.body.classList.remove('menu-open');}});
addEventListener('keydown',function(e){if(e.key==='Escape'){panel.classList.remove('open');menuButton.setAttribute('aria-expanded','false');document.body.classList.remove('menu-open');}});
}
const reveal=$$('[data-reveal]');
if('IntersectionObserver' in window){
const observer=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){entry.target.classList.add('is-visible');observer.unobserve(entry.target);}});},{threshold:.12,rootMargin:'0px 0px -6% 0px'});
reveal.forEach(function(el){observer.observe(el);});
}else reveal.forEach(function(el){el.classList.add('is-visible');});

const visual=$('.hero-visual');
if(visual&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
let tx=0,ty=0,x=0,y=0;
addEventListener('pointermove',function(e){tx=(e.clientX/innerWidth-.5)*14;ty=(e.clientY/innerHeight-.5)*10;},{passive:true});
(function loop(){x+=(tx-x)*.045;y+=(ty-y)*.045;visual.style.setProperty('--px',x.toFixed(2));visual.style.setProperty('--py',y.toFixed(2));const sy=scrollY;$$('.hero-slice',visual).forEach(function(el,i){const shift=Math.min(innerHeight,sy)*(i+1)*.018;el.style.transform='translate3d(0,'+shift.toFixed(2)+'px,0)';});requestAnimationFrame(loop);})();
}
let lastY=scrollY,ticking=false;
const headerEl=$('.site-header');
addEventListener('scroll',function(){if(ticking)return;ticking=true;requestAnimationFrame(function(){const y=scrollY;if(headerEl){const hide=y>lastY&&y>180&&!(panel&&panel.classList.contains('open'));headerEl.style.transform=hide?'translate(-50%,-150%)':'translate(-50%,0)';headerEl.style.transition='transform .55s cubic-bezier(.5,.1,0,1)';}lastY=y;ticking=false;});},{passive:true});
})();