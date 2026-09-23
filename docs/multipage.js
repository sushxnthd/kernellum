(() => {
'use strict';
const BASE='/kernellum/';
const raw=location.pathname.replace(BASE,'').replace(/^\/+|\/+$/g,'');
const route=raw||'home';
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const pages={
home:{title:'Kernellum | Architecture search grounded in physical evidence',hero:'Search the<br>Machine',intro:'From workload to architecture, RTL, and routed evidence. A design loop that learns what physical implementation changes.'},
'what-we-do':{title:'What We Do | Kernellum',hero:'A New Design<br>Paradigm',intro:'We combine workload modelling, architecture search, verifiable RTL, and routed physical evidence to understand which accelerator choices survive implementation.'},
'who-we-are':{title:'Who We Are | Kernellum',hero:'Built for Systems That<br>Shape What Comes Next.',intro:'Architecture, ML, RTL, and physical design united by one mission: turn fast search into implementation evidence that survives increasingly physical validation.'},
careers:{title:'Careers | Kernellum',hero:'Build Systems That<br>Shape Real-World<br>Outcomes.',intro:'Work across architecture search, verification, EDA, and experimental systems. The standard is not a convincing demo. It is evidence that survives the route.'},
contact:{title:'Contact | Kernellum'}
};
const data=pages[route]||pages.home;
document.title=data.title;
document.body.className='page-'+route;

const nav=[['Home',BASE,'home'],['What We Do',BASE+'what-we-do/','what-we-do'],['Who We Are',BASE+'who-we-are/','who-we-are'],['Contact',BASE+'contact/','contact'],['Careers',BASE+'careers/','careers']];
const pip='<span class="pips" aria-hidden="true"></span>';
const dots='<span class="menu-icon" aria-hidden="true">'+('<i></i>'.repeat(16))+'</span>';
const header='<header class="site-header">'+
'<a class="brand" href="'+BASE+'" aria-label="Kernellum home">KERNELLUM</a>'+
'<button class="menu-button" type="button" aria-expanded="false" aria-controls="site-menu"><span>Menu</span>'+dots+'</button>'+
'<div class="menu-panel" id="site-menu"><nav aria-label="Main navigation">'+nav.map(function(n){return '<a href="'+n[1]+'" '+(route===n[2]?'aria-current="page"':'')+'>'+pip+'<span>'+n[0]+'</span>'+pip+'</a>';}).join('')+'</nav></div>'+
'</header>';

const imageSet={
home:['study-researcher.webp','study-wafer.webp','study-die.webp','study-wafer.webp'],
'what-we-do':['study-researcher.webp','study-die.webp','study-wafer.webp','route-topology.svg'],
'who-we-are':['study-researcher.webp','study-wafer.webp','study-researcher.webp','study-die.webp'],
careers:['study-researcher.webp','study-die.webp','study-wafer.webp','study-researcher.webp']
};
function heroVisual(){
 const imgs=imageSet[route]||imageSet.home;
 return '<div class="hero-visual" aria-hidden="true">'+imgs.map(function(img,i){return '<div class="hero-slice slice-'+(i+1)+'"><img src="'+BASE+'assets/'+img+'" alt=""></div>';}).join('')+'</div>';
}
function button(label,href,secondary){
 return '<a class="button '+(secondary?'secondary':'')+'" href="'+href+'" '+(href.indexOf('http')===0?'target="_blank" rel="noopener noreferrer"':'')+'><span>→&nbsp; '+label+'</span></a>';
}
function hero(){
 if(route==='contact')return '';
 const action=route==='home'?'<div class="scroll-cue">Scroll for more</div>':'<div class="hero-action">'+button('Get in touch',BASE+'contact/',false)+'</div>';
 return '<section class="hero '+route+'">'+heroVisual()+
 '<div class="hero-copy"><div class="hero-center" data-reveal><h1>'+data.hero+'</h1></div>'+
 '<div class="hero-bottom" data-reveal data-reveal-delay="1"><p class="hero-subtitle">'+data.intro+'</p>'+action+'</div></div></section>';
}
function metrics(){
 return '<div class="metric-strip"><div class="metrics" data-reveal>'+
 '<div class="metric"><strong>9 / 9</strong><span>Held-out K1 architectures routed successfully in the reported campaign.</span></div>'+
 '<div class="metric"><strong>0.944</strong><span>Mean Spearman correlation for final-routed ordering in the K1 evaluation.</span></div>'+
 '<div class="metric"><strong>0.583%</strong><span>Gap between the selected K1 architecture and the final-routed oracle.</span></div>'+
 '</div><p class="metric-note">Routed implementation evidence, not board-measured latency, power, or energy. Scope and methods are documented in the public experiment ledger and K1 reports.</p></div>';
}
function sock(title,copy,href,label,img){
 return '<section class="visual-band"><div class="band-image"><img src="'+BASE+'assets/'+img+'" alt=""></div><div class="band-fragments"></div>'+
 '<div class="band-copy"><h2 class="display" data-reveal>'+title+'</h2><div data-reveal data-reveal-delay="1"><p>'+copy+'</p><div class="cta-row">'+button(label,href,false)+'</div></div></div></section>';
}
function home(){
 return '<section class="story" data-story><div class="story-inner"><h2 class="story-title">Search continuously, route the candidates, and let physical evidence reshape what gets built next.</h2><div class="story-cards">'+
 '<article class="story-card" data-story-card="0"><p>K1 routed 9/9 held-out architectures; final-routed ordering reached mean Spearman ρ 0.944.</p></article>'+
 '<article class="story-card" data-story-card="1"><p>The selected K1 architecture finished within 0.583% of the final-routed oracle.</p></article>'+
 '</div></div></section>'+
 '<section class="rolodex" data-rolodex><div class="rolodex-inner"><div><h2>Kernellum turns workload and physical implementation evidence into<br><span class="rolodex-word">architecture candidates</span></h2>'+button('What We Do',BASE+'what-we-do/',false)+'</div></div></section>'+
 '<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>The Kernellum Difference</div><div class="cards">'+
 '<article class="card" data-reveal><span class="card-index">01</span><h3>Physical feedback, not proxy-only</h3><p>K1 uses final-routed timing as part of the search loop, so implementation effects can change what the system chooses next.</p></article>'+
 '<article class="card" data-reveal data-reveal-delay="1"><span class="card-index">02</span><h3>Closed-loop architecture search</h3><p>The first closed-loop campaign reached 6.475% final-route-Fmax surrogate MAPE; active search found 16.74 ms best latency versus 19.44 ms for the random baseline.</p></article>'+
 '<article class="card" data-reveal data-reveal-delay="2"><span class="card-index">03</span><h3>Implementation-aware scaling</h3><p>Across 96 routed designs, the corrected interconnect model reached 0.3039 ns held-out tax MAE with 0.8921 correlation.</p></article>'+
 '</div></div></section>'+
 '<section class="large-quote"><h2 data-reveal>A breakthrough is only real <em>when its evidence survives</em> physical implementation.</h2></section>'+
 sock('Explore the research behind Kernellum.','Plans, scripts, frozen results, routed reports, and the experiment ledger live alongside the code.','https://github.com/sushxnthd/kernellum','Public Repository','route-topology.svg');
}
function whatWeDo(){
 const primary=[
 ['01','Physical feedback, not proxy-only','Architecture choices can change after placement and routing. Routed timing is treated as evidence, not an afterthought.'],
 ['02','Agentic search over architecture space','Parameterized candidates are explored against workload-specific objectives instead of hand-picking a single design.'],
 ['03','Real implementation feedback','Verified RTL, synthesis, placement, routing, and timing feed the next acquisition step.']
 ];
 const loop=[
 ['01','Map workload drivers','Translate tensor shapes, reuse, bandwidth, and deployment constraints into architecture-level objectives.'],
 ['02','Anticipate implementation response','Predict which candidate choices will survive synthesis and routing well enough to justify physical evaluation.'],
 ['03','Track routed effects','Measure target-aware timing and preserve the distinction between modeled, routed, and future board-measured results.'],
 ['04','Adapt at tempo','Use new routed observations to update the surrogate and choose the next candidates.']
 ];
 return '<section class="statement-block"><h2 data-reveal>Accelerator design is decided by how architecture choices <mark>survive physical implementation.</mark></h2></section>'+
 '<section class="statement-block"><h2 data-reveal>Fast search is useful. <mark>Routed evidence</mark> is what closes the loop.</h2></section>'+
 '<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>The Kernellum Difference</div><div class="cards">'+
 primary.map(function(x,i){return '<article class="card" data-reveal data-reveal-delay="'+i+'"><span class="card-index">'+x[0]+'</span><h3>'+x[1]+'</h3><p>'+x[2]+'</p></article>';}).join('')+
 '</div></div></section>'+
 '<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>What sets Kernellum apart</div><h2 class="display small" data-reveal>Physical evidence changes what the system builds next.</h2><div class="accordion">'+
 ['Closed-loop authority','Operational agility','Models that survive routing','Built for the evidence'].map(function(t,i){return '<div class="acc-item '+(i===0?'open':'')+'"><button class="acc-button" type="button"><h3>'+t+'</h3><span>+</span></button><div class="acc-panel"><p>'+[
 'Search is updated from implementation observations rather than frozen around analytical estimates.',
 'The loop can acquire, route, and learn from new candidates without rebuilding the methodology around each one.',
 'Surrogate models are judged against held-out routed timing and target-specific implementation behavior.',
 'Scientific boundaries are explicit: analytical, routed, and future physical measurements are never collapsed into one claim.'
 ][i]+'</p></div></div>';}).join('')+
 '</div></div></section>'+
 '<section class="statement-block"><h2 data-reveal>Most design systems stop at the estimate, leaving the physical consequences <mark>for later.</mark></h2></section>'+
 '<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>The Effect</div><h2 class="display small" data-reveal>Plan the first architecture. Own the routed outcome.</h2><div class="feature-list">'+
 loop.map(function(x,i){return '<div class="feature" data-reveal data-reveal-delay="'+Math.min(i,3)+'"><span class="n">'+x[0]+'</span><h3>'+x[1]+'</h3><p>'+x[2]+'</p></div>';}).join('')+
 '</div></div></section>'+metrics()+
 sock('Meet the research behind the loop.','Architecture search, RTL, verification, and physical design are treated as one experimental system.',BASE+'who-we-are/','Who We Are','study-researcher.webp');
}
function whoWeAre(){
 const vals=[
 ['01','Craftsmanship','Reproducibility and implementation details matter down to the last constraint, script, and frozen result.'],
 ['02','Curiosity','Hard questions are followed into routing, target effects, negative results, and the places where simple proxies fail.'],
 ['03','Evidence centricity','Every public claim is tied to the evidence level that actually supports it.'],
 ['04','Collaboration','Architecture, ML, RTL, verification, and physical design are treated as one loop, not separate silos.']
 ];
 return '<section class="section"><div class="section-inner split"><div><div class="eyebrow" data-reveal>Our Vision</div><h2 class="display small" data-reveal>Reason continuously as the design becomes physical.</h2></div><div class="split-copy" data-reveal data-reveal-delay="1"><p>The next advantage is not simply more architecture candidates or faster estimates. It is the ability to search continuously as implementation evidence arrives.</p><p>Through workload modelling, parameterized RTL, target-aware routing, and closed-loop acquisition, Kernellum is building toward an AI-native hardware/software co-design system.</p><p class="muted">Those who can connect model constraints to implementable architecture faster can define the design space instead of merely reacting to it.</p></div></div></section>'+
 '<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>Our Values</div><h2 class="display small" data-reveal>Stay true to the evidence and the mission.</h2><div class="values">'+
 vals.map(function(v,i){return '<article class="value-row" data-reveal data-reveal-delay="'+Math.min(i,3)+'"><span class="num">'+v[0]+'</span><h3>'+v[1]+'</h3><p>'+v[2]+'</p></article>';}).join('')+
 '</div></div></section>'+
 '<section class="section"><div class="section-inner split"><div><div class="eyebrow" data-reveal>Our Team</div><h2 class="display small" data-reveal>Join the design loop.</h2></div><div class="split-copy" data-reveal data-reveal-delay="1"><p>Kernellum is assembling the research, software, RTL, and physical-design pieces required to move from workload constraints to hardware evidence.</p><p class="muted">The project is currently research-stage and public-first. The best way in is to reproduce a result, challenge a claim, or contribute an experiment.</p><div class="cta-row">'+button('Career Openings',BASE+'careers/',false)+'</div></div></div></section>'+
 sock('Build for physical reality.','The research is designed to get harder to fool as it moves from model to route to measurement.','https://github.com/sushxnthd/kernellum','View Repository','study-wafer.webp');
}
function careers(){
 const f=[
 ['01','Architecture + ML','Search, surrogate modelling, workload characterization, and acquisition strategies.'],
 ['02','RTL + verification','Parameterized datapaths, controllers, functional simulation, and regression testing.'],
 ['03','Physical design','Synthesis, place-and-route, timing analysis, constraints, and target-aware modelling.'],
 ['04','Research engineering','Experiment automation, data integrity, reproducibility, reports, and visualization.']
 ];
 return '<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>Join Kernellum</div><h2 class="display small" data-reveal>Small systems. High ownership.</h2><div class="split" style="margin-top:4rem"><div class="split-copy" data-reveal><p>The interesting problems sit between machine learning, computer architecture, EDA, and experimental science.</p></div><div class="split-copy" data-reveal data-reveal-delay="1"><p>Contributions can cross modelling, RTL, tooling, experiments, documentation, and reproducibility rather than living inside narrow silos.</p></div></div></div></section>'+
 '<section class="section"><div class="section-inner"><div class="eyebrow" data-reveal>Where the work lives</div><div class="feature-list">'+f.map(function(x,i){return '<div class="feature" data-reveal data-reveal-delay="'+Math.min(i,3)+'"><span class="n">'+x[0]+'</span><h3>'+x[1]+'</h3><p>'+x[2]+'</p></div>';}).join('')+'</div></div></section>'+
 '<section class="large-quote"><h2 data-reveal>Evidence over demos. <em>Implementation over illusion.</em></h2></section>'+
 sock('Interested in contributing?','Start with the repository, reproduce a result, open an issue, or propose a focused experiment that makes the evidence stronger.','https://github.com/sushxnthd/kernellum/issues','Open Issues','study-researcher.webp');
}
function contact(){
 return '<section class="contact-shell"><div class="contact-grid"><div class="contact-copy"><h1>Get in touch<br>with Kernellum.</h1><p>Use the form to open a focused discussion around research, reproduction, collaboration, or investment.</p><div class="contact-links">'+
 '<div class="contact-mini"><small>Research</small><a href="https://github.com/sushxnthd/kernellum/issues" target="_blank" rel="noopener noreferrer">GitHub Issues ↗</a></div>'+
 '<div class="contact-mini"><small>Repository</small><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener noreferrer">sushxnthd/kernellum ↗</a></div>'+
 '<div class="contact-mini"><small>Current stage</small><span>Routed / board-ready research</span></div>'+
 '</div></div>'+
 '<form class="contact-form" id="contact-form"><select class="full" name="reason" required><option value="">Reason for Contact</option><option>Research collaboration</option><option>Reproduction question</option><option>Investment / funding</option><option>Contribution</option><option>General</option></select>'+
 '<input name="first" placeholder="First Name *" required><input name="last" placeholder="Last Name *" required>'+
 '<input class="full" name="email" type="email" placeholder="Business Email"><input class="full" name="org" placeholder="Company / Institution">'+
 '<input class="full" name="title" placeholder="Role / Job Title"><textarea class="full" name="message" placeholder="Message *" required></textarea>'+
 '<button class="button submit" type="submit"><span>Submit</span><span>→</span></button></form></div></section>'+
 sock('Explore the public research.','The fastest way to understand Kernellum is through the evidence, not a pitch deck.','https://github.com/sushxnthd/kernellum','View Repository','study-die.webp');
}
function footer(){
 return '<footer class="site-footer"><div class="footer-inner"><div class="footer-top"><h2 data-reveal>Build what <span>survives</span> the route.</h2><div class="footer-nav" data-reveal data-reveal-delay="1">'+
 '<div class="footer-col"><span>Explore</span><a href="'+BASE+'what-we-do/">What We Do</a><a href="'+BASE+'who-we-are/">Who We Are</a><a href="'+BASE+'contact/">Contact</a><a href="'+BASE+'careers/">Careers</a></div>'+
 '<div class="footer-col"><span>Evidence</span><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener noreferrer">GitHub ↗</a><a href="https://github.com/sushxnthd/kernellum/blob/main/docs/EXPERIMENT_LEDGER.md" target="_blank" rel="noopener noreferrer">Experiment Ledger ↗</a><a href="https://github.com/sushxnthd/kernellum/blob/main/docs/K2_BOARD_READY_REPORT.md" target="_blank" rel="noopener noreferrer">Current Stage ↗</a></div>'+
 '</div></div><div class="footer-wordmark">KERNELLUM</div><div class="footer-meta"><span>Architecture / RTL / Physical Design</span><span>Public Research / 2026</span></div></div></footer>';
}
const builders={home:home,'what-we-do':whatWeDo,'who-we-are':whoWeAre,careers:careers,contact:contact};
document.body.innerHTML='<div class="noise" aria-hidden="true"></div>'+header+'<main>'+hero()+(builders[route]||home)()+'</main>'+footer();

const menuButton=$('.menu-button'),panel=$('.menu-panel');
if(menuButton&&panel){
 menuButton.addEventListener('click',function(){const open=!panel.classList.contains('open');panel.classList.toggle('open',open);menuButton.setAttribute('aria-expanded',String(open));document.body.classList.toggle('menu-open',open);});
 panel.addEventListener('click',function(e){if(e.target.closest('a')){panel.classList.remove('open');menuButton.setAttribute('aria-expanded','false');document.body.classList.remove('menu-open');}});
 addEventListener('keydown',function(e){if(e.key==='Escape'){panel.classList.remove('open');menuButton.setAttribute('aria-expanded','false');document.body.classList.remove('menu-open');}});
}

$$('.acc-button').forEach(function(btn){btn.addEventListener('click',function(){const item=btn.closest('.acc-item');item.classList.toggle('open');});});

const form=$('#contact-form');
if(form){
 form.addEventListener('submit',function(e){
   e.preventDefault();
   const fd=new FormData(form);
   const reason=fd.get('reason')||'Contact';
   const name=((fd.get('first')||'')+' '+(fd.get('last')||'')).trim();
   const body=[
     'Reason: '+reason,
     'Name: '+name,
     'Email: '+(fd.get('email')||''),
     'Company / Institution: '+(fd.get('org')||''),
     'Role: '+(fd.get('title')||''),
     '',
     String(fd.get('message')||'')
   ].join('\n');
   location.href='https://github.com/sushxnthd/kernellum/issues/new?title='+encodeURIComponent('[Contact] '+reason)+'&body='+encodeURIComponent(body);
 });
}

const reveal=$$('[data-reveal]');
if('IntersectionObserver' in window){
 const io=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){entry.target.classList.add('is-visible');io.unobserve(entry.target);}});},{threshold:.12,rootMargin:'0px 0px -6% 0px'});
 reveal.forEach(function(el){io.observe(el);});
}else reveal.forEach(function(el){el.classList.add('is-visible');});

