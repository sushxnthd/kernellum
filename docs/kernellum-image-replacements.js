(() => {
  const A = n => n === 1 ? "/kernellum-replacements/01-hero-v2.webp" : `/kernellum-replacements/${String(n).padStart(2, "0")}.png`;

  // Every raster/image slot on every page is assigned to the new Kernellum set.
  // No legacy Boon image, earlier Kernellum placeholder, or responsive derivative
  // is allowed to survive hydration.
  const pageAssets = {
    "/":                 [1,2,3,4,5,6,7,8,9],
    "/architecture/":      [10,11,12,5,6,7,8,9],
    "/research/":      [1,3,4,9],
    "/contribute/":         [11,2,6,9],
    "/collaborate/":         [5,6,7,8,9],
    "/insights/":        [9],
    "/legal/privacy-policy/": [9],
    "/legal/terms-of-use/":   [9]
  };

  function pathKey() {
    return location.pathname.endsWith("/") ? location.pathname : location.pathname + "/";
  }


  function prioritizeResearchNav() {
    document.querySelectorAll("header nav ul").forEach(list => {
      const items = [...list.children];
      const research = items.find(item => item.querySelector('a[href="/research/"], a[href="/research"]'));
      const architecture = items.find(item => item.querySelector('a[href="/architecture/"], a[href="/architecture"]'));
      if (research && architecture && research.nextElementSibling !== architecture) {
        list.insertBefore(research, architecture);
      }
    });
  }

  function fixKernellumLinks() {
    document.querySelectorAll("a").forEach(link => {
      const label=(link.textContent || "").replace(/\\s+/g," ").trim().toLowerCase();
      if (label.includes("view the repository") || label.includes("research repository") || label.includes("explore the research")) {
        link.href = "https://github.com/sushxnthd/kernellum";
        link.target = "_blank";
        link.rel = "noopener noreferrer";
      }
    });
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
  fixKernellumLinks();
  prioritizeResearchNav();

  let queued = false;
  const observer = new MutationObserver(() => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      replaceAllImages();
      removeResearchRepositoryHoverImage();
      fixKernellumLinks();
      prioritizeResearchNav();
    });
  });

  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    attributeFilter: ["src", "srcset", "sizes"]
  });
})();
