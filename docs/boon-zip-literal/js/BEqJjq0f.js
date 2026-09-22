import{d as z,V as G,H as V,ae as D,U as W,W as K,ag as w,R as Q,u as C,at as x,ao as _,au as q,S as N,o as P,h as Z,F as $,j as H,c as J}from"./BWg2ILet.js";import{a as X,O as Y,b as ee,f as re,Z as te,A as ne,g as oe,e as se,V as ae,M as ie,P as de}from"./CV1CKauh.js";const ue=Symbol("three-context"),M=Symbol("three-loop"),j=Symbol("three-parent"),ce=Symbol("three-view"),le=z({__name:"ThreeNode",props:K({is:{},args:{},options:{},attach:{}},{modelValue:{},modelModifiers:{}}),emits:["update:modelValue"],setup(n){const s=n,r=w(j),i=Q(),l=G(n,"modelValue");x(j,i);function f(){i.value&&S();const t=s.is,a=new t(...s.args||[]);y(a,s.options),i.value=a,l.value=a;const d=C(r);d&&(s.attach?d[s.attach]=a:a.isObject3D&&typeof d.add=="function"?d.add(a):(a.isBufferGeometry||a.isGeometry)&&"geometry"in d?d.geometry=a:a.isMaterial&&"material"in d&&(d.material=a))}function y(t,a){if(!(!t||!a))for(const[d,p]of Object.entries(a))if(typeof t[d]=="function"){const T=Array.isArray(p)?p:[p];t[d](...T)}else Array.isArray(p)&&t[d]&&typeof t[d].set=="function"?t[d].set(...p):t[d]&&typeof t[d].set=="function"&&(typeof p=="number"||typeof p=="string")?t[d].set(p):t[d]&&typeof t[d].copy=="function"&&!t[d].uuid&&p!==null&&typeof p=="object"?t[d].copy(p):t[d]=p}function S(){const t=i.value;if(!t)return;typeof t.dispose=="function"&&t.dispose();const a=C(r);a&&(s.attach&&a[s.attach]===t?a[s.attach]=null:t.isObject3D&&typeof a.remove=="function"?a.remove(t):(t.isBufferGeometry||t.isGeometry)&&a.geometry===t?a.geometry=null:t.isMaterial&&a.material===t&&(a.material=null)),l.value=void 0}return V([()=>s.is,()=>s.args],f,{deep:!0,immediate:!0}),V(()=>s.options,t=>y(i.value,t),{deep:!0}),D(()=>{S(),i.value=void 0}),(t,a)=>W(t.$slots,"default")}}),Re=Object.assign(le,{__name:"ThreeNode"});function A(){const n=[];return{add:(s,r=0)=>{const i={callback:s,priority:r},l=n.findIndex(f=>f.priority>r);l===-1?n.push(i):n.splice(l,0,i)},remove:s=>{const r=n.findIndex(i=>i.callback===s);r!==-1&&n.splice(r,1)},run:s=>{for(let r=0;r<n.length;r++)n[r]?.callback(s)},get hasCallbacks(){return n.length>0}}}function ye(){const n=A(),s=A(),r=A(),i={addBeforeRender:n.add,removeBeforeRender:n.remove,addRender:s.add,removeRender:s.remove,addAfterRender:r.add,removeAfterRender:r.remove};return x(M,i),{runThreeLoop:(f,y)=>{n.run(f),s.hasCallbacks?s.run(f):y(),r.run(f)}}}function fe(){const n=w(M);if(!n)throw new Error("useThreeLoop() must be called inside <ThreeCanvas>.");return{onBeforeRender:(l,f=0)=>{n.addBeforeRender(l,f),_(()=>n.removeBeforeRender(l))},render:(l,f=0)=>{n.addRender(l,f),_(()=>n.removeRender(l))},onAfterRender:(l,f=0)=>{n.addAfterRender(l,f),_(()=>n.removeAfterRender(l))}}}const pe=()=>{const n=w(ue);if(!n)throw new Error("useThree() must be called inside <ThreeCanvas>.");return n};function me(n,s,r){if(n.isPerspectiveCamera){const i=n;i.aspect=s/r,i.updateProjectionMatrix()}else if(n.isOrthographicCamera){const i=n;i.left=s/-2,i.right=s/2,i.top=r/2,i.bottom=r/-2,i.updateProjectionMatrix()}}const b=q(new Map),ge=z({__name:"ThreeViewRenderer",props:{renderBelow:{type:Boolean,default:!1}},setup(n){const{canvas:s,renderer:r,scene:i,camera:l,viewport:f}=pe(),{render:y}=fe(),S=n,t=new WeakMap,a=new Set,d=new WeakMap,p=z({props:{view:{type:Object,required:!0}},setup({view:o}){const e=w(M);if(e){const m=new WeakMap,h=c=>{let u=m.get(c);return u||(u=g=>{o.isIntersecting&&c(g)},m.set(c,u)),u},v=c=>{const u=m.get(c);return u&&m.delete(c),u};x(M,{addBeforeRender:(c,u)=>{e.addBeforeRender(h(c),u)},removeBeforeRender:c=>{const u=v(c);u&&e.removeBeforeRender(u)},addRender:(c,u)=>{e.addRender(h(c),u)},removeRender:c=>{const u=v(c);u&&e.removeRender(u)},addAfterRender:(c,u)=>{e.addAfterRender(h(c),u)},removeAfterRender:c=>{const u=v(c);u&&e.removeAfterRender(u)}})}return x(j,o.scene),x(ce,o),o.slot}}),T=new X,U=new Y(-1,1,1,-1,0,1),L=new ee({uniforms:{uSize:{value:new ae},uBorderRadius:{value:new se}},vertexShader:`
      varying vec2 vUv;

      void main() {
         vUv = uv;
         gl_Position = vec4(position, 1.0);
      }
   `,fragmentShader:`
      uniform vec2 uSize;
      uniform vec4 uBorderRadius;
      varying vec2 vUv;

      void main() {
         vec2 px = vUv * uSize;
         float alpha = 0.0;
         
         float rTL = uBorderRadius.x;
         float rTR = uBorderRadius.y;
         float rBR = uBorderRadius.z;
         float rBL = uBorderRadius.w;

         if (px.x < rBL && px.y < rBL) {
            float dist = length(px - vec2(rBL, rBL));
            alpha = smoothstep(rBL - 0.5, rBL + 0.5, dist);
         } else if (px.x > uSize.x - rBR && px.y < rBR) {
            float dist = length(px - vec2(uSize.x - rBR, rBR));
            alpha = smoothstep(rBR - 0.5, rBR + 0.5, dist);
         } else if (px.x > uSize.x - rTR && px.y > uSize.y - rTR) {
            float dist = length(px - vec2(uSize.x - rTR, uSize.y - rTR));
            alpha = smoothstep(rTR - 0.5, rTR + 0.5, dist);
         } else if (px.x < rTL && px.y > uSize.y - rTL) {
            float dist = length(px - vec2(rTL, uSize.y - rTL));
            alpha = smoothstep(rTL - 0.5, rTL + 0.5, dist);
         }

         if (alpha == 0.0) discard;
         gl_FragColor = vec4(0.0, 0.0, 0.0, alpha); 
      }
   `,blending:oe,blendEquation:ne,blendSrc:te,blendDst:re,depthWrite:!1,depthTest:!1,transparent:!0}),F=new ie(new de(2,2),L);T.add(F);let B,R;function E(o,e){if(R=R??s.value?.getBoundingClientRect(),e=e??o.domElement.getBoundingClientRect(),!R||e.width===0||e.height===0){o.bounds=void 0;return}o.bounds={left:e.left-R.left,bottom:R.bottom-e.bottom,width:e.width,height:e.height}}function k(){if(!B)return;const o=new Set;b.forEach(e=>{o.add(e.domElement),a.has(e.domElement)||(B?.observe(e.domElement),a.add(e.domElement),t.set(e.domElement,e),E(e))}),a.forEach(e=>{o.has(e)||(B?.unobserve(e),a.delete(e),t.delete(e))})}function O(){!i.value||!l.value||(r.value?.setViewport(0,0,f.width,f.height),r.value?.render(i.value,l.value))}function I(){R=s.value?.getBoundingClientRect(),r.value?.setScissorTest(!0),b.forEach(o=>{if(!o.scene||!o.isIntersecting||(E(o),!o.bounds))return;if(!o.camera){const g=o.scene.getObjectByProperty("isCamera",!0);if(!g)return;o.camera=g}const{left:e,bottom:m,width:h,height:v}=o.bounds,c=d.get(o);(!c||c.width!==h||c.height!==v)&&(me(o.camera,h,v),d.set(o,{width:h,height:v})),r.value?.setViewport(e,m,h,v),r.value?.setScissor(e,m,h,v),r.value?.render(o.scene,o.camera);const u=o.borderRadius.value;u.some(g=>g>0)&&(L.uniforms.uSize?.value.set(h,v),L.uniforms.uBorderRadius?.value.set(...u),r.value?.render(T,U))}),r.value?.setScissorTest(!1),R=void 0}return N(()=>{r.value&&(r.value.autoClear=!1,B=new IntersectionObserver(o=>{o.forEach(e=>{const m=t.get(e.target);m&&(e.isIntersecting&&E(m,e.boundingClientRect),m.isIntersecting=e.isIntersecting)})}),k())}),y(()=>{S.renderBelow?(I(),r.value?.clearDepth(),O()):(O(),r.value?.clearDepth(),I())}),V(b,k,{flush:"post"}),D(()=>{r.value&&(r.value.autoClear=!0),B?.disconnect(),b.forEach(o=>o.isIntersecting=!1)}),(o,e)=>(P(!0),Z($,null,H(C(b),([m,h])=>(P(),J(C(p),{key:m,view:h},null,8,["view"]))),128))}});export{Re as _,ge as a,pe as b,ye as c,ue as d,j as e,me as r,ce as t,fe as u,b as v};
