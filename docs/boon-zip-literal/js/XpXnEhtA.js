import{d as T,o as s,c as p,r as K,a as Q,m as v,u as r,b as H,e as X,f as J,g as x,w as M,h as l,i as d,F as w,j as N,k as B,_ as U,t as b,l as u,n as V,p as O,q as $,s as z,v as Z,x as ee,y as te,z as G,A as ne,B as se,C as oe,D as S,E as ae}from"./BWg2ILet.js";import re from"./C9JD9LUG.js";import C from"./D2jCMkLa.js";import ie from"./DMftEAj3.js";import ce from"./DYLIcWIl.js";import{_ as le,f as _e,c as de,r as ue}from"./Bq-CSWMy.js";import pe from"./BcInndtU.js";import me from"./CKK_ITnc.js";import{b as P,i as R,a as m,m as Y,p as I,c as q,l as W,d as ye,n as E,s as he,g as ge,u as ke}from"./Cs1zKDta.js";import{u as $e}from"./Cecn1SPc.js";import"./DTVziQxs.js";import"./BSgwrZLn.js";import"./CpJfINCX.js";import"./CV1CKauh.js";import"./DRE_wQ1D.js";import"./CcGBHYOs.js";import"./By-qMKMM.js";import"./BEqJjq0f.js";import"./wa5M3ceU.js";import"./BkXUNdA6.js";import"./CwAE7HMs.js";import"./DipsUwhN.js";import"./D-KWWw4O.js";import"./Y-Lt9TyD.js";import"./CzsHsjRX.js";import"./Cnn4cZyj.js";import"./Beq67LXS.js";import"./BEW1fCGd.js";const xe=T({__name:"ModuleRenderer",props:{data:{}},setup(e){const{_key:t,...o}=e.data;return(a,_)=>(s(),p(K("Lazy"+Q(o._type)),v(o,{"data-key":r(t)}),null,16,["data-key"]))}}),fe=Object.assign(xe,{__name:"ModuleRenderer"}),be={ref:"section",class:"sock"},ve={class:"images"},we={class:"content"},Te=T({__name:"Sock",props:{blockText:{},images:{}},setup(e){const{utils:t,splitText:o,createTimeline:a,onScroll:_}=H().$anime,y=X("section");return J({root:y},n=>{const i=t.$(".image-wrapper"),c=t.$("img"),h=t.$(".btn");o("h2",{lines:{wrap:!0}}).addEffect(({lines:g})=>{t.set(g,{y:"100%"}),h&&t.set(h,{opacity:0});const k=a({defaults:{duration:100,ease:"none"},autoplay:_({target:n?.root,enter:"bottom top",leave:"bottom bottom",sync:.5})}).add(c[0],{scale:[1.15,1]},0).add(i[1],{x:["-10%","0%"]},0).add(c[1],{x:["5%","0%"]},0).add(i[2],{y:["50%","0%"]},0).add(c[2],{y:["-25%","0%"]},0).add(i[3],{y:["-50%","0%"]},0).add(c[3],{y:["25%","0%"]},0).add(g,{y:["100%","0%"],duration:60},40);return h&&k.add(h,{opacity:[0,1],y:["50%","0%"],duration:50},50),k})}),(n,i)=>{const c=re,h=C,g=x("theme"),k=x("particles");return M((s(),l("section",be,[d("div",ve,[(s(!0),l(w,null,N(e.images,f=>(s(),p(c,{key:f._key,image:f,fit:"cover"},null,8,["image"]))),128))]),d("div",we,[B(h,{blocks:e.blockText,layout:"centered"},null,8,["blocks"])])])),[[g,"dark"],[k,"none"]])}}}),De=Object.assign(U(Te,[["__scopeId","data-v-511f88dc"]]),{__name:"Sock"}),Ee={class:"legal-page"},Ie={class:"header"},Se={class:"title"},Be={class:"content-wrapper"},Me={class:"content"},Ne=T({__name:"LegalPage",props:{title:{},blockText:{}},setup(e){return(t,o)=>{const a=C,_=x("theme"),y=x("particles");return M((s(),l("section",Ee,[d("header",Ie,[d("h1",Se,b(e.title),1)]),o[0]||(o[0]=d("div",{class:"divider"},null,-1)),d("div",Be,[d("div",Me,[e.blockText?(s(),p(a,{key:0,blocks:e.blockText},null,8,["blocks"])):u("",!0)])])])),[[_,"light"],[y,"none"]])}}}),Ce=Object.assign(U(Ne,[["__scopeId","data-v-84b67a18"]]),{__name:"LegalPage"}),Pe={class:"news-index"},Re={key:0,class:"page-header-index"},Le={key:1,class:"articles"},Ae=T({__name:"NewsIndex",props:{_id:{},_type:{},_rev:{},blockText:{},slug:{},seo:{},entries:{}},setup(e){return(t,o)=>{const a=C,_=ie,y=x("theme"),n=x("particles");return M((s(),l("section",Pe,[e.blockText?(s(),l("div",Re,[B(a,{blocks:e.blockText,layout:"centered"},null,8,["blocks"])])):u("",!0),e.entries?(s(),l("div",Le,[(s(!0),l(w,null,N(e.entries,i=>(s(),p(_,v({key:i._id},{ref_for:!0},i),null,16))),128))])):u("",!0)])),[[y,"dark"],[n]])}}}),je=Object.assign(Ae,{__name:"NewsIndex"}),Ue=(e,t="")=>{const o=encodeURIComponent(e),a=encodeURIComponent(t);return[{label:"Facebook",url:`https://www.facebook.com/sharer/sharer.php?u=${o}`},{label:"LinkedIn",url:`https://www.linkedin.com/sharing/share-offsite/?url=${o}`},{label:"X",url:`https://twitter.com/intent/tweet?url=${o}&text=${a}`}]},Fe={class:"news-entry"},He={class:"header"},Ve={class:"back-to-index"},Oe={class:"title"},ze={class:"content-wrapper"},Ge={class:"meta"},Ye={key:0},qe={key:1},We={key:2},Ke={class:"content"},Qe={class:"actions"},Xe={key:0,class:"share"},Je=["href"],Ze=T({__name:"NewsEntry",props:{title:{},author:{},publisher:{},publishedDate:{},categories:{},image:{},blockText:{},url:{}},setup(e){const t=e,o=$(()=>{if(!t.url)return"/";const c=t.url.replace(/^\/+|\/+$/g,"").split("/").slice(0,-1).join("/");return c?`/${c}/`:"/"}),a=$(()=>{if(!t.blockText?.length)return;const i=t.blockText.flatMap(h=>(h.children??[]).map(g=>g.text??"")).join(" "),c=de(i);return c>0?c:void 0}),_=V(),y=z(),n=$(()=>{const i=y.public?.siteUrl??"";return Ue(`${i}${_.path}`,t.title)});return(i,c)=>{const h=ce,g=le,k=pe,f=C,L=me,A=x("theme"),j=x("particles");return M((s(),l("section",Fe,[d("header",He,[d("div",Ve,[B(g,{to:r(o)},{default:O(()=>[B(h,{type:"arrowRight",class:"rotated",color:"black","hover-color":"orange"})]),_:1},8,["to"])]),d("h1",Oe,b(e.title),1)]),c[0]||(c[0]=d("div",{class:"divider"},null,-1)),d("div",ze,[d("aside",Ge,[e.author?(s(),l("p",Ye,b(e.author),1)):u("",!0),e.publishedDate?(s(),l("p",qe,b(("formatDate"in i?i.formatDate:r(_e))(e.publishedDate,"MMMM D, YYYY")),1)):u("",!0),r(a)?(s(),l("p",We,b(r(a))+" min read",1)):u("",!0)]),d("div",Ke,[e.image?(s(),p(k,{key:0,image:e.image,class:"hero",loading:"preload"},null,8,["image"])):u("",!0),e.blockText?(s(),p(f,{key:1,blocks:e.blockText},null,8,["blocks"])):u("",!0),d("div",Qe,[r(o)?(s(),p(L,{key:0,link:{type:"page",slug:r(o)},text:"Back to Index",variant:"outline"},null,8,["link"])):u("",!0)])]),r(n).length?(s(),l("aside",Xe,[(s(!0),l(w,null,N(r(n),D=>(s(),l("a",{key:D.label,href:D.url,target:"_blank",rel:"noopener noreferrer"},b(D.label),9,Je))),128))])):u("",!0)])])),[[A,"light"],[j,"none"]])}}}),et=Object.assign(U(Ze,[["__scopeId","data-v-5adf46ee"]]),{__name:"NewsEntry"}),tt=`
_type == 'pageHeader' => {
   type,
   title,
   subtitle,
   type == 'home' => {
      scrollText
   },
   type != 'home' => {
      cta {
         ${P}
      }
   },
   images[] {
      _key,
      ${R}
   }
}`,nt=`
_type == 'textMedia' => {
   theme,
   ${m},
   mediaSide,
   ${Y}
}`,st=`
_type == 'cardGrid' => {
   theme,
   ${I},
   cardType,
   grid,
   ${m},
   cards[] {
      _key,
      ${Y},
      title,
      text[] {
         ${q}
      },
      button {
         ${P}
      }
   }
}`,ot=`
_type == 'linkList' => {
   theme,
   ${m},
   links[] {
      _key,
      title,
      subtitle,
      ${W}
   }
}`,at=`
_type == 'testimonialBlock' => {
   theme,
   ${I},
   testimonials[]-> {
      _id,
      quote,
      citation
   },
}`,rt=`
_type == 'centeredText' => {
   ${I},
   mainText,
   includeRolodexText,
   includeRolodexText == true => {
      rolodexText[]
   },
   includeCta,
   includeCta == true => {
      cta {
         ${P}
      }
   },
   cards[] {
      _key,
      type,
      type == 'stat' => {
         statValue
      },
      type != 'insight' => {
         title,
         description
      },
      type == 'textImage' || type == 'link' => {
         ${ye}
      },
      type == 'link' => {
         ${W}
      },
      type == 'insight' => {
         "title": newsEntry->title,
         "image": newsEntry->image { ${R} },
         "publisher": newsEntry->publisher,
         "publishedDate": newsEntry->publishedDate
      }
   }
}`,it=`
_type == 'teamGrid' => {
   theme,
   eyebrow,
   ${m},
   people[]-> {
      _id,
      name,
      role,
      'portrait': portrait {
         ${R}
      }
   }
}`,ct=`
_type == 'expandableBlocks' => {
   theme,
   ${I},
   ${m},
   items[] {
      _key,
      headline,
      ${m},
      x,
      y,
   }
}`,lt=`
_type == 'formBlock' => {
   ${m},
   form -> {
      ...,
      "redirectUrl": redirectUrl->slug.current,
   }
}`,_t=`
_type == 'textIntro' => {
   label,
   highlightText,
   content[] {
      ${q}
   }
}`,dt=`
_type == 'largeText' => {
   ${I},
   ${m}
}`,ut=`
_type == 'featuredArticles' => {
   theme,
   ${m},
   type,
   type == 'latest' => {
      "entries": *[_type == 'newsEntry'] | order(publishedDate desc) [0...3] {
         ${E}
      }
   },
   type == 'cat' => {
      "entries": *[
         _type == 'newsEntry' &&
         references(^.categories[]._ref)
      ] | order(publishedDate desc) [0...3] {
         ${E}
      }
   },
   type == 'custom' => {
      entries[] -> {
         ${E} 
      }
   },
   cta {
      ${P}
   }
}`,pt=`
   pageModules[] {
      _key,
      _type,
      ${tt},
      ${nt},
      ${st},
      ${ot},
      ${at},
      ${rt},
      ${it},
      ${ct},
      ${lt},
      ${_t},
      ${dt},
      ${ut}
   }
`,mt=ge`
   *[_type in ['page', 'newsIndex','newsEntry'] && slug.current == $slug][0] {
      _type,
      _id,
      _rev,
      title,
      slug,
      type,
      showParticles,
      type == 'default' => {
         ${pt},
         sock -> {
            ${m},
            images[] {
               _key,
               ${R}
            }
         }
      },
      type == 'legal' => {
         ${m},
      },
      _type == 'newsIndex' => {
         ${m},
         'entries': *[_type == 'newsEntry'][] {
            ${E}
         },
      },
      _type == 'newsEntry' => {
         _rev,
         title,
         ${E},
         ${m},
      },
      ${he}
   }
`;function yt(){const e=Z("pageState",()=>({page:{}})),t=a=>{e.value=a},o=(a,_)=>{e.value[a]=_};return{globalState:ee(e),setState:t,setValue:o}}const ht=e=>{const{enabled:t}=te();G(()=>{if(!t.value&&!e?._id)throw ne({statusCode:404,statusMessage:"Page Not Found",fatal:!0})})};function gt(e,t,o=!1){const{$getImageUrlBuilder:a}=H(),_=z(),y=$(()=>e?.image?.asset?a(e.image.asset)?.width(1200).url():t?.image?.asset?a(t.image.asset)?.width(1200).url():null),n=$(()=>e?.description??t?.description??null),i=$(()=>e?.title??t?.title??null),c=$(()=>e?.noindex??!1);se({title:i.value,ogTitle:i.value,description:n.value,ogDescription:n.value,ogImage:y.value,robots:{noindex:c.value},titleTemplate:o?`${_.public.siteName} • %s `:`%s • ${_.public.siteName}`,articleModifiedTime:e?.updatedAt,articlePublishedTime:e?.createdAt})}const Yt=T({__name:"[...slug]",async setup(e){let t,o;const a=V(),{watchForFresh:_}=$e(),{setValue:y}=yt(),{data:n,refresh:i}=([t,o]=oe(()=>ke(mt,{slug:a.path==="/"?"/":ue(a.path)})),t=await t,o(),t),c=$(()=>{if(n.value&&"sock"in n.value)return n.value.sock});return G(()=>{y("page",{type:n.value?._type,id:n.value?._id})}),_(i),ht(n.value),gt(n.value?.seo,n.value?.globalSeo,a.path==="/"),(h,g)=>{const k=fe,f=De,L=Ce,A=je,j=et,D=ae;return s(),p(D,{key:r(n)?._rev},{default:O(()=>[r(n)?._type==="page"?(s(),l(w,{key:0},[r(n)?.type==="default"?(s(),l(w,{key:0},["pageModules"in r(n)?(s(!0),l(w,{key:0},N(r(n)?.pageModules,F=>(s(),p(k,{key:F._key,data:F},null,8,["data"]))),128)):u("",!0),r(c)?(s(),p(f,S(v({key:1},r(c))),null,16)):u("",!0)],64)):r(n)?.type==="legal"?(s(),p(L,S(v({key:1},r(n))),null,16)):u("",!0)],64)):r(n)?._type==="newsIndex"?(s(),p(A,S(v({key:1},r(n))),null,16)):r(n)?._type==="newsEntry"?(s(),p(j,S(v({key:2},r(n))),null,16)):u("",!0)]),_:1})}}});export{Yt as default};
