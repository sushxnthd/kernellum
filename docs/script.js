(() => {
  const root = document.documentElement;
  const stage = document.getElementById('heroStage');
  const scene = document.getElementById('scene');
  const menuToggle = document.getElementById('menuToggle');
  const navLinks = document.getElementById('navLinks');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

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

  let pointerFrame = 0;
  let lastPointer = null;
  function renderPointer() {
    pointerFrame = 0;
    const e = lastPointer;
    if (!e) return;
    root.style.setProperty('--mx', e.x + 'px');
    root.style.setProperty('--my', e.y + 'px');
    if (stage && scene && innerWidth > 700) {
      const r = stage.getBoundingClientRect();
      const x = clamp((e.x - r.left) / r.width - .5, -.5, .5);
      const y = clamp((e.y - r.top) / r.height - .5, -.5, .5);
      scene.style.transform =
        'translate(-50%,-50%) rotateX(' + (58 - y * 8).toFixed(2) +
        'deg) rotateZ(' + (-32 + x * 8).toFixed(2) + 'deg)';
      stage.querySelectorAll('[data-depth]').forEach(el => {
        const d = parseFloat(el.dataset.depth || 0);
        el.style.marginLeft = (x * d * 34).toFixed(2) + 'px';
        el.style.marginTop = (y * d * 34).toFixed(2) + 'px';
      });
    }
  }

  if (!reduced) {
    window.addEventListener('pointermove', e => {
      lastPointer = {x:e.clientX,y:e.clientY};
      if (!pointerFrame) pointerFrame = requestAnimationFrame(renderPointer);
    }, {passive:true});

    if (stage && scene) {
      stage.addEventListener('pointerleave', () => {
        if (innerWidth > 700) {
          scene.style.transform = 'translate(-50%,-50%) rotateX(58deg) rotateZ(-32deg)';
          stage.querySelectorAll('[data-depth]').forEach(el => {
            el.style.marginLeft = '0px';
            el.style.marginTop = '0px';
          });
        }
      });
    }
  }

  let scrollFrame = 0;
  function renderScroll() {
    scrollFrame = 0;
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    root.style.setProperty('--scroll', ((scrollY / max) * 100) + '%');

    if (!reduced && innerWidth > 700) {
      document.querySelectorAll('[data-parallax-y]').forEach(el => {
        const rect = el.getBoundingClientRect();
        const center = rect.top + rect.height / 2 - innerHeight / 2;
        const amount = parseFloat(el.dataset.parallaxY || 0);
        const y = clamp((-center / innerHeight) * amount, -Math.abs(amount), Math.abs(amount));
        el.style.transform = 'translate3d(0,' + y.toFixed(2) + 'px,0)';
      });
    }
  }
  function queueScroll() {
    if (!scrollFrame) scrollFrame = requestAnimationFrame(renderScroll);
  }

  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, {threshold:.12});

  document.querySelectorAll('[data-reveal]').forEach(el => io.observe(el));
  window.addEventListener('scroll', queueScroll, {passive:true});
  window.addEventListener('resize', queueScroll, {passive:true});
  renderScroll();
})();