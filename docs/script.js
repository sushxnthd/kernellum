(() => {
  const menuToggle = document.getElementById('menuToggle');
  const navLinks = document.getElementById('navLinks');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      const open = !navLinks.classList.contains('open');
      navLinks.classList.toggle('open', open);
      menuToggle.setAttribute('aria-expanded', String(open));
    });

    navLinks.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      menuToggle.setAttribute('aria-expanded', 'false');
    }));
  }

  const reveal = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
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
})();
