(() => {
  const A = n => n === 1 ? "/kernellum/kernellum-replacements/01-hero-v2.webp" : `/kernellum/kernellum-replacements/${String(n).padStart(2, "0")}.png`;

  // Every raster/image slot on every page is assigned to the new Kernellum set.
  // No legacy Boon image, earlier Kernellum placeholder, or responsive derivative
  // is allowed to survive hydration.
  const pageAssets = {
    "/kernellum/":                 [1,2,3,4,5,6,7,8,9],
    "/kernellum/what-we-do/":      [10,11,12,5,6,7,8,9],
    "/kernellum/who-we-are/":      [1,3,4,9],
    "/kernellum/careers/":         [11,2,6,9],
    "/kernellum/contact/":         [5,6,7,8,9],
    "/kernellum/insights/":        [9],
    "/kernellum/legal/privacy-policy/": [9],
    "/kernellum/legal/terms-of-use/":   [9]
  };

  function pathKey() {
    return location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  }

  function removeResearchRepositoryHoverImage() {
    document.querySelectorAll("footer .secondary a").forEach(link => {
      if ((link.textContent || "").toLowerCase().includes("research repository")) {
        link.querySelectorAll(".hover-image, figure.image-wrapper").forEach(el => el.remove());
      }
    });
  }

  function replaceAllImages() {
    removeResearchRepositoryHoverImage();
    const map = pageAssets[pathKey()] || [];
    const images = [...document.querySelectorAll("img")];

    images.forEach((img, index) => {
      const asset = A(map[index] || ((index % 13) + 1));

      const picture = img.closest("picture");
      if (picture) {
        picture.querySelectorAll("source").forEach(source => {
          source.removeAttribute("srcset");
          source.removeAttribute("sizes");
        });
      }

      img.removeAttribute("srcset");
      img.removeAttribute("sizes");
      if (img.getAttribute("src") !== asset) img.setAttribute("src", asset);
      img.dataset.kernellumReplacement = asset;
      img.style.filter = "none";
    });
  }

  replaceAllImages();
  removeResearchRepositoryHoverImage();

  let queued = false;
  const observer = new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      replaceAllImages();
      removeResearchRepositoryHoverImage();
    });
  });

  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["src", "srcset", "sizes"]
  });
})();
