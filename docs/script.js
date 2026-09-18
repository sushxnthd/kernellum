(() => {
  const root = document.documentElement;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

  const menuToggle = document.getElementById('menuToggle');
  const navLinks = document.getElementById('navLinks');
  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      const open = !navLinks.classList.contains('open');
      navLinks.classList.toggle('open', open);
      menuToggle.setAttribute('aria-expanded', String(open));
    });
    navLinks.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      navLinks.classList.remove('open');
      menuToggle.setAttribute('aria-expanded','false');
    }));
    document.addEventListener('click', e => {
      if (!navLinks.contains(e.target) && !menuToggle.contains(e.target)) {
        navLinks.classList.remove('open');
        menuToggle.setAttribute('aria-expanded','false');
      }
    });
  }

  const stages = [];
  const homeStage = document.getElementById('heroStage');
  const homeScene = document.getElementById('scene');
  if (homeStage && homeScene) stages.push({stage:homeStage,scene:homeScene});

  document.querySelectorAll('[data-tilt-stage]').forEach(stage => {
    const scene = stage.querySelector('[data-tilt-scene]');
    if (scene) stages.push({stage,scene});
  });

  const resetStage = ({stage,scene}) => {
    scene.style.setProperty('--tilt-x','0deg');
    scene.style.setProperty('--tilt-y','0deg');
    stage.querySelectorAll('[data-depth]').forEach(el => {
      el.style.setProperty('--depth-x','0px');
      el.style.setProperty('--depth-y','0px');
    });
  };

  let pointerFrame = 0;
  let pointer = null;
  let activeStage = null;

  function renderPointer() {
    pointerFrame = 0;
    if (!pointer || reduced || !finePointer.matches || innerWidth <= 700) return;

    root.style.setProperty('--mx', pointer.x + 'px');
    root.style.setProperty('--my', pointer.y + 'px');

    let hit = null;
    for (const item of stages) {
      const r = item.stage.getBoundingClientRect();
      if (pointer.x >= r.left && pointer.x <= r.right && pointer.y >= r.top && pointer.y <= r.bottom) {
        hit = {...item,r};
        break;
      }
    }

    if (activeStage && (!hit || activeStage.stage !== hit.stage)) resetStage(activeStage);
    activeStage = hit ? {stage:hit.stage,scene:hit.scene} : null;
    if (!hit) return;

    const nx = clamp((pointer.x - hit.r.left) / hit.r.width - .5, -.5, .5);
    const ny = clamp((pointer.y - hit.r.top) / hit.r.height - .5, -.5, .5);

    // Anchored tilt: rotation only. Scroll owns translation.
    hit.scene.style.setProperty('--tilt-x',(nx * 8).toFixed(2) + 'deg');
    hit.scene.style.setProperty('--tilt-y',(-ny * 7).toFixed(2) + 'deg');

    // Depth offset composes with each element's existing transform through CSS translate.
    hit.stage.querySelectorAll('[data-depth]').forEach(el => {
      const d = clamp(parseFloat(el.dataset.depth || 0), 0, 1);
      const spread = 24 * d;
      el.style.setProperty('--depth-x',(nx * spread).toFixed(2) + 'px');
      el.style.setProperty('--depth-y',(ny * spread).toFixed(2) + 'px');
    });
  }

  if (!reduced && finePointer.matches) {
    window.addEventListener('pointermove', e => {
      pointer = {x:e.clientX,y:e.clientY};
      if (!pointerFrame) pointerFrame = requestAnimationFrame(renderPointer);
    }, {passive:true});

    stages.forEach(item => {
      item.stage.addEventListener('pointerleave', () => {
        resetStage(item);
        if (activeStage && activeStage.stage === item.stage) activeStage = null;
      });
    });
  }

  let scrollFrame = 0;
  function renderScroll() {
    scrollFrame = 0;
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const pageProgress = scrollY / max;

    root.style.setProperty('--scroll',(pageProgress * 100).toFixed(2) + '%');
    root.style.setProperty('--grid-y',(-scrollY * .045).toFixed(1) + 'px');

    document.querySelectorAll('[data-parallax-y]').forEach(el => {
      const rect = el.getBoundingClientRect();
      const center = rect.top + rect.height / 2 - innerHeight / 2;
      const amount = parseFloat(el.dataset.parallaxY || 0);
      const mobileFactor = innerWidth <= 700 ? .35 : 1;
      const y = clamp((-center / innerHeight) * amount * mobileFactor, -Math.abs(amount), Math.abs(amount));
      el.style.setProperty('--parallax-y',y.toFixed(2) + 'px');
    });

    stages.forEach(({stage,scene}) => {
      const rect = stage.getBoundingClientRect();
      const center = rect.top + rect.height / 2 - innerHeight / 2;
      const normalized = clamp(center / innerHeight,-1,1);
      const sceneY = reduced ? 0 : clamp(-normalized * 30,-30,30);
      const glowY = reduced ? 0 : clamp(-normalized * 46,-46,46);
      scene.style.setProperty('--scene-scroll-y',sceneY.toFixed(2) + 'px');
      stage.style.setProperty('--stage-glow-y',glowY.toFixed(2) + 'px');
    });
  }
  const queueScroll = () => {
    if (!scrollFrame) scrollFrame = requestAnimationFrame(renderScroll);
  };

  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, {threshold:.11});
  document.querySelectorAll('[data-reveal]').forEach(el => io.observe(el));

  document.querySelectorAll('.notebook-row,.program-card,.deep-pipeline article,.principle-grid article,.artifact-node').forEach((el,i) => {
    el.style.setProperty('--delay',(i % 6) * 55 + 'ms');
  });

  window.addEventListener('scroll',queueScroll,{passive:true});
  window.addEventListener('resize',() => {
    stages.forEach(resetStage);
    queueScroll();
  },{passive:true});

  renderScroll();
})();