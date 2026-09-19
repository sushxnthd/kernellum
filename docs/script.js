document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('#menuToggle');
  const links = document.querySelector('#navLinks');

  toggle?.addEventListener('click', () => {
    const open = links?.classList.toggle('open') || false;
    toggle.setAttribute('aria-expanded', String(open));
  });

  links?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
    links.classList.remove('open');
    toggle?.setAttribute('aria-expanded', 'false');
  }));

  const reveal = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px' });
    reveal.forEach(element => observer.observe(element));
  } else {
    reveal.forEach(element => element.classList.add('visible'));
  }

  const filterButtons = [...document.querySelectorAll('[data-evidence-filter]')];
  const evidenceRows = [...document.querySelectorAll('[data-evidence-kind]')];
  filterButtons.forEach(button => button.addEventListener('click', () => {
    const filter = button.dataset.evidenceFilter || 'all';
    filterButtons.forEach(item => item.classList.toggle('active', item === button));
    evidenceRows.forEach(row => {
      row.hidden = filter !== 'all' && row.dataset.evidenceKind !== filter;
    });
  }));

  const stage = document.querySelector('#kernelStage');
  const precisePointer = matchMedia('(hover:hover) and (pointer:fine)').matches;
  if (stage && precisePointer) {
    stage.addEventListener('pointermove', event => {
      const rect = stage.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      stage.style.setProperty('--rx', `${x * 7}deg`);
      stage.style.setProperty('--ry', `${y * -5}deg`);
    });
    stage.addEventListener('pointerleave', () => {
      stage.style.setProperty('--rx', '0deg');
      stage.style.setProperty('--ry', '0deg');
    });
  }
});
