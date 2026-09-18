(() => {
  const root = document.documentElement;
  const stage = document.getElementById('heroStage');
  const scene = document.getElementById('scene');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

  function updateScroll() {
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    const p = (scrollY / max) * 100;
    root.style.setProperty('--scroll', p + '%');

    if (!reduced) {
      document.querySelectorAll('[data-parallax-y]').forEach(el => {
        const rect = el.getBoundingClientRect();
        const center = rect.top + rect.height / 2 - innerHeight / 2;
        const amount = parseFloat(el.dataset.parallaxY || 0);
        const y = clamp((-center / innerHeight) * amount, -Math.abs(amount), Math.abs(amount));
        el.style.transform = 'translate3d(0,' + y.toFixed(2) + 'px,0)';
      });
    }
  }

  if (!reduced) {
    window.addEventListener('pointermove', e => {
      root.style.setProperty('--mx', e.clientX + 'px');
      root.style.setProperty('--my', e.clientY + 'px');

      if (stage && scene) {
        const r = stage.getBoundingClientRect();
        const x = clamp((e.clientX - r.left) / r.width - .5, -.5, .5);
        const y = clamp((e.clientY - r.top) / r.height - .5, -.5, .5);
        scene.style.transform =
          'translate(-50%,-50%) rotateX(' + (58 - y * 8).toFixed(2) +
          'deg) rotateZ(' + (-32 + x * 8).toFixed(2) + 'deg)';

        stage.querySelectorAll('[data-depth]').forEach(el => {
          const d = parseFloat(el.dataset.depth || 0);
          el.style.marginLeft = (x * d * 34).toFixed(2) + 'px';
          el.style.marginTop = (y * d * 34).toFixed(2) + 'px';
        });
      }
    }, {passive:true});

    if (stage && scene) {
      stage.addEventListener('pointerleave', () => {
        scene.style.transform = 'translate(-50%,-50%) rotateX(58deg) rotateZ(-32deg)';
        stage.querySelectorAll('[data-depth]').forEach(el => {
          el.style.marginLeft = '0px';
          el.style.marginTop = '0px';
        });
      });
    }
  }

  const io = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, {threshold: .12});

  document.querySelectorAll('[data-reveal]').forEach(el => io.observe(el));
  window.addEventListener('scroll', updateScroll, {passive:true});
  window.addEventListener('resize', updateScroll, {passive:true});
  updateScroll();
})();