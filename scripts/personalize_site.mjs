import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('docs');
const replacements=new Map([
 ['Build The Evidence','Architecture. Proven.'],
 ['Build the Evidence Loop','From Model to Metal'],
 ['Kernellum closes the loop between workload, architecture, RTL, and routed physical evidence.','AI-native architecture research. Workload-specific accelerators, tested against synthesis, timing, and routing.'],
 ['Reason continuously and anticipate behavioural responses.\nOwn what happens next. ','From workload to architecture. From architecture to RTL. From RTL to routed evidence. '],
 ['A New Hardware Design Loop','Design. Route. Learn.'],
 ['Human centricity','Reproducibility'],
 ['Craftsmanship','Measured claims'],
 ['Our Team','Open Research'],
 ['Join our team','Build with Kernellum'],
 ['Career openings','Explore the research'],
 ['Senior AI Engineer','Research principle / 01'],
 ['Technology & Platform Developer','Research principle / 02'],
 ['It is rare to bring together a team of such diverse expertise and yet still maintain a deeply collaborative and collegiate environment. We seem to find novel and innovative ways to solve problems almost every day.','A predicted advantage is a hypothesis. Synthesis and routing tell us which architecture choices survive implementation.'],
 ['From the top-down, research and innovation are encouraged, and failure, learning and iteration is seen as the key to how we solve new and deeply complex problems. We are genuinely breaking new ground.','Publish the constraints, the baselines, and the failures. A result should be inspectable before it becomes a claim.'],
 ['We are a multidisciplinary team of operators, scientists, and engineers focused on one mission: helping decision-makers act with clarity in complex, high-stakes environments.','Kernellum is an independent research effort connecting AI workloads to accelerator architecture and reproducible physical-design evidence.'],
 ['A reasoning partner built around the operator, drawing on their experience and intuition, expanding their solution space, and encouraging creative thinking without diminishing their judgment','Begin with actual kernels, memory demands, and deployment constraints. Search the architectures those workloads can use.'],
 ['KERNELLUM uses behavioural science, enabled with reasoning-based AI agents, to enhance decision quality and operational outcomes, delivering cross-domain optionality by surfacing adversarial vulnerabilities, and predicting second and third order effects','Connect architecture models to RTL, verification, synthesis, and routing. Feed implementation results back into the next search.'],
 ['Proven in live operational environments, not demos or theoretical models. KERNELLUM is tested, adapted, and refined where real decisions are made.','K1 studies an INT8 GEMM architecture family on ECP5. Reported latency is derived from cycle counts and final-routed timing, not physical-board measurements.'],
 ['Physically Validated Evidence','Routed evidence'],
 ['Agnostic, sovereign, and adaptable by design, KERNELLUM integrates into existing command structures, data pipelines and infrastructure without friction.','Open RTL, reproducible experiments, and explicit target constraints keep the evidence inspectable. Results are scoped to the implementation family tested.'],
 ['Operational Agility','Reproducible experiments'],
 ['KERNELLUM continuously updates objectives and constraints as conditions shift, ensuring that your planning, execution, and assessment stay aligned with reality.','Search learns from final-route timing and implementation costs. Candidate rankings are tested on held-out configurations rather than assumed to transfer.'],
 ['Built for the Win','Built to be tested'],
 ['Most systems stop at the decision or the strike, leaving commanders blind to the effects that follow.','Architecture estimates are only the beginning. Implementation exposes the timing and routing costs that analytical models can miss.'],
 ['We combine behavioral science and AI to understand human behavior, intent, and influence, and predict what comes next.','We connect workload analysis, accelerator architecture, and final-route timing to test which predicted gains survive implementation.'],
 ['Map Key Drivers ','Map the workload'],['Anticipate response','Search architectures'],['Track effects','Measure implementation'],['Adapt at tempo','Close the loop'],
 ['Model how dataflow, memory, and topology choices change timing, area, and energy.','Test how dataflow, memory, and topology choices change resource use and final-route timing.'],
 ['We win as one','Make the result reproducible'],
 ['At Kernellum, you\'re not just joining a company, you\'re becoming part of a mission to harness the power of technology for the betterment of society.  ','Contribute to open hardware research through reproducible experiments, RTL verification, and architecture analysis.'],
 ['Press Inquires','Research enquiries'],['Job openings ','Contribute on GitHub'],
 ['ISO/IEC 27001 Cert.','Research repository'],
 ['stylized image of a helicopter in motion','accelerator architecture study'],
 ["Kernellum research workspace's face",'hardware research study'],
 ]);
