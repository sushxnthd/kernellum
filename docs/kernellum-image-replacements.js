(() => {
  const assets = Array.from({ length: 13 }, (_, i) =>
    `/kernellum/kernellum-replacements/${String(i + 1).padStart(2, "0")}.png`
  );

  const pageOffsets = {
    "/kernellum/": 0,
    "/kernellum/what-we-do/": 4,
    "/kernellum/who-we-are/": 7,
    "/kernellum/careers/": 10,
    "/kernellum/contact/": 10,
    "/kernellum/insights/": 12
  };

  const cleanPath = location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  const offset = pageOffsets[cleanPath] ?? 0;

  function replaceImages() {
    const wrappers = [...document.querySelectorAll(".image-wrapper")];

    wrappers.forEach((wrapper, index) => {
      const img = wrapper.querySelector("img");
      if (!img) return;

      const asset = assets[(offset + index) % assets.length];

      wrapper.querySelectorAll("source").forEach(source => {
        source.removeAttribute("srcset");
        source.removeAttribute("sizes");
      });

      if (img.dataset.kernellumReplacement !== asset) {
        img.dataset.kernellumReplacement = asset;
        img.removeAttribute("srcset");
        img.removeAttribute("sizes");
        img.src = asset;
        img.style.filter = "none";
      }
    });
  }

  replaceImages();

  let queued = false;
  const observer = new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      replaceImages();
    });
  });

  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["src", "srcset"]
  });
})();
