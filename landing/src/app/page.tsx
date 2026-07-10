import Link from "next/link";

export default function Home() {
  return (
    <>
      {/* Topbar — Sky blue (#3B82F6) */}
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 24px",
          background: "#3B82F6",
          color: "#fff",
          position: "sticky",
          top: 0,
          zIndex: 1000,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontFamily: '"Hubot Sans","Nunito","Quicksand",system-ui,sans-serif', fontWeight: 700, fontSize: "19px" }}>
          <img src="/accident-protection.png" alt="" style={{ width: 28, height: 28, objectFit: "contain", filter: "brightness(10)" }} />
          Road Safety Dar es Salaam
        </div>
        <nav style={{ display: "flex", alignItems: "center", gap: "24px" }}>
          <Link href="/dashboard/" className="topbar-link">Dashboard</Link>
          <Link href="/report/" className="topbar-link">Report</Link>
          <Link href="/login" className="btn-signin">Sign In</Link>
        </nav>
      </header>

      <main style={{ maxWidth: 1280, margin: "0 auto", padding: "48px 24px" }}>
        {/* Hero Section */}
        <section className="hero-section">
          <div style={{ position: "relative", zIndex: 1 }}>
            <h1 style={{ margin: 0, fontSize: "56px", fontWeight: 800, lineHeight: 1.05, color: "#fff" }}>
              Road Safety{" "}
              <span style={{ color: "#60A5FA" }}>Dar es Salaam</span>
            </h1>
            <p style={{ margin: "12px 0 0", fontSize: "20px", color: "#94A3B8", maxWidth: "56ch" }}>
              Real-time accident hotspot intelligence for Tanzania&apos;s commercial capital. Crowdsourced reports, official police data, and AI-powered safety insights for every junction.
            </p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "16px", position: "relative", flexShrink: 0 }}>
            <span className="live-badge">
              <span className="live-dot" />
              LIVE DATA
            </span>
            <img src="/map-icon-2.png" alt="Map" style={{ width: 120, height: 120, objectFit: "contain", opacity: 0.8 }} />
          </div>
        </section>

        {/* KPI Grid */}
        <div className="kpi-grid">
          {[
            { num: "1,200+", label: "Total Reports", color: "#F87171", border: "#F87171" },
            { num: "850+", label: "Verified Reports", color: "#22C55E", border: "#22C55E" },
            { num: "60+", label: "Tracked Junctions", color: "#3B82F6", border: "#3B82F6" },
            { num: "40%", label: "Police Verified", color: "#FBBF24", border: "#FBBF24" },
          ].map((kpi) => (
            <div key={kpi.label} className="kpi-card" style={{ borderTop: `3px solid ${kpi.border}` }}>
              <div className="kpi-value" style={{ color: kpi.color }}>{kpi.num}</div>
              <div className="kpi-label">{kpi.label}</div>
            </div>
          ))}
        </div>

        {/* Action Bar */}
        <div className="action-bar">
          <Link href="/report/" className="btn-primary">+ Report Accident</Link>
          <Link href="/dashboard/" className="btn-secondary">Hotspot Map</Link>
          <Link href="/login" className="btn-ghost">Sign In</Link>
          <div className="lang-switch">
            <a href="/">EN</a> | <a href="/sw/">SW</a>
          </div>
        </div>

        {/* Featured Stat Cards */}
        <div className="featured-stat-grid">
          {[
            { label: "Total Reports", sublabel: "Crowdsourced + official", value: "1,200+", icon: "/add-report.png", gradient: "linear-gradient(135deg, #DBEAFE, #FFFFFF)", color: "#3B82F6" },
            { label: "Fatal Accidents", sublabel: "Since Jan 2024", value: "45", icon: "/stone-hazard.png", gradient: "linear-gradient(135deg, #FEE2E2, #FFFFFF)", color: "#F87171" },
            { label: "Tracked Junctions", sublabel: "Across 5 districts", value: "60+", icon: "/map-icon.png", gradient: "linear-gradient(135deg, #FEF3C7, #FFFFFF)", color: "#D97706" },
            { label: "Police Verified", sublabel: "Official records", value: "850+", icon: "/badge-72x72.png", gradient: "linear-gradient(135deg, #DCFCE7, #FFFFFF)", color: "#16A34A" },
          ].map((card) => (
            <div key={card.label} className="featured-stat-card" style={{ background: card.gradient }}>
              <img src={card.icon} alt="" style={{ width: 44, height: 44, objectFit: "contain", opacity: 0.7, marginBottom: 8 }} />
              <div className="featured-stat-card-body">
                <div className="featured-stat-value">{card.value}</div>
                <div className="featured-stat-label" style={{ color: card.color }}>{card.label}</div>
                <div className="featured-stat-sublabel">{card.sublabel}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Charts Grid */}
        <div className="charts-grid">
          <div className="chart-card">
            <h3>Severity Distribution</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {[
                { label: "Fatal", value: 15, color: "#F87171" },
                { label: "Critical", value: 25, color: "#FBBF24" },
                { label: "Serious", value: 35, color: "#3B82F6" },
                { label: "Minor", value: 25, color: "#22C55E" },
              ].map((s) => (
                <div key={s.label}>
                  <div className="severity-bar-header">
                    <span>{s.label}</span>
                    <span className="severity-bar-value">{s.value}%</span>
                  </div>
                  <div className="severity-bar-track">
                    <div className="severity-bar-fill" style={{ width: `${s.value}%`, background: s.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-card">
            <h3>Key Features</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {[
                { icon: "📍", text: "Crowdsourced accident reports from citizens across all 5 districts" },
                { icon: "🤖", text: "AI-powered recommendations for high-risk junctions" },
                { icon: "👮", text: "Police verification workflow for data integrity" },
                { icon: "📊", text: "Real-time statistics and CSV data export" },
              ].map((f) => (
                <div key={f.text} className="feature-item">
                  <span style={{ fontSize: "24px" }}>{f.icon}</span>
                  <span className="feature-text">{f.text}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="chart-card wide">
            <h3>Coverage Area — Dar es Salaam</h3>
            <div className="district-grid">
              {[
                { district: "Ilala", wards: 17 },
                { district: "Kinondoni", wards: 20 },
                { district: "Temeke", wards: 24 },
                { district: "Ubungo", wards: 14 },
                { district: "Kigamboni", wards: 8 },
              ].map((d) => (
                <div key={d.district} className="district-card">
                  <div className="district-name">{d.district}</div>
                  <div className="district-wards">{d.wards} wards</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      <footer className="site-footer">
        <small>SDG 11.2 — Safer urban transport in Dar es Salaam · Built by Mwijay · 2026</small>
      </footer>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }
        .topbar-link {
          color: #fff; text-decoration: none; font-size: 16px; font-weight: 600;
          padding: 8px 12px; border-radius: 8px; transition: background 0.24s;
        }
        .topbar-link:hover { background: rgba(255,255,255,0.15); }
        .btn-signin {
          background: #60A5FA; color: #fff; padding: 0.4rem 1rem; border-radius: 6px;
          font-weight: 700; text-decoration: none; font-size: 0.85rem;
          box-shadow: 0 2px 6px rgba(59,130,246,0.3);
          transition: background 0.2s, transform 0.15s;
        }
        .btn-signin:hover { background: #3B82F6; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(59,130,246,0.4); }
        .hero-section {
          display: flex; align-items: flex-start; justify-content: space-between; gap: 48px;
          margin-bottom: 48px; padding: 48px;
          background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
          border-radius: 28px; color: #fff; position: relative; overflow: hidden;
        }
        .live-badge {
          display: inline-flex; align-items: center; gap: 8px;
          background: rgba(34, 197, 94, 0.15); color: #22C55E;
          padding: 8px 16px; border-radius: 999px; font-size: 16px; font-weight: 600;
          letter-spacing: 0.04em; text-transform: uppercase;
          border: 1px solid rgba(34, 197, 94, 0.3); backdrop-filter: blur(4px);
        }
        .live-dot {
          width: 8px; height: 8px; border-radius: 50%; background: #22C55E;
          animation: pulse 1.5s ease-in-out infinite;
        }
        .kpi-grid {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px; margin-bottom: 48px;
        }
        .kpi-card {
          background: #fff; padding: 24px; border-radius: 20px;
          border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(15,23,42,0.04);
          text-align: center;
          transition: transform 0.24s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.24s;
        }
        .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(15,23,42,0.06); }
        .kpi-value {
          font-family: "Hubot Sans","Nunito","Quicksand",system-ui,sans-serif;
          font-size: 40px; font-weight: 800; line-height: 1;
        }
        .kpi-label { font-size: 16px; color: #475569; margin-top: 8px; font-weight: 600; }
        .action-bar {
          display: flex; flex-wrap: wrap; gap: 12px; align-items: center;
          margin-bottom: 48px; padding: 24px 32px;
          background: #fff; border-radius: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.04);
        }
        .btn-primary, .btn-secondary, .btn-ghost {
          display: inline-flex; align-items: center; gap: 8px;
          text-decoration: none; font-family: "Atkinson Hyperlegible","Nunito Sans","Inter",system-ui,sans-serif;
          font-size: 12px; text-transform: uppercase; letter-spacing: 2.5px;
          font-weight: 600; min-height: 56px; padding: 1.3em 3em;
          border-radius: 45px; cursor: pointer; line-height: 1;
          box-shadow: 0px 8px 15px rgba(0, 0, 0, 0.1);
          transition: all 0.3s ease 0s;
        }
        .btn-primary { background: #fff; color: #000; }
        .btn-primary:hover { background-color: #23c483; box-shadow: 0px 15px 20px rgba(46, 229, 157, 0.4); color: #fff; transform: translateY(-7px); }
        .btn-secondary { background: #fff; color: #000; }
        .btn-secondary:hover { background-color: #3B82F6; box-shadow: 0px 15px 20px rgba(59, 130, 246, 0.4); color: #fff; transform: translateY(-7px); }
        .btn-ghost { background: transparent; box-shadow: none; color: #000; }
        .btn-ghost:hover { background: #f1f5f9; box-shadow: 0px 8px 15px rgba(0, 0, 0, 0.08); transform: translateY(-3px); }
        .lang-switch { margin-left: auto; display: flex; align-items: center; gap: 8px; font-size: 16px; color: #475569; }
        .lang-switch a { color: #3B82F6; text-decoration: none; font-weight: 600; padding: 8px 12px; border-radius: 8px; }
        .lang-switch a:hover { background: #DBEAFE; }
        .featured-stat-grid {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 24px; margin: 48px 0;
        }
        .featured-stat-card {
          position: relative; width: 100%; max-width: 320px; height: 260px;
          border-radius: 20px; overflow: hidden; isolation: isolate;
          transition: transform 0.24s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.24s;
          border: 1px solid #E2E8F0;
        }
        .featured-stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(15,23,42,0.06); }
        .featured-stat-card-body {
          z-index: 1; position: relative; width: 100%; height: 100%;
          border-radius: 19px; background: rgba(255,255,255,0.88);
          backdrop-filter: blur(4px); display: flex; flex-direction: column;
          align-items: center; justify-content: center; padding: 24px 16px;
          text-align: center; gap: 4px;
        }
        .featured-stat-value {
          font-family: "Hubot Sans","Nunito","Quicksand",system-ui,sans-serif;
          font-weight: 800; font-size: 40px; letter-spacing: -0.02em; color: #0F172A;
        }
        .featured-stat-label {
          font-family: "Hubot Sans","Nunito","Quicksand",system-ui,sans-serif;
          font-size: 19px; font-weight: 600; margin-top: 8px;
        }
        .featured-stat-sublabel { font-size: 14px; color: #475569; margin-top: 4px; }
        .charts-grid {
          display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-bottom: 48px;
        }
        .chart-card {
          background: #fff; padding: 24px; border-radius: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.04);
        }
        .chart-card h3 {
          margin: 0 0 16px; font-family: "Hubot Sans","Nunito","Quicksand",system-ui,sans-serif;
          font-size: 19px; color: #0F172A; font-weight: 600;
        }
        .chart-card.wide { grid-column: span 2; }
        .severity-bar-header { display: flex; justify-content: space-between; font-size: 14px; color: #475569; margin-bottom: 4px; }
        .severity-bar-value { font-weight: 700; color: #0F172A; }
        .severity-bar-track { height: 8px; background: #E2E8F0; border-radius: 999px; overflow: hidden; }
        .severity-bar-fill { height: 100%; border-radius: 999px; transition: width 300ms ease; }
        .feature-item { display: flex; gap: 12px; align-items: center; }
        .feature-text { font-size: 14px; color: #475569; line-height: 1.5; }
        .district-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; }
        .district-card { padding: 16px; background: #F8FAFC; border-radius: 16px; border: 1px solid #E2E8F0; text-align: center; }
        .district-name { font-family: "Hubot Sans","Nunito","Quicksand",system-ui,sans-serif; font-weight: 700; font-size: 16px; color: #0F172A; }
        .district-wards { font-size: 12px; color: #475569; margin-top: 4px; }
        .site-footer { text-align: center; padding: 48px 24px; color: #94A3B8; font-size: 14px; border-top: 1px solid #E2E8F0; }
      `}</style>
    </>
  );
}
