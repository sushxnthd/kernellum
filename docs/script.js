document.addEventListener("DOMContentLoaded", function () {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.body.dataset.scene = "0";

  const boot = document.getElementById("boot");
  const bootCount = document.getElementById("bootCount");
  if (boot && !reduced) {
    let n = 5;
    const tick = setInterval(function () {
      n -= 1;
      if (bootCount) bootCount.textContent = String(Math.max(0, n)).padStart(2, "0");
      if (n <= 0) {
        clearInterval(tick);
        setTimeout(function () { boot.classList.add("out"); }, 220);
      }
    }, 120);
  } else if (boot) {
    boot.style.display = "none";
  }

  const reveal = document.querySelectorAll(".reveal");
  if (reduced) {
    reveal.forEach(function (el) { el.classList.add("in"); });
  } else {
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.13, rootMargin: "0px 0px -8% 0px" });
    reveal.forEach(function (el, i) {
      el.style.transitionDelay = Math.min(i % 3, 2) * 55 + "ms";
      io.observe(el);
    });
  }

  const stageData = [
    {
      kicker: "MODEL",
      title: "Start with the workload.",
      body: "A supported ONNX graph enters the compiler as a constrained hardware problem, not as a prompt for HDL generation.",
      a: "GRAPH / 64 → 32 → 16 → 10",
      b: "STATE / VALIDATED"
    },
    {
      kicker: "HARDWARE IR",
      title: "Turn the graph into a machine-readable design problem.",
      body: "The supported operators, shapes, numeric assumptions and deployment constraints become an explicit intermediate representation.",
      a: "PRECISION / INT8",
      b: "LOWERING / EXPLICIT"
    },
    {
      kicker: "SEARCH",
      title: "Generate candidate machines.",
      body: "Parallelism is searched rather than assumed. Candidate accelerator configurations are evaluated against cycle and implementation constraints.",
      a: "CANDIDATES / 1 · 2 · 4 · 8",
      b: "OBJECTIVE / FEASIBLE LATENCY"
    },
    {
      kicker: "RTL",
      title: "Emit something you can inspect.",
      body: "SystemVerilog, weights and golden vectors are generated together so the implementation can be simulated, synthesized and traced back to the reference path.",
      a: "GOLDEN VECTORS / 32 · 32 PASS",
      b: "SYNTHESIS / PASS"
    },
    {
      kicker: "PHYSICAL",
      title: "Let implementation push back.",
      body: "Post-route timing feeds back into architecture selection. The cycle-faster 4 and 8 lane variants miss the 25 MHz reference target.",
      a: "SELECTED / 2 MAC LANES",
      b: "POST-ROUTE / 29.64 MHz"
    }
  ];

  const stageCopy = document.getElementById("stageCopy");
  const stageKicker = document.getElementById("stageKicker");
  const stageTitle = document.getElementById("stageTitle");
  const stageBody = document.getElementById("stageBody");
  const stageA = document.getElementById("stageReadoutA");
  const stageB = document.getElementById("stageReadoutB");
  const stageNumber = document.getElementById("stageNumber");
  const stageTrack = Array.from(document.querySelectorAll(".system-track span"));
  let activeStep = -1;

  function setStage(index) {
    if (index === activeStep || !stageData[index]) return;
    activeStep = index;
    const data = stageData[index];
    if (stageCopy) stageCopy.classList.add("out");
    setTimeout(function () {
      if (stageKicker) stageKicker.textContent = data.kicker;
      if (stageTitle) stageTitle.textContent = data.title;
      if (stageBody) stageBody.textContent = data.body;
      if (stageA) stageA.textContent = data.a;
      if (stageB) stageB.textContent = data.b;
      if (stageNumber) stageNumber.textContent = String(index + 1).padStart(2, "0");
      stageTrack.forEach(function (el, i) { el.classList.toggle("active", i === index); });
      if (stageCopy) stageCopy.classList.remove("out");
      window.dispatchEvent(new CustomEvent("kernellum:compiler-stage", { detail: { index: index } }));
    }, reduced ? 0 : 140);
  }

  const triggers = Array.from(document.querySelectorAll(".stage-trigger"));
  if (triggers.length) {
    const stageObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) setStage(Number(entry.target.dataset.step || 0));
      });
    }, { threshold: 0.01, rootMargin: "-46% 0px -46% 0px" });
    triggers.forEach(function (el) { stageObserver.observe(el); });
    setStage(0);
  }

  const zones = Array.from(document.querySelectorAll(".scene-zone"));
  const zoneObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        const value = entry.target.dataset.scene || "0";
        document.body.dataset.scene = value;
        window.dispatchEvent(new CustomEvent("kernellum:scene", { detail: { index: Number(value) } }));
      }
    });
  }, { threshold: 0.01, rootMargin: "-45% 0px -45% 0px" });
  zones.forEach(function (zone) { zoneObserver.observe(zone); });

  const navLinks = Array.from(document.querySelectorAll('.nav-links a[href^="#"]'));
  function updateNav() {
    const y = scrollY + innerHeight * 0.35;
    let id = "";
    navLinks.forEach(function (link) {
      const target = document.querySelector(link.getAttribute("href"));
      if (target && target.offsetTop <= y) id = link.getAttribute("href");
    });
    navLinks.forEach(function (link) { link.classList.toggle("active", link.getAttribute("href") === id); });
  }
  addEventListener("scroll", updateNav, { passive: true });
  updateNav();

  const cursor = document.getElementById("cursorState");
  if (cursor && matchMedia("(hover:hover) and (pointer:fine)").matches) {
    let x = innerWidth / 2;
    let y = innerHeight / 2;
    let visible = false;
    addEventListener("pointermove", function (e) {
      x = e.clientX;
      y = e.clientY;
      cursor.style.transform = "translate(" + (x + 16) + "px," + (y + 16) + "px)";
      if (!visible) {
        visible = true;
        cursor.style.opacity = "1";
      }
    });
    const interactive = document.querySelectorAll("a,.lane-list div");
    interactive.forEach(function (el) {
      el.addEventListener("pointerenter", function () {
        cursor.textContent = el.tagName === "A" ? "OPEN" : "READ";
      });
      el.addEventListener("pointerleave", function () {
        cursor.textContent = "OBSERVE";
      });
    });
  }
});