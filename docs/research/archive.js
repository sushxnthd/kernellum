(function(){
  "use strict";
  const archive = window.KernellumResearchArchive;
  if (!archive) return;
  const esc = (v) => String(v).replace(/[&<>"']/g, (ch) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  const metric = (m) => '<span class="krn-metric">'+esc(m)+'</span>';
  const link = (href,label,primary,external) => '<a class="krn-archive-link'+(primary?' primary':'')+'" href="'+esc(href)+'"'+(external?' target="_blank" rel="noopener noreferrer"':'')+'>'+esc(label)+' <span aria-hidden="true">↗</span></a>';
  function render(){
    if (document.getElementById("research-publications")) return;
    const main = document.querySelector("main");
    if (!main) return;
    const sections = Array.from(main.querySelectorAll(":scope > section"));
    const nextSection = sections.find((section) => {
      const label = section.querySelector(".text-label");
      return label && label.textContent.trim().toLowerCase() === "next falsification";
    });
    const featured = archive.reports.filter((r) => r.featured);
    const reportRows = archive.reports.map((r) => '<article class="krn-report-row">'+
      '<div class="krn-archive-id">'+esc(r.shortId)+'</div>'+
      '<time class="krn-archive-date" datetime="'+esc(r.date)+'">'+esc(r.dateLabel)+'</time>'+
      '<div class="krn-report-copy"><h4>'+esc(r.title)+'</h4><p>'+esc(r.summary)+'</p></div>'+
      '<div class="krn-report-actions">'+link(r.href,"Read report",true,false)+'</div>'+
    '</article>').join("");
    const featureCards = featured.map((r) => '<article class="krn-feature-card">'+
      '<div class="krn-feature-top"><span class="krn-archive-id">'+esc(r.id)+'</span><time datetime="'+esc(r.date)+'">'+esc(r.dateLabel)+'</time></div>'+
      '<h3 class="krn-feature-title">'+esc(r.title)+'</h3>'+
      '<p class="krn-feature-summary">'+esc(r.summary)+'</p>'+
      '<div class="krn-metrics">'+r.metrics.map(metric).join("")+'</div>'+
      '<div class="krn-card-links">'+link(r.href,"Read report",true,false)+link(r.source,"Source record",false,true)+'</div>'+
    '</article>').join("");
    const ev = archive.evidence;
    const html = '<div class="krn-archive-wrap">'+
      '<header class="krn-archive-heading"><div><span class="krn-archive-eyebrow">Research publications</span></div><div><h2>Technical reports and evidence.</h2><p>Permanent publication records for Kernellum\'s compiler, routed architecture search, causal timing work, and claim-to-artifact evidence stack.</p></div></header>'+
      '<div class="krn-archive-block"><div class="krn-archive-block-head"><div><span class="krn-archive-kicker">Featured research</span><h3>Current reports</h3></div><span class="krn-archive-count">'+featured.length.toString().padStart(2,"0")+' featured</span></div><div class="krn-feature-grid">'+featureCards+'</div></div>'+
      '<div class="krn-archive-block"><div class="krn-archive-block-head"><div><span class="krn-archive-kicker">Publication index</span><h3>Technical reports</h3></div><span class="krn-archive-count">'+archive.reports.length.toString().padStart(2,"0")+' reports</span></div><div class="krn-report-list">'+reportRows+'</div></div>'+
      '<div class="krn-archive-block"><div class="krn-evidence-panel"><div><span class="krn-archive-kicker">'+esc(ev.id)+'</span><h3>'+esc(ev.title)+'</h3></div><div class="krn-evidence-copy"><p>'+esc(ev.summary)+'</p><div class="krn-metrics">'+ev.metrics.map(metric).join("")+'</div><div class="krn-card-links">'+link(ev.href,"Open dossier",true,false)+link(ev.source,"Evidence index",false,true)+'</div></div></div></div>'+
    '</div>';
    const section = document.createElement("section");
    section.id = "research-publications";
    section.className = "krn-archive-shell";
    section.setAttribute("aria-label","Kernellum research publications");
    section.innerHTML = html;
    if (nextSection) main.insertBefore(section,nextSection); else main.appendChild(section);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded",()=>setTimeout(render,0),{once:true});
  else setTimeout(render,0);
  window.addEventListener("pageshow",render,{once:true});
})();