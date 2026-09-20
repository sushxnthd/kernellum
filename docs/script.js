(() => {
  const $ = (s, p=document) => p.querySelector(s);
  const $$ = (s, p=document) => [...p.querySelectorAll(s)];
  const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));

  // Cursor
  const cursor=$('.cursor');
  let mx=innerWidth/2,my=innerHeight/2,cx=mx,cy=my;
  addEventListener('pointermove',e=>{mx=e.clientX;my=e.clientY});
  function cursorLoop(){cx+=(mx-cx)*.18;cy+=(my-cy)*.18;cursor.style.transform=`translate(${cx-17}px,${cy-17}px)`;requestAnimationFrame(cursorLoop)}cursorLoop();
  $$('a,button,.candidate').forEach(el=>{el.addEventListener('mouseenter',()=>cursor.classList.add('big'));el.addEventListener('mouseleave',()=>cursor.classList.remove('big'))});

  // Scroll buttons
  $$('[data-scroll]').forEach(b=>b.addEventListener('click',()=>$(b.dataset.scroll)?.scrollIntoView({behavior:'smooth'})));

  // Top bar state
  const topbar=$('#topbar');
  addEventListener('scroll',()=>topbar.classList.toggle('scrolled',scrollY>40),{passive:true});

  // Hero architecture field - custom perspective particle engine
  const canvas=$('#field'),ctx=canvas.getContext('2d');
  let W=0,H=0,DPR=Math.min(devicePixelRatio||1,2);
  const N=220;
  const pts=Array.from({length:N},(_,i)=>({
    x:(Math.random()-.5)*2.5,y:(Math.random()-.5)*1.7,z:Math.random()*2.5+.25,
    s:Math.random()*1.3+.35,phase:Math.random()*Math.PI*2,kind:Math.random()<.08?1:0
  }));
  function resize(){W=canvas.clientWidth;H=canvas.clientHeight;canvas.width=W*DPR;canvas.height=H*DPR;ctx.setTransform(DPR,0,0,DPR,0,0)}
  addEventListener('resize',resize);resize();
  let heroMouseX=0,heroMouseY=0;
  $('.hero').addEventListener('pointermove',e=>{heroMouseX=(e.clientX/W-.5);heroMouseY=(e.clientY/H-.5)});
  let t=0;
  function renderField(){
    t+=.004;ctx.clearRect(0,0,W,H);
    const scrollP=clamp(scrollY/(H*.95),0,1);
    const focal=Math.min(W,H)*.75;
    const projected=[];
    for(const p of pts){
      const zz=((p.z - t*.35)%2.7+2.7)%2.7+.15;
      const wobX=Math.sin(t*2+p.phase)*.035, wobY=Math.cos(t*1.6+p.phase)*.03;
      const x=(p.x+wobX+heroMouseX*.12)/(zz),y=(p.y+wobY+heroMouseY*.1)/(zz);
      const sx=W/2+x*focal, sy=H/2+y*focal;
      if(sx<-30||sx>W+30||sy<-30||sy>H+30) continue;
      const a=clamp(1-zz/3.0,.05,.5)*(1-scrollP*.7),r=p.s*(3.2/zz);
      projected.push({sx,sy,a,r,kind:p.kind,zz});
    }
    projected.sort((a,b)=>b.zz-a.zz);
    for(const p of projected){
      ctx.beginPath();ctx.arc(p.sx,p.sy,p.r,0,Math.PI*2);
      ctx.fillStyle=p.kind?`rgba(255,75,43,${p.a*.95})`:`rgba(241,239,233,${p.a})`;ctx.fill();
      if(p.kind&&p.a>.2){ctx.beginPath();ctx.arc(p.sx,p.sy,p.r*3,0,Math.PI*2);ctx.strokeStyle=`rgba(255,75,43,${p.a*.22})`;ctx.stroke()}
    }
    // sparse nearest-neighbour links
    ctx.lineWidth=.6;
    for(let i=0;i<projected.length;i+=10){const a=projected[i];let best=null,bd=10000;for(let j=i+1;j<Math.min(projected.length,i+45);j++){const b=projected[j],d=Math.hypot(a.sx-b.sx,a.sy-b.sy);if(d<bd&&d<120){bd=d;best=b}}if(best){ctx.beginPath();ctx.moveTo(a.sx,a.sy);ctx.lineTo(best.sx,best.sy);ctx.strokeStyle=`rgba(241,239,233,${Math.min(a.a,best.a)*.22})`;ctx.stroke()}}
    requestAnimationFrame(renderField)
  }renderField();

  // Hero logo parallax
  const heroMark=$('#heroMark');
  $('.hero').addEventListener('pointermove',e=>{const x=(e.clientX/innerWidth-.5)*9,y=(e.clientY/innerHeight-.5)*9;heroMark.style.transform=`translate(${x}px,${y}px) rotateX(${-y*.5}deg) rotateY(${x*.5}deg)`});

  // Candidate field
  const cloud=$('#candidateCloud');
  const count=46;
  const data=[];
  for(let i=0;i<count;i++){
    const d={id:1000+Math.floor(Math.random()*8999),area:(.2+Math.random()*.75),energy:(.18+Math.random()*.8),latency:(.15+Math.random()*.82),memory:(.2+Math.random()*.7),status:Math.random()<.28?'NON-DOMINATED':'DOMINATED'};
    data.push(d);
    const el=document.createElement('div');el.className='candidate';el.dataset.i=i;
    el.style.left=`${8+Math.random()*84}%`;el.style.top=`${12+Math.random()*74}%`;
    const z=-80+Math.random()*240, r=-20+Math.random()*40, s=.45+Math.random()*1.15;
    el.style.transform=`translateZ(${z}px) rotate(${r}deg) scale(${s})`;el.style.opacity=(.18+Math.random()*.72).toFixed(2);
    el.addEventListener('mouseenter',()=>selectCandidate(i,el));
    cloud.appendChild(el)
  }
  function selectCandidate(i,el){$$('.candidate').forEach(x=>x.classList.remove('active'));el.classList.add('active');const d=data[i];$('#candidateId').textContent=`KRN-${d.id}`;$('#mArea').textContent=d.area.toFixed(2);$('#mEnergy').textContent=d.energy.toFixed(2);$('#mLatency').textContent=d.latency.toFixed(2);$('#mMemory').textContent=d.memory.toFixed(2);$('#mStatus').textContent=d.status}
  selectCandidate(7,$$('.candidate')[7]);
  cloud.addEventListener('pointermove',e=>{const x=(e.clientX/innerWidth-.5)*16,y=(e.clientY/innerHeight-.5)*10;cloud.style.transform=`rotateX(${-y*.16}deg) rotateY(${x*.16}deg)`});

  // Evidence scatter dots
  const dots=$('.plot-card .dots');
  if(dots){for(let i=0;i<46;i++){const c=document.createElementNS('http://www.w3.org/2000/svg','circle');const x=70+Math.random()*400;const frontier=242-(x-70)*.45;const y=clamp(frontier+20+Math.random()*105,35,248);c.setAttribute('cx',x);c.setAttribute('cy',y);c.setAttribute('r',Math.random()<.12?4:2.5);c.setAttribute('fill',Math.random()<.12?'#ff4b2b':'#0b0b0a');c.setAttribute('opacity',Math.random()<.12?'1':'.48');dots.appendChild(c)}}

  // Intersection states
  const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add('seen');if(e.target.id==='synthesis')$('.metric-stack').classList.add('run')}}),{threshold:.28});
  $$('.chapter').forEach(s=>io.observe(s));

  // subtle progress-based transforms
  let ticking=false;
  addEventListener('scroll',()=>{if(!ticking){requestAnimationFrame(()=>{
    const h=innerHeight;$$('.chapter').forEach(sec=>{const r=sec.getBoundingClientRect();const p=clamp((h-r.top)/(h+r.height),0,1);sec.style.setProperty('--progress',p.toFixed(3))});
    ticking=false
  });ticking=true}}, {passive:true});
})();