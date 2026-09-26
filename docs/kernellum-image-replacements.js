(() => {
  const assets = [
    "/kernellum/kernellum-assets/study-wafer.webp",
    "/kernellum/kernellum-assets/study-researcher.webp",
    "/kernellum/kernellum-assets/study-die.webp",
    "/kernellum/kernellum-assets/architecture-die.svg",
    "/kernellum/kernellum-assets/measurement-array.svg",
    "/kernellum/kernellum-assets/route-topology.svg",
    "/kernellum/kernellum-assets/timing-field.svg",
    "/kernellum/kernellum-assets/particle-image.png"
  ];

  const pageOffsets = {
    "/kernellum/": 0,
    "/kernellum/what-we-do/": 2,
    "/kernellum/who-we-are/": 4,
    "/kernellum/careers/": 5,
    "/kernellum/contact/": 6,
    "/kernellum/insights/": 7
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