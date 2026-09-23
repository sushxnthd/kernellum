(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const lerp=(a,b,t)=>a+(b-a)*t;
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const out=t=>1-Math.pow(1-t,3);
const boonEase=t=>{
  // cubic-bezier(.5,.1,0,1): invert x(s) with Newton + bisection, return y(s)
  const x1=.5,y1=.1,x2=0,y2=1;
  const sample=(u,a1,a2)=>3*(1-u)*(1-u)*u*a1+3*(1-u)*u*u*a2+u*u*u;
  const deriv=(u,a1,a2)=>3*(1-u)*(1-u)*a1+6*(1-u)*u*(a2-a1)+3*u*u*(1-a2);
  let u=t;
  for(let i=0;i<6;i++){const d=deriv(u,x1,x2);if(Math.abs(d)<1e-6)break;u=clamp(u-(sample(u,x1,x2)-t)/d)}
  let lo=0,hi=1;
  for(let i=0;i<8;i++){const x=sample(u,x1,x2);if(Math.abs(x-t)<1e-6)break;if(x<t)lo=u;else hi=u;u=(lo+hi)/2}
  return sample(u,y1,y2);
};
const mobile=matchMedia('(max-width:58.749rem)');
const reduce=matchMedia('(prefers-reduced-motion:reduce)');

/* ---------- source-geometry header reconstruction ---------- */
const header=$('#header');
if(header){
  const menuDotPatterns={
    static:[[1,1],[2,1],[3,1],[4,1],[1,2],[2,2],[3,2],[4,2],[1,3],[2,3],[3,3],[4,3]],
    hover:[[1,1],[2,1],[3,1],[4,1],[1,2],[4,2],[1,3],[2,3],[3,3],[4,3]],
    close:[[1,1],[4,1],[2,2],[3,2],[1,3],[4,3]]
  };
  const dotGrid=pattern=>'<div class="dot-grid" data-v-c777a272 aria-hidden="true">'+
    menuDotPatterns[pattern].map(([c,r])=>'<div class="dot" data-v-c777a272 style="grid-column-start:'+c+';grid-row-start:'+r+'"></div>').join('')+
    '</div>';
  header.innerHTML=`
    <div class="nav-bar">
      <a class="logo" href="#home" aria-label="Kernellum">
        <svg viewBox="0 0 89 24" role="img" aria-label="Kernellum">
          <text x="44.5" y="16.8" text-anchor="middle" fill="currentColor" font-family="MSCHN, sans-serif" font-size="11.4" font-weight="600" letter-spacing=".35">KERNELLUM</text>
        </svg>
      </a>
      <button class="expand-btn" type="button" aria-expanded="false">
        <p>MENU</p><span class="k-menu-grid">${dotGrid('static')}</span>
      </button>
      <div class="expand-menu" aria-hidden="true">
        <nav aria-label="Primary">
          <ul>
            <li><a href="/kernellum/">Home</a></li>
            <li><a href="/kernellum/what-we-do/">What We Do</a></li>
            <li><a href="/kernellum/who-we-are/">Who We Are</a></li>
            <li><a href="/kernellum/careers/">Careers</a></li>
            <li><a href="/kernellum/contact/">Contact</a></li>
          </ul>
        </nav>
      </div>
    </div>`;
  const btn=$('.expand-btn',header),label=$('p',btn),panel=$('.expand-menu',header),navBar=$('.nav-bar',header);
  const menuGridHost=$('.k-menu-grid',header);
  let menuGridToken=0;
  const setMenuGrid=(pattern,instant=false)=>{
    if(!menuGridHost)return;
    const token=++menuGridToken;
    if(instant||reduce.matches){menuGridHost.innerHTML=dotGrid(pattern);return}
    const oldDots=$$('.dot',menuGridHost),order=oldDots.map((_,i)=>i).sort(()=>Math.random()-.5);
    oldDots.forEach((dot,i)=>dot.animate(
      [{opacity:1},{opacity:0},{opacity:1},{opacity:.5},{opacity:0}],
      {duration:300,delay:order.indexOf(i)*25,easing:'steps(2,end)',fill:'forwards'}
    ));
    setTimeout(()=>{
      if(token!==menuGridToken)return;
      menuGridHost.innerHTML=dotGrid(pattern);
      const dots=$$('.dot',menuGridHost),next=dots.map((_,i)=>i).sort(()=>Math.random()-.5);
      dots.forEach((dot,i)=>dot.animate(
        [{opacity:0},{opacity:1},{opacity:0},{opacity:.5},{opacity:1}],
        {duration:375,delay:next.indexOf(i)*25,easing:'steps(2,end)',fill:'forwards'}
      ));
    },150);
  };
  header.classList.add('visible');
  if(navBar&&!reduce.matches){
    navBar.animate(
      [{transform:'translateY(-100%)',opacity:0},{transform:'translateY(0)',opacity:1}],
      {duration:850,easing:'cubic-bezier(.215,.61,.355,1)',fill:'both'}
    );
  }
  const scramble=text=>{
    if(reduce.matches){label.textContent=text;return}
    const chars='░▒▓■□',start=performance.now(),dur=300;
    const f=now=>{const p=clamp((now-start)/dur),fixed=Math.floor(text.length*p);label.textContent=[...text].map((c,i)=>i<fixed?c:chars[(Math.random()*chars.length)|0]).join('');if(p<1)requestAnimationFrame(f);else label.textContent=text};requestAnimationFrame(f)
  };
  const setOpen=open=>{
    header.classList.toggle('k-expanded',open);
    header.classList.toggle('menu-expanded',open);
    btn.classList.toggle('open',open);
    btn.setAttribute('aria-expanded',String(open));
    panel.setAttribute('aria-hidden',String(!open));
    const from=panel.getBoundingClientRect().height;
    const to=open?panel.scrollHeight:0;
    panel.getAnimations().forEach(a=>a.cancel());
    const a=panel.animate(
      [{maxHeight:from+'px'},{maxHeight:to+'px'}],
      {duration:500,easing:'cubic-bezier(.5,.1,0,1)',fill:'forwards'}
    );
    a.onfinish=()=>{panel.style.maxHeight=to+'px';a.cancel()};
    setMenuGrid(open?'close':'static');
    scramble(open?'CLOSE':'MENU');
  };
  btn.addEventListener('click',()=>setOpen(!header.classList.contains('k-expanded')));
  btn.addEventListener('pointerenter',()=>{if(!header.classList.contains('k-expanded'))setMenuGrid('hover')});
  btn.addEventListener('pointerleave',()=>{if(!header.classList.contains('k-expanded'))setMenuGrid('static')});
  $$('.expand-menu a',header).forEach(a=>a.addEventListener('click',()=>setOpen(false)));
  document.addEventListener('pointerdown',e=>{if(header.classList.contains('k-expanded')&&!header.contains(e.target))setOpen(false)});
  addEventListener('resize',()=>{if(header.classList.contains('k-expanded'))panel.style.maxHeight=(panel.scrollHeight+32)+'px'},{passive:true});

  const blinkDots=(host,show=true)=>{
    const dots=$$('.dot, i',host);if(!dots.length)return;
    const order=dots.map((_,i)=>i).sort(()=>Math.random()-.5);
    dots.forEach((dot,i)=>{
      dot.getAnimations().forEach(a=>a.cancel());
      const delay=order.indexOf(i)*25;
      if(show){
        dot.animate(
          [{opacity:0},{opacity:1},{opacity:0},{opacity:1},{opacity:.5},{opacity:1}],
          {duration:375,delay,easing:'steps(2,end)',fill:'forwards'}
        );
      }else{
        dot.animate([{opacity:getComputedStyle(dot).opacity},{opacity:0}],
          {duration:180,delay:(dots.length-1-order.indexOf(i))*10,easing:'steps(2,end)',fill:'forwards'});
      }
    });
  };
  $$('.expand-menu a',header).forEach(a=>{
    const text=a.textContent.trim();
    a.innerHTML='<span class="k-nav-pips" aria-hidden="true"><i></i><i></i></span><span>'+text+'</span><span class="k-nav-pips" aria-hidden="true"><i></i><i></i></span>';
    a.addEventListener('pointerenter',()=>$$('.k-nav-pips',a).forEach(x=>blinkDots(x,true)));
    a.addEventListener('pointerleave',()=>$$('.k-nav-pips',a).forEach(x=>blinkDots(x,false)));
  });
  $$('.logo,.expand-btn,.expand-menu',header).forEach(surface=>{
    surface.classList.add('k-hover-surface');
    surface.addEventListener('pointermove',e=>{
      const r=surface.getBoundingClientRect();
      surface.style.setProperty('--krn-hover-x',((e.clientX-r.left)/r.width*100)+'%');
      surface.style.setProperty('--krn-hover-y',((e.clientY-r.top)/r.height*100)+'%');
    },{passive:true});
  });
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
  const heroLines=$$('.k-line>span',heroTitle);
  if(heroLines[1])heroLines[1].style.textIndent='20vw';
  heroImgs.forEach(im=>im.style.opacity='1');
}

const centered=$$('section.centered-text');
const lineOriginals=new WeakMap();
function groupRenderedWords(root){
  const words=$$('.k-measure-word',root);
  const groups=[];
  let top=null,current=null;
  words.forEach(w=>{
    const y=Math.round(w.offsetTop*2)/2;
    if(top===null||Math.abs(y-top)>1){top=y;current=[];groups.push(current)}
    current.push(w);
  });
  return groups;
}
function tokeniseForMeasure(root){
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);
  nodes.forEach(node=>{
    const frag=document.createDocumentFragment();
    const pieces=(node.nodeValue||'').split(/(\s+)/);
    pieces.forEach(piece=>{
      if(!piece)return;
      if(/^\s+$/.test(piece)){
        const nl=(piece.match(/\n/g)||[]).length;
        if(nl){
          for(let i=0;i<nl;i++)frag.appendChild(document.createElement('br'));
        }else frag.appendChild(document.createTextNode(' '));
      }else{
        const w=document.createElement('span');
        w.className='k-measure-word';
        w.style.display='inline-block';
        w.style.whiteSpace='nowrap';
        w.textContent=piece;
        frag.appendChild(w);
      }
    });
    node.replaceWith(frag);
  });
}
function splitPlainRenderedLines(el,transform='101%'){
  if(!el)return[];
  if(!lineOriginals.has(el))lineOriginals.set(el,{type:'text',value:el.textContent.trim()});
  const original=lineOriginals.get(el).value;
  el.textContent=original;
  tokeniseForMeasure(el);
  const groups=groupRenderedWords(el);
  const html=groups.map(g=>'<span class="line k-line"><span>'+g.map(w=>w.textContent).join(' ')+'</span></span>').join('');
  el.innerHTML=html;
  const lines=$$('.k-line>span',el);
  if(!reduce.matches)lines.forEach(l=>l.style.transform='translateY('+transform+')');
  return lines;
}
function splitRichRenderedLines(el,transform='100%'){
  if(!el)return[];
  if(!lineOriginals.has(el))lineOriginals.set(el,{type:'html',value:el.innerHTML});
  const original=lineOriginals.get(el).value;
  el.innerHTML=original;
  tokeniseForMeasure(el);
  const groups=groupRenderedWords(el);
  const out=groups.map(g=>{
    const content=g.map((w,i)=>{
      const word=w.textContent;
      const marked=!!w.closest('mark');
      const token=marked?'<mark>'+word+'</mark>':word;
      return (i?' ':'')+token;
    }).join('');
    return '<span class="line k-line"><span>'+content+'</span></span>';
  }).join('');
  el.innerHTML=out;
  const lines=$$('.k-line>span',el);
  if(!reduce.matches)lines.forEach(l=>l.style.transform='translateY('+transform+')');
  return lines;
}
function prepareCenteredLines(){
  centered.forEach((sec,i)=>{
    if(i===1)sec.id='difference';
    const main=$('.main-text',sec);if(!main)return;
    sec._kLines=splitPlainRenderedLines(main,'101%');
  });
}
prepareCenteredLines();
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(prepareCenteredLines);
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
cards.forEach((c,i)=>{if(!reduce.matches)c.style.transform=`translateY(${100+i*50}px)`;});