const roloWords=['architecture candidates','verifiable RTL','routed timing models','active-learning acquisitions','workload-specific accelerators','reproducible research'];
const story=$('[data-story]'),rolodex=$('[data-rolodex]'),rolo=$('.rolodex-word');
function scrollEffects(){
 if(story){
  const r=story.getBoundingClientRect();
  const max=story.offsetHeight-innerHeight;
  const p=Math.max(0,Math.min(1,-r.top/max));
  $$('[data-story-card]',story).forEach(function(card,i){
   const center=i===0?.42:.70;
   const d=Math.abs(p-center);
   const opacity=Math.max(0,Math.min(1,1-d/.23));
   card.style.opacity=opacity.toFixed(3);
   card.style.transform='translateY('+((1-opacity)*4).toFixed(2)+'rem) scale('+(0.96+opacity*.04).toFixed(3)+')';
  });
 }
 if(rolodex&&rolo){
  const r=rolodex.getBoundingClientRect();
  const max=rolodex.offsetHeight-innerHeight;
  const p=Math.max(0,Math.min(.999,-r.top/max));
  rolo.textContent=roloWords[Math.min(roloWords.length-1,Math.floor(p*roloWords.length))];
 }
}
addEventListener('scroll',scrollEffects,{passive:true});scrollEffects();

const visual=$('.hero-visual');
if(visual&&!matchMedia('(prefers-reduced-motion: reduce)').matches){
 let tx=0,ty=0,x=0,y=0;
 addEventListener('pointermove',function(e){tx=(e.clientX/innerWidth-.5)*9;ty=(e.clientY/innerHeight-.5)*7;},{passive:true});
 (function loop(){x+=(tx-x)*.04;y+=(ty-y)*.04;visual.style.setProperty('--px',x.toFixed(2));visual.style.setProperty('--py',y.toFixed(2));requestAnimationFrame(loop);})();
}
let lastY=scrollY,ticking=false;
const headerEl=$('.site-header');
addEventListener('scroll',function(){if(ticking)return;ticking=true;requestAnimationFrame(function(){const y=scrollY;if(headerEl){const hide=y>lastY&&y>180&&!(panel&&panel.classList.contains('open'));headerEl.style.transform=hide?'translate(-50%,-145%)':'translate(-50%,0)';headerEl.style.transition='transform .5s cubic-bezier(.5,.1,0,1)';}lastY=y;ticking=false;});},{passive:true});
})();