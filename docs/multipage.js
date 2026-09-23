(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const reduce=matchMedia('(prefers-reduced-motion:reduce)');
const mobile=matchMedia('(max-width:58.749rem)');
const base='/kernellum/';
const route=location.pathname.replace(base,'').replace(/\/+$/,'')||'home';
const pages={
'what-we-do':{
 title:'What We Do • Kernellum',
 heroLabel:'What We Do',
 hero:'Design for the workload.',
 intro:'Kernellum is building a design loop that moves from an AI workload to accelerator architecture, verified RTL, and routed evidence. Physical results inform the next candidate.',
 blocks:[
  ['The design gap','AI workloads evolve faster than fixed accelerator designs. Architecture decisions made from fast estimates can change once the design is placed and routed.'],
  ['The research wedge','K1 closes part of that gap: it routes candidate architectures on ECP5 and uses final-routed timing to guide the next search step.'],
  ['The path forward','The current system tests tiled INT8 GEMM candidates against Transformer workloads. Board measurements and wider targets are the next validation stages.']
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
 hero:'Build for physical reality.',
 intro:'Kernellum is a research-stage effort to automate the path from AI workload to implementable accelerator design. Every claim is tied to the evidence that supports it.',
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
 hero:'Build the next design loop.',
 intro:'The work crosses architecture search, RTL, verification, FPGA tooling, and physical design. Explore the open research and the problems still to solve.',
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
 hero:'Shape the next experiment.',
 intro:'Investors, research collaborators, and hardware builders can start with the public evidence, then open a focused discussion around what should be tested next.',
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
<a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener"><span>Research</span>${footerArrowDots()}</a>
<a href="${base}contact/"><span>Collaborate</span>${footerArrowDots()}</a>
</nav>
<div class="k-footer-cta">${arrow('Contact',base+'contact/')}</div>
<nav class="k-footer-secondary" aria-label="Secondary Footer Nav">
<a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">${footerPips()}<span>GitHub</span>${footerPips()}</a>
<a href="https://github.com/sushxnthd/kernellum/blob/main/docs/EXPERIMENT_LEDGER.md" target="_blank" rel="noopener">${footerPips()}<span>Experiment Ledger</span>${footerPips()}</a>
<a href="${base}careers/">${footerPips()}<span>Contribute</span>${footerPips()}</a>
</nav>
<a class="k-footer-brand" href="${base}">KERNELLUM</a>
</div></footer>`;

const particlePlans={
  'what-we-do':{hero:'circuit',statement:'rings-horizontal',cards:'circuit',features:'matrix',closing:'rings-horizontal'},
  'who-we-are':{hero:'rings-vertical',intro:'image',values:'rings-horizontal',closing:'rings-vertical'},
  'careers':{hero:'matrix',statement:'grid',cards:'matrix',features:'grid',closing:'matrix'},
  'contact':{hero:'image',contact:'rings-vertical',closing:'image'}
};
const particlePlan=particlePlans[route]||{hero:'none',closing:'rings-vertical'};
const heroType=route==='what-we-do'?'left':'center';
const hero=`<section class="route-page-header ${heroType} route-${route}" data-particles="${particlePlan.hero}">
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
 return `<section class="section card-section" id="content" data-particles="${particlePlan.cards}"><div>
 <div class="section-label">${route==='careers'?'Open research':'The opportunity'}</div>
 <h2 class="display wide">${route==='careers'?'Work across the whole stack.':'From estimate to evidence.'}</h2>
 <div class="cards">${data.blocks.map((b,i)=>`<article class="card"><span class="card-index">0${i+1}</span><h3>${b[0]}</h3><p>${b[1]}</p></article>`).join('')}</div>
 </div></section>`;
}
function features(){
 if(!data.features)return '';
 return `<section class="section compact feature-section" data-particles="${particlePlan.features}"><div>
 <div class="section-label">${route==='careers'?'Where the work lives':'The Loop'}</div>
 <h2 class="display">${route==='careers'?'Work across disciplines.':'From workload to routed evidence.'}</h2>
 <div class="feature-list">${data.features.map(f=>`<div class="feature"><span class="n">${f[0]}</span><h3>${f[1]}</h3><p>${f[2]}</p></div>`).join('')}</div>
 </div></section>`;
}
function who(){
 return `<section class="section intro-section" id="content" data-particles="${particlePlan.intro}"><div class="split">
 <div class="left"><div class="section-label">Our Vision</div><h2 class="display">Design with physical reality in the loop.</h2></div>
 <div class="right body-copy"><p class="lede">${data.vision}</p><div class="rule"></div><p>Kernellum's current evidence ladder runs from analytical architecture search through functional RTL, synthesis, final-route timing, and closed-loop acquisition. Physical-board latency, power, and energy remain future validation stages rather than assumed results.</p></div>
 </div></section>
 <section class="section compact values-section" data-particles="${particlePlan.values}"><div><div class="section-label">Our Values</div><h2 class="display wide">Stay true to the evidence and the mission.</h2>
 <div class="values">${data.values.map(v=>`<article class="value"><span class="num">${v[0]}</span><div><h3>${v[1]}</h3><p>${v[2]}</p></div></article>`).join('')}</div></div></section>`;
}
function contact(){
 return `<section class="section contact-section" id="content" data-particles="${particlePlan.contact}"><div>
 <div class="section-label">Contact</div><h2 class="display">Research should be inspectable.</h2>
 <div class="contact-grid">
 <div class="contact-info">
  <div class="contact-row"><small>Repository</small><a href="https://github.com/sushxnthd/kernellum" target="_blank" rel="noopener">github.com/sushxnthd/kernellum <span class="k-arrow-icon" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><path d="M3 13 13 3M6 3h7v7" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter"/></svg></span></a></div>
  <div class="contact-row"><small>Technical discussion</small><a href="https://github.com/sushxnthd/kernellum/issues" target="_blank" rel="noopener">GitHub Issues <span class="k-arrow-icon" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><path d="M3 13 13 3M6 3h7v7" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter"/></svg></span></a></div>
  <div class="contact-row"><small>Current stage</small><span>K2 board-ready; physical measurements not yet claimed</span></div>
 </div>
 <div class="contact-form contact-panel"><span class="section-label">Start a conversation</span><p class="lede">The research is public. Raise a reproduction question, propose a collaboration, or point out a result that needs a closer look.</p><div class="rule"></div>${arrow('Open a GitHub issue','https://github.com/sushxnthd/kernellum/issues/new')}</div>
 </div></div></section>`;
}
const statementMap={
  'what-we-do':'Architecture search matters only if its advantages survive implementation.',
  'careers':'The hardware does not respect org charts.'
};
function largeStatement(){
  const text=statementMap[route];if(!text)return '';
  return `<section class="large-statement" data-particles="${particlePlan.statement}"><h2>${text}</h2></section>`;
}
const closing=`<section class="closing" data-particles="${particlePlan.closing}"><div><div class="section-label">Kernellum</div><h2 class="display">${data.closing}</h2><div>${arrow(route==='careers'?'View Repository':'Read the Research','https://github.com/sushxnthd/kernellum')}</div></div></section>`;

let content='';
if(route==='who-we-are')content=who();
else if(route==='contact')content=contact();
else content=largeStatement()+blockCards()+features();

document.body.innerHTML=`<div id="particle-stage"><canvas></canvas></div><div class="site">${header}<main>${hero}${content}${closing}</main>${footer}</div>`;


const boonEase=t=>{
  const x1=.5,y1=.1,x2=0,y2=1;
  const sample=(u,a1,a2)=>3*(1-u)*(1-u)*u*a1+3*(1-u)*u*u*a2+u*u*u;
  const deriv=(u,a1,a2)=>3*(1-u)*(1-u)*a1+6*(1-u)*u*(a2-a1)+3*u*u*(1-a2);
  let u=t;
  for(let i=0;i<6;i++){const d=deriv(u,x1,x2);if(Math.abs(d)<1e-6)break;u=clamp(u-(sample(u,x1,x2)-t)/d)}
  let lo=0,hi=1;
  for(let i=0;i<8;i++){const x=sample(u,x1,x2);if(Math.abs(x-t)<1e-6)break;if(x<t)lo=u;else hi=u;u=(lo+hi)/2}
  return sample(u,y1,y2);
};

/* Header: source-style DotGrid, scramble, menu expansion and scroll visibility. */
const headerEl=$('#header'),btn=$('.expand-btn'),menu=$('.expand-menu'),menuLabel=$('.expand-btn p'),grid=$('.dotgrid');
const gridPatterns={
  static:[[1,1],[2,1],[3,1],[4,1],[1,2],[2,2],[3,2],[4,2],[1,3],[2,3],[3,3],[4,3]],
  hover:[[1,1],[2,1],[3,1],[4,1],[1,2],[4,2],[1,3],[2,3],[3,3],[4,3]],
  close:[[1,1],[4,1],[2,2],[3,2],[1,3],[4,3]]
};
let gridToken=0;
function renderGrid(pattern){
  if(!grid)return;
  grid.innerHTML=gridPatterns[pattern].map(p=>'<i style="grid-column:'+p[0]+';grid-row:'+p[1]+'"></i>').join('');
}
function blinkSequence(dots,show,randomOrder){
  if(!dots.length)return;
  const order=dots.map((_,i)=>i);
  if(randomOrder)order.sort(()=>Math.random()-.5);
  dots.forEach((d,i)=>{
    d.getAnimations().forEach(a=>a.cancel());
    const rank=order.indexOf(i);
    if(show)d.animate(
      [{opacity:0},{opacity:1},{opacity:0},{opacity:1},{opacity:.5},{opacity:1}],
      {duration:375,delay:rank*25,easing:'steps(2,end)',fill:'forwards'}
    );
    else d.animate(
      [{opacity:getComputedStyle(d).opacity},{opacity:0}],
      {duration:190,delay:(dots.length-1-rank)*8,easing:'steps(2,end)',fill:'forwards'}
    );
  });
}
function transitionGrid(pattern,instant){
  if(!grid)return;
  if(instant||reduce.matches){renderGrid(pattern);return}
  const token=++gridToken,dots=$$('i',grid),order=dots.map((_,i)=>i).sort(()=>Math.random()-.5);
  dots.forEach((d,i)=>d.animate(
    [{opacity:1},{opacity:0},{opacity:1},{opacity:.5},{opacity:0}],
    {duration:300,delay:order.indexOf(i)*25,easing:'steps(2,end)',fill:'forwards'}
  ));
  setTimeout(()=>{
    if(token!==gridToken)return;
    renderGrid(pattern);
    blinkSequence($$('i',grid),true,true);
  },150);
}
renderGrid('static');
function scramble(text){
  if(reduce.matches){menuLabel.textContent=text;return}
  const chars='░▒▓■□',start=performance.now();
  const tick=now=>{
    const p=clamp((now-start)/300),fixed=Math.floor(text.length*p);
    menuLabel.textContent=[...text].map((c,i)=>i<fixed?c:chars[(Math.random()*chars.length)|0]).join('');
    if(p<1)requestAnimationFrame(tick);else menuLabel.textContent=text;
  };
  requestAnimationFrame(tick);
}
function menuOpen(open){
  headerEl.classList.toggle('menu-expanded',open);
  btn.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-hidden',String(!open));
  const from=menu.getBoundingClientRect().height,to=open?menu.scrollHeight:0;
  menu.getAnimations().forEach(a=>a.cancel());
  const a=menu.animate([{maxHeight:from+'px'},{maxHeight:to+'px'}],{duration:500,easing:'cubic-bezier(.5,.1,0,1)',fill:'forwards'});
  a.onfinish=()=>{menu.style.maxHeight=to+'px';a.cancel()};
  transitionGrid(open?'close':'static',false);scramble(open?'CLOSE':'MENU');
}
btn?.addEventListener('click',()=>menuOpen(btn.getAttribute('aria-expanded')!=='true'));
btn?.addEventListener('pointerenter',()=>{if(btn.getAttribute('aria-expanded')!=='true')transitionGrid('hover',false)});
btn?.addEventListener('pointerleave',()=>{if(btn.getAttribute('aria-expanded')!=='true')transitionGrid('static',false)});
document.addEventListener('pointerdown',e=>{if(headerEl?.classList.contains('menu-expanded')&&!headerEl.contains(e.target))menuOpen(false)});
$$('.expand-menu a').forEach(a=>{
  a.addEventListener('click',()=>menuOpen(false));
  a.addEventListener('pointerenter',()=>$$('.k-nav-pips',a).forEach(x=>blinkSequence($$('i',x),true,false)));
  a.addEventListener('pointerleave',()=>$$('.k-nav-pips',a).forEach(x=>blinkSequence($$('i',x),false,false)));
});

/* Footer: source-style dot icon pulse and lightweight ThreeView-like glow. */
$$('.k-footer nav a').forEach(a=>{
  const icons=$$('.footer-dot-icon',a);
  icons.forEach(icon=>$$('i',icon).forEach(d=>d.style.opacity='0'));
  a.addEventListener('pointerenter',()=>icons.forEach(icon=>blinkSequence($$('i',icon),true,false)));
  a.addEventListener('pointerleave',()=>icons.forEach(icon=>blinkSequence($$('i',icon),false,false)));
});
$$('.k-footer-primary,.k-footer-secondary,.k-footer-cta,.k-footer-brand').forEach(surface=>{
  surface.addEventListener('pointermove',e=>{
    const r=surface.getBoundingClientRect();
    surface.style.setProperty('--gx',((e.clientX-r.left)/r.width*100)+'%');
    surface.style.setProperty('--gy',((e.clientY-r.top)/r.height*100)+'%');
  },{passive:true});
});

class ParticleField{
  constructor(canvas){
    this.canvas=canvas;
    this.motionMode=({'what-we-do':1,'who-we-are':2,'careers':3,'contact':4})[route]||0;
    this.gl=canvas.getContext('webgl2',{alpha:true,antialias:true,premultipliedAlpha:true});
    this.shape='none';this.target='none';this.duration=1500;this.morphing=false;this.transition=0;
    this.parallax=0;this.parallaxFrom=0;this.parallaxTo=0;this.start=0;
    this.mouseX=0;this.mouseY=0;this.targetMouseX=0;this.targetMouseY=0;
    this.image=null;this.imageReady=false;this.count=0;
    if(this.gl)this.initGL();
    else this.ctx=canvas.getContext('2d',{alpha:true});
    if(!this.gl&&!this.ctx){this.disabled=true;return}
    addEventListener('mousemove',e=>{this.targetMouseX=e.clientX/innerWidth*2-1;this.targetMouseY=-(e.clientY/innerHeight)*2+1},{passive:true});
    addEventListener('mouseleave',()=>{this.targetMouseX=0;this.targetMouseY=0},{passive:true});
    addEventListener('resize',()=>this.resize(),{passive:true});
    this.loadImage();this.resize();this.set('none',true);
    window.__kernellumParticles=this;
  }
  shader(type,src){
    const g=this.gl,sh=g.createShader(type);g.shaderSource(sh,src);g.compileShader(sh);
    if(!g.getShaderParameter(sh,g.COMPILE_STATUS)){console.warn(g.getShaderInfoLog(sh));g.deleteShader(sh);return null}
    return sh;
  }
  initGL(){
    const g=this.gl;
    const vsSrc=[
      '#version 300 es','precision highp float;',
      'uniform float uBaseSize;','uniform float uTime;','uniform float uMotionMode;','uniform vec2 uViewport;','uniform vec2 uMouse;',
      'uniform float uParallaxStrength;','uniform float uTransition;',
      'in vec3 aPosition;','in vec3 aTargetPosition;','in float aScale;','in float aTargetScale;','in float aRandom;',
      'out float vScale;','out float vIntensity;',
      'void main(){',
      'vec3 finalPos=mix(aPosition,aTargetPosition,uTransition);',
      'float pathArc=sin(uTransition*3.141592653589793);',
      'float rand1=aRandom;','float rand2=fract(aRandom*123.456);',
      'finalPos.x+=(rand1-0.5)*250.0*pathArc;','finalPos.y+=(rand2-0.5)*250.0*pathArc;',
      'finalPos.xy+=uMouse*finalPos.z*4.0*uParallaxStrength;',
      'if(uMotionMode<1.5){',
      'finalPos.x+=sin(uTime*2.2+finalPos.y*.022+rand1*6.28)*12.0;',
      '}else if(uMotionMode<2.5){',
      'float a=uTime*.035;finalPos.xy=mat2(cos(a),-sin(a),sin(a),cos(a))*finalPos.xy;',
      'finalPos.xy*=1.0+.015*sin(uTime*.8);',
      '}else if(uMotionMode<3.5){',
      'finalPos.y+=sin(uTime*1.4+finalPos.x*.015+rand1*2.0)*9.0;',
      '}else{',
      'float r=length(finalPos.xy);finalPos.xy+=normalize(finalPos.xy+vec2(.001))*(sin(r*.018-uTime*1.8)*13.0);',
      '}',
      'gl_Position=vec4(finalPos.x/(uViewport.x*0.5),finalPos.y/(uViewport.y*0.5),0.0,1.0);',
      'float finalScale=mix(aScale,aTargetScale,uTransition);','vScale=finalScale;',
      'float pulse=sin(uTime*2.0+(rand1*6.283185307179586))*0.5+0.5;',
      'float oscillationScale=mix(0.35,0.9,pulse);','gl_PointSize=uBaseSize*oscillationScale*finalScale;',
      'vec2 mouseWorld=uMouse*uViewport*0.5;','float distToMouse=distance(finalPos.xy,mouseWorld);',
      'float screenMin=min(uViewport.x,uViewport.y);','float outerRadius=screenMin*0.65;',
      'vIntensity=smoothstep(outerRadius,0.0,distToMouse);','}'
    ].join('\n');
    const fsSrc=[
      '#version 300 es','precision highp float;','uniform vec3 uBaseColor;','uniform vec3 uHighlightColor;',
      'in float vScale;','in float vIntensity;','out vec4 outColor;','void main(){',
      'if(vScale<0.001)discard;','vec2 p=gl_PointCoord-0.5;','float dist=length(p);','float aa=fwidth(dist);',
      'if(dist>0.5+aa)discard;','float alpha=1.0-smoothstep(0.5-aa,0.5+aa,dist);',
      'vec3 finalColor=mix(uBaseColor,uHighlightColor,vIntensity);','outColor=vec4(finalColor,alpha);','}'
    ].join('\n');
    const vs=this.shader(g.VERTEX_SHADER,vsSrc),fs=this.shader(g.FRAGMENT_SHADER,fsSrc);
    if(!vs||!fs){this.disabled=true;return}
    const p=g.createProgram();g.attachShader(p,vs);g.attachShader(p,fs);g.linkProgram(p);
    if(!g.getProgramParameter(p,g.LINK_STATUS)){console.warn(g.getProgramInfoLog(p));this.disabled=true;return}
    g.deleteShader(vs);g.deleteShader(fs);this.program=p;g.useProgram(p);
    this.loc={
      pos:g.getAttribLocation(p,'aPosition'),target:g.getAttribLocation(p,'aTargetPosition'),
      scale:g.getAttribLocation(p,'aScale'),targetScale:g.getAttribLocation(p,'aTargetScale'),
      random:g.getAttribLocation(p,'aRandom'),baseSize:g.getUniformLocation(p,'uBaseSize'),
      time:g.getUniformLocation(p,'uTime'),motionMode:g.getUniformLocation(p,'uMotionMode'),viewport:g.getUniformLocation(p,'uViewport'),
      mouse:g.getUniformLocation(p,'uMouse'),parallax:g.getUniformLocation(p,'uParallaxStrength'),
      transition:g.getUniformLocation(p,'uTransition'),baseColor:g.getUniformLocation(p,'uBaseColor'),
      highlight:g.getUniformLocation(p,'uHighlightColor')
    };
    this.buffers={pos:g.createBuffer(),target:g.createBuffer(),scale:g.createBuffer(),targetScale:g.createBuffer(),random:g.createBuffer()};
    g.enable(g.BLEND);g.blendFunc(g.SRC_ALPHA,g.ONE_MINUS_SRC_ALPHA);g.disable(g.DEPTH_TEST);
    g.uniform1f(this.loc.baseSize,18);g.uniform3f(this.loc.baseColor,36/255,107/255,73/255);g.uniform3f(this.loc.highlight,185/255,243/255,93/255);
  }
  bindBuffer(name,data,size){
    if(this.disabled||!this.gl)return;const g=this.gl,b=this.buffers[name],loc=this.loc[name];
    g.bindBuffer(g.ARRAY_BUFFER,b);g.bufferData(g.ARRAY_BUFFER,data,g.DYNAMIC_DRAW);g.enableVertexAttribArray(loc);g.vertexAttribPointer(loc,size,g.FLOAT,false,0,0);
  }
  uploadAll(){this.bindBuffer('pos',this.positions,3);this.bindBuffer('target',this.targetPositions,3);this.bindBuffer('scale',this.scales,1);this.bindBuffer('targetScale',this.targetScales,1);this.bindBuffer('random',this.random,1)}
  loadImage(){
    const im=new Image();im.src='/kernellum/assets/particle-mask.svg';
    im.onload=()=>{this.image=im;this.imageReady=true;if(this.target==='image')this.set('image',false,true)};
  }
  resize(){
    if(this.disabled)return;
    const dpr=Math.min(devicePixelRatio||1,2),w=innerWidth,h=innerHeight,g=this.gl;this.w=w;this.h=h;this.dpr=dpr;
    this.canvas.width=Math.floor(w*dpr);this.canvas.height=Math.floor(h*dpr);this.canvas.style.width=w+'px';this.canvas.style.height=h+'px';if(g)g.viewport(0,0,this.canvas.width,this.canvas.height);
    this.gap=g?13.5:22;this.cols=Math.ceil(w/this.gap)+1;this.rows=Math.ceil(h/this.gap)+1;this.count=this.cols*this.rows;
    this.startX=this.cols*this.gap/-2+this.gap/2;this.startY=this.rows*this.gap/-2+this.gap/2;
    const base=this.makeNone();this.positions=base.positions;this.scales=base.scales;this.targetPositions=new Float32Array(this.positions);this.targetScales=new Float32Array(this.scales);
    this.random=new Float32Array(this.count);for(let i=0;i<this.count;i++)this.random[i]=Math.random();this.uploadAll();
    if(this.target!=='none')this.set(this.target,true,true);
  }
  empty(){return{positions:new Float32Array(this.count*3),scales:new Float32Array(this.count)}}
  shuffle(){const a=Array.from({length:this.count},(_,i)=>i);for(let i=a.length-1;i>0;i--){const j=(Math.random()*(i+1))|0;const t=a[i];a[i]=a[j];a[j]=t}return a}
  fallback(out,scales,index,prior){
    const j=index*3;if(prior&&Number.isFinite(prior[j])){out[j]=prior[j];out[j+1]=prior[j+1];out[j+2]=prior[j+2]}
    else{const c=index%this.cols,r=(index/this.cols)|0;out[j]=this.startX+c*this.gap;out[j+1]=this.startY+r*this.gap;out[j+2]=0}scales[index]=0;
  }
  makeNone(){
    const o=this.empty();let a=0;for(let r=0;r<this.rows;r++)for(let c=0;c<this.cols;c++){o.positions[a*3]=this.startX+c*this.gap;o.positions[a*3+1]=this.startY+r*this.gap;o.positions[a*3+2]=0;o.scales[a]=0;a++}return o;
  }
  makeGrid(){
    const o=this.empty(),order=this.shuffle();let n=0;
    for(let r=0;r<this.rows;r++)for(let c=0;c<this.cols;c++){const i=order[n++],x=this.startX+c*this.gap,y=this.startY+r*this.gap;o.positions[i*3]=x;o.positions[i*3+1]=y;o.positions[i*3+2]=(x*x+y*y)/400000;o.scales[i]=Math.random()<.5?0:Math.random()}return o;
  }
  makeHorizontal(){
    const o=this.empty(),prior=this.positions,ringCount=10,radius=Math.max(Math.min(this.w,this.h)*.25,150),spacing=radius*.3,start=-((ringCount-1)*spacing)/2,order=this.shuffle();
    let ring=0,point=0,per=Math.floor(2*Math.PI*radius/this.gap);
    for(let n=0;n<this.count;n++){const i=order[n];if(ring<ringCount){const t=point/per*Math.PI*2,x=start+ring*spacing;o.positions[i*3]=x+Math.cos(t)*radius;o.positions[i*3+1]=Math.sin(t)*radius;o.positions[i*3+2]=(ring-ringCount/2)*-5;o.scales[i]=1;if(++point>=per){ring++;point=0}}else this.fallback(o.positions,o.scales,i,prior)}return o;
  }
  makeVertical(){
    const o=this.empty(),prior=this.positions,ringCount=6,order=this.shuffle();let ring=0,radius=Math.max(Math.min(this.w,this.h)*.35,250),z=0,point=0,per=Math.floor(2*Math.PI*radius/this.gap);
    for(let n=0;n<this.count;n++){const i=order[n];if(ring<ringCount&&radius>0){const t=point/per*Math.PI*2;o.positions[i*3]=Math.cos(t)*radius;o.positions[i*3+1]=Math.sin(t)*radius;o.positions[i*3+2]=z;o.scales[i]=1;if(++point>=per){ring++;radius-=40;z-=15;per=Math.floor(2*Math.PI*radius/this.gap);point=0}}else this.fallback(o.positions,o.scales,i,prior)}return o;
  }
  makeCircuit(){
    const o=this.empty(),order=this.shuffle(),n=Math.min(this.count,Math.floor(this.w*this.h/250));
    for(let k=0;k<this.count;k++){const i=order[k];if(k>=n){this.fallback(o.positions,o.scales,i,this.positions);continue}
      const lane=k%15,step=Math.floor(k/15),x=(step%Math.ceil(this.w/12))*12-this.w/2;
      const branch=lane%3===0?Math.max(-90,Math.min(90,x*.34)):0;
      o.positions[i*3]=x;o.positions[i*3+1]=(lane-7)*this.h/22+branch;o.positions[i*3+2]=lane*2;
      o.scales[i]=(step%19===0)?1.45:.45;
    }return o;
  }
  makeWave(){
    const o=this.empty(),order=this.shuffle(),n=Math.min(this.count,Math.floor(this.w*this.h/220));
    for(let k=0;k<this.count;k++){const i=order[k];if(k>=n){this.fallback(o.positions,o.scales,i,this.positions);continue}
      const band=k%9,x=((Math.floor(k/9)*11)%Math.max(1,this.w))-this.w/2;
      o.positions[i*3]=x;o.positions[i*3+1]=(band-4)*this.h/13+Math.sin(x/95+band*.46)*this.h*.10;
      o.positions[i*3+2]=band*4;o.scales[i]=.45+(band%3===0?.45:0);
    }return o;
  }
  makeMatrix(){
    const o=this.empty(),order=this.shuffle(),cols=Math.max(12,Math.floor(this.w/22)),rows=Math.max(9,Math.floor(this.h/22));
    for(let k=0;k<this.count;k++){const i=order[k];if(k>=cols*rows){this.fallback(o.positions,o.scales,i,this.positions);continue}
      const col=k%cols,row=Math.floor(k/cols),x=(col-(cols-1)/2)*20,y=(row-(rows-1)/2)*20;
      o.positions[i*3]=x;o.positions[i*3+1]=y;o.positions[i*3+2]=0;
      o.scales[i]=(col%7===0||row%7===0||((col+row)%11===0))?.95:.15;
    }return o;
  }
  makeImage(){
    if(!this.imageReady||!this.image)return this.makeNone();
    const c=document.createElement('canvas'),ctx=c.getContext('2d',{willReadFrequently:true}),w=this.cols,h=this.rows;c.width=w;c.height=h;
    const ratio=this.image.width/this.image.height,target=w/h;let dw,dh,ox,oy;
    if(ratio>target){dh=h;dw=this.image.width*(h/this.image.height);ox=(w-dw)/2;oy=0}else{dw=w;dh=this.image.height*(w/this.image.width);ox=0;oy=(h-dh)/2}
    ctx.drawImage(this.image,ox,oy,dw,dh);const data=ctx.getImageData(0,0,w,h).data,pixels=[];
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){const p=(y*w+x)*4;if(data[p+3]>128){const darkness=1-(.299*data[p]+.587*data[p+1]+.114*data[p+2])/255,th=.33;pixels.push({x:x,y:y,scale:darkness<=th?0:(darkness-th)/(1-th)})}}
    const o=this.empty(),prior=this.positions,order=this.shuffle();
    for(let n=0;n<this.count;n++){const i=order[n];if(n<pixels.length){const px=pixels[n],yy=this.rows-1-px.y;o.positions[i*3]=this.startX+px.x*this.gap;o.positions[i*3+1]=this.startY+yy*this.gap;o.positions[i*3+2]=0;o.scales[i]=px.scale}else this.fallback(o.positions,o.scales,i,prior)}return o;
  }
  build(shape){if(shape==='grid')return this.makeGrid();if(shape==='rings-horizontal')return this.makeHorizontal();if(shape==='rings-vertical')return this.makeVertical();if(shape==='image')return this.makeImage();if(shape==='circuit')return this.makeCircuit();if(shape==='wave')return this.makeWave();if(shape==='matrix')return this.makeMatrix();return this.makeNone()}
  transitionValue(now=performance.now()){if(!this.morphing)return this.transition;const raw=clamp((now-this.start)/this.duration);return boonEase(raw)}
  bake(now=performance.now()){
    if(!this.morphing)return;const t=this.transitionValue(now),arc=Math.sin(t*Math.PI);
    for(let i=0;i<this.count;i++){const j=i*3,r=this.random[i],r2=(r*123.456)%1;this.positions[j]=lerp(this.positions[j],this.targetPositions[j],t)+(r-.5)*250*arc;this.positions[j+1]=lerp(this.positions[j+1],this.targetPositions[j+1],t)+(r2-.5)*250*arc;this.positions[j+2]=lerp(this.positions[j+2],this.targetPositions[j+2],t);this.scales[i]=lerp(this.scales[i],this.targetScales[i],t)}
    this.transition=0;this.morphing=false;this.bindBuffer('pos',this.positions,3);this.bindBuffer('scale',this.scales,1);
  }
  set(shape,instant=false,force=false){
    if(this.disabled)return;if(shape===this.target&&!force)return;if(this.morphing)this.bake();this.target=shape;const next=this.build(shape);
    if(instant||reduce.matches){this.positions=next.positions;this.scales=next.scales;this.targetPositions=new Float32Array(next.positions);this.targetScales=new Float32Array(next.scales);this.random=new Float32Array(this.count);for(let i=0;i<this.count;i++)this.random[i]=Math.random();this.parallax=shape==='none'||shape==='image'?0:1;this.parallaxFrom=this.parallaxTo=this.parallax;this.transition=0;this.morphing=false;this.uploadAll();this.shape=shape;return}
    this.targetPositions=next.positions;this.targetScales=next.scales;this.bindBuffer('target',this.targetPositions,3);this.bindBuffer('targetScale',this.targetScales,1);this.parallaxFrom=this.parallax;this.parallaxTo=shape==='none'||shape==='image'?0:1;this.start=performance.now();this.transition=0;this.morphing=true;this.shape=shape;
  }
  draw(now,dt){
    if(this.disabled)return;this.mouseX=lerp(this.mouseX,this.targetMouseX,1-Math.exp(-5*dt));this.mouseY=lerp(this.mouseY,this.targetMouseY,1-Math.exp(-5*dt));
    let t=this.morphing?this.transitionValue(now):this.transition;
    if(this.morphing){const raw=clamp((now-this.start)/this.duration);this.parallax=lerp(this.parallaxFrom,this.parallaxTo,t);if(raw>=1){this.positions=new Float32Array(this.targetPositions);this.scales=new Float32Array(this.targetScales);this.bindBuffer('pos',this.positions,3);this.bindBuffer('scale',this.scales,1);this.transition=0;t=0;this.morphing=false;this.parallax=this.parallaxTo}}
    if(this.ctx){
      const c=this.ctx;c.setTransform(this.dpr,0,0,this.dpr,0,0);c.clearRect(0,0,this.w,this.h);c.fillStyle='#b9f35d';
      for(let i=0;i<this.count;i++){
        const j=i*3,scale=lerp(this.scales[i],this.targetScales[i],t);if(scale<.08)continue;
        const z=lerp(this.positions[j+2],this.targetPositions[j+2],t);
        let px=lerp(this.positions[j],this.targetPositions[j],t)+this.mouseX*z*4*this.parallax;
        let py=lerp(this.positions[j+1],this.targetPositions[j+1],t)+this.mouseY*z*4*this.parallax;
        const seconds=now*.001;
        if(this.motionMode===1)px+=Math.sin(seconds*2.2+py*.022+this.random[i]*6.28)*12;
        else if(this.motionMode===2){const a=seconds*.035,s=1+.015*Math.sin(seconds*.8),ox=px;px=(ox*Math.cos(a)-py*Math.sin(a))*s;py=(ox*Math.sin(a)+py*Math.cos(a))*s}
        else if(this.motionMode===3)py+=Math.sin(seconds*1.4+px*.015+this.random[i]*2)*9;
        else if(this.motionMode===4){const d=Math.hypot(px,py)||1,shift=Math.sin(d*.018-seconds*1.8)*13;px+=px/d*shift;py+=py/d*shift}
        const x=px+this.w/2,y=this.h/2-py;
        if(x<0||x>this.w||y<0||y>this.h)continue;
        const pulse=.68+.32*Math.sin(now*.002+this.random[i]*6.28);
        c.globalAlpha=Math.min(.75,(.25+.35*(1-Math.hypot(x-this.w/2,y-this.h/2)/Math.max(this.w,this.h)))*scale);
        c.beginPath();c.arc(x,y,Math.max(.5,2.1*scale*pulse),0,Math.PI*2);c.fill();
      }
      c.globalAlpha=1;return;
    }
    const g=this.gl;g.useProgram(this.program);
    g.clearColor(0,0,0,0);g.clear(g.COLOR_BUFFER_BIT);g.uniform1f(this.loc.time,now*.001);g.uniform1f(this.loc.motionMode,this.motionMode);g.uniform2f(this.loc.viewport,this.w,this.h);g.uniform2f(this.loc.mouse,this.mouseX,this.mouseY);g.uniform1f(this.loc.parallax,this.parallax);g.uniform1f(this.loc.transition,t);g.drawArrays(g.POINTS,0,this.count);
  }
}
const canvas=$('#particle-stage canvas'),particles=canvas?new ParticleField(canvas):null;

/* Text and particles share the same scroll coordinate. */
function splitHeadingChars(el){
  if(!el||el.dataset.revealSplit)return[];
  el.dataset.revealSplit='chars';
  const words=el.textContent.trim().split(/\s+/);el.textContent='';const chars=[];
  words.forEach((word,wi)=>{
    const ws=document.createElement('span');ws.style.display='inline-block';ws.style.whiteSpace='nowrap';
    [...word].forEach(ch=>{const c=document.createElement('span');c.className='boon-char';c.textContent=ch;ws.appendChild(c);chars.push(c)});
    el.appendChild(ws);if(wi<words.length-1)el.append(' ');
  });
  return chars;
}
function splitLines(el){
  if(!el||el.dataset.revealSplit)return[];
  el.dataset.revealSplit='lines';
  const words=el.textContent.trim().split(/\s+/);el.textContent='';const probes=[];
  words.forEach((word,wi)=>{
    const w=document.createElement('span');w.textContent=word;w.style.cssText='display:inline-block;white-space:nowrap';
    el.appendChild(w);probes.push(w);if(wi<words.length-1)el.append(' ');
  });
  const rows=[];let top=null,row=[];
  probes.forEach(w=>{const y=Math.round(w.offsetTop);if(top===null||Math.abs(y-top)<=1)row.push(w.textContent);else{rows.push(row);row=[w.textContent]}top=y});
  if(row.length)rows.push(row);
  el.innerHTML=rows.map(r=>'<span class="boon-line-clip"><span class="boon-line">'+r.join(' ')+'</span></span>').join('');
  return $$('.boon-line',el);
}
const revealGroups=[];
function revealScope(scope){
  if(!scope||scope.dataset.revealReady)return;
  scope.dataset.revealReady='1';
  const headings=$$('h2,h3,h4,h5,h6',scope).filter(h=>!h.closest('.large-statement'));
  const paragraphs=$$('p',scope).filter(p=>!p.closest('form'));
  const labels=$$('.section-label,.card-index,.n,.num',scope);
  headings.forEach(el=>revealGroups.push({el,nodes:splitHeadingChars(el),kind:'chars'}));
  paragraphs.forEach(el=>revealGroups.push({el,nodes:splitLines(el),kind:'lines'}));
  labels.forEach(el=>revealGroups.push({el,nodes:[el],kind:'labels'}));
  if(reduce.matches)return;
  revealGroups.forEach(group=>{
    group.nodes.forEach(node=>{
      node.style.opacity='0';
      if(group.kind!=='chars')node.style.transform=group.kind==='labels'?'translateY(20px)':'translateY(50%)';
    });
  });
}
$$('.section,.closing').forEach(revealScope);
function scrubReveals(vh){
  if(reduce.matches)return;
  revealGroups.forEach(group=>{
    const r=group.el.getBoundingClientRect();
    if(r.top>vh*1.05||r.bottom<-vh*.1)return;
    const progress=clamp((vh*.89-r.top)/(vh*.51));
    const n=group.nodes.length;
    group.nodes.forEach((node,i)=>{
      const stagger=group.kind==='chars'?(i/Math.max(1,n-1))*.32:i*.055;
      const local=clamp((progress-stagger)/.58),eased=1-Math.pow(1-local,3);
      node.style.opacity=String(eased);
      if(group.kind!=='chars')node.style.transform=`translateY(${(group.kind==='labels'?20:50)*(1-eased)}${group.kind==='labels'?'px':'%'})`;
    });
  });
}

/* Scroll-scrubbed PageHeader / LargeText / CardGrid */
const heroEl=$('.route-page-header'),heroTitle=$('.route-title'),heroLines=splitLines(heroTitle);
const heroImages=$$('.route-image'),heroViz=$$('.route-viz'),heroSub=$('.route-subtitle'),heroCta=$('.route-cta');
const statement=$('.large-statement'),statementLines=statement?splitLines($('h2',statement)):[];
if(!reduce.matches)statementLines.forEach(l=>l.style.transform='translateY(100%)');
const cards=$$('.cards>.card');
if(!reduce.matches)cards.forEach((c,i)=>c.style.transform='translateY('+(100+i*50)+'px)');

/* Page transition */
if(!reduce.matches){
  const main=$('main');
  const a=main.animate(
    [{clipPath:'inset(50% 25% 50% 25%)',transform:'scale(.5)',filter:'blur(8px)'},
     {clipPath:'inset(0 0 0 0)',transform:'scale(1)',filter:'blur(0px)'}],
    {duration:1000,easing:'cubic-bezier(.25,.46,.45,.94)',fill:'both'}
  );
  a.finished.finally(()=>{main.style.clipPath='';main.style.transform='';main.style.filter=''});
}

/* Section / particle focus follows the same smoothed coordinate as text. */
const focus=$$('[data-particles]').map(el=>[el,el.dataset.particles]).filter(x=>x[1]);
let focusEl=null,smoothY=scrollY,lastY=scrollY,lastToggle=scrollY,lastTime=performance.now();
function smoothRect(el){
  const raw=el.getBoundingClientRect();
  return{top:raw.top,bottom:raw.bottom,height:raw.height};
}
function chooseFocus(){
  if(!particles)return;
  const vh=innerHeight,line=vh*(scrollY>lastY?.4:scrollY<lastY?.6:.5);let best=null,score=-1;
  focus.forEach(item=>{
    const r=smoothRect(item[0]),vis=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));
    if(vis<vh*.05)return;
    const ratio=vis/Math.min(vh,r.height),d=(r.top<=line&&r.bottom>=line)?0:Math.min(Math.abs(r.top-line),Math.abs(r.bottom-line));
    const center=1-Math.min(1,d/vh),sc=ratio*.6+center*.4;
    if(sc>score){score=sc;best=item}
  });
  if(best&&best[0]!==focusEl){focusEl=best[0];particles.set(best[1])}
}
function frame(now){
  const dt=Math.min(.05,(now-lastTime)/1000);lastTime=now;
  const y=scrollY,dir=Math.sign(y-lastY),vh=innerHeight;
  smoothY=y;
  if(headerEl){
    let visible=headerEl.classList.contains('visible'),hh=headerEl.offsetHeight;
    if(y<hh)visible=true;else if(Math.abs(y-lastToggle)>=50){visible=dir<0;lastToggle=y}
    headerEl.classList.toggle('visible',visible);headerEl.style.transform=visible?'translateY(0)':'translateY(-150%)';
  }
  if(heroEl&&!reduce.matches){
    const p=clamp(smoothY/vh);
    if(heroType==='left'){
      if(heroImages[1])heroImages[1].style.transform='translateX('+(-25*p)+'%)';
      if(heroViz[1])heroViz[1].style.transform='translateX('+(12.5*p)+'%)';
      if(heroImages[2])heroImages[2].style.transform='translateX('+(-25*p)+'%)';
      if(heroViz[2])heroViz[2].style.transform='translateX('+(12.5*p)+'%)';
    }else{
      if(heroImages[1])heroImages[1].style.transform='translateX('+(-25*p)+'%)';
      if(heroViz[1])heroViz[1].style.transform='translateX('+(12.5*p)+'%)';
      if(heroImages[2])heroImages[2].style.transform='translateX('+(25*p)+'%)';
      if(heroViz[2])heroViz[2].style.transform='translateX('+(-12.5*p)+'%)';
    }
    heroLines.forEach(l=>l.style.transform='translateY('+(-250*p)+'%)');
    if(heroViz[0])heroViz[0].style.transform='scale('+(1+.15*p)+')';
    if(heroSub){heroSub.style.opacity=String(Math.max(0,1-1.5*p));if(!mobile.matches)heroSub.style.transform='translateX('+(-5*p)+'vw)'}
    if(heroCta){heroCta.style.opacity=String(Math.max(0,1-1.5*p));if(!mobile.matches)heroCta.style.transform='translateX('+(5*p)+'vw)'}
  }
  const cardWrap=$('.cards');
  if(cardWrap&&!reduce.matches){
    const r=smoothRect(cardWrap),p=clamp((vh-r.top)/(vh*.65));
    cards.forEach((c,i)=>{
      const lp=clamp((p-i*(150/800)*.35)/(1-i*.035)),e=1-Math.pow(1-lp,3);
      c.style.transform='translateY('+((100+i*50)*(1-e))+'px)';
    });
  }
  if(statement&&!reduce.matches){
    const r=smoothRect(statement),p=clamp((vh*.9-r.top)/(vh*.85));
    statementLines.forEach(l=>l.style.transform='translateY('+(100*(1-p))+'%)');
  }
  scrubReveals(vh);chooseFocus();particles?.draw(now,dt);lastY=y;requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

/* Lenis-equivalent desktop interpolation. */
if(!reduce.matches&&matchMedia('(hover:hover) and (pointer:fine)').matches){
  let target=scrollY,current=scrollY,driving=false;
  const max=()=>Math.max(0,document.documentElement.scrollHeight-innerHeight);
  addEventListener('wheel',e=>{
    if(e.ctrlKey||e.metaKey)return;
    const t=e.target;if(t instanceof Element&&t.closest('input,textarea,select,[contenteditable="true"]'))return;
    e.preventDefault();driving=true;current=scrollY;target=clamp(target+e.deltaY,0,max());
  },{passive:false});
  addEventListener('keydown',e=>{
    const amt=e.key==='PageDown'?innerHeight*.9:e.key==='PageUp'?-innerHeight*.9:e.key==='ArrowDown'?40:e.key==='ArrowUp'?-40:0;
    if(!amt)return;e.preventDefault();driving=true;current=scrollY;target=clamp(target+amt,0,max());
  });
  const scrollRaf=()=>{
    if(driving){current+=(target-current)*.1;if(Math.abs(target-current)<.2){current=target;driving=false}scrollTo(0,current)}
    else{current=scrollY;target=scrollY}
    requestAnimationFrame(scrollRaf);
  };
  requestAnimationFrame(scrollRaf);
  $$('a[href^="#"]').forEach(a=>a.addEventListener('click',e=>{
    const id=a.getAttribute('href'),el=id&&$(id);if(!el)return;
    e.preventDefault();target=clamp(scrollY+el.getBoundingClientRect().top,0,max());current=scrollY;driving=true;
  }));
}

})();
