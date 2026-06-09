/* ================================================================
   ATLAS — Main JavaScript
   Star particles · Scroll reveal · Counter animation · Toast
   ================================================================ */

// ── Star Particle Canvas ────────────────────────────────────────
(function initStars() {
  const canvas = document.getElementById('stars-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let stars = [], W, H, animId;

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
    buildStars();
  }

  function buildStars() {
    stars = Array.from({ length: 160 }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: Math.random() * 1.4 + 0.2,
      a: Math.random(),
      da: (Math.random() - 0.5) * 0.004,
      vx: (Math.random() - 0.5) * 0.06,
      vy: (Math.random() - 0.5) * 0.06,
    }));
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    for (const s of stars) {
      s.x = (s.x + s.vx + W) % W;
      s.y = (s.y + s.vy + H) % H;
      s.a = Math.max(0.05, Math.min(1, s.a + s.da));
      if (s.a <= 0.05 || s.a >= 1) s.da *= -1;

      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${s.a * 0.7})`;
      ctx.fill();
    }
    animId = requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resize);
  resize();
  draw();
})();

// ── Scroll Reveal ───────────────────────────────────────────────
(function initReveal() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        e.target.classList.add('revealed');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.06 });

  document.querySelectorAll('.reveal').forEach(el => io.observe(el));
})();

// ── Counter Animation ───────────────────────────────────────────
(function initCounters() {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const el = e.target;
      const target = parseInt(el.dataset.target, 10) || 0;
      animateCounter(el, target);
      io.unobserve(el);
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('.counter').forEach(el => io.observe(el));
})();

function animateCounter(el, target) {
  const duration = 1600;
  const start = performance.now();
  const startVal = 0;
  function step(now) {
    const t = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - t, 3); // easeOutCubic
    el.textContent = Math.round(startVal + (target - startVal) * ease);
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── Toast Notifications ─────────────────────────────────────────
function showToast(message, type = 'info', duration = 5000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-msg">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast-show'));

  setTimeout(() => {
    toast.classList.remove('toast-show');
    toast.addEventListener('transitionend', () => toast.remove(), { once: true });
  }, duration);
}

// ── Tab Switcher (shared) ───────────────────────────────────────
function switchTab(tabId, groupClass) {
  const group = groupClass || 'tab-btn';
  // deactivate all tabs in the same nav
  document.querySelectorAll(`.${group}`).forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

  const btn = document.querySelector(`[data-tab="${tabId}"]`);
  const panel = document.getElementById(`tab-${tabId}`);
  if (btn) btn.classList.add('active');
  if (panel) panel.classList.add('active');
}

// ── Skeleton Loader Helper ──────────────────────────────────────
function showSkeleton(containerId, rows = 3) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = Array.from({ length: rows }, () =>
    `<div class="skeleton" style="height:48px;margin-bottom:10px;border-radius:8px;"></div>`
  ).join('');
}

// ── Utility: Format number ──────────────────────────────────────
function fmt(val, decimals = 2) {
  if (val === null || val === undefined || isNaN(val)) return '—';
  return parseFloat(val).toFixed(decimals);
}

// ── Utility: Debounce ───────────────────────────────────────────
function debounce(fn, delay) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

// ── Navbar scroll shrink ────────────────────────────────────────
(function initNavbarScroll() {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  let lastY = 0;
  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    if (y > 60) {
      navbar.classList.add('navbar-compact');
    } else {
      navbar.classList.remove('navbar-compact');
    }
    lastY = y;
  }, { passive: true });
})();

// ── Mobile nav toggle ───────────────────────────────────────────
(function initMobileNav() {
  const toggle = document.querySelector('.nav-mobile-toggle');
  const links  = document.querySelector('.nav-links');
  if (!toggle || !links) return;
  toggle.addEventListener('click', () => {
    links.classList.toggle('nav-open');
  });
})();

// ── Plotly default config ───────────────────────────────────────
window.PLOTLY_CONFIG = {
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
  responsive: true,
};

window.PLOTLY_LAYOUT_BASE = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor:  'rgba(0,0,0,0)',
  font: { family: 'Space Grotesk, Inter, sans-serif', color: '#c8cad4', size: 12 },
  margin: { l: 40, r: 20, t: 40, b: 40 },
};

// ── Expose helpers globally ─────────────────────────────────────
window.showToast    = showToast;
window.switchTab    = switchTab;
window.showSkeleton = showSkeleton;
window.fmt          = fmt;
window.debounce     = debounce;

// ── Conspiracy / Ambient Alerts ─────────────────────────────────
(function initConspiracyAlerts() {
  const ALERTS = [
    { icon: '📡', title: 'SIGNAL INTERCEPTED', msg: 'Anomalous radio burst detected from GJ 273 — pattern matches no known pulsar.', color: '#d4a574' },
    { icon: '👁️', title: 'CLASSIFIED OBJECT', msg: 'Object 2031-XK7 on approach vector. NASA has not issued a statement.', color: '#a084dc' },
    { icon: '🛸', title: 'UNIDENTIFIED SIGNATURE', msg: 'Thermal anomaly near Proxima Cen b exceeds stellar wind models by 340%.', color: '#5eead4' },
    { icon: '⚡', title: 'DYSON STRUCTURE?', msg: 'KIC 8462852 flux drop recorded. Megastructure hypothesis not ruled out.', color: '#facc15' },
    { icon: '🌀', title: 'WORMHOLE CANDIDATE', msg: 'Spacetime curvature spike logged at RA 14h29m, Dec −62°. Duration: 0.003s.', color: '#38bdf8' },
    { icon: '🔭', title: 'TECHNOSIGNATURE', msg: 'Laser-wavelength emission at 656.3 nm from TRAPPIST-1 system. Hydrogen line. Intentional?', color: '#4ade80' },
    { icon: '📻', title: 'WOW! ECHO', msg: 'Sequence 6EQUJ5 re-observed at Big Ear coordinates. Source: unknown.', color: '#fb923c' },
    { icon: '🧬', title: 'BIOSIGNATURE ALERT', msg: 'Phosphine absorption lines confirmed in K2-18b atmosphere. Abiotic origin unlikely.', color: '#4ade80' },
    { icon: '🔐', title: 'ENCRYPTED BURST', msg: 'Prime-number-spaced pulses from HD 164922 b orbit. Encoded message suspected.', color: '#a084dc' },
    { icon: '🌑', title: 'DARK FLEET DETECTED?', msg: 'Gravitational microlensing at L2 Lagrange of Kepler-442 — object mass: ~1.3 Jupiter.', color: '#94a3b8' },
    { icon: '⚗️', title: 'FORBIDDEN CHEMISTRY', msg: 'Nitrogen trifluoride detected in TOI-700d exosphere. No known geological source.', color: '#d4a574' },
    { icon: '🌐', title: 'GRID PATTERN DETECTED', msg: 'Surface albedo variations on Gliese 667Cc show 6° angular periodicity. Not geological.', color: '#38bdf8' },
  ];

  function showConspiracyToast(alert) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast toast-conspiracy';
    toast.style.setProperty('--c-accent', alert.color);
    toast.innerHTML = `
      <div class="toast-conspiracy-header">
        <span class="toast-conspiracy-icon">${alert.icon}</span>
        <span class="toast-conspiracy-title">${alert.title}</span>
        <span class="toast-conspiracy-badge">⬤ LIVE</span>
        <button class="toast-close" onclick="this.closest('.toast').remove()">×</button>
      </div>
      <div class="toast-conspiracy-body">${alert.msg}</div>
      <div class="toast-conspiracy-footer">ATLAS DEEP SCAN · SIGNAL CONFIDENCE: ${(Math.random()*30+65).toFixed(1)}%</div>
    `;

    container.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add('toast-show'));

    setTimeout(() => {
      toast.classList.remove('toast-show');
      toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    }, 5000);
  }

  const MAX_TOASTS = 3;

  function canShow() {
    if (document.hidden) return false;
    return document.querySelectorAll('.toast-conspiracy.toast-show').length < MAX_TOASTS;
  }

  function scheduleNext() {
    const delay = (120 + Math.random() * 60) * 1000;
    setTimeout(() => {
      if (canShow()) showConspiracyToast(ALERTS[Math.floor(Math.random() * ALERTS.length)]);
      scheduleNext();
    }, delay);
  }

  // Clear stale toasts when user returns to tab
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      document.querySelectorAll('.toast-conspiracy').forEach(t => {
        t.classList.remove('toast-show');
        setTimeout(() => t.remove(), 350);
      });
    }
  });

  setTimeout(() => {
    if (canShow()) showConspiracyToast(ALERTS[Math.floor(Math.random() * ALERTS.length)]);
    scheduleNext();
  }, (60 + Math.random() * 30) * 1000);
})();
window.animateCounter = animateCounter;
