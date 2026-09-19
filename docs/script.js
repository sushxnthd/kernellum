document.addEventListener('DOMContentLoaded', () => {
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const precisePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const file = location.pathname.split('/').pop() || 'index.html';
  const page = file.replace('.html', '') || 'index';
  document.body.dataset.page = page;
  document.body.classList.add('experience-ready');

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
  if ('IntersectionObserver' in window && !reducedMotion) {
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
    filterButtons.forEach(item => {
      const selected = item === button;
      item.classList.toggle('active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    evidenceRows.forEach(row => {
      row.hidden = filter !== 'all' && row.dataset.evidenceKind !== filter;
    });
  }));

  enhanceNavigation();
  enhanceMetrics();
  animateHeroField();
  initKernelStage();

  function enhanceNavigation() {
    const progress = document.createElement('div');
    progress.className = 'read-progress';
    progress.setAttribute('aria-hidden', 'true');
    document.body.append(progress);

    const sync = () => {
      const max = document.documentElement.scrollHeight - innerHeight;
      const ratio = max > 0 ? scrollY / max : 0;
      progress.style.transform = `scaleX(${Math.min(1, Math.max(0, ratio))})`;
    };
    addEventListener('scroll', sync, { passive: true });
    addEventListener('resize', sync);
    sync();

    if (!precisePointer || reducedMotion) return;
    const cursor = document.createElement('div');
    cursor.className = 'field-cursor';
    cursor.setAttribute('aria-hidden', 'true');
    cursor.innerHTML = '<i></i><span>KRN</span>';
    document.body.append(cursor);
    let targetX = -80;
    let targetY = -80;
    let x = targetX;
    let y = targetY;
    addEventListener('pointermove', event => {
      targetX = event.clientX;
      targetY = event.clientY;
      cursor.classList.add('seen');
    }, { passive: true });
    document.querySelectorAll('a, button, input, [tabindex]').forEach(item => {
      item.addEventListener('pointerenter', () => cursor.classList.add('hot'));
      item.addEventListener('pointerleave', () => cursor.classList.remove('hot'));
    });
    const tick = () => {
      x += (targetX - x) * 0.16;
      y += (targetY - y) * 0.16;
      cursor.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      requestAnimationFrame(tick);
    };
    tick();
  }

  function enhanceMetrics() {
    document.querySelectorAll('.metric').forEach((metric, index) => {
      metric.tabIndex = 0;
      const value = metric.querySelector('strong')?.textContent?.trim() || '';
      let ratio = 0.72;
      if (value.includes('/')) {
        const [a, b] = value.split('/').map(Number);
        if (b) ratio = a / b;
      } else if (value.includes('%')) {
        ratio = Number.parseFloat(value) / 100;
      } else if (/pending/i.test(value)) {
        ratio = 0.08;
      } else if (/pass|public|generated/i.test(value)) {
        ratio = 1;
      } else {
        const number = Number.parseFloat(value.replace(/,/g, ''));
        if (Number.isFinite(number)) ratio = Math.min(1, 0.32 + ((number * 0.061 + index * 0.13) % 0.64));
      }
      const bar = document.createElement('i');
      bar.className = 'metric-signal';
      bar.style.setProperty('--metric', ratio.toFixed(3));
      bar.innerHTML = '<b></b>';
      metric.append(bar);
    });
  }

  function initKernelStage() {
    const stage = document.querySelector('#kernelStage');
    if (!stage || !precisePointer || reducedMotion) return;
    stage.addEventListener('pointermove', event => {
      const rect = stage.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - 0.5;
      const y = (event.clientY - rect.top) / rect.height - 0.5;
      stage.style.setProperty('--rx', `${x * 13}deg`);
      stage.style.setProperty('--ry', `${y * -10}deg`);
      stage.style.setProperty('--px', `${(x + 0.5) * 100}%`);
      stage.style.setProperty('--py', `${(y + 0.5) * 100}%`);
    });
    stage.addEventListener('pointerleave', () => {
      stage.style.setProperty('--rx', '0deg');
      stage.style.setProperty('--ry', '0deg');
    });
  }

  function animateHeroField() {
    const hero = document.querySelector('.cover, .page-hero');
    if (!hero) return;
    const canvas = document.createElement('canvas');
    canvas.className = 'compute-field';
    canvas.setAttribute('aria-hidden', 'true');
    hero.prepend(canvas);
    const context = canvas.getContext('2d');
    if (!context) return;
    const seed = [...page].reduce((sum, char) => sum + char.charCodeAt(0), 0);
    const nodes = Array.from({ length: 34 }, (_, index) => ({
      x: ((index * 79 + seed * 3) % 997) / 997,
      y: ((index * 47 + seed * 7) % 991) / 991,
      z: 0.25 + (((index * 29 + seed) % 97) / 97) * 0.75,
      p: index % 7 === 0
    }));
    let width = 0;
    let height = 0;
    let pointerX = 0;
    let pointerY = 0;
    let frame = 0;
    const resize = () => {
      const rect = hero.getBoundingClientRect();
      const dpr = Math.min(devicePixelRatio || 1, 1.75);
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    addEventListener('resize', resize);
    if (precisePointer) {
      hero.addEventListener('pointermove', event => {
        const rect = hero.getBoundingClientRect();
        pointerX = (event.clientX - rect.left) / rect.width - 0.5;
        pointerY = (event.clientY - rect.top) / rect.height - 0.5;
      }, { passive: true });
    }
    const draw = time => {
      context.clearRect(0, 0, width, height);
      const points = nodes.map((node, index) => {
        const drift = reducedMotion ? 0 : Math.sin(time * 0.00023 + index * 1.7) * 8 * node.z;
        return {
          x: node.x * width + pointerX * 38 * node.z + drift,
          y: node.y * height + pointerY * 26 * node.z + Math.cos(time * 0.00019 + index) * 5,
          z: node.z,
          p: node.p
        };
      });
      context.lineWidth = 0.7;
      points.forEach((a, index) => {
        for (let j = index + 1; j < points.length; j += 1) {
          const b = points[j];
          const distance = Math.hypot(a.x - b.x, a.y - b.y);
          if (distance < 126) {
            context.strokeStyle = `rgba(185,243,93,${(1 - distance / 126) * 0.12})`;
            context.beginPath();
            context.moveTo(a.x, a.y);
            context.lineTo(b.x, b.y);
            context.stroke();
          }
        }
        context.fillStyle = a.p ? 'rgba(121,216,193,.62)' : `rgba(185,243,93,${0.16 + a.z * 0.22})`;
        const size = a.p ? 3.2 : 1.2 + a.z * 1.4;
        context.fillRect(a.x - size / 2, a.y - size / 2, size, size);
      });
      if (!reducedMotion && !document.hidden) frame = requestAnimationFrame(draw);
    };
    draw(0);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && !reducedMotion) {
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(draw);
      }
    });
  }

  function createTransformLab(scope) {
    const anchor = document.querySelector(scope === 'index' ? '.cover' : '.page-hero');
    if (!anchor) return;
    const section = document.createElement('section');
    section.className = 'transform-lab';
    section.dataset.step = '0';
    section.innerHTML = `
      <div class="transform-intro">
        <div><span class="superlabel">${scope === 'index' ? '01 / Live compiler path' : '01 / Inside the transformation'}</span><h2>Do not read the pipeline.<br><em>Move through it.</em></h2></div>
        <p>The same workload is re-expressed at each level. Scroll, focus or select a stage to inspect what changes and what survives.</p>
      </div>
      <div class="transform-grid">
        <div class="transform-sticky">
          <div class="transform-hud"><span data-transform-counter>01 / 05</span><b data-transform-title>Model graph</b><small>LIVE SYSTEM VIEW</small></div>
          <div class="transform-viewport" role="img" aria-label="Interactive model-to-hardware transformation">
            <div class="axis axis-x"></div><div class="axis axis-y"></div><div class="axis axis-z"></div>
            <div class="transform-object">
              <div class="scene-group scene-graph">
                <i class="edge e1"></i><i class="edge e2"></i><i class="edge e3"></i><i class="edge e4"></i><i class="edge e5"></i>
                <b class="node n1"></b><b class="node n2"></b><b class="node n3"></b><b class="node n4"></b><b class="node n5"></b><b class="node n6"></b>
              </div>
              <div class="scene-group scene-ir"><span>TENSOR 64</span><span>GEMM 32</span><span>RELU 16</span><span>GEMM 10</span></div>
              <div class="scene-group scene-search">${Array.from({ length: 16 }, (_, i) => `<i style="--h:${22 + ((i * 37) % 70)}%"></i>`).join('')}</div>
              <div class="scene-group scene-rtl"><code>always_ff @(posedge clk)</code><code>acc &lt;= acc + x * w;</code><code>lane[1:0] / int8</code><code>valid_o &lt;= stage_4;</code></div>
              <div class="scene-group scene-chip"><div class="chip-top">KRN</div><div class="chip-face face-a"></div><div class="chip-face face-b"></div><span>2 MAC LANES</span></div>
            </div>
            <div class="transform-readout"><span data-transform-readout>64 → 32 → 16 → 10</span><i></i></div>
          </div>
          <div class="transform-progress">${Array.from({ length: 5 }, (_, i) => `<button type="button" data-transform-dot="${i}" aria-label="Show stage ${i + 1}"><span>0${i + 1}</span></button>`).join('')}</div>
        </div>
        <div class="transform-steps">
          <article class="transform-step active" tabindex="0" role="button" data-transform-step="0"><span>01 / Input</span><h3>Model graph</h3><p>A supported ONNX graph enters as connected tensor operations, not as a picture of a network.</p><b>64 → 32 → 16 → 10</b></article>
          <article class="transform-step" tabindex="0" role="button" data-transform-step="1"><span>02 / Lower</span><h3>Hardware IR</h3><p>Tensors, operators, shapes and quantization choices become explicit objects for hardware reasoning.</p><b>Validated operator subset</b></article>
          <article class="transform-step" tabindex="0" role="button" data-transform-step="2"><span>03 / Search</span><h3>Architecture field</h3><p>Candidate parallelism is searched under cycle, device and physical timing constraints.</p><b>1 / 2 / 4 / 8 lanes</b></article>
          <article class="transform-step" tabindex="0" role="button" data-transform-step="3"><span>04 / Emit</span><h3>Generated RTL</h3><p>The selected structure resolves into inspectable SystemVerilog, memories and golden vectors.</p><b>32 / 32 vectors pass</b></article>
          <article class="transform-step" tabindex="0" role="button" data-transform-step="4"><span>05 / Select</span><h3>Accelerator</h3><p>Physical feedback rejects faster modeled candidates that miss the board timing target.</p><b>2 lanes · 29.64 MHz</b></article>
        </div>
      </div>`;
    anchor.insertAdjacentElement('afterend', section);

    const stages = [
      ['Model graph', '64 → 32 → 16 → 10'],
      ['Hardware IR', 'TENSORS / OPS / SHAPES'],
      ['Architecture search', '1 / 2 / 4 / 8 MAC LANES'],
      ['Generated RTL', 'SYSTEMVERILOG / MEMORIES / VECTORS'],
      ['Selected accelerator', '2 LANES / 29.64 MHz / L5']
    ];
    const stepElements = [...section.querySelectorAll('[data-transform-step]')];
    const dots = [...section.querySelectorAll('[data-transform-dot]')];
    const setStage = index => {
      section.dataset.step = String(index);
      section.querySelector('[data-transform-counter]').textContent = `0${index + 1} / 05`;
      section.querySelector('[data-transform-title]').textContent = stages[index][0];
      section.querySelector('[data-transform-readout]').textContent = stages[index][1];
      stepElements.forEach((item, itemIndex) => item.classList.toggle('active', itemIndex === index));
      dots.forEach((item, itemIndex) => item.classList.toggle('active', itemIndex === index));
    };
    stepElements.forEach((item, index) => {
      item.addEventListener('click', () => setStage(index));
      item.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          setStage(index);
        }
      });
    });
    dots.forEach((item, index) => item.addEventListener('click', () => {
      setStage(index);
      stepElements[index].scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'center' });
    }));
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) setStage(stepElements.indexOf(entry.target));
        });
      }, { threshold: 0.58 });
      stepElements.forEach(item => observer.observe(item));
    }
    setStage(0);
  }

  function createPageInstrument(name) {
    const anchor = document.querySelector('.page-hero');
    if (!anchor) return;
    const factories = {
      research: researchInstrument,
      evidence: evidenceInstrument,
      publications: publicationsInstrument,
      hardware: hardwareInstrument,
      log: logInstrument,
      about: aboutInstrument,
      partner: partnerInstrument,
      news: newsInstrument
    };
    const factory = factories[name];
    if (!factory) return;
    const module = factory();
    anchor.insertAdjacentElement('afterend', module.element);
    module.init?.(module.element);
  }

  const sweep = [
    { lanes: 1, cycles: 2836, fmax: 35.96, latency: 113.44, logic: 3562, mult: 5 },
    { lanes: 2, cycles: 1476, fmax: 29.64, latency: 59.04, logic: 5727, mult: 6 },
    { lanes: 4, cycles: 796, fmax: 22.12, latency: 31.84, logic: 10561, mult: 8 },
    { lanes: 8, cycles: 456, fmax: 16.10, latency: 18.24, logic: 19652, mult: 12 }
  ];

  if (page === 'index' || page === 'compiler') {
    createTransformLab(page);
  } else {
    createPageInstrument(page);
  }

  function makeShell(label, title, intro, body, extraClass = '') {
    const element = document.createElement('section');
    element.className = `lab-instrument ${extraClass}`;
    element.innerHTML = `<div class="instrument-head"><div><span class="superlabel">${label}</span><h2>${title}</h2></div><p>${intro}</p></div>${body}`;
    return element;
  }

  function researchInstrument() {
    const body = `<div class="constraint-console">
      <div class="constraint-controls"><span class="instrument-label">Clock constraint</span><div class="segmented" role="group" aria-label="Clock target">${[20, 25, 30, 35].map(value => `<button type="button" data-clock="${value}" class="${value === 25 ? 'active' : ''}">${value} MHz</button>`).join('')}</div><p data-constraint-copy></p></div>
      <div class="candidate-field">${sweep.map(item => `<button type="button" class="candidate" data-lanes="${item.lanes}"><span>${item.lanes} lane${item.lanes > 1 ? 's' : ''}</span><i><b style="--f:${item.fmax / 40}"></b></i><strong>${item.fmax.toFixed(2)} MHz</strong><small>${item.cycles.toLocaleString()} cycles</small></button>`).join('')}</div>
      <div class="selection-readout"><span>Compiler selection</span><strong data-selection></strong><small>Lowest modeled cycle count among candidates that close timing.</small></div>
    </div>`;
    const element = makeShell('Live research instrument / Constraint field', 'Change one constraint.<br><em>Watch the machine change.</em>', 'This explorer applies the published selection rule to the real ULX3S-85F sweep. It is a research result, not a product estimator.', body, 'instrument-dark');
    return { element, init: root => initConstraint(root, false) };
  }

  function hardwareInstrument() {
    const body = `<div class="hardware-console">
      <div class="hardware-target"><label for="clockRange">Board clock target <output data-clock-output>25 MHz</output></label><input id="clockRange" data-clock-range type="range" min="16" max="36" value="25" step="1"><div><span>16</span><span>Target MHz</span><span>36</span></div></div>
      <div class="hardware-orbit">${sweep.map(item => `<button type="button" class="hardware-card" data-lanes="${item.lanes}"><span>0${Math.log2(item.lanes) + 1}</span><strong>${item.lanes}</strong><b>MAC lanes</b><i><em style="--f:${item.fmax / 40}"></em></i><small>${item.fmax.toFixed(2)} MHz Fmax<br>${item.logic.toLocaleString()} COMB</small></button>`).join('')}</div>
      <div class="hardware-detail"><div><span>Selected architecture</span><strong data-selection></strong></div><div><span>Modeled latency @25 MHz</span><strong data-latency></strong></div><div><span>Physical status</span><strong data-status></strong></div></div>
    </div>`;
    const element = makeShell('KRN-PNR-001 / Interactive sweep', 'Physical timing is a design input.', 'Move the board clock target to see which implementations remain feasible. The published reference target is 25 MHz.', body, 'instrument-dark');
    return {
      element,
      init: root => {
        const range = root.querySelector('[data-clock-range]');
        const update = () => {
          const clock = Number(range.value);
          root.querySelector('[data-clock-output]').textContent = `${clock} MHz`;
          const feasible = sweep.filter(item => item.fmax >= clock);
          const selected = feasible.sort((a, b) => a.cycles - b.cycles)[0];
          root.querySelectorAll('.hardware-card').forEach(card => {
            const item = sweep.find(entry => entry.lanes === Number(card.dataset.lanes));
            card.classList.toggle('pass', item.fmax >= clock);
            card.classList.toggle('selected', selected?.lanes === item.lanes);
          });
          root.querySelector('[data-selection]').textContent = selected ? `${selected.lanes} MAC lane${selected.lanes > 1 ? 's' : ''}` : 'No feasible candidate';
          root.querySelector('[data-latency]').textContent = selected ? `${selected.latency.toFixed(2)} µs` : 'Not available';
          root.querySelector('[data-status]').textContent = clock === 25 ? 'Published target' : 'Exploration only';
        };
        range.addEventListener('input', update);
        update();
      }
    };
  }

  function initConstraint(root) {
    const buttons = [...root.querySelectorAll('[data-clock]')];
    const update = clock => {
      const feasible = sweep.filter(item => item.fmax >= clock);
      const selected = feasible.sort((a, b) => a.cycles - b.cycles)[0];
      root.querySelectorAll('.candidate').forEach(card => {
        const item = sweep.find(entry => entry.lanes === Number(card.dataset.lanes));
        card.classList.toggle('pass', item.fmax >= clock);
        card.classList.toggle('selected', selected?.lanes === item.lanes);
      });
      buttons.forEach(button => button.classList.toggle('active', Number(button.dataset.clock) === clock));
      root.querySelector('[data-selection]').textContent = selected ? `${selected.lanes} MAC lane${selected.lanes > 1 ? 's' : ''} · ${selected.fmax.toFixed(2)} MHz` : 'No feasible candidate';
      root.querySelector('[data-constraint-copy]').textContent = `${feasible.length} of 4 candidates close a ${clock} MHz target.`;
    };
    buttons.forEach(button => button.addEventListener('click', () => update(Number(button.dataset.clock))));
    update(25);
  }

  function evidenceInstrument() {
    const levels = [
      ['L0', 'Model', 'Accuracy and quantization behavior', '96.44% INT8 accuracy', 'complete'],
      ['L1', 'Reference', 'Integer and vector behavior', '450 held-out samples', 'complete'],
      ['L2', 'Cycle model', 'Cycle-exact architecture behavior', '450 / 450 exact', 'complete'],
      ['L3', 'RTL', 'Generated implementation simulation', '32 / 32 vectors', 'complete'],
      ['L4', 'Synthesis', 'Technology-family mapping', 'ECP5 pass', 'complete'],
      ['L5', 'Place and route', 'Named device, package and timing', '29.64 MHz selected', 'current'],
      ['L6', 'Physical board', 'Measured latency, power and energy', 'Pending', 'pending']
    ];
    const body = `<div class="evidence-console"><div class="evidence-orbit">${levels.map((item, index) => `<button type="button" data-level="${index}" class="${index === 5 ? 'active' : ''}"><i></i><span>${item[0]}</span><b>${item[1]}</b></button>`).join('')}</div><div class="evidence-scope"><div class="scope-ring"><span data-level-code>L5</span><i></i></div><div><span class="instrument-label" data-level-state>Current public ceiling</span><h3 data-level-title>Place and route</h3><p data-level-copy>Named device, package and timing</p><strong data-level-result>29.64 MHz selected</strong></div></div></div>`;
    const element = makeShell('Evidence ladder / Claim resolution', 'A number becomes credible<br><em>one threshold at a time.</em>', 'Select an evidence level to see exactly what it can establish. Higher levels do not erase the boundaries of lower ones.', body, 'instrument-dark');
    return {
      element,
      init: root => {
        const setLevel = index => {
          const item = levels[index];
          root.querySelectorAll('[data-level]').forEach(button => button.classList.toggle('active', Number(button.dataset.level) === index));
          root.querySelector('[data-level-code]').textContent = item[0];
          root.querySelector('[data-level-title]').textContent = item[1];
          root.querySelector('[data-level-copy]').textContent = item[2];
          root.querySelector('[data-level-result]').textContent = item[3];
          root.querySelector('[data-level-state]').textContent = item[4] === 'pending' ? 'Next threshold' : item[4] === 'current' ? 'Current public ceiling' : 'Completed evidence';
          root.style.setProperty('--level', index / 6);
        };
        root.querySelectorAll('[data-level]').forEach(button => button.addEventListener('click', () => setLevel(Number(button.dataset.level))));
        setLevel(5);
      }
    };
  }

  function publicationsInstrument() {
    const reports = [
      ['TR-001', 'Constraint-Driven Generation of a Quantized Neural Accelerator', 'First complete model-to-RTL prototype.', 'TR-001.pdf'],
      ['DOS-02', 'Evidence Dossier v0.2', 'Claim-to-artifact map for the public evidence record.', 'Kernellum_Evidence_Dossier_v0.2.pdf'],
      ['REP-02', 'Reproducibility Guide v0.2', 'Commands and boundaries for clean-room verification.', 'Kernellum_Reproducibility_Guide_v0.2.pdf'],
      ['HW-01', 'FPGA Bring-up Protocol', 'Measurement plan for the next physical threshold.', 'Kernellum_FPGA_Bringup_Protocol_v0.1.pdf'],
      ['LOG-09', 'September Build Log', 'Curated record of research-relevant changes.', 'Kernellum_Build_Log_2026-09.pdf']
    ];
    const body = `<div class="report-console"><div class="report-stack" aria-hidden="true">${reports.map((_, index) => `<i style="--i:${index}"><span>${reports[index][0]}</span></i>`).join('')}</div><div class="report-index">${reports.map((item, index) => `<button type="button" data-report="${index}" class="${index === 0 ? 'active' : ''}"><span>0${index + 1}</span><b>${item[0]}</b><small>${item[2]}</small></button>`).join('')}</div><div class="report-readout"><span class="instrument-label" data-report-code>TR-001</span><h3 data-report-title>${reports[0][1]}</h3><p data-report-copy>${reports[0][2]}</p><a class="btn primary" data-report-link href="${reports[0][3]}">Open document →</a></div></div>`;
    const element = makeShell('Research archive / Live index', 'The work should leave<br><em>an inspectable record.</em>', 'Rotate through the current publication stack. Each document answers a different diligence question.', body, 'instrument-dark');
    return {
      element,
      init: root => {
        const setReport = index => {
          const report = reports[index];
          root.style.setProperty('--report', index);
          root.querySelectorAll('[data-report]').forEach(button => button.classList.toggle('active', Number(button.dataset.report) === index));
          root.querySelector('[data-report-code]').textContent = report[0];
          root.querySelector('[data-report-title]').textContent = report[1];
          root.querySelector('[data-report-copy]').textContent = report[2];
          root.querySelector('[data-report-link]').href = report[3];
        };
        root.querySelectorAll('[data-report]').forEach(button => button.addEventListener('click', () => setReport(Number(button.dataset.report))));
        setReport(0);
      }
    };
  }

  function logInstrument() {
    const events = [
      ['17 SEP', 'v0.1 released', 'Model to RTL path enters the public record.'],
      ['17 SEP', 'Synthesis safe', 'RTL initialization is corrected before evidence is accepted.'],
      ['17 SEP', 'Hardware IR', 'A narrow ONNX front end lowers to explicit hardware IR.'],
      ['17 SEP', 'ONNX to ECP5', 'Generated RTL reaches family synthesis in CI.'],
      ['18 SEP', 'Physical feedback', 'ULX3S timing changes the selected architecture.'],
      ['NEXT', 'Board measurement', 'Correctness, latency, power and energy remain open.']
    ];
    const body = `<div class="timeline-console"><div class="timeline-rail">${events.map((item, index) => `<button type="button" data-event="${index}" class="${index === 4 ? 'active' : ''}"><i></i><span>${item[0]}</span></button>`).join('')}</div><div class="timeline-screen"><span data-event-index>05 / 06</span><h3 data-event-title>${events[4][1]}</h3><p data-event-copy>${events[4][2]}</p><div class="timeline-wave">${Array.from({ length: 42 }, (_, index) => `<i style="--h:${18 + ((index * 23) % 76)}%"></i>`).join('')}</div></div></div>`;
    const element = makeShell('Build telemetry / September 2026', 'A lab should leave<br><em>a visible trail.</em>', 'Select a milestone to replay the technical progression. The final node remains deliberately open.', body, 'instrument-dark');
    return {
      element,
      init: root => {
        const setEvent = index => {
          root.style.setProperty('--event', index / (events.length - 1));
          root.querySelectorAll('[data-event]').forEach(button => button.classList.toggle('active', Number(button.dataset.event) === index));
          root.querySelector('[data-event-index]').textContent = `0${index + 1} / 06`;
          root.querySelector('[data-event-title]').textContent = events[index][1];
          root.querySelector('[data-event-copy]').textContent = events[index][2];
        };
        root.querySelectorAll('[data-event]').forEach(button => button.addEventListener('click', () => setEvent(Number(button.dataset.event))));
        setEvent(4);
      }
    };
  }

  function aboutInstrument() {
    const principles = [
      ['Evidence', 'Claims follow artifacts.', 'Code, vectors, simulation, synthesis and measured hardware outrank adjectives.'],
      ['Scope', 'Narrow is acceptable.', 'Unsupported structures are rejected explicitly. Scope grows when the implementation does.'],
      ['Reproducibility', 'Research should rerun.', 'Source, generated artifacts, tests and CI travel together.']
    ];
    const body = `<div class="principle-console"><div class="principle-glyph" aria-hidden="true"><span></span><i></i><b></b><em></em></div><div class="principle-selector">${principles.map((item, index) => `<button type="button" data-principle="${index}" class="${index === 0 ? 'active' : ''}"><span>0${index + 1}</span><b>${item[0]}</b></button>`).join('')}</div><div class="principle-readout"><span class="instrument-label" data-principle-label>Evidence</span><h3 data-principle-title>${principles[0][1]}</h3><p data-principle-copy>${principles[0][2]}</p></div></div>`;
    const element = makeShell('Operating system / Lab principles', 'Ambition needs<br><em>hard constraints.</em>', 'The identity is not a moodboard. These principles determine which claims appear on the site and which ones wait.', body, 'instrument-dark');
    return {
      element,
      init: root => {
        const setPrinciple = index => {
          const item = principles[index];
          root.dataset.principle = String(index);
          root.querySelectorAll('[data-principle]').forEach(button => button.classList.toggle('active', Number(button.dataset.principle) === index));
          root.querySelector('[data-principle-label]').textContent = item[0];
          root.querySelector('[data-principle-title]').textContent = item[1];
          root.querySelector('[data-principle-copy]').textContent = item[2];
        };
        root.querySelectorAll('[data-principle]').forEach(button => button.addEventListener('click', () => setPrinciple(Number(button.dataset.principle))));
        setPrinciple(0);
      }
    };
  }

  function partnerInstrument() {
    const criteria = [
      ['Compact graph', 'The current path targets small dense or matrix-dominant networks.'],
      ['INT8 tolerant', 'Quantization should be acceptable for the intended workload.'],
      ['Real constraint', 'A target clock, latency, area or memory objective should matter.'],
      ['Public start', 'The first evaluation should avoid confidential inputs and data.']
    ];
    const body = `<div class="fit-console"><div class="fit-dial"><div><strong data-fit-score>0</strong><span>/ 4 signals</span></div><i></i></div><div class="fit-criteria">${criteria.map((item, index) => `<button type="button" aria-pressed="false" data-fit="${index}"><i></i><span><b>${item[0]}</b><small>${item[1]}</small></span></button>`).join('')}</div><div class="fit-result"><span class="instrument-label">Evaluation signal</span><h3 data-fit-title>Select the traits that describe your workload.</h3><p data-fit-copy>This is a scope check, not a promise of compatibility.</p></div></div>`;
    const element = makeShell('Design partner / Workload fit', 'Bring a workload.<br><em>Interrogate the fit.</em>', 'Use this lightweight scope check before opening a public design-partner conversation. No information leaves the page.', body, 'instrument-dark');
    return {
      element,
      init: root => {
        const buttons = [...root.querySelectorAll('[data-fit]')];
        const update = () => {
          const count = buttons.filter(button => button.getAttribute('aria-pressed') === 'true').length;
          root.style.setProperty('--fit', count / 4);
          root.querySelector('[data-fit-score]').textContent = String(count);
          const title = count === 4 ? 'Strong research-fit signal.' : count >= 2 ? 'Potential fit with scoping needed.' : count === 1 ? 'One useful signal so far.' : 'Select the traits that describe your workload.';
          const copy = count === 4 ? 'The current research path may be worth evaluating through the public partner template.' : 'This is a scope check, not a promise of compatibility.';
          root.querySelector('[data-fit-title]').textContent = title;
          root.querySelector('[data-fit-copy]').textContent = copy;
        };
        buttons.forEach(button => button.addEventListener('click', () => {
          const active = button.getAttribute('aria-pressed') === 'true';
          button.setAttribute('aria-pressed', String(!active));
          button.classList.toggle('active', !active);
          update();
        }));
        update();
      }
    };
  }

  function newsInstrument() {
    const steps = [
      ['Graph', 'Supported neural graph'],
      ['INT8', 'Quantized reference'],
      ['Search', 'Candidate architectures'],
      ['RTL', 'Verified SystemVerilog'],
      ['P&R', 'Physical-feedback selection']
    ];
    const body = `<div class="launch-console"><div class="launch-signal">${Array.from({ length: 5 }, (_, index) => `<i style="--i:${index}"></i>`).join('')}<b></b></div><div class="launch-stages">${steps.map((item, index) => `<button type="button" data-launch="${index}" class="${index === 4 ? 'active' : ''}"><span>0${index + 1}</span><b>${item[0]}</b><small>${item[1]}</small></button>`).join('')}</div><div class="launch-readout"><span data-launch-index>05 / 05</span><h3 data-launch-title>Physical-feedback selection</h3><p>The launch system has progressed beyond cycle-only search. Board measurement remains the next threshold.</p></div></div>`;
    const element = makeShell('Launch signal / System evolution', 'The first public path<br><em>keeps moving.</em>', 'Replay the system from supported graph to the current physical-feedback ceiling.', body, 'instrument-dark');
    return {
      element,
      init: root => {
        const setLaunch = index => {
          root.style.setProperty('--launch', index);
          root.querySelectorAll('[data-launch]').forEach(button => button.classList.toggle('active', Number(button.dataset.launch) === index));
          root.querySelector('[data-launch-index]').textContent = `0${index + 1} / 05`;
          root.querySelector('[data-launch-title]').textContent = steps[index][1];
        };
        root.querySelectorAll('[data-launch]').forEach(button => button.addEventListener('click', () => setLaunch(Number(button.dataset.launch))));
        setLaunch(4);
      }
    };
  }
});