/* draw Kernellum signal-green animated research marks into the existing lottie canvases */
$$('.card-grid .lottie-canvas canvas').forEach((cv,idx)=>{
  const ctx=cv.getContext('2d');let start=performance.now();
  const draw=now=>{if(!cv.isConnected)return;
    const r=cv.getBoundingClientRect(),dpr=Math.min(devicePixelRatio||1,2),w=Math.max(1,Math.round(r.width*dpr)),h=Math.max(1,Math.round(r.height*dpr));
    if(cv.width!==w||cv.height!==h){cv.width=w;cv.height=h}ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,r.width,r.height);
    const cx=r.width/2,cy=r.height/2,R=Math.min(r.width,r.height)*.36,t=(now-start)*.001;
    ctx.strokeStyle=getComputedStyle(document.documentElement).getPropertyValue('--clr-primary').trim()||'#b9f35d';ctx.lineWidth=1;
    ctx.beginPath();ctx.arc(cx,cy,R,0,Math.PI*2);ctx.stroke();
    ctx.setLineDash([1.5,4]);
    ctx.beginPath();ctx.arc(cx,cy,R*(idx===0?.58:idx===1?.7:.8),t*(idx+1)*.35,t*(idx+1)*.35+Math.PI*1.7);ctx.stroke();ctx.setLineDash([]);
    if(idx===1){ctx.beginPath();ctx.arc(cx,cy,R*.28,0,Math.PI*2);ctx.stroke()}
    if(idx===2){ctx.beginPath();ctx.moveTo(cx-R*.38,cy);ctx.lineTo(cx+R*.38,cy);ctx.stroke()}
    requestAnimationFrame(draw)
  };requestAnimationFrame(draw)
});


