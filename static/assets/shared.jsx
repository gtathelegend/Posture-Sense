// Shared nav + footer + page shell
const { useState, useEffect, useRef } = React;

const NAV_LINKS = [
  { id: 'home',      label: 'home',      href: '/landing' },
  { id: 'demo',      label: 'live demo', href: '/pose_detection' },
  { id: 'poses',     label: 'poses',     href: '/yoga-poses' },
  { id: 'dashboard', label: 'dashboard', href: '/dashboard' },
];

function useAuth() {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('ps_user') || 'null'); }
    catch { return null; }
  });
  useEffect(() => {
    const h = () => {
      try { setUser(JSON.parse(localStorage.getItem('ps_user') || 'null')); }
      catch { setUser(null); }
    };
    window.addEventListener('storage', h);
    window.addEventListener('ps-auth', h);
    return () => { window.removeEventListener('storage', h); window.removeEventListener('ps-auth', h); };
  }, []);
  const login = (u) => { localStorage.setItem('ps_user', JSON.stringify(u)); window.dispatchEvent(new Event('ps-auth')); };
  const logout = () => { localStorage.removeItem('ps_user'); window.dispatchEvent(new Event('ps-auth')); };
  return { user, login, logout };
}

function Logo() {
  return (
    <a href="/landing" className="ps-logo">
      <div className="ps-logo-mark"></div>
      <span>posture<span className="dot">.</span>sense</span>
    </a>
  );
}

function TopNav({ active }) {
  const { user, logout } = useAuth();
  return (
    <nav className="ps-nav">
      <div className="ps-nav-inner">
        <Logo />
        <div className="ps-navmenu">
          {NAV_LINKS.map(l => (
            <a key={l.id} href={l.href} className={active === l.id ? 'active' : ''}>{l.label}</a>
          ))}
        </div>
        <div className="ps-nav-cta">
          {user ? (
            <>
              <span className="chip cyan" style={{ textTransform: 'none' }}>
                <span className="pulse-dot" style={{ width: 6, height: 6 }}></span>
                {user.username}
              </span>
              <button className="btn btn-sm btn-ghost" onClick={() => { logout(); location.href = '/landing'; }}>logout</button>
            </>
          ) : (
            <>
              <a href="/login" className="btn btn-sm btn-ghost">sign in</a>
              <a href="/register" className="btn btn-sm btn-primary">get access &rarr;</a>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

function Footer() {
  return (
    <footer className="ps-footer">
      <div className="wrap">
        <div className="ps-footer-grid">
          <div>
            <Logo />
            <p style={{ marginTop: 16, maxWidth: 320, fontSize: 14 }}>
              Real-time computer vision for posture correction and exercise feedback.
            </p>
            <div style={{ marginTop: 20, display: 'flex', gap: 8 }}>
              <span className="chip mono">v2.4 &middot; april 2026</span>
            </div>
          </div>
          <div>
            <h4>Product</h4>
            <ul>
              <li><a href="/landing#features">Features</a></li>
              <li><a href="/pose_detection">Live demo</a></li>
              <li><a href="/yoga-poses">Pose library</a></li>
              <li><a href="/dashboard">Dashboard</a></li>
            </ul>
          </div>
          <div>
            <h4>Company</h4>
            <ul>
              <li><a href="/landing#about">About</a></li>
              <li><a href="#">Research</a></li>
              <li><a href="#">Changelog</a></li>
              <li><a href="/contact">Contact</a></li>
            </ul>
          </div>
          <div>
            <h4>System</h4>
            <ul>
              <li className="mono" style={{ color: 'var(--fg-2)', fontSize: 13 }}>
                <span style={{ color: 'var(--lime)' }}>&#9679;</span>&nbsp; all systems nominal
              </li>
              <li className="mono" style={{ color: 'var(--fg-3)', fontSize: 12 }}>latency &middot; 18ms</li>
              <li className="mono" style={{ color: 'var(--fg-3)', fontSize: 12 }}>accuracy &middot; 97.3%</li>
            </ul>
          </div>
        </div>
        <div className="ps-footer-bottom">
          <span>&#169; 2026 POSTURE.SENSE &mdash; ALL RIGHTS RESERVED</span>
          <span>VIVEKANANDA GLOBAL UNIVERSITY &middot; JAIPUR</span>
        </div>
      </div>
    </footer>
  );
}

window.TopNav = TopNav;
window.Footer = Footer;
window.Logo = Logo;
window.useAuth = useAuth;
