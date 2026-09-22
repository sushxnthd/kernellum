import{u as F,_ as N}from"./BEqJjq0f.js";import{d as G,V as O,O as q,e as X,b as j,M as z,P as H}from"./CV1CKauh.js";import{d as I,H as v,ae as K,o as V,h as L,k,al as b,u as i,p as Y,c as J,l as Q,F as W,x as Z,R as y,q as w,b as ee}from"./BWg2ILet.js";const $=`
   varying vec2 vMeshUv;
   varying vec2 vTexUv;
   uniform mat3 uUvTransform;
`,C=`
   vMeshUv = uv;
   vTexUv = (uUvTransform * vec3(uv, 1.0)).xy;
`,P=`
   uniform sampler2D uTexture;
   uniform vec4 uBorderRadius;
   uniform vec2 uResolution;
   varying vec2 vMeshUv;
   varying vec2 vTexUv;

   float sdRoundRect(vec2 p, vec2 b, vec4 r) {
      vec2 r2 = (p.x > 0.0) ? r.yz : r.xw;
      float radius = (p.y > 0.0) ? r2.x : r2.y;
      vec2 q = abs(p) - b + radius;
      return min(max(q.x, q.y), 0.0) + length(max(q, 0.0)) - radius;
   }
`,D=`
   vec2 maskHalfSize = uResolution * 0.5;
   vec2 maskP = (vMeshUv - 0.5) * uResolution;
   float maskDist = sdRoundRect(maskP, maskHalfSize, uBorderRadius);
   float maskAa = fwidth(maskDist) * 0.75;
   float maskAlpha = 1.0 - smoothstep(-maskAa, maskAa, maskDist);

   if (maskAlpha <= 0.0) discard;
   gl_FragColor = vec4(gl_FragColor.rgb, gl_FragColor.a * maskAlpha);
`,d=new Map,te=I({__name:"ThreeMediaPlane",props:{texture:{},aspect:{},fit:{default:"contain"},position:{default:()=>({x:.5,y:.5})},borderRadius:{default:()=>Z([0,0,0,0])},segments:{default:1},vertexShader:{default:void 0},fragmentShader:{default:void 0},uniforms:{default:void 0}},setup(u){const{onBeforeRender:f}=F(),o=u,n=y(),l=y(),T=y();let c;const _=new O,R=new X,M=new G,m={uTexture:{value:o.texture},uUvTransform:{value:M},uResolution:{value:_},uBorderRadius:{value:R},...o.uniforms},B=w(()=>o.vertexShader?`
      ${$}

      #define main userMain
      ${o.vertexShader}
      #undef main

      void main() {
         ${C}
         userMain();
      }
   `:`
         ${$}

         void main() {
            ${C}
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
         }
      `),E=w(()=>o.fragmentShader?`
      ${P}

      #define main userMain
      ${o.fragmentShader}
      #undef main

      void main() {
         userMain();
         ${D}

         #include <tonemapping_fragment>
         #include <colorspace_fragment>
      }
   `:`
         ${P}

         void main() {
            gl_FragColor = texture2D(uTexture, vTexUv);
            ${D}

            #include <tonemapping_fragment>
            #include <colorspace_fragment>
         }
      `);function S(e){if(!e)return;const t=d.get(e);t&&(t.count--,t.count<=0&&(t.geometry.dispose(),d.delete(e)))}return v(()=>o.texture,e=>{m.uTexture.value=e}),v(()=>o.uniforms,e=>{if(e)for(const[t,r]of Object.entries(e)){const a=r,s=m[t];s?s.value=a.value:m[t]=a}},{deep:!0}),v(()=>o.borderRadius,e=>{R.set(...e)},{immediate:!0}),v(()=>o.segments,e=>{const t=Array.isArray(e)?e[0]:e,r=Array.isArray(e)?e[1]:e,a=`${t}x${r}`;if(c===a)return;S(c);let s=d.get(a);s||(s={geometry:new H(1,1,t,r),count:0},d.set(a,s)),s.count++,c=a,T.value=s.geometry},{immediate:!0}),f(()=>{if(!n.value||!l.value||!o.texture)return;const e=n.value.right-n.value.left,t=n.value.top-n.value.bottom;if(e===0||t===0)return;const r=e/t,a=o.aspect,s=o.fit;let p=e,x=t;s==="contain"&&(r>a?p=t*a:x=e/a),l.value.scale.set(p,x,1),_.set(p,x);let h=1,g=1,U=0,A=0;s==="cover"&&(r>a?(g=a/r,A=(1-g)*o.position.y):(h=r/a,U=(1-h)*o.position.x)),M.set(h,0,U,0,g,A,0,0,1)}),K(()=>{S(c)}),(e,t)=>{const r=N;return V(),L(W,null,[k(r,{is:i(q),modelValue:i(n),"onUpdate:modelValue":t[0]||(t[0]=a=>b(n)?n.value=a:null),options:{position:[0,0,1]}},null,8,["is","modelValue"]),k(r,{is:i(z),modelValue:i(l),"onUpdate:modelValue":t[1]||(t[1]=a=>b(l)?l.value=a:null),options:{geometry:i(T),visible:!!u.texture}},{default:Y(()=>[u.texture?(V(),J(r,{key:0,is:i(j),options:{vertexShader:i(B),fragmentShader:i(E),uniforms:m,transparent:!0}},null,8,["is","options"])):Q("",!0)]),_:1},8,["is","modelValue","options"])],64)}}}),ne=Object.assign(te,{__name:"ThreeMediaPlane"});function se(){const{$lenis:u}=ee(),{onBeforeRender:f}=F(),o=`
      uniform float uVelocity;

      void main() {
         float intensity = 0.002;
         vec2 shift = vec2(0.0, uVelocity * intensity);

         float r = texture2D(uTexture, vTexUv + shift).r;
         float g = texture2D(uTexture, vTexUv).g; // Green stays anchored
         float b = texture2D(uTexture, vTexUv - shift).b;
         float a = texture2D(uTexture, vTexUv).a;

         gl_FragColor = vec4(r, g, b, a);
      }
   `,n={uVelocity:{value:0}};return f(()=>{n.uVelocity.value=u.value?.velocity??0}),{chromaticFragmentShader:o,chromaticUniforms:n}}export{ne as _,se as u};