const escapeHtml=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
for(const file of walk(root)){
 if(!/\.(html|js|css|json|webmanifest)$/.test(file))continue;
 let s=fs.readFileSync(file,'utf8').replaceAll('\\u002F','/');
 s=s.replaceAll('https://www.linkedin.com/company/boon-io/','https://github.com/sushxnthd/kernellum');
 if(file.endsWith('.json')||file.endsWith('replica-data.js'))s=s.replace(/\/kernellum\/(what-we-do|who-we-are|careers|contact|legal|insights)/g,'/$1');
 for(const [a,b]of replacements){s=s.replaceAll(a,b).replaceAll(JSON.stringify(a).slice(1,-1),JSON.stringify(b).slice(1,-1));if(file.endsWith('.html'))s=s.replaceAll(escapeHtml(a),escapeHtml(b));}
 s=s.replaceAll('https://cdn.sanity.io/images/cktal3h7/production/6e6c3150c4aee4b572782ae46c37e742f19fb173-1600x1066.png','/kernellum/kernellum-replacements/04.png');
 s=s.replaceAll('https://cdn.sanity.io/images/cktal3h7/production/d40065334339bf34f53b28717da2543132da8afe-572x456.png','/kernellum/kernellum-replacements/12.png');
 // The Nuxt router owns the project prefix. Content slugs stay route-relative.
 s=s.replace(/(?<!\/kernellum)\/(?:_nuxt|fonts|favi|media-files|media-originals|media-rendered|kernellum-assets)(?=\/)/g,m=>'/kernellum'+m);
 if(file.endsWith('.html')){
   s=s.replace(/href="\/(?!\/|kernellum\/)([^"]*)"/g,'href="/kernellum/$1"');

   const rel=path.relative(root,file).replaceAll('\\\\','/');
   const pageMaps={
     'index.html':[1,2,3,4,5,6,7,8,9],
     'what-we-do/index.html':[10,11,12,5,6,7,8,9],
     'who-we-are/index.html':[1,3,4,9],
     'careers/index.html':[11,2,6,9],
     'contact/index.html':[5,6,7,8,9],
     'insights/index.html':[9],
     'legal/privacy-policy/index.html':[9],
     'legal/terms-of-use/index.html':[9]
   };
   const map=pageMaps[rel]||[];
   let imageIndex=0;
   s=s.replace(/<link\\b[^>]*rel="preload"[^>]*as="image"[^>]*>/gi,'');
   s=s.replace(/<source\\b[^>]*>/gi,'');
   s=s.replace(/<img\\b[^>]*>/gi,tag=>{
     const n=map[imageIndex]||((imageIndex%13)+1); imageIndex++;
     const asset='/kernellum/kernellum-replacements/'+String(n).padStart(2,'0')+'.png';
     let t=tag.replace(/\\s+srcset="[^"]*"/gi,'').replace(/\\s+sizes="[^"]*"/gi,'').replace(/\\s+src="[^"]*"/gi,'');
     return t.replace(/^<img\\b/i,'<img src="'+asset+'"');
   });
   const og=(map[0]||9).toString().padStart(2,'0');
   s=s.replace(/<meta property="og:image" content="[^"]*">/i,'<meta property="og:image" content="/kernellum/kernellum-replacements/'+og+'.png">');
   s=s.replaceAll('/kernellum/media-originals/6e6c3150c4aee4b572782ae46c37e742f19fb173-1600x1066.png','/kernellum/kernellum-replacements/04.png');
   s=s.replaceAll('/kernellum/media-originals/d40065334339bf34f53b28717da2543132da8afe-572x456.png','/kernellum/kernellum-replacements/12.png');
   s=s.replace('baseURL:"/"','baseURL:"/kernellum/"');
   s=s.replaceAll('buildAssetsDir:"/kernellum/_nuxt/"','buildAssetsDir:"/_nuxt/"');
   s=s.replace(/<link[^>]+(?:rel="(?:icon|apple-touch-icon)"|href="[^\"]*favicon[^\"]*")[^>]*>/g,'');
   s=s.replaceAll('<link rel="stylesheet" href="/kernellum/kernellum-brand.css">','');
   s=s.replace('</head>','<link rel="icon" type="image/svg+xml" href="/kernellum/favi/kernellum.svg"><link rel="stylesheet" href="/kernellum/kernellum-brand.css"></head>');
   s=s.replaceAll('<script src="/kernellum/kernellum-image-replacements.js" defer></script>','');
   s=s.replace('</body>','<script src="/kernellum/kernellum-image-replacements.js" defer></script></body>');
   s=s.replace(/<svg[^>]*viewBox="0 0 89 24"[^>]*>[\s\S]*?<\/svg>/g,'<svg viewBox="0 0 248 32" role="img" aria-label="Kernellum"><path fill="#b9f35d" d="M0 1h5v13L18 1h7L10 16l15 15h-7L5 18v13H0z"/><text x="35" y="25" fill="currentColor" font-family="MSCHN, sans-serif" font-size="27" letter-spacing="1">KERNELLUM</text></svg>');
 }
 fs.writeFileSync(file,s);
}
const logo=`import{o as t,h as c,i as e}from"./BWg2ILet.js";const r={xmlns:"http://www.w3.org/2000/svg",viewBox:"0 0 248 32",role:"img","aria-label":"Kernellum"};function n(s,o){return t(),c("svg",r,[e("path",{fill:"#b9f35d",d:"M0 1h5v13L18 1h7L10 16l15 15h-7L5 18v13H0z"}),e("text",{x:35,y:25,fill:"currentColor","font-family":"MSCHN, sans-serif","font-size":27,"letter-spacing":1},"KERNELLUM")])}export{n as render};export default{render:n};`;
fs.writeFileSync(path.join(root,'_nuxt/DHMWGXoR.js'),logo);
console.log('Applied Kernellum identity and research copy.');