/* Kernellum card motion stays local so all animated accents inherit --clr-primary. */
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
if(sockH){sockH.innerHTML=`<span class="line k-line"><span>${sockH.textContent.trim()}</span></span>`}

/* minimal visible brand substitutions, no geometry changes */
document.title='Kernellum';
$$('.text-label').forEach(el=>{if(/boon difference/i.test(el.textContent))el.textContent='The Kernellum Difference'});
$$('p,h1,h2,h3,h4,h5,span,a').forEach(el=>{
  if(el.children.length===0){
    el.textContent=el.textContent.replace(/\bBOON\b/g,'KERNELLUM').replace(/\bBoon\b/g,'Kernellum');
  }
});
const footerLogo=$('footer#footer a.logo');
if(footerLogo){
  footerLogo.setAttribute('aria-label','Kernellum');
  footerLogo.href='/kernellum/';
  footerLogo.innerHTML='<svg viewBox="0 0 89 24" role="img" aria-label="Kernellum"><text x="44.5" y="16.8" text-anchor="middle" fill="currentColor" font-family="MSCHN, sans-serif" font-size="11.4" font-weight="600" letter-spacing=".35">KERNELLUM</text></svg>';
}
const hrefMap=new Map([
  ['/what-we-do/','/kernellum/what-we-do/'],
  ['/who-we-are/','/kernellum/who-we-are/'],
  ['/contact/','/kernellum/contact/'],
  ['/careers/','/kernellum/careers/'],
  ['/legal/privacy-policy/','https://github.com/sushxnthd/kernellum'],
  ['https://www.linkedin.com/company/boon-io/','https://github.com/sushxnthd/kernellum']
]);
$$('a[href]').forEach(a=>{const h=a.getAttribute('href');if(hrefMap.has(h)){a.setAttribute('href',hrefMap.get(h));if(a.getAttribute('href').startsWith('https://github.com/')){a.target='_blank';a.rel='noopener noreferrer'}}});
const footer=$('footer#footer');
if(footer){
  const exactText=(from,to)=>$$('a,span',footer).forEach(el=>{if(el.children.length===0&&el.textContent.trim()===from)el.textContent=to});
  exactText('LinkedIn','GitHub');
  exactText('Privacy Policy','Repository');
  exactText('ISO/IEC 27001 Cert.','Public Evidence');
  exactText('Join Us','Research');
  $$('a',footer).forEach(a=>{
    const label=a.textContent.trim();
    if(label==='GitHub'||label==='Repository'||label==='Public Evidence'||label==='Research'){
      a.href='https://github.com/sushxnthd/kernellum';
      a.target='_blank';
      a.rel='noopener noreferrer';
    }
  });
}

