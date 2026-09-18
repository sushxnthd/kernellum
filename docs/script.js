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

    if (journey && journeyStage && journeySteps.length) {
      const shell = journey.querySelector('.journey-shell');
      const shellRect = shell.getBoundingClientRect();
      const total = Math.max(1,shellRect.height-innerHeight);
      const local = clamp((-shellRect.top)/total,0,1);

      journeyStage.style.setProperty('--journey-scroll-y',(-local*54).toFixed(2)+'px');

      let nearest = journeyIndex;
      let nearestDistance = Infinity;
      const targetY = innerHeight * .5;
      journeySteps.forEach((step,i) => {
        const r = step.getBoundingClientRect();
        const center = r.top + r.height/2;
        const distance = Math.abs(center-targetY);
        if(distance<nearestDistance){nearestDistance=distance;nearest=i;}
      });

      if(nearest!==journeyIndex) setJourneyStage(nearest);
    }

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

  const journey = document.getElementById('compilerJourney');
  const journeyStage = document.getElementById('journeyStage');
  const journeyMachine = document.getElementById('journeyMachine');
  const journeySteps = [...document.querySelectorAll('[data-journey-step]')];
  const journeyDots = journeyStage ? [...journeyStage.querySelectorAll('.journey-progress span')] : [];
  const journeyProgressBar = document.getElementById('journeyProgressBar');
  const journeyStageNo = document.getElementById('journeyStageNo');
  const journeyStageLabel = document.getElementById('journeyStageLabel');
  const journeyStageTitle = document.getElementById('journeyStageTitle');
  const journeyStageText = document.getElementById('journeyStageText');

  const journeyCopy = [
    {
      no:'00', label:'Graph ingest', title:'Start with the workload.',
      text:'The compiler accepts a deliberately narrow model graph and validates what it can actually lower.'
    },
    {
      no:'01', label:'Hardware IR', title:'Make the graph hardware-readable.',
      text:'Tensors, operators and shapes become explicit compiler objects for downstream hardware reasoning.'
    },
    {
      no:'02', label:'Architecture search', title:'Search under constraints.',
      text:'Candidate parallelism is compared using modeled latency. Four MAC lanes are the smallest current candidate meeting the 10 μs target.'
    },
    {
      no:'03', label:'RTL generation', title:'Emit an inspectable implementation.',
      text:'The selected architecture becomes SystemVerilog, quantized memories and golden vectors.'
    },
    {
      no:'04', label:'Selected accelerator', title:'The output is a machine.',
      text:'The current prototype resolves to a 4-lane INT8 accelerator with a reproducible verification path.'
    }
  ];

  let journeyIndex = 0;
  function setJourneyStage(index) {
    if (!journeyStage || !journeySteps.length) return;
    const next = clamp(index,0,journeySteps.length-1);
    journeyIndex = next;
    journeyStage.dataset.stage = String(next);

    journeySteps.forEach((step,i) => step.classList.toggle('active',i===next));
    journeyDots.forEach((dot,i) => dot.classList.toggle('active',i<=next));

    if (journeyProgressBar) {
      journeyProgressBar.style.setProperty('--unused','0');
      journeyProgressBar.style.width = ((next / Math.max(1,journeySteps.length-1)) * 100) + '%';
    }

    const copy = journeyCopy[next];
    if (journeyStageNo) journeyStageNo.textContent = copy.no;
    if (journeyStageLabel) journeyStageLabel.textContent = copy.label;
    if (journeyStageTitle) journeyStageTitle.textContent = copy.title;
    if (journeyStageText) journeyStageText.textContent = copy.text;
  }

  if (journeyStage && journeyMachine && journeySteps.length) {
    setJourneyStage(0);

    journeySteps.forEach((step,i) => {
      step.addEventListener('click',() => setJourneyStage(i));
      step.addEventListener('focus',() => setJourneyStage(i));
    });

    if (!reduced && finePointer.matches) {
      let journeyFrame = 0;
      let journeyPointer = null;

      const renderJourneyPointer = () => {
        journeyFrame = 0;
        if (!journeyPointer) return;
        const r = journeyStage.getBoundingClientRect();
        const nx = clamp((journeyPointer.x-r.left)/r.width-.5,-.5,.5);
        const ny = clamp((journeyPointer.y-r.top)/r.height-.5,-.5,.5);

        journeyMachine.style.setProperty('--j-tilt-x',(nx*7).toFixed(2)+'deg');
        journeyMachine.style.setProperty('--j-tilt-y',(-ny*6).toFixed(2)+'deg');

        journeyStage.querySelectorAll('[data-j-depth]').forEach(el => {
          const d = clamp(parseFloat(el.dataset.jDepth || 0),0,1);
          el.style.setProperty('--jdx',(nx*d*20).toFixed(2)+'px');
          el.style.setProperty('--jdy',(ny*d*20).toFixed(2)+'px');
        });
      };

      journeyStage.addEventListener('pointermove',e => {
        journeyPointer={x:e.clientX,y:e.clientY};
        if(!journeyFrame) journeyFrame=requestAnimationFrame(renderJourneyPointer);
      },{passive:true});

      journeyStage.addEventListener('pointerleave',() => {
        journeyPointer=null;
        journeyMachine.style.setProperty('--j-tilt-x','0deg');
        journeyMachine.style.setProperty('--j-tilt-y','0deg');
        journeyStage.querySelectorAll('[data-j-depth]').forEach(el => {
          el.style.setProperty('--jdx','0px');
          el.style.setProperty('--jdy','0px');
        });
      });
    }
  }

  const cardSelector = [
    '.program-card',
    '.deep-pipeline article',
    '.principle-grid article',
    '.flow-node',
    '.metric-wall > div',
    '.detail-row',
    '.featured-meta > div',
    '.ladder-item'
  ].join(',');

  if (!reduced && finePointer.matches) {
    document.querySelectorAll(cardSelector).forEach(card => {
      card.classList.add('tilt-card');
      let frame = 0;
      let point = null;

      const renderCard = () => {
        frame = 0;
        if (!point) return;
        const r = card.getBoundingClientRect();
        const nx = clamp((point.x - r.left) / r.width - .5,-.5,.5);
        const ny = clamp((point.y - r.top) / r.height - .5,-.5,.5);
        card.style.setProperty('--card-rx',(-ny * 5).toFixed(2) + 'deg');
        card.style.setProperty('--card-ry',(nx * 6).toFixed(2) + 'deg');
      };

      card.addEventListener('pointermove',e => {
        point={x:e.clientX,y:e.clientY};
        if(!frame) frame=requestAnimationFrame(renderCard);
      },{passive:true});

      card.addEventListener('pointerleave',() => {
        point=null;
        card.style.setProperty('--card-rx','0deg');
        card.style.setProperty('--card-ry','0deg');
      });
    });
  }

  window.addEventListener('scroll',queueScroll,{passive:true});
  window.addEventListener('resize',() => {
    stages.forEach(resetStage);
    queueScroll();
  },{passive:true});

  renderScroll();
})();