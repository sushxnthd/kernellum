(()=>{'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v)),lerp=(a,b,t)=>a+(b-a)*t;
const reduce=matchMedia('(prefers-reduced-motion:reduce)'),mobile=matchMedia('(max-width:58.749rem)');
const boonEase=t=>{const x1=.5,y1=.1,x2=0,y2=1,sample=(u,a1,a2)=>3*(1-u)*(1-u)*u*a1+3*(1-u)*u*u*a2+u*u*u,deriv=(u,a1,a2)=>3*(1-u)*(1-u)*a1+6*(1-u)*u*(a2-a1)+3*u*u*(1-a2);let u=t;for(let i=0;i<6;i++){const d=deriv(u,x1,x2);if(Math.abs(d)<1e-6)break;u=clamp(u-(sample(u,x1,x2)-t)/d)}let lo=0,hi=1;for(let i=0;i<8;i++){const x=sample(u,x1,x2);if(Math.abs(x-t)<1e-6)break;if(x<t)lo=u;else hi=u;u=(lo+hi)/2}return sample(u,y1,y2)};
class ParticleField{
  constructor(canvas){
    this.canvas=canvas;
    this.gl=canvas.getContext('webgl2',{alpha:true,antialias:true,premultipliedAlpha:true});
    this.shape='none';this.target='none';this.duration=1500;this.morphing=false;this.transition=0;
    this.parallax=0;this.parallaxFrom=0;this.parallaxTo=0;this.start=0;
    this.mouseX=0;this.mouseY=0;this.targetMouseX=0;this.targetMouseY=0;
    this.image=null;this.imageReady=false;this.count=0;
    if(!this.gl){this.disabled=true;return}
    this.initGL();
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
      'uniform float uBaseSize;','uniform float uTime;','uniform vec2 uViewport;','uniform vec2 uMouse;',
      'uniform float uParallaxStrength;','uniform float uTransition;',
      'in vec3 aPosition;','in vec3 aTargetPosition;','in float aScale;','in float aTargetScale;','in float aRandom;',
      'out float vScale;','out float vIntensity;',
      'void main(){',
      'vec3 finalPos=mix(aPosition,aTargetPosition,uTransition);',
      'float pathArc=sin(uTransition*3.141592653589793);',
      'float rand1=aRandom;','float rand2=fract(aRandom*123.456);',
      'finalPos.x+=(rand1-0.5)*250.0*pathArc;','finalPos.y+=(rand2-0.5)*250.0*pathArc;',
      'finalPos.xy+=uMouse*finalPos.z*4.0*uParallaxStrength;',
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
      time:g.getUniformLocation(p,'uTime'),viewport:g.getUniformLocation(p,'uViewport'),
      mouse:g.getUniformLocation(p,'uMouse'),parallax:g.getUniformLocation(p,'uParallaxStrength'),
      transition:g.getUniformLocation(p,'uTransition'),baseColor:g.getUniformLocation(p,'uBaseColor'),
      highlight:g.getUniformLocation(p,'uHighlightColor')
    };
    this.buffers={pos:g.createBuffer(),target:g.createBuffer(),scale:g.createBuffer(),targetScale:g.createBuffer(),random:g.createBuffer()};
    g.enable(g.BLEND);g.blendFunc(g.SRC_ALPHA,g.ONE_MINUS_SRC_ALPHA);g.disable(g.DEPTH_TEST);
    g.uniform1f(this.loc.baseSize,18);g.uniform3f(this.loc.baseColor,49/255,44/255,33/255);g.uniform3f(this.loc.highlight,227/255,70/255,8/255);
  }
  bindBuffer(name,data,size){
    if(this.disabled)return;const g=this.gl,b=this.buffers[name],loc=this.loc[name];
    g.bindBuffer(g.ARRAY_BUFFER,b);g.bufferData(g.ARRAY_BUFFER,data,g.DYNAMIC_DRAW);g.enableVertexAttribArray(loc);g.vertexAttribPointer(loc,size,g.FLOAT,false,0,0);
  }
  uploadAll(){this.bindBuffer('pos',this.positions,3);this.bindBuffer('target',this.targetPositions,3);this.bindBuffer('scale',this.scales,1);this.bindBuffer('targetScale',this.targetScales,1);this.bindBuffer('random',this.random,1)}
  loadImage(){
    const im=new Image();im.crossOrigin='anonymous';im.src='/kernellum/boon-rebuild/assets/particle-image.png?v=2';
    im.onload=()=>{this.image=im;this.imageReady=true;if(this.target==='image')this.set('image',false,true)};
  }
  resize(){
    if(this.disabled)return;
    const dpr=Math.min(devicePixelRatio||1,2),w=innerWidth,h=innerHeight,g=this.gl;this.w=w;this.h=h;this.dpr=dpr;
    this.canvas.width=Math.floor(w*dpr);this.canvas.height=Math.floor(h*dpr);this.canvas.style.width=w+'px';this.canvas.style.height=h+'px';g.viewport(0,0,this.canvas.width,this.canvas.height);
    this.gap=13.5;this.cols=Math.ceil(w/this.gap)+1;this.rows=Math.ceil(h/this.gap)+1;this.count=this.cols*this.rows;
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
  build(shape){if(shape==='grid')return this.makeGrid();if(shape==='rings-horizontal')return this.makeHorizontal();if(shape==='rings-vertical')return this.makeVertical();if(shape==='image')return this.makeImage();return this.makeNone()}
  transitionValue(now=performance.now()){if(!this.morphing)return this.transition;const raw=clamp((now-this.start)/this.duration);return boonEase(raw)}
  bake(now=performance.now()){
    if(!this.morphing)return;const t=this.transitionValue(now),arc=Math.sin(t*Math.PI);
    for(let i=0;i<this.count;i++){const j=i*3,r=this.random[i],r2=(r*123.456)%1;this.positions[j]=lerp(this.positions[j],this.targetPositions[j],t)+(r-.5)*250*arc;this.positions[j+1]=lerp(this.positions[j+1],this.targetPositions[j+1],t)+(r2-.5)*250*arc;this.positions[j+2]=lerp(this.positions[j+2],this.targetPositions[j+2],t);this.scales[i]=lerp(this.scales[i],this.targetScales[i],t)}
    this.transition=0;this.morphing=false;this.bindBuffer('pos',this.positions,3);this.bindBuffer('scale',this.scales,1);
  }
  set(shape,instant=false,force=false){
    if(this.disabled)return;if(shape===this.target&&!force)return;if(this.morphing)this.bake();this.target=shape;const next=this.build(shape);
    if(instant||reduce.matches){this.positions=next.positions;this.scales=next.scales;this.targetPositions=new Float32Array(next.positions);this.targetScales=new Float32Array(next.scales);this.random=new Float32Array(this.count);for(let i=0;i<this.count;i++)this.random[i]=Math.random();this.parallax=(shape==='grid'||shape==='rings-horizontal'||shape==='rings-vertical')?1:0;this.parallaxFrom=this.parallaxTo=this.parallax;this.transition=0;this.morphing=false;this.uploadAll();this.shape=shape;return}
    this.targetPositions=next.positions;this.targetScales=next.scales;this.bindBuffer('target',this.targetPositions,3);this.bindBuffer('targetScale',this.targetScales,1);this.parallaxFrom=this.parallax;this.parallaxTo=(shape==='grid'||shape==='rings-horizontal'||shape==='rings-vertical')?1:0;this.start=performance.now();this.transition=0;this.morphing=true;this.shape=shape;
  }
  draw(now,dt){
    if(this.disabled)return;const g=this.gl;g.useProgram(this.program);this.mouseX=lerp(this.mouseX,this.targetMouseX,1-Math.exp(-5*dt));this.mouseY=lerp(this.mouseY,this.targetMouseY,1-Math.exp(-5*dt));
    let t=this.morphing?this.transitionValue(now):this.transition;
    if(this.morphing){const raw=clamp((now-this.start)/this.duration);this.parallax=lerp(this.parallaxFrom,this.parallaxTo,t);if(raw>=1){this.positions=new Float32Array(this.targetPositions);this.scales=new Float32Array(this.targetScales);this.bindBuffer('pos',this.positions,3);this.bindBuffer('scale',this.scales,1);this.transition=0;t=0;this.morphing=false;this.parallax=this.parallaxTo}}
    g.clearColor(0,0,0,0);g.clear(g.COLOR_BUFFER_BIT);g.uniform1f(this.loc.time,now*.001);g.uniform2f(this.loc.viewport,this.w,this.h);g.uniform2f(this.loc.mouse,this.mouseX,this.mouseY);g.uniform1f(this.loc.parallax,this.parallax);g.uniform1f(this.loc.transition,t);g.drawArrays(g.POINTS,0,this.count);
  }
}

const base='/kernellum/boon-rebuild/';
const header=$('#header'),btn=$('.expand-btn',header),panel=$('.expand-menu',header),label=$('.expand-btn p',header),navBar=$('.nav-bar',header);
if(navBar){navBar.style.opacity='1';if(!reduce.matches)navBar.animate([{transform:'translateY(-100%)',opacity:0},{transform:'translateY(0)',opacity:1}],{duration:850,easing:'cubic-bezier(.215,.61,.355,1)',fill:'both'})}
function scramble(text){if(!label)return;const chars='░▒▓■□',start=performance.now();function f(now){const p=clamp((now-start)/300),fixed=Math.floor(text.length*p);label.textContent=[...text].map((c,i)=>i<fixed?c:chars[(Math.random()*chars.length)|0]).join('');if(p<1)requestAnimationFrame(f);else label.textContent=text}requestAnimationFrame(f)}
function setMenu(open){if(!panel||!btn)return;btn.classList.toggle('open',open);header?.classList.toggle('menu-expanded',open);btn.setAttribute('aria-expanded',String(open));panel.setAttribute('aria-hidden',String(!open));const from=panel.getBoundingClientRect().height,to=open?panel.scrollHeight:0;panel.getAnimations().forEach(a=>a.cancel());const a=panel.animate([{maxHeight:from+'px'},{maxHeight:to+'px'}],{duration:500,easing:'cubic-bezier(.5,.1,0,1)',fill:'forwards'});a.onfinish=()=>{panel.style.maxHeight=to+'px';a.cancel()};scramble(open?'Close':'Menu')}
btn?.addEventListener('click',()=>setMenu(btn.getAttribute('aria-expanded')!=='true'));
document.addEventListener('pointerdown',e=>{if(header&&header.classList.contains('menu-expanded')&&!header.contains(e.target))setMenu(false)});

const hrefMap=new Map([['/','/kernellum/boon-rebuild/'],['/what-we-do/','/kernellum/boon-rebuild/what-we-do/'],['/who-we-are/','/kernellum/boon-rebuild/who-we-are/'],['/contact/','/kernellum/boon-rebuild/contact/'],['/careers/','/kernellum/boon-rebuild/careers/'],['/legal/privacy-policy/','https://github.com/sushxnthd/kernellum'],['https://www.linkedin.com/company/boon-io/','https://github.com/sushxnthd/kernellum']]);
$$('a[href]').forEach(a=>{const h=a.getAttribute('href');if(hrefMap.has(h))a.setAttribute('href',hrefMap.get(h))});
const footerLogo=$('#footer a.logo');if(footerLogo){footerLogo.href=base;footerLogo.setAttribute('aria-label','Kernellum');footerLogo.innerHTML='<svg viewBox="0 0 89 24" role="img"><text x="44.5" y="16.8" text-anchor="middle" fill="currentColor" font-family="MSCHN,sans-serif" font-size="11.4" font-weight="600" letter-spacing=".35">KERNELLUM</text></svg>'}

function splitLines(el){
 if(!el||el.dataset.split)return[];el.dataset.split='1';
 const text=el.textContent.trim(),words=text.split(/\s+/);el.textContent='';
 const probes=[];words.forEach((word,i)=>{const w=document.createElement('span');w.textContent=word;w.style.cssText='display:inline-block;white-space:nowrap';el.appendChild(w);probes.push(w);if(i<words.length-1)el.append(' ')});
 const rows=[];let top=null,row=[];probes.forEach(w=>{const y=Math.round(w.offsetTop);if(top===null||Math.abs(y-top)<=1)row.push(w.textContent);else{rows.push(row);row=[w.textContent]}top=y});if(row.length)rows.push(row);
 el.innerHTML=rows.map(r=>'<span class="line k-line"><span>'+r.join(' ')+'</span></span>').join('');return $$('.k-line>span',el)
}
const headerSec=$('.page-header'),headerTitle=$('.page-header .title'),headerLines=splitLines(headerTitle),headerWraps=$$('.page-header .images>.image-wrapper'),headerImgs=$$('.page-header .images>.image-wrapper img'),subtitle=$('.page-header .subtitle'),headerCta=$('.page-header .scroll');
const headerType=headerSec?.dataset.headerType||'center';

const largeSections=$$('.large-text');largeSections.forEach(sec=>{const h=$('h2',sec);if(h){const html=h.innerHTML;h.textContent=h.textContent;const lines=splitLines(h);sec._lines=lines;if(html.includes('<mark>')){const phrase=(html.match(/<mark>(.*?)<\/mark>/)||[])[1];if(phrase){lines.forEach(line=>{if(line.textContent.includes(phrase.split(' ')[0]))line.innerHTML=line.innerHTML.replace(phrase,'<mark>'+phrase+'</mark>')})}}if(!reduce.matches)lines.forEach(l=>l.style.transform='translateY(100%)')}});

const cards=$$('.card-grid .cards');cards.forEach(list=>{const cs=$$('li.card',list);cs.forEach((c,i)=>{if(!reduce.matches)c.style.transform='translateY('+(100+i*50)+'px)'});list._cards=cs;list.classList.remove('pre-anim')});

$$('.accordion-row').forEach(row=>{const tab=$('.tab',row),drawer=$('.drawer',row);tab?.addEventListener('click',()=>{const open=!row.classList.contains('open');$$('.accordion-row.open').forEach(other=>{if(other!==row){other.classList.remove('open');const d=$('.drawer',other);if(d)d.style.maxHeight='0px';$('.tab',other)?.setAttribute('aria-expanded','false')}});row.classList.toggle('open',open);tab.setAttribute('aria-expanded',String(open));drawer.inert=!open;const to=open?drawer.scrollHeight:0;drawer.animate([{maxHeight:drawer.getBoundingClientRect().height+'px'},{maxHeight:to+'px'}],{duration:500,easing:'cubic-bezier(.5,.1,0,1)',fill:'forwards'}).onfinish=()=>drawer.style.maxHeight=open?'none':'0px'})});

const form=$('#kernellum-contact');form?.addEventListener('submit',e=>{e.preventDefault();const fd=new FormData(form),title='Kernellum contact: '+(fd.get('reason')||'Research discussion'),body=['Name: '+fd.get('name'),'Email: '+fd.get('email'),'','Message:',fd.get('message')].join('\n');location.href='https://github.com/sushxnthd/kernellum/issues/new?title='+encodeURIComponent(title)+'&body='+encodeURIComponent(body)});

const revealIO=new IntersectionObserver(entries=>entries.forEach(e=>{if(!e.isIntersecting||e.target.dataset.revealed)return;e.target.dataset.revealed='1';e.target.animate([{opacity:0,transform:'translateY(20px)'},{opacity:1,transform:'translateY(0)'}],{duration:850,easing:'cubic-bezier(.165,.84,.44,1)',fill:'both'})}),{rootMargin:'0px 0px -20% 0px',threshold:.01});
$$('.text-intro p,.text-media .block-text>* ,.form-block .section-header>* ,.testimonial-block blockquote,.testimonial-block cite').forEach(el=>revealIO.observe(el));

const canvas=$('.three-canvas'),particles=canvas?new ParticleField(canvas):null;
const focus=$$('[data-particles]').map(el=>[el,el.dataset.particles]).filter(x=>x[1]);
let focusEl=null,lastY=scrollY,lastToggle=scrollY,lastTime=performance.now(),smoothY=scrollY;
function chooseFocus(){if(!particles)return;const vh=innerHeight,line=vh*(scrollY>lastY?.4:scrollY<lastY?.6:.5);let best=null,score=-1;focus.forEach(([el,shape])=>{const r=el.getBoundingClientRect(),vis=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));if(vis<vh*.05)return;const ratio=vis/Math.min(vh,r.height),d=(r.top<=line&&r.bottom>=line)?0:Math.min(Math.abs(r.top-line),Math.abs(r.bottom-line)),center=1-Math.min(1,d/vh),s=ratio*.6+center*.4;if(s>score){score=s;best=[el,shape]}});if(best&&best[0]!==focusEl){focusEl=best[0];particles.set(best[1])}}
function frame(now){
 const dt=Math.min(.05,(now-lastTime)/1000);lastTime=now;const y=scrollY,dir=Math.sign(y-lastY),vh=innerHeight;smoothY=lerp(smoothY,y,1-Math.exp(-8*dt));
 if(header){let visible=header.classList.contains('visible'),hh=header.offsetHeight;if(y<hh)visible=true;else if(Math.abs(y-lastToggle)>=50){visible=dir<0;lastToggle=y}header.classList.toggle('visible',visible);header.style.transform=visible?'translateY(0)':'translateY(-150%)'}
 if(headerSec&&!reduce.matches){const p=clamp(smoothY/vh);if(headerType==='left'){if(headerWraps[1])headerWraps[1].style.transform='translateX('+(-25*p)+'%)';if(headerImgs[1])headerImgs[1].style.transform='translateX('+(12.5*p)+'%)';if(headerWraps[2])headerWraps[2].style.transform='translateX('+(-25*p)+'%)';if(headerImgs[2])headerImgs[2].style.transform='translateX('+(12.5*p)+'%)'}else{if(headerWraps[1])headerWraps[1].style.transform='translateX('+(-25*p)+'%)';if(headerImgs[1])headerImgs[1].style.transform='translateX('+(12.5*p)+'%)';if(headerWraps[2])headerWraps[2].style.transform='translateX('+(25*p)+'%)';if(headerImgs[2])headerImgs[2].style.transform='translateX('+(-12.5*p)+'%)'}headerLines.forEach(l=>l.style.transform='translateY('+(-250*p)+'%)');if(headerImgs[0])headerImgs[0].style.transform='scale('+(1+.15*p)+')';if(subtitle){subtitle.style.opacity=String(Math.max(0,1-1.5*p));if(!mobile.matches)subtitle.style.transform='translateX('+(-5*p)+'vw)'}if(headerCta){headerCta.style.opacity=String(Math.max(0,1-1.5*p));if(!mobile.matches)headerCta.style.transform='translateX('+(5*p)+'vw)'}}
 cards.forEach(list=>{const r=list.getBoundingClientRect(),p=clamp((vh-r.top)/(vh*.65));(list._cards||[]).forEach((c,i)=>{const lp=clamp((p-i*(150/800)*.35)/(1-i*.035)),e=1-Math.pow(1-lp,3);c.style.transform='translateY('+((100+i*50)*(1-e))+'px)'})});
 largeSections.forEach(sec=>{const r=sec.getBoundingClientRect(),p=clamp((vh-r.bottom)/(vh*.5));(sec._lines||[]).forEach(l=>l.style.transform='translateY('+(100*(1-p))+'%)')});
 chooseFocus();particles?.draw(now,dt);lastY=y;requestAnimationFrame(frame)
}
requestAnimationFrame(frame);
})();