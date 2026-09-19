(() => {
  const canvas = document.getElementById("kernelCanvas");
  if (!canvas) return;

  let THREE;
  let renderer;
  let scene;
  let camera;
  let root;
  let points;
  let pointGeo;
  let pointMat;
  let lineMesh;
  let lineGeo;
  let dieGroup;
  let ringGroup;
  let chipGroup;
  let fieldMaterial;
  let targetScene = 0;
  let compilerStage = 0;
  let pointerX = 0;
  let pointerY = 0;
  let smoothX = 0;
  let smoothY = 0;
  let elapsed = 0;
  let last = performance.now();
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const pointCount = 900;
  const current = new Float32Array(pointCount * 3);
  const shapes = [];

  function seeded(seed) {
    let t = seed >>> 0;
    return function () {
      t += 0x6D2B79F5;
      let x = t;
      x = Math.imul(x ^ x >>> 15, x | 1);
      x ^= x + Math.imul(x ^ x >>> 7, x | 61);
      return ((x ^ x >>> 14) >>> 0) / 4294967296;
    };
  }

  function makeSphere() {
    const out = new Float32Array(pointCount * 3);
    const rnd = seeded(11);
    for (let i = 0; i < pointCount; i++) {
      const y = 1 - (i / (pointCount - 1)) * 2;
      const r = Math.sqrt(Math.max(0, 1 - y * y));
      const theta = Math.PI * (3 - Math.sqrt(5)) * i;
      const radius = 2.15 + (rnd() - .5) * .22;
      out[i * 3] = Math.cos(theta) * r * radius;
      out[i * 3 + 1] = y * radius;
      out[i * 3 + 2] = Math.sin(theta) * r * radius;
    }
    return out;
  }

  function makeGrid() {
    const out = new Float32Array(pointCount * 3);
    const cols = 30;
    const rows = 30;
    for (let i = 0; i < pointCount; i++) {
      const x = i % cols;
      const y = Math.floor(i / cols) % rows;
      const nx = (x / (cols - 1) - .5) * 5.2;
      const ny = (y / (rows - 1) - .5) * 5.2;
      out[i * 3] = nx;
      out[i * 3 + 1] = ny;
      out[i * 3 + 2] = Math.sin(nx * 1.6) * .28 + Math.cos(ny * 1.4) * .22;
    }
    return out;
  }

  function makeHelix() {
    const out = new Float32Array(pointCount * 3);
    for (let i = 0; i < pointCount; i++) {
      const t = i / (pointCount - 1);
      const a = t * Math.PI * 18;
      const r = 1.0 + .85 * Math.sin(t * Math.PI);
      out[i * 3] = Math.cos(a) * r;
      out[i * 3 + 1] = (t - .5) * 5.2;
      out[i * 3 + 2] = Math.sin(a) * r;
    }
    return out;
  }

  function makeLattice() {
    const out = new Float32Array(pointCount * 3);
    const n = 10;
    let ptr = 0;
    for (let z = 0; z < n && ptr < pointCount; z++) {
      for (let y = 0; y < n && ptr < pointCount; y++) {
        for (let x = 0; x < n && ptr < pointCount; x++) {
          if (ptr >= pointCount) break;
          out[ptr * 3] = (x - 4.5) * .48;
          out[ptr * 3 + 1] = (y - 4.5) * .48;
          out[ptr * 3 + 2] = (z - 4.5) * .48;
          ptr++;
        }
      }
    }
    return out;
  }

  function makeChipPlane() {
    const out = new Float32Array(pointCount * 3);
    const cols = 30;
    const rows = 30;
    for (let i = 0; i < pointCount; i++) {
      const x = i % cols;
      const y = Math.floor(i / cols) % rows;
      const nx = (x / (cols - 1) - .5) * 4.6;
      const ny = (y / (rows - 1) - .5) * 4.6;
      const edge = Math.max(Math.abs(nx), Math.abs(ny));
      out[i * 3] = nx;
      out[i * 3 + 1] = ny;
      out[i * 3 + 2] = edge > 1.8 ? .12 : -.12;
    }
    return out;
  }

  function makeProceduralField() {
    const geometry = new THREE.PlaneGeometry(26, 16, 1, 1);
    fieldMaterial = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      uniforms: {
        uTime: { value: 0 },
        uIntensity: { value: .12 }
      },
      vertexShader: [
        "varying vec2 vUv;",
        "void main(){",
        "vUv=uv;",
        "gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);",
        "}"
      ].join(""),
      fragmentShader: [
        "varying vec2 vUv;",
        "uniform float uTime;",
        "uniform float uIntensity;",
        "void main(){",
        "vec2 p=(vUv-.5)*2.0;",
        "float a=sin(p.x*13.0 + sin(p.y*4.0+uTime*.22)*2.0);",
        "float b=sin(p.y*17.0 + cos(p.x*3.0-uTime*.18)*2.5);",
        "float c=sin(length(p)*18.0-uTime*.35);",
        "float v=(a+b+c)/3.0;",
        "float line=smoothstep(.78,.98,abs(v));",
        "float vign=1.0-smoothstep(.42,1.35,length(p));",
        "vec3 col=mix(vec3(.035,.045,.036),vec3(.55,.95,.24),line);",
        "gl_FragColor=vec4(col,line*uIntensity*vign);",
        "}"
      ].join("")
    });
    const mesh = new THREE.Mesh(geometry, fieldMaterial);
    mesh.position.z = -5.5;
    scene.add(mesh);
  }

  function makeDie() {
    dieGroup = new THREE.Group();
    root.add(dieGroup);

    const bodyGeo = new THREE.BoxGeometry(2.5, .13, 2.5);
    const bodyMat = new THREE.MeshPhysicalMaterial({
      color: 0x0c100d,
      roughness: .36,
      metalness: .72,
      clearcoat: .28,
      clearcoatRoughness: .5
    });

    for (let i = 0; i < 7; i++) {
      const layer = new THREE.Mesh(bodyGeo, bodyMat);
      layer.userData.baseY = (i - 3) * .14;
      layer.position.y = layer.userData.baseY;
      layer.rotation.y = i * .025;
      dieGroup.add(layer);

      const edges = new THREE.LineSegments(
        new THREE.EdgesGeometry(bodyGeo),
        new THREE.LineBasicMaterial({
          color: i === 3 ? 0xbaf55d : 0x314034,
          transparent: true,
          opacity: i === 3 ? .85 : .33
        })
      );
      edges.position.copy(layer.position);
      edges.rotation.copy(layer.rotation);
      edges.userData.baseY = layer.userData.baseY;
      edges.userData.edge = true;
      dieGroup.add(edges);
    }

    const coreGeo = new THREE.BoxGeometry(.72, .31, .72);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0xbaf55d,
      emissive: 0x315e13,
      emissiveIntensity: .72,
      roughness: .34,
      metalness: .18
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    core.position.y = .25;
    core.name = "core";
    dieGroup.add(core);

    const routeMat = new THREE.LineBasicMaterial({ color: 0x79d8bf, transparent: true, opacity: .58 });
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      const path = new Float32Array([
        Math.cos(a) * .52, .18, Math.sin(a) * .52,
        Math.cos(a) * 1.18, .18, Math.sin(a) * 1.18
      ]);
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(path, 3));
      dieGroup.add(new THREE.Line(g, routeMat));
    }
  }

  function makeRings() {
    ringGroup = new THREE.Group();
    root.add(ringGroup);
    const specs = [
      [2.2, .012, 0xbaf55d, .42],
      [2.55, .008, 0x7bd8bf, .28],
      [3.0, .006, 0xbaf55d, .16]
    ];
    specs.forEach(function (s, i) {
      const geo = new THREE.TorusGeometry(s[0], s[1], 4, 180);
      const mat = new THREE.MeshBasicMaterial({ color: s[2], transparent: true, opacity: s[3] });
      const ring = new THREE.Mesh(geo, mat);
      ring.rotation.x = Math.PI * (.34 + i * .09);
      ring.rotation.y = i * .42;
      ring.userData.speed = i % 2 ? -.16 : .11;
      ringGroup.add(ring);
    });
  }

  function makeChips() {
    chipGroup = new THREE.Group();
    root.add(chipGroup);
    const geo = new THREE.BoxGeometry(.12, .05, .12);
    const mat = new THREE.MeshStandardMaterial({ color: 0x263127, metalness: .65, roughness: .45 });
    const rand = seeded(91);
    for (let i = 0; i < 52; i++) {
      const chip = new THREE.Mesh(geo, mat);
      const a = rand() * Math.PI * 2;
      const r = 2.9 + rand() * 1.4;
      chip.position.set(Math.cos(a) * r, (rand() - .5) * 2.8, Math.sin(a) * r);
      chip.rotation.set(rand() * 2, rand() * 2, rand() * 2);
      chip.userData.phase = rand() * Math.PI * 2;
      chipGroup.add(chip);
    }
  }

  function initThree(T) {
    THREE = T;
    renderer = new THREE.WebGLRenderer({
      canvas: canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.75));
    renderer.setSize(innerWidth, innerHeight, false);
    renderer.setClearColor(0x050605, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050605, .052);
    camera = new THREE.PerspectiveCamera(34, innerWidth / innerHeight, .1, 80);
    camera.position.set(0, 0, 9.2);

    root = new THREE.Group();
    scene.add(root);

    shapes.push(makeSphere(), makeGrid(), makeHelix(), makeLattice(), makeChipPlane());
    current.set(shapes[0]);

    pointGeo = new THREE.BufferGeometry();
    pointGeo.setAttribute("position", new THREE.BufferAttribute(current, 3));
    pointMat = new THREE.PointsMaterial({
      color: 0xbaf55d,
      size: .032,
      sizeAttenuation: true,
      transparent: true,
      opacity: .72,
      depthWrite: false,
      blending: THREE.AdditiveBlending
    });
    points = new THREE.Points(pointGeo, pointMat);
    root.add(points);

    const linePositions = new Float32Array(210 * 2 * 3);
    lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
    lineMesh = new THREE.LineSegments(
      lineGeo,
      new THREE.LineBasicMaterial({ color: 0x92c867, transparent: true, opacity: .12, depthWrite: false })
    );
    root.add(lineMesh);

    makeDie();
    makeRings();
    makeChips();
    makeProceduralField();

    const ambient = new THREE.HemisphereLight(0xeceee7, 0x0b0f0c, 1.25);
    scene.add(ambient);
    const key = new THREE.PointLight(0xbaf55d, 18, 20, 2);
    key.position.set(3.5, 4, 5);
    key.name = "key";
    scene.add(key);
    const rim = new THREE.PointLight(0x78d7bf, 12, 20, 2);
    rim.position.set(-4, -2, 3);
    scene.add(rim);

    addEventListener("resize", resize, { passive: true });
    addEventListener("pointermove", onPointer, { passive: true });
    addEventListener("kernellum:scene", function (e) { targetScene = e.detail.index; });
    addEventListener("kernellum:compiler-stage", function (e) { compilerStage = e.detail.index; });

    document.addEventListener("visibilitychange", function () {
      last = performance.now();
    });

    resize();
    requestAnimationFrame(tick);
  }

  function onPointer(e) {
    pointerX = e.clientX / innerWidth * 2 - 1;
    pointerY = -(e.clientY / innerHeight * 2 - 1);
  }

  function resize() {
    if (!renderer || !camera) return;
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, innerWidth < 700 ? 1.3 : 1.75));
    renderer.setSize(innerWidth, innerHeight, false);
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
  }

  function updateMorph(dt) {
    let targetShape = 0;
    if (targetScene === 2) targetShape = compilerStage;
    else if (targetScene === 3) targetShape = 4;
    else if (targetScene === 4) targetShape = 1;
    else if (targetScene === 5) targetShape = 3;
    else if (targetScene >= 6) targetShape = 2;
    else if (targetScene === 1) targetShape = 1;

    const target = shapes[Math.max(0, Math.min(shapes.length - 1, targetShape))];
    const speed = reduced ? 1 : Math.min(1, dt * 2.4);
    for (let i = 0; i < current.length; i++) {
      current[i] += (target[i] - current[i]) * speed;
    }
    pointGeo.attributes.position.needsUpdate = true;

    const lp = lineGeo.attributes.position.array;
    for (let i = 0; i < 210; i++) {
      const a = (i * 13) % pointCount;
      const b = (a + 1 + (i % 11)) % pointCount;
      lp[i * 6] = current[a * 3];
      lp[i * 6 + 1] = current[a * 3 + 1];
      lp[i * 6 + 2] = current[a * 3 + 2];
      lp[i * 6 + 3] = current[b * 3];
      lp[i * 6 + 4] = current[b * 3 + 1];
      lp[i * 6 + 5] = current[b * 3 + 2];
    }
    lineGeo.attributes.position.needsUpdate = true;
  }

  const sceneTargets = [
    { x: 2.9, y: .05, z: -.1, s: 1.0, rx: .25, ry: -.35, rz: .08 },
    { x: 3.35, y: -.2, z: -.6, s: 1.18, rx: .65, ry: -.3, rz: -.2 },
    { x: 2.55, y: .0, z: -.25, s: 1.18, rx: .35, ry: -.2, rz: 0 },
    { x: 2.15, y: -.1, z: -.35, s: 1.52, rx: 1.18, ry: 0, rz: .78 },
    { x: 0, y: -.1, z: -1.3, s: 1.68, rx: .2, ry: .1, rz: .1 },
    { x: -2.9, y: .0, z: -.8, s: 1.15, rx: .55, ry: .25, rz: -.22 },
    { x: 3.0, y: .15, z: -.5, s: 1.0, rx: .4, ry: -.2, rz: .16 },
    { x: 2.75, y: -.1, z: -.2, s: 1.15, rx: .2, ry: -.3, rz: 0 }
  ];

  function updateTransforms(dt) {
    const t = sceneTargets[Math.max(0, Math.min(sceneTargets.length - 1, targetScene))];
    const ease = reduced ? 1 : Math.min(1, dt * 1.7);

    root.position.x += (t.x - root.position.x) * ease;
    root.position.y += (t.y - root.position.y) * ease;
    root.position.z += (t.z - root.position.z) * ease;
    const targetScale = t.s * (innerWidth < 700 ? .72 : 1);
    root.scale.x += (targetScale - root.scale.x) * ease;
    root.scale.y += (targetScale - root.scale.y) * ease;
    root.scale.z += (targetScale - root.scale.z) * ease;

    smoothX += (pointerX - smoothX) * Math.min(1, dt * 3);
    smoothY += (pointerY - smoothY) * Math.min(1, dt * 3);

    root.rotation.x += ((t.rx + smoothY * .08) - root.rotation.x) * ease;
    root.rotation.y += ((t.ry + smoothX * .11) - root.rotation.y) * ease;
    root.rotation.z += (t.rz - root.rotation.z) * ease;

    camera.position.x += ((smoothX * .34) - camera.position.x) * Math.min(1, dt * 1.5);
    camera.position.y += ((smoothY * .22) - camera.position.y) * Math.min(1, dt * 1.5);

    ringGroup.rotation.y += dt * .12;
    ringGroup.rotation.z += dt * .04;
    ringGroup.children.forEach(function (ring) {
      ring.rotation.z += dt * ring.userData.speed;
    });

    chipGroup.children.forEach(function (chip, i) {
      chip.rotation.x += dt * (.05 + (i % 3) * .013);
      chip.rotation.y -= dt * (.035 + (i % 5) * .009);
      chip.position.y += Math.sin(elapsed * .6 + chip.userData.phase) * dt * .018;
    });

    const spreadTarget = targetScene === 2 ? compilerStage * .15 : targetScene === 3 ? .24 : .06;
    dieGroup.children.forEach(function (child, idx) {
      if (child.name === "core") {
        child.rotation.y += dt * .32;
        child.position.y += ((.25 + spreadTarget * 1.2) - child.position.y) * ease;
        return;
      }
      if (typeof child.userData.baseY === "number") {
        const direction = child.userData.baseY === 0 ? 0 : Math.sign(child.userData.baseY);
        const desired = child.userData.baseY + direction * spreadTarget * (1 + (idx % 4) * .18);
        child.position.y += (desired - child.position.y) * ease;
      }
    });

    pointMat.opacity += ((targetScene === 3 ? .45 : .72) - pointMat.opacity) * ease;
    lineMesh.material.opacity += ((targetScene === 2 ? .22 : .1) - lineMesh.material.opacity) * ease;
    dieGroup.visible = targetScene >= 2 || targetScene === 0;
    ringGroup.visible = targetScene !== 5;
  }

  function tick(now) {
    const dt = Math.min(.05, Math.max(.001, (now - last) / 1000));
    last = now;
    if (!document.hidden) {
      elapsed += dt;
      if (fieldMaterial) fieldMaterial.uniforms.uTime.value = elapsed;
      updateMorph(dt);
      updateTransforms(dt);
      points.rotation.y += dt * .045;
      points.rotation.x += dt * .012;
      renderer.render(scene, camera);
    }
    requestAnimationFrame(tick);
  }

  (async function bootThree() {
    try {
      const mod = await import("https://cdn.jsdelivr.net/npm/three@0.183.2/build/three.module.js");
      initThree(mod);
    } catch (err) {
      document.documentElement.classList.add("webgl-fallback");
      console.warn("Kernellum WebGL scene unavailable", err);
    }
  })();
})();