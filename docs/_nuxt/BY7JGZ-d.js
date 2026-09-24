const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./C5519GSD.js","./Bne1fdj4.js","./CwAE7HMs.js","./Bq-CSWMy.js","./BWg2ILet.js","./DTVziQxs.js","./BSgwrZLn.js","./CpJfINCX.js","./CV1CKauh.js","./entry.DcSZNwz6.css","./v7rF5gio.js","./AlertBanner.GrF68s0o.css","./DHMWGXoR.js","./Beq67LXS.js","./BEqJjq0f.js","./BEW1fCGd.js","./wa5M3ceU.js","./ThreeView.EvK2eRF-.css","./DMjiie3U.js","./DyDaNXIu.js","./DotGrid.CvSgzoXR.css","./CAcCrSPu.js","./DrZo1_5l.js","./DYLIcWIl.js","./DotIcon.P5q4Tl8_.css","./C9JD9LUG.js","./DRE_wQ1D.js","./CcGBHYOs.js","./ImageWrapper.INIjzDgY.css","./By-qMKMM.js","./SanityImage.BjZBy7rz.css","./NavHelper.CcLCvgMY.css","./DXkU3Htz.js","./Cs1zKDta.js","./DWPLS5pp.js","./Header.CZVL2hbf.css"])))=>i.map(i=>d[i]);
import{_ as Ee}from"./DTVziQxs.js";import{a as Ne,b as Oe,u as Ve,_ as ze,r as ie,c as Be,d as He,e as Ye}from"./BEqJjq0f.js";import{V as te,O as De,i as Fe,B as Ue,b as We,j as ke,k as Ze,W as Ge,a as je}from"./CV1CKauh.js";import{a as ce}from"./BEW1fCGd.js";import{d as he,b as pe,H as le,ae as me,o as ae,h as ne,F as qe,k as N,u as H,p as ve,al as Ke,aF as Je,R as Z,ao as Qe,e as ue,S as et,i as _e,U as we,l as tt,J as at,aw as nt,at as de,x as ot,q as W,_ as Se,Q as st}from"./BWg2ILet.js";import"./BSgwrZLn.js";import"./CpJfINCX.js";const rt=Object.assign(Ne,{__name:"ThreeViewRenderer"}),fe=18,it=1500,k=250,ct=2,lt=.35,ut=.9,dt=.65,ge=123.456,ft=2e5,gt=`
   uniform vec3 uBaseColor;
   uniform vec3 uHighlightColor;

   varying float vScale;
   varying float vIntensity;

   void main() {
      if (vScale < 0.001) discard;

      vec2 p = gl_PointCoord - 0.5;
      float dist = length(p);
      float aa = fwidth(dist);
      if (dist > 0.5 + aa) discard;

      float alpha = 1.0 - smoothstep(0.5 - aa, 0.5 + aa, dist);

      vec3 finalColor = mix(uBaseColor, uHighlightColor, vIntensity);
      gl_FragColor = vec4(finalColor, alpha);

      #include <colorspace_fragment>
   }
`,ht=he({__name:"ParticleScene",setup(L){function v(e){return Number.isInteger(e)?`${e}.0`:`${e}`}const{utils:I,createTimeline:C}=pe().$anime,{viewport:c}=Oe(),{onBeforeRender:y}=Ve(),{baseColor:R,highlightColor:D,targetType:A,targetImageUrl:X}=Je(),b=Z();let O=A.value,F,z,f;const h=new te(0,0),p={uBaseSize:{value:fe},uBaseColor:{value:R},uHighlightColor:{value:D},uTime:{value:0},uViewport:{value:new te(0,0)},uMouse:{value:new te(0,0)},uParallaxStrength:{value:0},uTransition:{value:0}},Te=`
   uniform float uBaseSize;
   uniform float uTime;
   uniform vec2 uViewport;
   uniform vec2 uMouse;
   uniform float uParallaxStrength;
   uniform float uTransition;

   attribute vec3 aTargetPosition;
   attribute float aScale;
   attribute float aTargetScale;
   attribute float aRandom;

   varying float vScale;
   varying float vIntensity;

   void main() {
      vec3 finalPos = mix(position, aTargetPosition, uTransition);
      float pathArc = sin(uTransition * ${v(Math.PI)});

      float rand1 = aRandom;
      float rand2 = fract(aRandom * ${v(ge)});

      finalPos.x += (rand1 - 0.5) * ${v(k)} * pathArc;
      finalPos.y += (rand2 - 0.5) * ${v(k)} * pathArc;

      finalPos.xy += uMouse * finalPos.z * 4.0 * uParallaxStrength;

      vec4 mvPosition = modelViewMatrix * vec4(finalPos, 1.0);
      gl_Position = projectionMatrix * mvPosition;

      float finalScale = mix(aScale, aTargetScale, uTransition);
      vScale = finalScale;

      float pulse = sin(uTime * ${v(ct)} + (rand1 * ${v(Math.PI*2)})) * 0.5 + 0.5;
      float oscillationScale = mix(${v(lt)}, ${v(ut)}, pulse);

      gl_PointSize = uBaseSize * oscillationScale * finalScale;

      vec2 mouseWorld = uMouse * uViewport * 0.5;
      float distToMouse = distance(finalPos.xy, mouseWorld);
      float screenMin = min(uViewport.x, uViewport.y);
      float outerRadius = screenMin * ${v(dt)};
      vIntensity = smoothstep(outerRadius, 0.0, distToMouse);
   }
`;function $(e){return b.value?.getAttribute(e)}function _(e,n,a){const s=$(e),o=s?.array;o&&o.length===n.length?(o.set(n),s.needsUpdate=!0):b.value?.setAttribute(e,new ke(new Float32Array(n),a))}function Y(){return{positions:new Float32Array(t.count*3),scales:new Float32Array(t.count)}}function U(e){return I.shuffle(Array.from({length:e},(n,a)=>a))}function G(e,n,a,s){const o=a*3;if(s&&s[o]!==void 0&&!Number.isNaN(s[o]))e[o]=s[o],e[o+1]=s[o+1],e[o+2]=s[o+2];else{const i=a%t.cols,r=Math.floor(a/t.cols);e[o]=t.startX+i*t.gap,e[o+1]=t.startY+r*t.gap,e[o+2]=0}n[a]=0}function oe(){const{positions:e,scales:n}=Y();let a=0;for(let s=0;s<t.rows;s++)for(let o=0;o<t.cols;o++)e[a*3]=t.startX+o*t.gap,e[a*3+1]=t.startY+s*t.gap,e[a*3+2]=0,n[a]=0,a++;return{positions:e,scales:n}}function xe(){const{positions:e,scales:n}=Y(),a=U(t.count);let s=0;for(let o=0;o<t.rows;o++)for(let i=0;i<t.cols;i++){const r=a[s],l=t.startX+i*t.gap,d=t.startY+o*t.gap;e[r*3]=l,e[r*3+1]=d,e[r*3+2]=(l*l+d*d)/(2*ft),n[r]=Math.random()<.5?0:Math.random(),s++}return{positions:e,scales:n}}function Me(){const{positions:e,scales:n}=Y(),a=$("position")?.array,s=10,o=Math.max(Math.min(c.width,c.height)*.25,150),i=o*.3,l=-((s-1)*i)/2,d=-5,u=U(t.count);let m=0,w=0;const x=Math.floor(2*Math.PI*o/t.gap);for(let S=0;S<t.count;S++){const g=u[S];if(m<s){const T=w/x*Math.PI*2,V=l+m*i;e[g*3]=V+Math.cos(T)*o,e[g*3+1]=Math.sin(T)*o,e[g*3+2]=(m-s/2)*d,n[g]=1,w++,w>=x&&(m++,w=0)}else G(e,n,g,a)}return{positions:e,scales:n}}function Ie(){const{positions:e,scales:n}=Y(),a=$("position")?.array,s=6,o=Math.max(Math.min(c.width,c.height)*.35,250),i=40,r=-15,l=U(t.count);let d=0,u=o,m=0,w=Math.floor(2*Math.PI*u/t.gap),x=0;for(let S=0;S<t.count;S++){const g=l[S];if(d<s&&u>0){const T=x/w*Math.PI*2;e[g*3]=Math.cos(T)*u,e[g*3+1]=Math.sin(T)*u,e[g*3+2]=m,n[g]=1,x++,x>=w&&(d++,u-=i,m+=r,w=Math.floor(2*Math.PI*u/t.gap),x=0)}else G(e,n,g,a)}return{positions:e,scales:n}}async function Re(e){if(e===z&&f)return f;const n=new Image;return n.crossOrigin="anonymous",n.src=e,await n.decode(),z=e,f=n,n}async function Pe(e,n){n?.throwIfAborted();const a=await Re(e);n?.throwIfAborted();const s=document.createElement("canvas"),o=s.getContext("2d",{willReadFrequently:!0}),i=t.cols,r=t.rows;s.width=i,s.height=r;const l=a.width/a.height,d=i/r;let u,m,w,x;l>d?(m=r,u=a.width*(r/a.height),w=(i-u)/2,x=0):(u=i,m=a.height*(i/a.width),w=0,x=(r-m)/2),o.drawImage(a,w,x,u,m);const S=o.getImageData(0,0,i,r).data,g=[];for(let M=0;M<r;M++)for(let P=0;P<i;P++){const E=(M*i+P)*4,Q=S[E],Le=S[E+1],Xe=S[E+2];if(S[E+3]>128){const re=1-(.299*Q+.587*Le+.114*Xe)/255,ee=.33,$e=re<=ee?0:(re-ee)/(1-ee);g.push({x:P,y:M,scale:$e})}}const{positions:T,scales:V}=Y(),K=$("position")?.array,J=U(t.count);for(let M=0;M<t.count;M++){const P=J[M];if(M<g.length){const E=g[M],Q=t.rows-1-E.y;T[P*3]=t.startX+E.x*t.gap,T[P*3+1]=t.startY+Q*t.gap,T[P*3+2]=0,V[P]=E.scale}else G(T,V,P,K)}return{positions:T,scales:V}}const ye={none:oe,grid:xe,"rings-horizontal":Me,"rings-vertical":Ie};let B,j;function Ae(){const e=$("position"),n=$("aTargetPosition"),a=$("aScale"),s=$("aTargetScale"),o=$("aRandom");if(!e||!n||!a||!s||!o)return;const i=p.uTransition.value,r=Math.sin(i*Math.PI);for(let l=0;l<t.count;l++){const d=e.getX(l),u=e.getY(l),m=e.getZ(l),w=n.getX(l),x=n.getY(l),S=n.getZ(l),g=o.getX(l),T=g*ge,V=T-Math.floor(T),K=(g-.5)*k*r,J=(V-.5)*k*r;e.setXYZ(l,d+(w-d)*i+K,u+(x-u)*i+J,m+(S-m)*i);const M=a.getX(l),P=s.getX(l);a.setX(l,M+(P-M)*i)}e.needsUpdate=!0,a.needsUpdate=!0,p.uTransition.value=0}async function q(e,n={}){const{instant:a=!1,force:s=!1}=n,o=X.value;if(O===e&&F===o&&!s)return;F=o,j?.abort();const i=new AbortController;j=i;let r;try{e==="image"?o&&(r=await Pe(o,i.signal)):r=ye[e]()}catch(d){d?.name!=="AbortError"&&console.error(d);return}if(i.signal.aborted||!r)return;if(O=e,B&&(B.cancel(),a||Ae(),B=void 0),a){const d=new Float32Array(t.count);for(let u=0;u<t.count;u++)d[u]=Math.random();_("aRandom",d,1),_("position",r.positions,3),_("aTargetPosition",r.positions,3),_("aScale",r.scales,1),_("aTargetScale",r.scales,1),p.uTransition.value=0;return}_("aTargetPosition",r.positions,3),_("aTargetScale",r.scales,1);const l=e==="grid"||e==="rings-horizontal"||e==="rings-vertical"?1:0;B=C({defaults:{duration:it,onComplete:()=>{_("position",r.positions,3),_("aScale",r.scales,1),p.uTransition.value=0,B=void 0}}}).add(p.uTransition,{value:1}).add(p.uParallaxStrength,{value:l},"<<")}const t={gap:0,cols:0,rows:0,count:0,startX:0,startY:0};let se=!1;le([()=>c.width,()=>c.height,b],()=>{if(!(!c.width||!c.height||!b.value))if(p.uViewport.value.set(c.width,c.height),t.gap=fe*.75,t.cols=Math.ceil(c.width/t.gap)+1,t.rows=Math.ceil(c.height/t.gap)+1,t.count=t.cols*t.rows,t.startX=t.cols*t.gap/-2+t.gap/2,t.startY=t.rows*t.gap/-2+t.gap/2,se)q(O,{instant:!0,force:!0});else{const e=oe(),n=new Float32Array(t.count);for(let a=0;a<t.count;a++)n[a]=Math.random();_("aRandom",n,1),_("position",e.positions,3),_("aTargetPosition",e.positions,3),_("aScale",e.scales,1),_("aTargetScale",e.scales,1),se=!0,A.value!=="none"&&(O="none",q(A.value))}},{immediate:!0}),le([A,X],([e])=>{q(e)});function Ce(e){h.x=e.clientX/window.innerWidth*2-1,h.y=-(e.clientY/window.innerHeight)*2+1}function be(){h.set(0,0)}return ce(document,"mousemove",Ce),ce(document,"mouseleave",be),y(({elapsed:e,delta:n})=>{p.uTime.value=e,p.uMouse.value.lerp(h,1-Math.exp(-5*n))}),me(()=>{j?.abort(),B?.revert()}),(e,n)=>{const a=ze;return ae(),ne(qe,null,[N(a,{is:H(De),options:{position:[0,0,1e3]}},null,8,["is"]),N(a,{is:H(Fe)},{default:ve(()=>[N(a,{is:H(Ue),modelValue:H(b),"onUpdate:modelValue":n[0]||(n[0]=s=>Ke(b)?b.value=s:null)},null,8,["is","modelValue"]),N(a,{is:H(We),options:{transparent:!0,depthWrite:!1,vertexShader:Te,fragmentShader:gt,uniforms:p}},null,8,["is","options"])]),_:1},8,["is"])],64)}}}),pt=Object.assign(ht,{__name:"ParticleScene"});function mt(L,v){const{$addRafTick:I,$removeRafTick:C}=pe();I(L,v),Qe(()=>C(L))}const vt=he({__name:"ThreeCanvas",setup(L){const{runThreeLoop:v}=Be(),I=ue("container"),C=ue("canvas"),c=Z(),y=Z(),R=Z(),D=at(!1),A=nt({width:0,height:0,pixelRatio:1}),X=new Ze;de(He,{canvas:W(()=>C.value??void 0),renderer:W(()=>c.value),scene:W(()=>y.value),camera:W(()=>R.value),viewport:ot(A)}),de(Ye,y);function b(f){if(f.isCamera)return f;for(let h=0;h<f.children.length;h++){const p=b(f.children[h]);if(p)return p}}function O(f){v(f,()=>{y.value&&R.value&&c.value?.render(y.value,R.value)})}function F(){if(!I.value||!c.value)return;const f=I.value.clientWidth,h=I.value.clientHeight,p=Math.min(window.devicePixelRatio,2);A.width=f,A.height=h,A.pixelRatio=p,c.value.setSize(f,h,!1),c.value.setPixelRatio(p),R.value&&ie(R.value,f,h),O({delta:0,elapsed:X.getElapsed()})}let z;return et(()=>{if(!I.value||!C.value)return;try{c.value=new Ge({canvas:C.value,antialias:!0,alpha:!0})}catch(e){console.warn("Kernellum site: WebGL unavailable; 3D layer skipped.");return;}(c.value.setClearAlpha(0),y.value=new je,X.connect(document),D.value=!0,z=new ResizeObserver(F),z.observe(I.value),mt(f=>{if(!(!c.value||!y.value)){if(R.value&&!R.value.parent&&(R.value=void 0),!R.value){const h=b(y.value);h?(ie(h,A.width,A.height),R.value=h):c.value.clear()}X.update(f),O({delta:X.getDelta(),elapsed:X.getElapsed()})}},"three"))}),me(()=>{z?.disconnect(),c.value?.dispose(),X.dispose()}),(f,h)=>(ae(),ne("div",{ref_key:"container",ref:I,class:"three-canvas-container"},[_e("canvas",{ref_key:"canvas",ref:C,class:"three-canvas"},null,512),H(D)?we(f.$slots,"default",{key:0},void 0,!0):tt("",!0)],512))}}),_t=Object.assign(Se(vt,[["__scopeId","data-v-d8c2c3e2"]]),{__name:"ThreeCanvas"}),wt=st(()=>Ee(()=>import("./C5519GSD.js"),__vite__mapDeps([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35]),import.meta.url).then(L=>L.default||L)),St={},Tt={style:{position:"fixed",inset:"0","z-index":"-1"}};function xt(L,v){const I=pt,C=rt,c=_t,y=wt;return ae(),ne("div",null,[_e("div",Tt,[N(c,null,{default:ve(()=>[N(I),N(C)]),_:1})]),N(y),we(L.$slots,"default")])}const Lt=Se(St,[["render",xt]]);export{Lt as default};
