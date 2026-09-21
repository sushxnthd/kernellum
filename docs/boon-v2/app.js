const params = new URLSearchParams(location.search);
if (params.has('still')) document.body.classList.add('still');

const menuButton = document.getElementById('menuButton');
const menuPanel = document.getElementById('menuPanel');
const menuLabel = menuButton.querySelector('.menuLabel');
menuButton.addEventListener('click', () => {
  const open = menuPanel.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', String(open));
  menuLabel.textContent = open ? 'CLOSE' : 'MENU';
});
menuPanel.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
  menuPanel.classList.remove('open');
  menuButton.setAttribute('aria-expanded','false');
  menuLabel.textContent = 'MENU';
}));

document.querySelectorAll('.evidenceChip').forEach(chip => {
  const original = chip.querySelector('span').textContent;
  chip.dataset.original = original;
  chip.addEventListener('click', () => {
    const already = chip.classList.contains('active');
    document.querySelectorAll('.evidenceChip').forEach(c => {
      c.classList.remove('active');
      c.querySelector('span').textContent = c.dataset.original;
      c.querySelector('b').textContent = '+';
    });
    if (!already) {
      chip.classList.add('active');
      chip.querySelector('span').textContent = chip.dataset.detail;
      chip.querySelector('b').textContent = '×';
    }
  });
});

const pages = [...document.querySelectorAll('.page')];
const observer = new IntersectionObserver(entries => {
  const visible = entries.filter(e => e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
  if (!visible) return;
  const tone = visible.target.dataset.tone;
  document.querySelector('.navCluster').dataset.tone = tone || '';
}, {threshold:[.35,.55,.7]});
pages.forEach(p => observer.observe(p));

if (!params.has('still')) {
  const hero = document.querySelector('.heroArt');
  window.addEventListener('pointermove', e => {
    const x = (e.clientX / innerWidth - .5) * 10;
    const y = (e.clientY / innerHeight - .5) * 7;
    hero.style.transform = `translate3d(${x}px,${y}px,0)`;
  }, {passive:true});
}
