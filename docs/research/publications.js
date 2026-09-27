(() => {
  "use strict";

  const script = document.currentScript;
  const baseURL = script && script.src
    ? new URL(".", script.src)
    : new URL("./", window.location.href);

  const manifestURL = new URL("reports.json", baseURL);
  const stylesheetURL = new URL("publications.css", baseURL);

  function addStylesheet() {
    if (document.querySelector('link[data-kernellum-publications]')) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = stylesheetURL.href;
    link.dataset.kernellumPublications = "true";
    document.head.appendChild(link);
  }

  function node(tag, className, text) {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text !== undefined && text !== null) item.textContent = text;
    return item;
  }

  function reportURL(path) {
    return new URL(path, baseURL).href;
  }

  function actionLink(label, href, download) {
    const a = node("a", "krn-publications__action");
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    if (download) a.setAttribute("download", "");
    a.append(node("span", "", label));
    a.append(node("span", "krn-publications__arrow", "↗"));
    return a;
  }

  function reportRow(report) {
    const li = node("li", "krn-publications__row");
    const meta = node("div", "krn-publications__meta");
    meta.append(
      node("span", "krn-publications__eyebrow", report.id),
      node("time", "krn-publications__date", report.date),
      node("span", "krn-publications__type", report.type)
    );
    meta.querySelector("time").dateTime = report.dateISO;

    const body = node("div", "krn-publications__body");
    body.append(
      node("h3", "", report.title),
      node("p", "krn-publications__summary", report.summary),
      node("p", "krn-publications__result", report.result)
    );

    const links = node("div", "krn-publications__links");
    const href = reportURL(report.pdf);
    links.append(
      actionLink("Read PDF", href, false),
      actionLink("Download", href, true)
    );
    li.append(meta, body, links);
    return li;
  }

  function evidenceRow(report) {
    const wrapper = node("div", "krn-publications__evidence");
    const meta = node("div", "krn-publications__meta");
    meta.append(
      node("span", "krn-publications__evidence-mark", "E"),
      node("span", "krn-publications__eyebrow", report.id),
      node("time", "krn-publications__date", report.date)
    );
    meta.querySelector("time").dateTime = report.dateISO;

    const body = node("div", "krn-publications__body");
    body.append(
      node("h3", "", report.title),
      node("p", "krn-publications__summary", report.summary),
      node("p", "krn-publications__result", report.result)
    );

    const links = node("div", "krn-publications__links");
    const href = reportURL(report.pdf);
    links.append(
      actionLink("Open dossier", href, false),
      actionLink("Download", href, true)
    );
    wrapper.append(meta, body, links);
    return wrapper;
  }

  async function mount() {
    if (document.getElementById("research-publications")) return;

    const main = document.querySelector(".page-wrapper main") || document.querySelector("main");
    if (!main) return;

    let data;
    try {
      const response = await fetch(manifestURL.href, { cache: "no-cache" });
      if (!response.ok) return;
      data = await response.json();
    } catch (_) {
      return;
    }

    const reports = (data.reports || [])
      .filter(item => item && item.published !== false)
      .sort((a, b) => String(b.dateISO).localeCompare(String(a.dateISO)));

    const evidence = (data.evidence || [])
      .filter(item => item && item.published !== false)
      .sort((a, b) => String(b.dateISO).localeCompare(String(a.dateISO)));

    if (!reports.length && !evidence.length) return;

    addStylesheet();

    const section = node("section", "krn-publications");
    section.id = "research-publications";
    section.setAttribute("aria-labelledby", "research-publications-title");

    const head = node("div", "krn-publications__head");
    head.append(node("p", "krn-publications__label", "Publication Archive"));

    const intro = node("div", "krn-publications__intro");
    const title = node("h2", "", "Technical reports");
    title.id = "research-publications-title";
    intro.append(
      title,
      node("p", "", "Methods, measurements, and reproducible evidence from Kernellum Research. Reports are published against the date the underlying result was established.")
    );
    head.append(intro, node("p", "krn-publications__year", "2026 —"));

    section.append(head);

    if (reports.length) {
      const list = node("ol", "krn-publications__list");
      reports.forEach(report => list.append(reportRow(report)));
      section.append(list);
    }

    if (evidence.length) {
      evidence.forEach(item => section.append(evidenceRow(item)));
    }

    const note = node(
      "p",
      "krn-publications__note",
      "The archive is publication-driven: new reports are added as immutable PDFs with stable report IDs and dates, without changing the research-page layout."
    );
    section.append(note);
    main.append(section);
  }

  function scheduleMount() {
    requestAnimationFrame(() => requestAnimationFrame(mount));
  }

  if (document.readyState === "complete") {
    scheduleMount();
  } else {
    window.addEventListener("load", scheduleMount, { once: true });
  }
})();
