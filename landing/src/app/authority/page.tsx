"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase-browser";

interface Stats {
  total: number;
  fatal: number;
  serious: number;
  minor: number;
  critical: number;
  verified: number;
  pending: number;
  totalFatalities: number;
  totalCasualties: number;
  junctionCount: number;
  severity: Record<string, number>;
  vehicles: Record<string, number>;
  monthly: { month: string; count: number }[];
}

export default function AuthorityPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [user, setUser] = useState<any>(null);
  const [role, setRole] = useState<string>("");

  useEffect(() => {
    const init = async () => {
      const supabase = createClient();
      const { data: { user: su } } = await supabase.auth.getUser();

      const res = await fetch("/api/auth/me");
      const data = await res.json();
      setUser(data.supabaseUser);
      setRole(data.role);

      if (!su) { window.location.href = "/login"; return; }

      fetch("/api/stats").then((r) => r.json()).then(setStats);
    };
    init();
  }, []);

  const sevColors: Record<string, string> = { fatal: "#DC2626", critical: "#FBBF24", serious: "#3B82F6", minor: "#22C55E" };

  return (
    <div style={{ minHeight: "100vh", background: "#F8FAFC" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 24px", background: "#1E293B", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 19 }}>
          <img src="/accident-protection.png" alt="" style={{ width: 28, height: 28, objectFit: "contain", filter: "brightness(10)" }} />
          Authority Dashboard
        </div>
        <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <Link href="/dashboard" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Map</Link>
          <Link href="/editor" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Queue</Link>
          <span style={{ color: "#94A3B8", fontSize: 13 }}>{user?.email}</span>
        </nav>
      </header>

      <main style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 24px" }}>
        <h2 style={{ margin: "0 0 24px", fontSize: 24 }}>Traffic Authority Overview</h2>

        {stats && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 32 }}>
              {[
                { label: "Total Reports", value: stats.total, color: "#3B82F6" },
                { label: "Verified", value: stats.verified, color: "#22C55E" },
                { label: "Pending Review", value: stats.pending, color: "#FBBF24" },
                { label: "Fatal", value: stats.fatal, color: "#DC2626" },
                { label: "Tracked Junctions", value: stats.junctionCount, color: "#A855F7" },
                { label: "Total Fatalities", value: stats.totalFatalities, color: "#DC2626" },
              ].map((kpi) => (
                <div key={kpi.label} style={{ background: "#fff", padding: 20, borderRadius: 16, border: "1px solid #E2E8F0", borderTop: `3px solid ${kpi.color}` }}>
                  <div style={{ fontFamily: '"Hubot Sans","Nunito","Quicksand",system-ui,sans-serif', fontSize: 32, fontWeight: 800, color: kpi.color }}>{kpi.value}</div>
                  <div style={{ fontSize: 13, color: "#475569", fontWeight: 600, marginTop: 4 }}>{kpi.label}</div>
                </div>
              ))}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
              <div style={{ background: "#fff", padding: 20, borderRadius: 16, border: "1px solid #E2E8F0" }}>
                <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Severity Distribution</h3>
                {Object.entries(stats.severity).map(([sev, count]) => (
                  <div key={sev} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#475569", marginBottom: 2 }}>
                      <span style={{ textTransform: "capitalize" }}>{sev}</span>
                      <span style={{ fontWeight: 700 }}>{count}</span>
                    </div>
                    <div style={{ height: 10, background: "#E2E8F0", borderRadius: 999 }}>
                      <div style={{ width: `${(count / stats.total) * 100}%`, height: "100%", background: sevColors[sev] || "#3B82F6", borderRadius: 999 }} />
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ background: "#fff", padding: 20, borderRadius: 16, border: "1px solid #E2E8F0" }}>
                <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Vehicle Types</h3>
                {Object.entries(stats.vehicles).map(([v, count]) => (
                  <div key={v} style={{ marginBottom: 10 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#475569", marginBottom: 2 }}>
                      <span style={{ textTransform: "capitalize" }}>{v}</span>
                      <span style={{ fontWeight: 700 }}>{count}</span>
                    </div>
                    <div style={{ height: 10, background: "#E2E8F0", borderRadius: 999 }}>
                      <div style={{ width: `${(count / stats.total) * 100}%`, height: "100%", background: "#A855F7", borderRadius: 999 }} />
                    </div>
                  </div>
                ))}
              </div>

              {stats.monthly.length > 0 && (
                <div style={{ background: "#fff", padding: 20, borderRadius: 16, border: "1px solid #E2E8F0" }}>
                  <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Monthly Reports</h3>
                  {stats.monthly.slice(-6).map((m) => (
                    <div key={m.month} style={{ marginBottom: 8 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#475569", marginBottom: 2 }}>
                        <span>{m.month}</span>
                        <span style={{ fontWeight: 700 }}>{m.count}</span>
                      </div>
                      <div style={{ height: 8, background: "#E2E8F0", borderRadius: 999 }}>
                        <div style={{ width: `${Math.min(100, (m.count / Math.max(...stats.monthly.map((x) => x.count))) * 100)}%`, height: "100%", background: "#3B82F6", borderRadius: 999 }} />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={{ marginTop: 32, textAlign: "center" }}>
              <Link href="/editor" style={{ display: "inline-block", background: "#3B82F6", color: "#fff", padding: "14px 40px", borderRadius: 45, textDecoration: "none", fontWeight: 600, fontSize: 16 }}>
                Review Pending Reports
              </Link>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
