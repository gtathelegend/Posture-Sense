const { useState: uS, useEffect: uE, useRef: uR } = React;

// ─── Tweak defaults (persisted via EDITMODE markers) ───
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "light",
  "accent1": 210,
  "accent2": 340,
  "accent3": 140,
  "blobOpacity": 0.55,
  "animSpeed": 1,
  "parallax": true,
  "scrollReveal": true,
  "noise": true,
  "mesh": true
}/*EDITMODE-END*/;

// ─── Animated hero skeleton (theme-aware) ───
function PoseCanvas({ theme }) {
  const ref = uR(null);
  uE(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext('2d');
    const w = c.width, h = c.height;
    let t = 0, raf;
    const kpAt = tt => {
      const cx = w/2, cy = h/2 + 20;
      const sway = Math.sin(tt * 0.6) * 6;
      return {
        head:[cx+sway,cy-160], neck:[cx+sway*0.7,cy-110],
        lShoulder:[cx-55+sway*0.5,cy-95], rShoulder:[cx+55+sway*0.5,cy-95],
        lElbow:[cx-110+Math.sin(tt*0.8)*4,cy-30], rElbow:[cx+110+Math.sin(tt*0.9)*4,cy-30],
        lWrist:[cx-150,cy+30+Math.sin(tt*1.1)*6], rWrist:[cx+150,cy+30+Math.cos(tt*1.1)*6],
        hip:[cx,cy], lHip:[cx-30,cy+5], rHip:[cx+30,cy+5],
        lKnee:[cx-35,cy+90], rKnee:[cx+35,cy+90],
        lAnkle:[cx-40,cy+180], rAnkle:[cx+40,cy+180],
      };
    };
    const bones = [['head','neck'],['neck','lShoulder'],['neck','rShoulder'],
      ['lShoulder','lElbow'],['lElbow','lWrist'],['rShoulder','rElbow'],['rElbow','rWrist'],
      ['neck','hip'],['hip','lHip'],['hip','rHip'],['lHip','lKnee'],['lKnee','lAnkle'],
      ['rHip','rKnee'],['rKnee','rAnkle']];
    const draw = () => {
      t += 0.016;
      ctx.clearRect(0,0,w,h);
      const kp = kpAt(t);
      const isLight = theme === 'light';
      const grad = ctx.createLinearGradient(0, 0, w, h);
      if (isLight) {
        grad.addColorStop(0, 'oklch(0.55 0.18 210)');
        grad.addColorStop(0.5, 'oklch(0.55 0.22 285)');
        grad.addColorStop(1, 'oklch(0.55 0.25 340)');
      } else {
        grad.addColorStop(0, 'rgba(6, 214, 233, 0.9)');
        grad.addColorStop(1, 'rgba(255, 70, 200, 0.9)');
      }
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = grad;
      ctx.shadowBlur = isLight ? 6 : 12;
      ctx.shadowColor = isLight ? 'rgba(98, 70, 234, 0.3)' : 'rgba(6, 214, 233, 0.6)';
      bones.forEach(([a,b]) => { ctx.beginPath(); ctx.moveTo(...kp[a]); ctx.lineTo(...kp[b]); ctx.stroke(); });
      ctx.shadowBlur = 0;
      Object.values(kp).forEach(([x,y]) => {
        ctx.fillStyle = isLight ? '#0a0b1f' : '#fff';
        ctx.beginPath(); ctx.arc(x,y,4,0,Math.PI*2); ctx.fill();
        ctx.fillStyle = isLight ? 'oklch(0.62 0.25 340)' : 'rgba(255, 70, 200, 0.9)';
        ctx.beginPath(); ctx.arc(x,y,2,0,Math.PI*2); ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => cancelAnimationFrame(raf);
  }, [theme]);
  return <canvas ref={ref} width={520} height={620} style={{ width:'100%', height:'100%' }} />;
}

// ─── Scroll reveal: just toggle a body class; CSS does the work ───
function useReveal(enabled) {
  uE(() => {
    if (enabled) document.body.classList.add('anim-reveal');
    else document.body.classList.remove('anim-reveal');
  }, [enabled]);
}

// ─── Parallax on scroll (rAF-throttled; writes inline transform) ───
function useParallax(enabled) {
  uE(() => {
    const els = document.querySelectorAll('[data-parallax]');
    if (!enabled) {
      els.forEach(el => { el.style.transform = ''; });
      return;
    }
    let ticking = false;
    const update = () => {
      const sy = window.scrollY;
      const vh = window.innerHeight;
      els.forEach(el => {
        const speed = parseFloat(el.dataset.parallax);
        const rect = el.getBoundingClientRect();
        const elMid = sy + rect.top + rect.height / 2;
        const viewMid = sy + vh / 2;
        const delta = (viewMid - elMid) * speed;
        el.style.transform = `translate3d(0, ${delta.toFixed(1)}px, 0)`;
      });
      ticking = false;
    };
    const onScroll = () => { if (!ticking) { requestAnimationFrame(update); ticking = true; } };
    window.addEventListener('scroll', onScroll, { passive: true });
    update();
    return () => {
      window.removeEventListener('scroll', onScroll);
      els.forEach(el => { el.style.transform = ''; });
    };
  }, [enabled]);
}

// ─── Animated counter ───
function Counter({ to, suffix='', decimals=0, duration=1600 }) {
  const [v, setV] = uS(0);
  const ref = uR();
  uE(() => {
    const io = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        const s = performance.now();
        const step = n => {
          const p = Math.min((n - s) / duration, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          setV(to * eased);
          if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
        io.disconnect();
      }
    });
    if (ref.current) io.observe(ref.current);
    return () => io.disconnect();
  }, [to]);
  return <span ref={ref}>{v.toFixed(decimals)}{suffix}</span>;
}

// ─── Aurora background ───
function Aurora({ showMesh, showNoise, opacity, speed }) {
  const style = { '--blob-opacity': opacity, animationDuration: `${22/speed}s` };
  return (
    <>
      <div className="aurora" aria-hidden="true">
        <div className="aurora-blob b1" data-parallax="0.05" style={{ ...style, animationDuration: `${22/speed}s` }}></div>
        <div className="aurora-blob b2" data-parallax="-0.03" style={{ ...style, animationDuration: `${26/speed}s` }}></div>
        <div className="aurora-blob b3" data-parallax="0.04" style={{ ...style, animationDuration: `${30/speed}s` }}></div>
        <div className="aurora-blob b4" data-parallax="-0.02" style={{ ...style, animationDuration: `${24/speed}s` }}></div>
      </div>
      {showMesh && <div className="l-mesh" aria-hidden="true"></div>}
      {showNoise && <div className="aurora-noise" aria-hidden="true"></div>}
    </>
  );
}

// ─── Hero ───
function Hero({ theme }) {
  return (
    <section className="hero-section">
      <div className="wrap">
        <div className="hero-grid">
          <div className="hero-left reveal">
            <div className="chip mono" style={{ marginBottom: 32 }}>
              <span className="pulse-dot"></span>
              SYSTEM ONLINE · 33 KEYPOINTS · 30FPS
            </div>
            <h1 className="hero-title">
              Your body,<br/>
              <span className="grad-text">calibrated</span>.
            </h1>
            <p style={{ marginTop: 28, fontSize: 18, maxWidth: 460 }}>
              Posture Sense reads your skeleton in real time and tells you,
              frame by frame, what your body is actually doing. No wearables.
              No guesswork.
            </p>
            <div style={{ display:'flex', gap:12, marginTop:40, flexWrap:'wrap' }}>
              <a href="app.html" className="btn btn-primary btn-lg">Launch live demo <span>→</span></a>
              <a href="#how" className="btn btn-ghost btn-lg">See how it works</a>
            </div>
            <div className="hero-trust">
              <div>
                <div className="mono" style={{ fontSize:11, color:'var(--fg-3)', letterSpacing:'0.1em' }}>ACCURACY</div>
                <div className="hero-stat"><Counter to={97.3} decimals={1} suffix="%" /></div>
              </div>
              <div>
                <div className="mono" style={{ fontSize:11, color:'var(--fg-3)', letterSpacing:'0.1em' }}>LATENCY</div>
                <div className="hero-stat"><Counter to={18} suffix="ms" /></div>
              </div>
              <div>
                <div className="mono" style={{ fontSize:11, color:'var(--fg-3)', letterSpacing:'0.1em' }}>POSES</div>
                <div className="hero-stat"><Counter to={24} suffix="+" /></div>
              </div>
            </div>
          </div>

          <div className="hero-right reveal delay-2" data-parallax="-0.04">
            <div className="hero-viewport" style={{ position:'relative' }}>
              <span className="orbit-dot" style={{ top:-6, left:'12%' }}></span>
              <span className="orbit-dot d2" style={{ top:'30%', right:-8 }}></span>
              <span className="orbit-dot d3" style={{ bottom:-6, left:'40%' }}></span>
              <span className="orbit-dot d4" style={{ top:'60%', left:-8 }}></span>
              <div className="hud-corners">
                <span className="hud-corner-bl"></span>
                <span className="hud-corner-br"></span>
              </div>
              <div className="hero-viewport-inner">
                <div className="viewport-gradient"></div>
                <PoseCanvas theme={theme} />
                <div className="scanline"></div>
              </div>
              <div className="viewport-chrome">
                <div className="mono viewport-label">
                  <span className="pulse-dot"></span>
                  LIVE · WARRIOR II · CONFIDENCE 0.94
                </div>
                <div className="mono viewport-coords">
                  <span>X: 0.512</span><span>Y: 0.488</span><span>Z: 0.003</span>
                </div>
              </div>
            </div>
            <div className="hero-telemetry">
              <div className="telem"><span className="mono">HIP ANGLE</span><strong>92°</strong></div>
              <div className="telem"><span className="mono">KNEE ALIGN</span><strong style={{ color:'var(--lime)' }}>OK</strong></div>
              <div className="telem"><span className="mono">SHOULDER</span><strong style={{ color:'var(--amber)' }}>TILT 4°</strong></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Marquee() {
  const items = ['REAL-TIME SKELETAL TRACKING','MEDIAPIPE · 33 LANDMARKS','POSTURE CLASSIFICATION',
    'BIOMETRIC FEEDBACK LOOP','YOGA · STRENGTH · MOBILITY','SUB-20MS INFERENCE','ZERO WEARABLES','WEBCAM-NATIVE'];
  return (
    <section className="marquee-section">
      <div className="marquee-track">
        {[...items, ...items].map((it, i) => (
          <span key={i} className="marquee-item mono">
            {it} <span style={{ color:'var(--cyan)', margin:'0 32px' }}>✦</span>
          </span>
        ))}
      </div>
    </section>
  );
}

function Capabilities() {
  const items = [
    { no:'01', accent:'cyan', title:'Skeletal mesh overlay', desc:'Thirty-three keypoints, tracked per frame. Bone-by-bone reasoning about what your body is doing right now.', stat:'33 pts' },
    { no:'02', accent:'magenta', title:'Posture classification', desc:'Continuously classifies your pose against a library of 24+ yoga, strength, and mobility postures.', stat:'24 poses' },
    { no:'03', accent:'lime', title:'Form correction', desc:'Detects deviation in joint angles and alignment, surfaces the fix in plain English — before you get hurt.', stat:'live' },
    { no:'04', accent:'cyan', title:'Session analytics', desc:'Reps, hold duration, pose distribution, accuracy over time. Your movement history, as data you can use.', stat:'∞ history' },
  ];
  return (
    <section className="cap-section" id="about">
      <div className="wrap">
        <div className="section-head reveal">
          <span className="eyebrow">§ CAPABILITIES</span>
          <h2 style={{ marginTop:16, maxWidth:720 }}>
            Four modules. One loop.
            <span style={{ color:'var(--fg-3)' }}> See. Classify. Correct. Log.</span>
          </h2>
        </div>
        <div className="cap-grid">
          {items.map((it, i) => (
            <div key={i} className={`cap-card accent-${it.accent} reveal delay-${(i%4)+1}`}>
              <div className="cap-card-head">
                <span className="mono cap-no">{it.no}</span>
                <span className={`chip ${it.accent}`}>{it.stat}</span>
              </div>
              <h3 style={{ marginTop:40, fontSize:24 }}>{it.title}</h3>
              <p style={{ marginTop:12, fontSize:15 }}>{it.desc}</p>
              <div className="cap-bar"></div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const [active, setActive] = uS(0);
  const steps = [
    { t:'Capture',  d:"Your webcam feeds raw video straight into the pipeline. No upload, no server round-trip.", n:'/01', code:'cam.open() → stream' },
    { t:'Infer',    d:"MediaPipe's pose model extracts 33 skeletal landmarks at 30+ frames per second.",        n:'/02', code:'pose.estimate(frame)' },
    { t:'Classify', d:"Joint angles and proportions are scored against our pose library in sub-5ms.",            n:'/03', code:'classify(angles) → pose' },
    { t:'Feedback', d:"Misalignment surfaces as a cue on-screen. You correct. The loop continues.",              n:'/04', code:'render(cue) → display' },
  ];
  uE(() => { const id = setInterval(() => setActive(a => (a+1) % steps.length), 2800); return () => clearInterval(id); }, []);
  return (
    <section className="how-section" id="how">
      <div className="wrap">
        <div className="section-head reveal" style={{ textAlign:'center' }}>
          <span className="eyebrow no-rule" style={{ justifyContent:'center' }}>§ PIPELINE</span>
          <h2 style={{ marginTop:16 }}>From pixels to posture cues<br/>in under 20 milliseconds.</h2>
        </div>
        <div className="how-pipeline reveal">
          {steps.map((s, i) => (
            <div key={i} className={`how-step ${active===i?'is-active':''}`} onMouseEnter={() => setActive(i)}>
              <span className="mono how-step-n">{s.n}</span>
              <h3 style={{ fontSize:28, marginTop:16 }}>{s.t}</h3>
              <p style={{ marginTop:10, fontSize:14 }}>{s.d}</p>
              <div className="how-code mono">{s.code}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function PoseStrip() {
  const poses = [
    { name:'Warrior II', sans:'Virabhadrasana II', diff:'intermediate', hue:210 },
    { name:'Tree',       sans:'Vrikshasana',       diff:'beginner',     hue:140 },
    { name:'Cobra',      sans:'Bhujangasana',      diff:'beginner',     hue:340 },
    { name:'T-Pose',     sans:'Calibration',       diff:'setup',        hue:70  },
  ];
  return (
    <section className="pose-strip-section">
      <div className="wrap">
        <div className="section-head reveal" style={{ display:'flex', justifyContent:'space-between', alignItems:'end', flexWrap:'wrap', gap:20 }}>
          <div>
            <span className="eyebrow">§ LIBRARY</span>
            <h2 style={{ marginTop:16 }}>Poses we speak.</h2>
          </div>
          <a href="yoga-poses.html" className="btn btn-ghost">Browse all 24 →</a>
        </div>
        <div className="pose-grid">
          {poses.map((p, i) => (
            <a href="yoga-poses.html" key={i} className={`pose-card reveal delay-${(i%4)+1}`} style={{ '--pose-hue': p.hue }}>
              <div className="pose-card-art">
                <div className="pose-silhouette" style={{ background: `radial-gradient(circle at 50% 40%, oklch(0.82 0.18 ${p.hue} / 0.5), transparent 60%)` }}>
                  <div className="pose-silhouette-lines"></div>
                </div>
                <span className="chip mono pose-card-diff">{p.diff}</span>
              </div>
              <div className="pose-card-body">
                <div className="mono" style={{ fontSize:11, color:'var(--fg-3)', letterSpacing:'0.08em' }}>
                  {String(i+1).padStart(2,'0')} / {p.sans}
                </div>
                <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginTop:8 }}>
                  <div style={{ fontSize:22, fontWeight:500, color:'var(--fg-0)' }}>{p.name}</div>
                  <span style={{ color:'var(--fg-3)' }}>→</span>
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

function StatBlock() {
  return (
    <section className="stat-section">
      <div className="wrap">
        <div className="stat-grid">
          <div className="stat-item reveal">
            <div className="stat-num"><Counter to={97.3} decimals={1} suffix="%" /></div>
            <div className="mono stat-label">Pose accuracy</div>
            <p>Tested across 4,200 sessions on adult subjects, 5'2″–6'4″, varied lighting conditions.</p>
          </div>
          <div className="stat-item reveal delay-2">
            <div className="stat-num"><Counter to={18} suffix="ms" /></div>
            <div className="mono stat-label">End-to-end latency</div>
            <p>Webcam frame to classification result, measured on a mid-range laptop. No GPU required.</p>
          </div>
          <div className="stat-item reveal delay-3">
            <div className="stat-num"><Counter to={33} /></div>
            <div className="mono stat-label">Skeletal keypoints</div>
            <p>Full-body landmark tracking via MediaPipe, including hands, feet, and facial anchors.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function Team() {
  const team = [
    { name:'Vedaang Sharma', role:'Lead · Computer vision', init:'VS' },
    { name:'Trisha Bohra',   role:'Product · Movement science', init:'TB' },
  ];
  return (
    <section className="team-section" id="team">
      <div className="wrap">
        <div className="section-head reveal">
          <span className="eyebrow">§ TEAM</span>
          <h2 style={{ marginTop:16 }}>Small crew.<br/>Sharp instincts.</h2>
        </div>
        <div className="team-grid">
          {team.map((m, i) => (
            <div key={i} className={`team-card reveal delay-${i+1}`}>
              <div className="team-avatar">
                <span>{m.init}</span>
                <div className="team-avatar-ring"></div>
              </div>
              <div style={{ flex:1 }}>
                <div style={{ fontSize:22, color:'var(--fg-0)', fontWeight:500 }}>{m.name}</div>
                <div className="mono" style={{ marginTop:6, fontSize:12, color:'var(--fg-3)', letterSpacing:'0.08em', textTransform:'uppercase' }}>{m.role}</div>
              </div>
              <span className="mono" style={{ fontSize:11, color:'var(--fg-3)' }}>0{i+1}/0{team.length}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="cta-section">
      <div className="wrap-narrow">
        <div className="cta-card reveal" data-parallax="0.02">
          <div className="hud-corners">
            <span className="hud-corner-bl"></span>
            <span className="hud-corner-br"></span>
          </div>
          <span className="eyebrow" style={{ justifyContent:'center' }}>→ GET ACCESS</span>
          <h2 style={{ marginTop:20, textAlign:'center', maxWidth:720, marginLeft:'auto', marginRight:'auto' }}>
            Stop guessing your form.<br/>
            <span className="grad-text">Start reading it.</span>
          </h2>
          <p style={{ marginTop:20, textAlign:'center', maxWidth:520, marginLeft:'auto', marginRight:'auto' }}>
            Free to try, no install. Works in your browser with any webcam.
          </p>
          <div style={{ display:'flex', gap:12, justifyContent:'center', marginTop:36, flexWrap:'wrap' }}>
            <a href="register.html" className="btn btn-primary btn-lg">Create account</a>
            <a href="app.html" className="btn btn-ghost btn-lg">Try demo first</a>
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Main app with tweaks ───
function LandingApp() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);

  // Apply theme & accent CSS vars to body
  uE(() => {
    document.body.setAttribute('data-theme', t.theme);
    document.body.style.setProperty('--cyan',    `oklch(0.68 0.17 ${t.accent1})`);
    document.body.style.setProperty('--magenta', `oklch(0.62 0.25 ${t.accent2})`);
    document.body.style.setProperty('--lime',    `oklch(0.78 0.22 ${t.accent3})`);
    document.body.style.setProperty('--gradient-hero',
      `linear-gradient(135deg, oklch(0.68 0.17 ${t.accent1}) 0%, oklch(0.62 0.22 285) 45%, oklch(0.62 0.25 ${t.accent2}) 100%)`);
    // Animation speed multiplier via style attr
    document.documentElement.style.setProperty('--anim-speed', t.animSpeed);
  }, [t.theme, t.accent1, t.accent2, t.accent3, t.animSpeed]);

  useReveal(t.scrollReveal);
  useParallax(t.parallax);

  return (
    <>
      <Aurora showMesh={t.mesh} showNoise={t.noise} opacity={t.blobOpacity} speed={t.animSpeed} />
      <TopNav active="home" />
      <Hero theme={t.theme} />
      <Marquee />
      <Capabilities />
      <HowItWorks />
      <PoseStrip />
      <StatBlock />
      <Team />
      <CTA />
      <Footer />

      <TweaksPanel title="Tweaks">
        <TweakSection label="Theme" />
        <TweakRadio label="Mode" value={t.theme} options={['light','dark']} onChange={v => setTweak('theme', v)} />

        <TweakSection label="Vibrant palette" />
        <TweakSlider label="Accent · primary hue" value={t.accent1} min={0} max={360} step={1} unit="°" onChange={v => setTweak('accent1', v)} />
        <TweakSlider label="Accent · secondary hue" value={t.accent2} min={0} max={360} step={1} unit="°" onChange={v => setTweak('accent2', v)} />
        <TweakSlider label="Accent · tertiary hue" value={t.accent3} min={0} max={360} step={1} unit="°" onChange={v => setTweak('accent3', v)} />

        <TweakSection label="Background & motion" />
        <TweakSlider label="Aurora intensity" value={t.blobOpacity} min={0} max={1} step={0.05} onChange={v => setTweak('blobOpacity', v)} />
        <TweakSlider label="Animation speed" value={t.animSpeed} min={0.25} max={2.5} step={0.05} unit="×" onChange={v => setTweak('animSpeed', v)} />
        <TweakToggle label="Paper grain" value={t.noise} onChange={v => setTweak('noise', v)} />
        <TweakToggle label="Gradient mesh lines" value={t.mesh} onChange={v => setTweak('mesh', v)} />

        <TweakSection label="Scroll effects" />
        <TweakToggle label="Parallax layers" value={t.parallax} onChange={v => setTweak('parallax', v)} />
        <TweakToggle label="Scroll reveal" value={t.scrollReveal} onChange={v => setTweak('scrollReveal', v)} />
      </TweaksPanel>
    </>
  );
}

window.LandingApp = LandingApp;
