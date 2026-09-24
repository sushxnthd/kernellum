import{u as M,_ as x,t as U}from"./BEqJjq0f.js";import{C as b,O as E,M as T,P as V,b as R,c as A}from"./CV1CKauh.js";import{a as n}from"./BEW1fCGd.js";import{d as B,S as I,o as P,h as S,F as j,k as p,u as i,al as k,p as F,ag as G,R as L}from"./BWg2ILet.js";const O=`
   varying vec2 vUv;

   void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
   }
`,N=`
   uniform vec3 uColor;
   uniform float uIntensity;
   uniform float uAlpha;

   varying vec2 vUv;

   void main() {
      // Distance from center, remapped so edge midpoints = 1.0
      float d = length(vUv - 0.5) * 2.0;

      // Invert and smooth so center is bright, edge fades to transparent
      float glow = 1.0 - smoothstep(0.0, 1.0, d);

      // Power curve sharpens the falloff — higher = tighter glow
      glow = pow(glow, 2.5);

      gl_FragColor = vec4(uColor, glow * uIntensity * uAlpha);
   }
`,X=B({__name:"ThreeGlowCursor",props:{radius:{default:240},color:{default:"#79d8c1"},intensity:{default:.4},target:{default:void 0}},setup(w){const a=w,f=G(U),o=L(),u={x:0,y:0};let c=!1,m=0;const h={uColor:{value:new b(a.color)},uIntensity:{value:a.intensity},uAlpha:{value:0}};I(()=>{const e=a.target??f?.domElement,r=f?.domElement??e;if(!e||!r)return;const t=(s,l)=>{const d=r.getBoundingClientRect();u.x=s-d.left-d.width/2,u.y=d.height/2-(l-d.top),c=!0},v=s=>t(s.clientX,s.clientY),C=()=>{c=!1},g=s=>{const l=s.touches[0];l&&t(l.clientX,l.clientY)},_=()=>{c=!1};n(e,"mousemove",v),n(e,"mouseleave",C),n(e,"touchmove",g,{passive:!0}),n(e,"touchstart",g,{passive:!0}),n(e,"touchend",_),n(e,"touchcancel",_)});const{onBeforeRender:y}=M();return y(({delta:e})=>{o.value&&(m=A.damp(m,c?1:0,6,e),o.value.visible=m>.001,o.value.visible&&(h.uAlpha.value=m,o.value.position.set(u.x,u.y,0),o.value.scale.set(a.radius*2,a.radius*2,1)))}),(e,r)=>{const t=x;return P(),S(j,null,[p(t,{is:i(E),options:{position:[0,0,1]}},null,8,["is"]),p(t,{is:i(T),modelValue:i(o),"onUpdate:modelValue":r[0]||(r[0]=v=>k(o)?o.value=v:null)},{default:F(()=>[p(t,{is:i(V),args:[1,1]},null,8,["is"]),p(t,{is:i(R),options:{vertexShader:O,fragmentShader:N,uniforms:h,depthWrite:!1,transparent:!0}},null,8,["is","options"])]),_:1},8,["is","modelValue"])],64)}}}),q=Object.assign(X,{__name:"ThreeGlowCursor"});export{q as _};
