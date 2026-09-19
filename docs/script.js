document.addEventListener("DOMContentLoaded", function () {
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var precisePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  var loader = document.getElementById("loader");
  var loaderCode = document.getElementById("loaderCode");
  var loaderTrack = document.getElementById("loaderTrack");
  var loaderStages = ["MODEL", "GRAPH", "IR", "SEARCH", "RTL", "P&R", "MACHINE"];

  if (loader && !reducedMotion) {
    var stageIndex = 0;
    var loaderTimer = window.setInterval(function () {
      stageIndex += 1;
      if (loaderCode) loaderCode.textContent = loaderStages[Math.min(stageIndex, loaderStages.length - 1)];
      if (loaderTrack) loaderTrack.style.width = Math.min(100, stageIndex / (loaderStages.length - 1) * 100) + "%";
      if (stageIndex >= loaderStages.length - 1) {
        window.clearInterval(loaderTimer);
        window.setTimeout(function () {
          loader.classList.add("out");
        }, 180);
      }
    }, 90);
  } else if (loader) {
    loader.style.display = "none";
  }

  var menuToggle = document.getElementById("menuToggle");
  var navLinks = document.getElementById("navLinks");
  if (menuToggle && navLinks) {
    menuToggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("open");
      menuToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    navLinks.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        navLinks.classList.remove("open");
        menuToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  var revealItems = document.querySelectorAll(".reveal");
  if (reducedMotion) {
    revealItems.forEach(function (el) { el.classList.add("in"); });
  } else {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    revealItems.forEach(function (el, index) {
      el.style.transitionDelay = Math.min(index % 4, 3) * 55 + "ms";
      revealObserver.observe(el);
    });
  }

  var fieldGrid = document.getElementById("fieldGrid");
  var fieldWrap = document.getElementById("fieldWrap");
  var heroObject = document.getElementById("heroObject");
  var fieldCells = [];

  if (fieldGrid) {
    for (var i = 0; i < 81; i += 1) {
      var cell = document.createElement("span");
      cell.className = "field-cell";
      if ([3, 6, 12, 16, 20, 25, 31, 36, 40, 42, 48, 52, 58, 64, 70, 74, 78].indexOf(i) >= 0) {
        cell.classList.add("hot");
      }
      if ([10, 27, 54, 68].indexOf(i) >= 0) {
        cell.classList.add("mint");
      }
      fieldGrid.appendChild(cell);
      fieldCells.push(cell);
    }
  }

  if (heroObject && fieldWrap && precisePointer && !reducedMotion) {
    heroObject.addEventListener("pointermove", function (event) {
      var rect = heroObject.getBoundingClientRect();
      var px = (event.clientX - rect.left) / rect.width - 0.5;
      var py = (event.clientY - rect.top) / rect.height - 0.5;
      fieldWrap.style.transform =
        "translate(-50%,-50%) rotateX(" + (58 - py * 8) + "deg) rotateZ(" + (-34 + px * 9) + "deg) translateZ(0)";
    });
    heroObject.addEventListener("pointerleave", function () {
      fieldWrap.style.transform = "translate(-50%,-50%) rotateX(58deg) rotateZ(-34deg)";
    });
  }

  if (fieldCells.length && !reducedMotion) {
    var pulse = 0;
    window.setInterval(function () {
      var oldIndex = (pulse * 7 + 11) % fieldCells.length;
      var nextIndex = (pulse * 13 + 17) % fieldCells.length;
      fieldCells[oldIndex].classList.remove("hot");
      fieldCells[nextIndex].classList.add("hot");
      pulse += 1;
    }, 520);
  }

  var systemSteps = Array.prototype.slice.call(document.querySelectorAll(".system-step"));
  var systemNodes = Array.prototype.slice.call(document.querySelectorAll(".system-node"));
  var systemReadoutLabel = document.getElementById("systemReadoutLabel");
  var systemReadoutValue = document.getElementById("systemReadoutValue");

  function activateSystemStep(step) {
    var index = Number(step.getAttribute("data-step"));
    systemSteps.forEach(function (item) {
      item.classList.toggle("active", item === step);
    });
    systemNodes.forEach(function (node) {
      var nodeIndex = Number(node.getAttribute("data-node"));
      node.classList.toggle("active", nodeIndex === index);
    });
    if (systemReadoutLabel) systemReadoutLabel.textContent = step.getAttribute("data-label") || "";
    if (systemReadoutValue) systemReadoutValue.textContent = step.getAttribute("data-value") || "";
  }

  if (systemSteps.length) {
    activateSystemStep(systemSteps[0]);
    var stepObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) activateSystemStep(entry.target);
      });
    }, { threshold: 0.2, rootMargin: "-34% 0px -44% 0px" });
    systemSteps.forEach(function (step) { stepObserver.observe(step); });
  }

  var lanes = document.querySelectorAll(".lane");
  lanes.forEach(function (lane) {
    lane.addEventListener("pointerenter", function () {
      lanes.forEach(function (item) { item.classList.remove("hovered"); });
      lane.classList.add("hovered");
    });
    lane.addEventListener("pointerleave", function () {
      lane.classList.remove("hovered");
    });
  });

  var progress = document.getElementById("scrollProgress");
  var navAnchors = Array.prototype.slice.call(document.querySelectorAll('.navlinks a[href^="#"]'));
  var sections = navAnchors.map(function (a) {
    return document.querySelector(a.getAttribute("href"));
  }).filter(Boolean);

  function updateScrollState() {
    var doc = document.documentElement;
    var max = Math.max(1, doc.scrollHeight - window.innerHeight);
    var ratio = Math.min(1, Math.max(0, window.scrollY / max));
    if (progress) progress.style.width = ratio * 100 + "%";

    var cursor = window.scrollY + window.innerHeight * 0.36;
    var currentId = "";
    sections.forEach(function (section) {
      if (section.offsetTop <= cursor) currentId = "#" + section.id;
    });
    navAnchors.forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("href") === currentId);
    });
  }

  updateScrollState();
  window.addEventListener("scroll", updateScrollState, { passive: true });
  window.addEventListener("resize", updateScrollState);

  if (precisePointer && !reducedMotion) {
    document.querySelectorAll(".big-link,.text-link,.record-row,.evidence-item").forEach(function (el) {
      el.addEventListener("pointermove", function (event) {
        var rect = el.getBoundingClientRect();
        var x = (event.clientX - rect.left) / rect.width - 0.5;
        var y = (event.clientY - rect.top) / rect.height - 0.5;
        el.style.setProperty("--mx", (x * 7).toFixed(2) + "px");
        el.style.setProperty("--my", (y * 5).toFixed(2) + "px");
      });
      el.addEventListener("pointerleave", function () {
        el.style.removeProperty("--mx");
        el.style.removeProperty("--my");
      });
    });
  }
});