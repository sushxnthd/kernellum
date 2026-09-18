(() => {
  const root = document.documentElement;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
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
  if (homeStage && homeScene) stages.push({stage:homeStage,scene:homeScene,baseX:58,baseZ:-32,home:true});
  document.querySelectorAll('[data-tilt-stage]').forEach(stage => {
    const scene = stage.querySelector('[data-tilt-scene]');
    if (!scene) return;
    stages.push({
      stage,scene,
      baseX:parseFloat(scene.dataset.baseX || 58),
      baseZ:parseFloat(scene.dataset.baseZ || -32),
      home:false
    });
  });

  let pointerFrame = 0;
  let lastPointer = null;
  function renderPointer() {
    pointerFrame = 0;
    const e = lastPointer;
    if (!e) return;
    root.style.setProperty('--mx', e.x + 'px');
    root.style.setProperty('--my', e.y + 'px');

    if (innerWidth <= 700) return;
    stages.forEach(({stage,scene,baseX,baseZ}) => {
      const r = stage.getBoundingClientRect();
      if (e.x < r.left-100 || e.x > r.right+100 || e.y < r.top-100 || e.y > r.bottom+100) return;
      const x = clamp((e.x - r.left) / r.width - .5, -.5, .5);
      const y = clamp((e.y - r.top) / r.height - .5, -.5, .5);
      scene.style.transform =
        'translate(-50%,-50%) rotateX(' + (baseX - y * 10).toFixed(2) +
        'deg) rotateZ(' + (baseZ + x * 10).toFixed(2) + 'deg)';
      stage.querySelectorAll('[data-depth]').forEach(el => {
        const d = parseFloat(el.dataset.depth || 0);
        el.style.marginLeft = (x * d * 42).toFixed(2) + 'px';
        el.style.marginTop = (y * d * 42).toFixed(2) + 'px';
      });
    });
  }

  if (!reduced) {
    window.addEventListener('pointermove', e => {
      lastPointer = {x:e.clientX,y:e.clientY};
      if (!pointerFrame) pointerFrame = requestAnimationFrame(renderPointer);
    }, {passive:true});
    stages.forEach(({stage,scene,baseX,baseZ}) => {
      stage.addEventListener('pointerleave', () => {
        if (innerWidth > 700) {
          scene.style.transform = 'translate(-50%,-50%) rotateX(' + baseX + 'deg) rotateZ(' + baseZ + 'deg)';
          stage.querySelectorAll('[data-depth]').forEach(el => {
            el.style.marginLeft='0px'; el.style.marginTop='0px';
          });
        }
      });
    });
  }

  let scrollFrame = 0;
  function renderScroll() {
    scrollFrame = 0;
    const max = Math.max(1, document.documentElement.scrollHeight - innerHeight);
    root.style.setProperty('--scroll', ((scrollY/max)*100) + '%');

    if (!reduced && innerWidth > 700) {
      document.querySelectorAll('[data-parallax-y]').forEach(el => {
        const rect=el.getBoundingClientRect();
        const center=rect.top+rect.height/2-innerHeight/2;
        const amount=parseFloat(el.dataset.parallaxY||0);
        const y=clamp((-center/innerHeight)*amount,-Math.abs(amount),Math.abs(amount));
        el.style.transform='translate3d(0,'+y.toFixed(2)+'px,0)';
      });

      document.querySelectorAll('.interior-stage,[data-tilt-stage]').forEach(stage => {
        const rect=stage.getBoundingClientRect();
        const progress=clamp((innerHeight-rect.top)/(innerHeight+rect.height),0,1);
        stage.style.setProperty('--stage-scroll',progress.toFixed(3));
      });
    }
  }
  function queueScroll(){if(!scrollFrame)scrollFrame=requestAnimationFrame(renderScroll)}

  const io=new IntersectionObserver(entries=>{
    entries.forEach(entry=>{
      if(entry.isIntersecting){entry.target.classList.add('visible');io.unobserve(entry.target)}
    });
  },{threshold:.11});
  document.querySelectorAll('[data-reveal]').forEach(el=>io.observe(el));

  document.querySelectorAll('.notebook-row,.program-card,.deep-pipeline article,.principle-grid article,.artifact-node').forEach((el,i)=>{
    el.style.setProperty('--delay',(i%6)*55+'ms');
  });

  window.addEventListener('scroll',queueScroll,{passive:true});
  window.addEventListener('resize',queueScroll,{passive:true});
  renderScroll();
})();