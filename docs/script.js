(() => {
  const $ = (s, p=document) => p.querySelector(s);
  const $$ = (s, p=document) => [...p.querySelectorAll(s)];
  const clamp = (v,a,b) => Math.max(a, Math.min(b,v));
  const lerp = (a,b,t) => a + (b-a)*t;

  // Boot
  addEventListener('load', () => setTimeout(() => $('#loader')?.classList.add('done'), 520));

  // Cursor + magnetic elements
  const cursor = $('.cursor');
  let mx = innerWidth * .5, my = innerHeight * .5, cx = mx, cy = my;
  addEventListener('pointermove', e => { mx = e.clientX; my = e.clientY; });
  function cursorLoop(){
    cx += (mx-cx)*.19; cy += (my-cy)*.19;
    if(cursor) cursor.style.transform = `translate3d(${cx-17}px,${cy-17}px,0)`;
    requestAnimationFrame(cursorLoop);
  }
  cursorLoop();
  $$('a,button,input,.magnetic').forEach(el => {
    el.addEventListener('mouseenter', () => cursor?.classList.add('hot'));
    el.addEventListener('mouseleave', () => cursor?.classList.remove('hot'));
  });
  $$('.magnetic').forEach(el => {
    el.addEventListener('pointermove', e => {
      if(innerWidth < 900) return;
      const r = el.getBoundingClientRect();
      const dx = (e.clientX-r.left-r.width/2)*.12;
      const dy = (e.clientY-r.top-r.height/2)*.12;
      el.style.transform = `translate(${dx}px,${dy}px)`;
    });
    el.addEventListener('pointerleave', () => el.style.transform = '');
  });

  const nav = $('#nav');
  addEventListener('scroll', () => nav?.classList.toggle('scrolled', scrollY > 32), {passive:true});

  // One normalized value drives the whole opening narrative.
  const journey = $('.journey');
  const stages = $$('.stage');
  const stageNames = ['ORIGIN','WORKLOAD','SEARCH','PRESSURE','SYNTHESIS'];
  let journeyP = 0, stageFloat = 0, stageIndex = 0;
  function updateJourney(){
    if(!journey) return;
    const rect = journey.getBoundingClientRect();
    const max = Math.max(1, journey.offsetHeight - innerHeight);
    journeyP = clamp(-rect.top / max, 0, 1);
    stageFloat = journeyP * 4;
    const nextStage = Math.min(4, Math.floor(stageFloat + .5));
    if(nextStage !== stageIndex){
      stageIndex = nextStage;
      stages.forEach((s,i) => s.classList.toggle('active', i===stageIndex));
      $('#navState').textContent = `FIELD / ${stageNames[stageIndex]}`;
      $('#systemMode').textContent = `OBSERVATION / ${stageNames[stageIndex]}`;
      $('#candidateMeta').textContent = stageIndex===2 ? 'POINTER / SELECT CANDIDATE' : stageIndex===4 ? 'STATE / IMPLEMENTATION' : 'OBJECTIVE / ACTIVE';
    }
    $('#journeyProgress').style.height = `${journeyP*100}%`;
  }
  addEventListener('scroll', updateJourney, {passive:true});
  addEventListener('resize', updateJourney);
  updateJourney();

  // Objective gate. Dragging the UI dot also moves the shader objective.
  let objective = 0, objectiveTarget = 0, gateDragging = false, gateStartX = 0;
  const gate = $('#objectiveGate'), gateHandle = $('#objectiveHandle'), gateState = $('#gateState');
  if(gateHandle){
    gateHandle.addEventListener('pointerdown', e => {
      gateDragging = true; gateStartX = e.clientX; gateHandle.setPointerCapture(e.pointerId);
    });
    gateHandle.addEventListener('pointermove', e => {
      if(!gateDragging) return;
      const d = clamp((gateStartX - e.clientX)/110, 0, 1);
      objectiveTarget = d;
      gateHandle.style.transform = `translateX(${-d*92}px)`;
      gateState.textContent = d > .76 ? 'RELEASE TO LOCK' : 'TO ENTER THE FIELD';
    });
    const finishGate = e => {
      if(!gateDragging) return; gateDragging = false;
      if(objectiveTarget > .72){
        objectiveTarget = 1; gate?.classList.add('locked');
        gateState.textContent = 'FIELD ACTIVE';
        gateHandle.style.transform = 'translateX(-92px)';
      } else {
        objectiveTarget = 0; gateHandle.style.transform = ''; gateState.textContent = 'TO ENTER THE FIELD';
      }
      try{gateHandle.releasePointerCapture(e.pointerId)}catch(_){}
    };
    gateHandle.addEventListener('pointerup', finishGate);
    gateHandle.addEventListener('pointercancel', finishGate);
    gateHandle.addEventListener('click', () => {
      if(!gate?.classList.contains('locked')){
        objectiveTarget = 1; gate.classList.add('locked'); gateState.textContent='FIELD ACTIVE'; gateHandle.style.transform='translateX(-92px)';
      }
    });
  }

  // --- WebGL ceramic architecture field ---
  const glCanvas = $('#glCanvas');
  const gl = glCanvas?.getContext('webgl2', {antialias:false, alpha:false, powerPreference:'high-performance'});
  let glProgram = null, glUniforms = {};
  const vertexSrc = `#version 300 es
    in vec2 a_position; void main(){ gl_Position=vec4(a_position,0.,1.); }`;
  const fragSrc = `#version 300 es
    precision highp float;
    out vec4 outColor;
    uniform vec2 u_res;
    uniform vec2 u_mouse;
    uniform float u_time;
    uniform float u_stage;
    uniform float u_obj;

    float smin(float a,float b,float k){ float h=clamp(.5+.5*(b-a)/k,0.,1.); return mix(b,a,h)-k*h*(1.-h); }
    float sdSphere(vec3 p,float r){ return length(p)-r; }
    float sdBox(vec3 p,vec3 b){ vec3 q=abs(p)-b; return length(max(q,0.))+min(max(q.x,max(q.y,q.z)),0.); }
    mat2 rot(float a){ float c=cos(a),s=sin(a); return mat2(c,-s,s,c); }

    vec2 mapScene(vec3 p){
      float s=u_stage;
      float spread=smoothstep(.65,2.2,s);
      float collapse=smoothstep(2.5,3.25,s);
      vec3 p0=p;
      vec3 c1=vec3(-.42,.62,0.); vec3 c2=vec3(-.44,-.63,.0); vec3 c3=vec3(.48,.0,.02); vec3 cc=vec3(-.02,.0,0.);
      c1.xy += vec2(-.18,.16)*spread; c2.xy += vec2(-.18,-.16)*spread; c3.x += .22*spread;
      c1*=1.-collapse*.22; c2*=1.-collapse*.22; c3*=1.-collapse*.22;
      float d=sdSphere(p-c1,.34); d=smin(d,sdSphere(p-c2,.34),.28); d=smin(d,sdSphere(p-c3,.36),.28); d=smin(d,sdSphere(p-cc,.38),.34);
      float rigid=smoothstep(3.15,3.95,s);
      float boxes=sdBox(p-vec3(-.48,.28,0.),vec3(.42,.24,.18));
      boxes=min(boxes,sdBox(p-vec3(.38,.28,0.),vec3(.34,.24,.18)));
      boxes=min(boxes,sdBox(p-vec3(-.25,-.38,0.),vec3(.28,.25,.18)));
      boxes=min(boxes,sdBox(p-vec3(.44,-.38,0.),vec3(.31,.25,.18)));
      d=mix(d,boxes,rigid);
      float ox=mix(1.34,.92,u_obj*.88);
      float od=sdSphere(p-vec3(ox,0.,.08),.15);
      if(od<d) return vec2(od,2.); return vec2(d,1.);
    }
    vec3 normalAt(vec3 p){ float e=.0025; vec2 h=vec2(e,0.); return normalize(vec3(mapScene(p+h.xyy).x-mapScene(p-h.xyy).x,mapScene(p+h.yxy).x-mapScene(p-h.yxy).x,mapScene(p+h.yyx).x-mapScene(p-h.yyx).x)); }
    float raymarch(vec3 ro,vec3 rd,out float mat){ float t=0.; mat=0.; for(int i=0;i<82;i++){ vec2 h=mapScene(ro+rd*t); if(h.x<.0015||t>8.){mat=h.y;break;} t+=h.x*.78; } return t; }
    float hash21(vec2 p){ p=fract(p*vec2(123.34,345.45)); p+=dot(p,p+34.345); return fract(p.x*p.y); }

    void main(){
      vec2 uv=(gl_FragCoord.xy*2.-u_res.xy)/u_res.y;
      vec2 m=(u_mouse-.5)*2.;
      vec3 ro=vec3(0.,0.,4.1); vec3 rd=normalize(vec3(uv,-2.25));
      float yaw=-m.x*.14, pitch=m.y*.1;
      ro.xz*=rot(yaw); rd.xz*=rot(yaw); ro.yz*=rot(pitch); rd.yz*=rot(pitch);
      float mat; float t=raymarch(ro,rd,mat);
      vec3 col=vec3(.035);
      // atmospheric field
      vec2 guv=uv*3.2; vec2 cell=floor(guv); vec2 f=fract(guv)-.5; float h=hash21(cell); float star=smoothstep(.045,0.,length(f))*step(.82,h);
      col += vec3(.24)*star*.25;
      if(t<8.){
        vec3 p=ro+rd*t; vec3 n=normalAt(p);
        vec3 key=normalize(vec3(-.5,.7,.8)); vec3 rim=vec3(pow(1.-max(dot(n,-rd),0.),2.6));
        float diff=max(dot(n,key),0.);
        if(mat>1.5){ col=vec3(1.,.15,.055)*(1.05+.45*diff)+rim*vec3(.6,.08,.02); }
        else{
          vec3 base=mix(vec3(.73,.72,.69),vec3(1.,.985,.94),.48+.52*diff);
          vec3 pearl=vec3(.08,.11,.14)*rim + vec3(.07,.035,.01)*pow(rim.r,2.);
          col=base*(.28+.9*diff)+pearl;
        }
        float ao=clamp(mapScene(p+n*.045).x/.045,0.,1.); col*=.72+.28*ao;
      }
      float vig=1.0-smoothstep(.35,1.55,length(uv*.72)); col*=.48+.52*vig;
      col += vec3(.055,.035,.02)*max(0.,1.-length(uv-vec2(.72,0.))*1.7)*.08;
      outColor=vec4(pow(col,vec3(.92)),1.);
    }`;
  function compile(type,src){ const sh=gl.createShader(type); gl.shaderSource(sh,src); gl.compileShader(sh); if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS)) console.warn(gl.getShaderInfoLog(sh)); return sh; }
  if(gl){
    glProgram=gl.createProgram(); gl.attachShader(glProgram,compile(gl.VERTEX_SHADER,vertexSrc)); gl.attachShader(glProgram,compile(gl.FRAGMENT_SHADER,fragSrc)); gl.linkProgram(glProgram); gl.useProgram(glProgram);
    const buf=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buf); gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
    const loc=gl.getAttribLocation(glProgram,'a_position'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
    ['u_res','u_mouse','u_time','u_stage','u_obj'].forEach(n=>glUniforms[n]=gl.getUniformLocation(glProgram,n));
  } else if(glCanvas){ glCanvas.style.background='radial-gradient(circle at 58% 44%,#2a2925,#090909 60%)'; }
  let shaderMouseX=.5, shaderMouseY=.5, targetMouseX=.5,targetMouseY=.5;
  $('.journey-sticky')?.addEventListener('pointermove',e=>{ targetMouseX=e.clientX/innerWidth; targetMouseY=1-e.clientY/innerHeight; });
  function resizeGL(){ if(!gl) return; const dpr=Math.min(devicePixelRatio||1, innerWidth<700?1:1.35); const w=Math.floor(glCanvas.clientWidth*dpr),h=Math.floor(glCanvas.clientHeight*dpr); if(glCanvas.width!==w||glCanvas.height!==h){glCanvas.width=w;glCanvas.height=h;gl.viewport(0,0,w,h);} }

  // Candidate field over shader
  const nodeCanvas=$('#nodeCanvas'), nctx=nodeCanvas?.getContext('2d');
  const nodes=Array.from({length:96},(_,i)=>({
    id:1000+i*37,
    x:(Math.random()-.5)*1.7,y:(Math.random()-.5)*1.15,z:Math.random()*1.5+.15,
    vx:0,vy:0,phase:Math.random()*6.28,
    area:.18+Math.random()*.78,energy:.18+Math.random()*.78,latency:.16+Math.random()*.8
  }));
  let selectedNode=18;
  function resizeNodes(){ if(!nctx)return; const dpr=Math.min(devicePixelRatio||1,1.5); nodeCanvas.width=nodeCanvas.clientWidth*dpr;nodeCanvas.height=nodeCanvas.clientHeight*dpr;nctx.setTransform(dpr,0,0,dpr,0,0); }
  addEventListener('resize',()=>{resizeGL();resizeNodes();resizePareto();resizeArtifact()}); resizeGL();resizeNodes();
  $('.journey-sticky')?.addEventListener('click',e=>{
    if(stageIndex!==2 || !nctx) return;
    const rect=nodeCanvas.getBoundingClientRect(); const x=e.clientX-rect.left,y=e.clientY-rect.top; let best=-1,bd=30;
    nodes.forEach((n,i)=>{if(!n.sx)return;const d=Math.hypot(n.sx-x,n.sy-y);if(d<bd){bd=d;best=i;}}); if(best>=0){selectedNode=best;showCandidate(nodes[best]);}
  });
  function showCandidate(n){
    $('#candidateId').textContent=`KRN-${n.id}`; $('#candidateArea').textContent=n.area.toFixed(2); $('#candidateEnergy').textContent=n.energy.toFixed(2); $('#candidateLatency').textContent=n.latency.toFixed(2); $('#candidateStatus').textContent=(n.area+n.energy+n.latency)<1.75?'SURVIVING':'DOMINATED';
  }
  showCandidate(nodes[selectedNode]);

  let last=performance.now();
  function render(now){
    const dt=Math.min(.035,(now-last)/1000); last=now;
    objective += (objectiveTarget-objective)*.08;
    shaderMouseX += (targetMouseX-shaderMouseX)*.055; shaderMouseY += (targetMouseY-shaderMouseY)*.055;
    if(gl){ resizeGL(); gl.useProgram(glProgram); gl.uniform2f(glUniforms.u_res,glCanvas.width,glCanvas.height); gl.uniform2f(glUniforms.u_mouse,shaderMouseX,shaderMouseY); gl.uniform1f(glUniforms.u_time,now*.001); gl.uniform1f(glUniforms.u_stage,stageFloat); gl.uniform1f(glUniforms.u_obj,objective); gl.drawArrays(gl.TRIANGLES,0,3); }
    renderNodes(now*.001,dt); renderArtifact(now*.001);
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);

  function renderNodes(t,dt){
    if(!nctx)return; const w=nodeCanvas.clientWidth,h=nodeCanvas.clientHeight; nctx.clearRect(0,0,w,h);
    const presence=1-clamp(Math.abs(stageFloat-2),0,1); if(presence<=.01)return;
    const pointerX=targetMouseX*w,pointerY=(1-targetMouseY)*h;
    const collapse=clamp(stageFloat-2.45,0,1);
    nodes.forEach((n,i)=>{
      const driftX=Math.sin(t*.5+n.phase)*.025,driftY=Math.cos(t*.42+n.phase)*.025;
      const perspective=1/(n.z+.8); let sx=w*.57+(n.x+driftX)*Math.min(w,h)*.48*perspective; let sy=h*.45+(n.y+driftY)*Math.min(w,h)*.48*perspective;
      if(stageIndex===2){ const dx=sx-pointerX,dy=sy-pointerY,d=Math.hypot(dx,dy); if(d<130&&d>0){sx+=dx/d*(130-d)*.09;sy+=dy/d*(130-d)*.09;} }
      sx=lerp(sx,w*.57+((i%8)-3.5)*18,collapse); sy=lerp(sy,h*.46+(Math.floor(i/8)-5.5)*10,collapse);
      n.sx=sx;n.sy=sy; const r=(i===selectedNode?4.6:1.4+2.4*perspective)*(1-collapse*.5); const survivor=(n.area+n.energy+n.latency)<1.75;
      nctx.beginPath();nctx.arc(sx,sy,r,0,Math.PI*2); nctx.fillStyle=i===selectedNode?'rgba(255,72,40,.95)':survivor?`rgba(240,237,230,${(.12+.45*perspective)*presence})`:`rgba(240,237,230,${(.05+.16*perspective)*presence})`;nctx.fill();
      if(i===selectedNode){nctx.beginPath();nctx.arc(sx,sy,13+Math.sin(t*3)*2,0,Math.PI*2);nctx.strokeStyle='rgba(255,72,40,.35)';nctx.stroke();}
    });
    // sparse constellation links
    nctx.lineWidth=.6;
    for(let i=0;i<nodes.length;i+=5){let best=null,bd=120;for(let j=i+1;j<Math.min(nodes.length,i+18);j++){const d=Math.hypot(nodes[i].sx-nodes[j].sx,nodes[i].sy-nodes[j].sy);if(d<bd){bd=d;best=nodes[j]}}if(best){nctx.beginPath();nctx.moveTo(nodes[i].sx,nodes[i].sy);nctx.lineTo(best.sx,best.sy);nctx.strokeStyle=`rgba(240,237,230,${.08*presence})`;nctx.stroke();}}
  }

  // Workload graph perturbs with pointer
  $('#graphMini')?.addEventListener('pointermove', e=>{
    const r=e.currentTarget.getBoundingClientRect(); const x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;
    $$('.graph-mini .n').forEach((n,i)=>n.style.transform=`translate(${x*(i-2)*3}px,${y*((i%2)?-1:1)*5}px)`);
  });
  $('#graphMini')?.addEventListener('pointerleave',()=>$$('.graph-mini .n').forEach(n=>n.style.transform=''));

  // Constraint lab / Pareto model
  const paretoCanvas=$('#paretoCanvas'), pctx=paretoCanvas?.getContext('2d'); const plotTip=$('#plotTip');
  const labPts=Array.from({length:64},(_,i)=>({id:2100+i*17,power:18+Math.random()*82,area:18+Math.random()*82,latency:18+Math.random()*82,energy:18+Math.random()*82}));
  let labW=0,labH=0,hoverPt=-1;
  function resizePareto(){if(!pctx)return;const dpr=Math.min(devicePixelRatio||1,1.5);labW=paretoCanvas.clientWidth;labH=paretoCanvas.clientHeight;paretoCanvas.width=labW*dpr;paretoCanvas.height=labH*dpr;pctx.setTransform(dpr,0,0,dpr,0,0);drawPareto();}
  const ranges=['power','area','latency'];
  function thresholds(){return {power:+$('#powerRange').value,area:+$('#areaRange').value,latency:+$('#latencyRange').value};}
  function drawPareto(){
    if(!pctx||!labW)return; const th=thresholds(); pctx.clearRect(0,0,labW,labH); const pad=58;
    pctx.strokeStyle='rgba(9,9,9,.1)';pctx.lineWidth=1; for(let i=0;i<6;i++){const x=pad+(labW-pad*1.35)*i/5;pctx.beginPath();pctx.moveTo(x,30);pctx.lineTo(x,labH-pad);pctx.stroke();const y=30+(labH-pad-30)*i/5;pctx.beginPath();pctx.moveTo(pad,y);pctx.lineTo(labW-pad*.35,y);pctx.stroke();}
    let survivors=[];labPts.forEach((p,i)=>{const survive=p.power<=th.power&&p.area<=th.area&&p.latency<=th.latency; if(survive)survivors.push(p); const x=pad+p.latency/100*(labW-pad*1.35), y=labH-pad-p.energy/100*(labH-pad-30);p._x=x;p._y=y;p._survive=survive;pctx.beginPath();pctx.arc(x,y,i===hoverPt?6:survive?3.4:2.3,0,Math.PI*2);pctx.fillStyle=i===hoverPt?'#ff4828':survive?'rgba(9,9,9,.68)':'rgba(9,9,9,.13)';pctx.fill();});
    // nondominated frontier among survivors, latency/energy
    const front=survivors.filter(a=>!survivors.some(b=>b!==a&&b.latency<=a.latency&&b.energy<=a.energy&&(b.latency<a.latency||b.energy<a.energy))).sort((a,b)=>a.latency-b.latency);
    if(front.length>1){pctx.beginPath();front.forEach((p,i)=>i?pctx.lineTo(p._x,p._y):pctx.moveTo(p._x,p._y));pctx.strokeStyle='#ff4828';pctx.lineWidth=1.6;pctx.stroke();}
    $('#survivorReadout').textContent=`${survivors.length} / ${labPts.length} SURVIVE`;
  }
  ranges.forEach(name=>{$(`#${name}Range`)?.addEventListener('input',e=>{$(`#${name}Value`).textContent=e.target.value;drawPareto();});});
  paretoCanvas?.addEventListener('pointermove',e=>{const r=paretoCanvas.getBoundingClientRect(),x=e.clientX-r.left,y=e.clientY-r.top;let best=-1,bd=18;labPts.forEach((p,i)=>{const d=Math.hypot(p._x-x,p._y-y);if(d<bd){bd=d;best=i;}});hoverPt=best;if(best>=0){const p=labPts[best];plotTip.innerHTML=`<span>KRN-${p.id}</span><b>PWR ${p.power.toFixed(0)} · AREA ${p.area.toFixed(0)} · LAT ${p.latency.toFixed(0)}${p._survive?' · SURVIVES':' · FILTERED'}</b>`;}else plotTip.innerHTML='<span>KRN-0000</span><b>MOVE OVER A CANDIDATE</b>';drawPareto();});
  paretoCanvas?.addEventListener('pointerleave',()=>{hoverPt=-1;plotTip.innerHTML='<span>KRN-0000</span><b>MOVE OVER A CANDIDATE</b>';drawPareto();});
  setTimeout(resizePareto,100);

  // Instrument interaction
  const dial=$('#instrumentDial'), needle=$('#instrumentDial b'), dialReadout=$('#dialReadout');
  dial?.parentElement.addEventListener('pointermove',e=>{const r=dial.getBoundingClientRect(),dx=e.clientX-(r.left+r.width/2),dy=e.clientY-(r.top+r.height/2),ang=Math.atan2(dy,dx)*180/Math.PI;needle.style.transform=`rotate(${ang}deg)`;const v=clamp(Math.hypot(dx,dy)/(r.width*.5),0,1);dialReadout.textContent=(.21+v*.68).toFixed(3);});

  // Reveal
  const io=new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('seen')}),{threshold:.16}); $$('.reveal').forEach(el=>io.observe(el));

  // Artifact field
  const artifactCanvas=$('#artifactCanvas'), actx=artifactCanvas?.getContext('2d'); let aW=0,aH=0;
  const orbitPts=Array.from({length:90},(_,i)=>({r:.16+Math.random()*.48,a:Math.random()*6.28,s:.04+Math.random()*.09,z:Math.random()}));
  function resizeArtifact(){if(!actx)return;const dpr=Math.min(devicePixelRatio||1,1.5);aW=artifactCanvas.clientWidth;aH=artifactCanvas.clientHeight;artifactCanvas.width=aW*dpr;artifactCanvas.height=aH*dpr;actx.setTransform(dpr,0,0,dpr,0,0)};resizeArtifact();
  function renderArtifact(t){if(!actx||!aW)return;actx.clearRect(0,0,aW,aH);const m=Math.min(aW,aH);orbitPts.forEach((p,i)=>{const a=p.a+t*p.s;const x=aW/2+Math.cos(a)*p.r*m;const y=aH/2+Math.sin(a)*p.r*m*.54;const rr=1+p.z*1.8;actx.beginPath();actx.arc(x,y,rr,0,Math.PI*2);actx.fillStyle=i%17===0?'rgba(255,72,40,.68)':`rgba(240,237,230,${.07+p.z*.22})`;actx.fill();});}
})();