/* ---------- Kernellum microinteractions ---------- */
const animateFooterDotIcon=(icon,show)=>{
  const dots=$$('.dot',icon);if(!dots.length)return;
  const order=dots.map((_,i)=>i);
  dots.forEach((dot,i)=>{
    dot.getAnimations().forEach(a=>a.cancel());
    const delay=order[i]*25;
    if(show){
      dot.animate(
        [{opacity:0},{opacity:1},{opacity:0},{opacity:1},{opacity:.5},{opacity:1}],
        {duration:375,delay,easing:'steps(2,end)',fill:'forwards'}
      );
    }else{
      dot.animate([{opacity:getComputedStyle(dot).opacity},{opacity:0}],
        {duration:220,delay:(dots.length-1-i)*8,easing:'steps(2,end)',fill:'forwards'});
    }
  });
};
$$('footer#footer nav a').forEach(link=>{
  const icons=$$('.dot-icon',link);
  icons.forEach(icon=>$$('.dot',icon).forEach(d=>d.style.opacity='0'));
  link.addEventListener('pointerenter',()=>icons.forEach(icon=>animateFooterDotIcon(icon,true)));
  link.addEventListener('pointerleave',()=>icons.forEach(icon=>animateFooterDotIcon(icon,false)));
});
$$('footer#footer nav,footer#footer .cta,footer#footer .logo').forEach(surface=>{
  surface.addEventListener('pointermove',e=>{
    const r=surface.getBoundingClientRect();
    surface.style.setProperty('--krn-glow-x',((e.clientX-r.left)/r.width*100)+'%');
    surface.style.setProperty('--krn-glow-y',((e.clientY-r.top)/r.height*100)+'%');
  },{passive:true});
});
$$('div.btn-wrapper .btn').forEach(btn=>{
  btn.addEventListener('pointerenter',()=>btn.classList.add('k-hover'));
  btn.addEventListener('pointerleave',()=>btn.classList.remove('k-hover'));
});

/* ---------- persistent BOON-style particle field ---------- */
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
    g.uniform1f(this.loc.baseSize,18);g.uniform3f(this.loc.baseColor,36/255,107/255,73/255);g.uniform3f(this.loc.highlight,185/255,243/255,93/255);
  }
  bindBuffer(name,data,size){
    if(this.disabled)return;const g=this.gl,b=this.buffers[name],loc=this.loc[name];
    g.bindBuffer(g.ARRAY_BUFFER,b);g.bufferData(g.ARRAY_BUFFER,data,g.DYNAMIC_DRAW);g.enableVertexAttribArray(loc);g.vertexAttribPointer(loc,size,g.FLOAT,false,0,0);
  }
  uploadAll(){this.bindBuffer('pos',this.positions,3);this.bindBuffer('target',this.targetPositions,3);this.bindBuffer('scale',this.scales,1);this.bindBuffer('targetScale',this.targetScales,1);this.bindBuffer('random',this.random,1)}
  loadImage(){
    const im=new Image();im.crossOrigin='anonymous';im.src='/kernellum/assets/particle-image.png?v=2';
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
const bgCanvas=$('.three-canvas');
if(bgCanvas){
  const stage=bgCanvas.closest('.three-canvas-container')?.parentElement;
  if(stage){stage.style.zIndex='0';stage.style.pointerEvents='none'}
  const wrapper=$('.page-wrapper');
  if(wrapper){wrapper.style.position='relative';wrapper.style.zIndex='1'}
}
const particles=bgCanvas?new ParticleField(bgCanvas):null;

const themeDark={base:'#070907',base2:'#0e120f',base3:'#303831',content:'#f2f1eb',content2:'#e4e6df',muted:'#626a63',border:'#303831',primary:'#b9f35d',secondary:'#246b49'};
const themeLight={base:'#e4e6df',base2:'#f2f1eb',base3:'#e4e6df',content:'#070907',content2:'#070907',muted:'#626a63',border:'#626a63',primary:'#246b49',secondary:'#b9f35d'};
function setTheme(){
  const t=themeDark,r=document.documentElement.style;
  r.setProperty('--clr-base-100',t.base);r.setProperty('--clr-base-200',t.base2);r.setProperty('--clr-base-300',t.base3);r.setProperty('--clr-base-400',t.base);
  r.setProperty('--clr-content-100',t.content);r.setProperty('--clr-content-200',t.content2);r.setProperty('--clr-content-300',t.muted);r.setProperty('--clr-border',t.border);r.setProperty('--clr-border-card',t.border);r.setProperty('--clr-primary',t.primary);r.setProperty('--clr-secondary',t.secondary);
  if(particles)particles.theme='dark';
}
const large=$('section.large-text');
let largeLines=[];
function prepareLargeLines(){
  if(!large)return;
  const h2=$('h2',large);
  if(h2)largeLines=splitRichRenderedLines(h2,'100%');
}
prepareLargeLines();
if(document.fonts&&document.fonts.ready)document.fonts.ready.then(prepareLargeLines);
const focus=[
  [hero,'dark','none'],
  [centered[0],'dark','grid'],
  [centered[1],'dark','image'],
  [cardGrid,'dark','rings-horizontal'],
  [large,'dark','rings-vertical'],
  [sock,'dark','none']
].filter(x=>x[0]);
let focusEl=null;
function smoothRect(el){
  const raw=el.getBoundingClientRect(),docTop=raw.top+scrollY,top=docTop-smoothY;
  return{top,bottom:top+raw.height,height:raw.height};
}
function chooseFocus(){
  const vh=innerHeight,line=vh*(scrollY>lastY?.4:scrollY<lastY?.6:.5);let best=null,score=-1;
  focus.forEach(item=>{const r=smoothRect(item[0]),vis=Math.max(0,Math.min(r.bottom,vh)-Math.max(r.top,0));if(vis<vh*.05)return;const ratio=vis/Math.min(vh,r.height),d=(r.top<=line&&r.bottom>=line)?0:Math.min(Math.abs(r.top-line),Math.abs(r.bottom-line)),center=1-Math.min(1,d/vh),scoreNow=ratio*.6+center*.4;if(scoreNow>score){score=scoreNow;best=item}});
  if(best&&best[0]!==focusEl){focusEl=best[0];setTheme();if(particles)particles.set(best[2])}
}

/* ---------- scroll choreography ---------- */
let smoothY=scrollY,lastY=scrollY,lastToggle=0,lastTime=performance.now();
function frame(now){
  const dt=Math.min(.05,(now-lastTime)/1000);lastTime=now;
  const y=scrollY,dir=Math.sign(y-lastY),vh=innerHeight;smoothY=lerp(smoothY,y,1-Math.exp(-6.5*dt));
  if(header){
    let visible=header.classList.contains('visible');
    const hh=header.offsetHeight;
    if(y<hh)visible=true;
    else if(Math.abs(y-lastToggle)>=50){visible=dir<0;lastToggle=y}
    header.classList.toggle('visible',visible);
    header.style.transform=visible?'translateY(0)':'translateY(-150%)';
  }
  const hp=clamp(smoothY/vh);
  if(hero&&!reduce.matches){
    if(heroWrappers[1])heroWrappers[1].style.transform=`translateY(${25*hp}%)`;if(heroImgs[1])heroImgs[1].style.transform=`translateY(${-12.5*hp}%)`;
    if(heroWrappers[2])heroWrappers[2].style.transform=`translateX(${-25*hp}%)`;if(heroImgs[2])heroImgs[2].style.transform=`translateX(${12.5*hp}%)`;
    if(heroWrappers[3])heroWrappers[3].style.transform=`translateX(${25*hp}%)`;if(heroImgs[3])heroImgs[3].style.transform=`translateX(${-12.5*hp}%)`;
    if(heroImgs[0])heroImgs[0].style.transform=`scale(${1+.15*hp})`;
    if(!mobile.matches){const ls=$$('.title>.k-line',hero);if(ls[0])ls[0].style.transform=`translateX(${-50*hp}vw)`;if(ls[1])ls[1].style.transform=`translateX(${50*hp}vw)`;if(heroSubtitle)heroSubtitle.style.transform=`translateX(${-5*hp}vw)`;if(heroScroll)heroScroll.style.transform=`translateX(${5*hp}vw)`}
    if(heroSubtitle)heroSubtitle.style.opacity=String(Math.max(0,1-1.5*hp));if(heroScroll)heroScroll.style.opacity=String(Math.max(0,1-1.5*hp));
  }
  centered.forEach(sec=>{const r=smoothRect(sec),p=clamp(-r.top/(vh*.5));(sec._kLines||[]).forEach(l=>l.style.transform=`translateY(${101*(1-p)}%)`);if(sec===roloSec)runRolodex(p>=1)});
  if(cardGrid&&!reduce.matches){const r=smoothRect(cardGrid),p=clamp((vh-r.top)/(vh*.65));cards.forEach((c,i)=>{const lp=clamp((p-i*(150/800)*.35)/(1-i*.035)),e=out(lp);c.style.transform=`translateY(${(100+i*50)*(1-e)}px)`})}
  if(large&&!reduce.matches){const r=smoothRect(large),p=clamp((vh-r.bottom)/(vh*.5));largeLines.forEach(l=>l.style.transform=`translateY(${100*(1-p)}%)`)}
  if(sock&&!reduce.matches){const r=smoothRect(sock),p=clamp((vh-r.bottom)/vh),wrap=$('.images>.image-wrapper',sock);if(sockImgs[0])sockImgs[0].style.transform=`scale(${1.15-.15*p})`;if(wrap[1])wrap[1].style.transform=`translateX(${-10*(1-p)}%)`;if(sockImgs[1])sockImgs[1].style.transform=`translateX(${5*(1-p)}%)`;if(wrap[2])wrap[2].style.transform=`translateY(${50*(1-p)}%)`;if(sockImgs[2])sockImgs[2].style.transform=`translateY(${-25*(1-p)}%)`;if(wrap[3])wrap[3].style.transform=`translateY(${-50*(1-p)}%)`;if(sockImgs[3])sockImgs[3].style.transform=`translateY(${25*(1-p)}%)`;const line=$('.k-line>span',sock),lp=clamp((p-.4)/.6);if(line)line.style.transform=`translateY(${100*(1-lp)}%)`;const btn=$('.btn',sock),bp=clamp((p-.5)/.5);if(btn){btn.style.opacity=String(bp);btn.style.transform=`translateY(${50*(1-bp)}%)`}}
  chooseFocus();if(particles)particles.draw(now,dt);lastY=y;requestAnimationFrame(frame)
}
/* Lenis-equivalent desktop smoothing: same root/sync intent without shipping another framework. */
if(!reduce.matches&&matchMedia('(hover:hover) and (pointer:fine)').matches){
  let scrollTarget=scrollY,scrollCurrent=scrollY,driving=false;
  const maxScroll=()=>Math.max(0,document.documentElement.scrollHeight-innerHeight);
  addEventListener('wheel',e=>{
    if(e.ctrlKey||e.metaKey)return;
    const t=e.target;
    if(t instanceof Element&&t.closest('input,textarea,select,[contenteditable="true"]'))return;
    e.preventDefault();
    driving=true;scrollCurrent=scrollY;scrollTarget=clamp(scrollTarget+e.deltaY,0,maxScroll());
  },{passive:false});
  addEventListener('keydown',e=>{
    const amount=e.key==='PageDown'?innerHeight*.9:e.key==='PageUp'?-innerHeight*.9:e.key==='ArrowDown'?40:e.key==='ArrowUp'?-40:0;
    if(!amount)return;e.preventDefault();driving=true;scrollCurrent=scrollY;scrollTarget=clamp(scrollTarget+amount,0,maxScroll());
  });
  const smoothScrollRaf=()=>{
    if(driving){
      scrollCurrent+=(scrollTarget-scrollCurrent)*.1;
      if(Math.abs(scrollTarget-scrollCurrent)<.2){scrollCurrent=scrollTarget;driving=false}
      scrollTo(0,scrollCurrent);
    }else{scrollCurrent=scrollY;scrollTarget=scrollY}
    requestAnimationFrame(smoothScrollRaf);
  };
  requestAnimationFrame(smoothScrollRaf);
}

setTheme();
requestAnimationFrame(frame);

addEventListener('load',()=>setTimeout(()=>{const l=$('#loader');if(l)l.classList.add('kernellum-loaded')},180),{once:true});
let splitResizeTimer=0;
addEventListener('resize',()=>{
  clearTimeout(splitResizeTimer);
  splitResizeTimer=setTimeout(()=>{prepareCenteredLines();prepareLargeLines()},180);
},{passive:true});
setTimeout(()=>{const l=$('#loader');if(l)l.classList.add('kernellum-loaded')},1200);
})();