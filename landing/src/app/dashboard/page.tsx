"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

interface Accident {
  id: number;
  lat: number;
  lng: number;
  severity: string;
  vehicleTypes: string[];
  district: string;
  junctionName: string;
  occurredAt: string;
  casualties: number;
  fatalities: number;
  verified: boolean;
  upvoteCount: number;
  intensity: number;
  photoUrl?: string;
  description?: string;
}

interface Stats {
  total: number;
  fatal: number;
  serious: number;
  minor: number;
  critical: number;
  verified: number;
  totalFatalities: number;
  totalCasualties: number;
  junctionCount: number;
  severity: Record<string, number>;
  vehicles: Record<string, number>;
  monthly: { month: string; count: number }[];
  hourly: { hour: number; count: number }[];
}

export default function DashboardPage() {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const heatRef = useRef<any>(null);
  const [accidents, setAccidents] = useState<Accident[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [selectedHour, setSelectedHour] = useState("all");
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    fetch("/api/accidents").then((r) => r.json()).then(setAccidents);
    fetch("/api/stats").then((r) => r.json()).then(setStats);
    // Check stored user
    const stored = localStorage.getItem("rsd_user");
    if (stored) setUser(JSON.parse(stored));
  }, []);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    const L = (window as any).L;
    if (!L) return;

    const map = L.map(mapRef.current).setView([-6.7924, 39.2083], 11);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; OpenStreetMap",
    }).addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  const markersRef = useRef<any[]>([]);

  useEffect(() => {
    const L = (window as any).L;
    if (!L || !mapInstanceRef.current) return;

    const map = mapInstanceRef.current;

    // Clear old markers
    markersRef.current.forEach((m: any) => map.removeLayer(m));
    markersRef.current = [];

    // Clear old heatmap
    if (heatRef.current) {
      map.removeLayer(heatRef.current);
      heatRef.current = null;
    }

    const filtered = selectedHour === "all"
      ? accidents
      : accidents.filter((a) => {
          const h = new Date(a.occurredAt).getHours();
          return h === parseInt(selectedHour);
        });

    const points = filtered.map((a) => [a.lat, a.lng, a.intensity]);
    if (points.length > 0) {
      heatRef.current = (L as any).heatLayer(points, {
        radius: 25,
        blur: 15,
        maxZoom: 10,
        max: 4,
        gradient: { 0.4: "#22C55E", 0.6: "#FBBF24", 0.8: "#F87171", 1: "#DC2626" },
      }).addTo(map);
    }

    // Add markers with popups
    filtered.forEach((a) => {
      const sevColors: Record<string, string> = { fatal: "#DC2626", critical: "#FBBF24", serious: "#3B82F6", minor: "#22C55E" };
      const photoHtml = a.photoUrl
        ? `<img src="${a.photoUrl}" alt="Accident photo" style="width:100%; max-height:150px; object-fit:cover; border-radius:8px; margin-bottom:8px;">`
        : "";
      const html = `
        <div style="min-width:220px; font-family:system-ui,sans-serif;">
          ${photoHtml}
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
            <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${sevColors[a.severity]};"></span>
            <strong style="font-size:14px; text-transform:capitalize;">${a.severity}</strong>
          </div>
          <div style="font-size:12px; color:#475569; margin-bottom:2px;"><strong>${a.junctionName}</strong>${a.district ? `, ${a.district}` : ""}</div>
          <div style="font-size:12px; color:#64748B;">${new Date(a.occurredAt).toLocaleDateString()}</div>
          ${a.description ? `<div style="font-size:12px; color:#475569; margin-top:4px; border-top:1px solid #E2E8F0; padding-top:4px;">${a.description}</div>` : ""}
        </div>`;
      const marker = L.circleMarker([a.lat, a.lng], {
        radius: 6,
        color: sevColors[a.severity],
        fillColor: sevColors[a.severity],
        fillOpacity: 0.8,
        weight: 1,
      }).addTo(map);
      marker.bindPopup(html);
      markersRef.current.push(marker);
    });
  }, [accidents, selectedHour]);

  const sevColors: Record<string, string> = {
    fatal: "#F87171",
    critical: "#FBBF24",
    serious: "#3B82F6",
    minor: "#22C55E",
  };

  return (
    <div style={{ minHeight: "100vh", background: "#F8FAFC" }}>
      {/* Topbar */}
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 24px", background: "#3B82F6", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <img src="/accident-protection.png" alt="" style={{ width: 32, height: 32, objectFit: "contain" }} />
          <span style={{ fontWeight: 700, fontSize: 19, fontFamily: '"Hubot Sans","Nunito","Quicksand",system-ui,sans-serif' }}>
            Road Safety Dar es Salaam
          </span>
        </div>
        <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <Link href="/dashboard" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Dashboard</Link>
          <Link href="/report" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Report</Link>
          {user ? (
            <span style={{ color: "#fff", fontSize: 14 }}>{user.email}</span>
          ) : (
            <Link href="/login" style={{ background: "#60A5FA", color: "#fff", padding: "6px 14px", borderRadius: 6, fontWeight: 700, textDecoration: "none", fontSize: 13 }}>Sign In</Link>
          )}
        </nav>
      </header>

      <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px 24px" }}>
        {/* KPI Grid */}
        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16, marginBottom: 24 }}>
            {[
              { label: "Total Reports", value: stats.total, color: "#F87171" },
              { label: "Verified", value: stats.verified, color: "#22C55E" },
              { label: "Fatal", value: stats.fatal, color: "#F87171" },
              { label: "Critical", value: stats.critical, color: "#FBBF24" },
              { label: "Serious", value: stats.serious, color: "#3B82F6" },
              { label: "Junctions", value: stats.junctionCount, color: "#A855F7" },
            ].map((kpi) => (
              <div key={kpi.label} style={{ background: "#fff", padding: "16px", borderRadius: 16, border: "1px solid #E2E8F0", borderTop: `3px solid ${kpi.color}`, textAlign: "center" }}>
                <div style={{ fontFamily: '"Hubot Sans","Nunito","Quicksand",system-ui,sans-serif', fontSize: 28, fontWeight: 800, color: kpi.color }}>{kpi.value}</div>
                <div style={{ fontSize: 13, color: "#475569", fontWeight: 600, marginTop: 4 }}>{kpi.label}</div>
              </div>
            ))}
          </div>
        )}

        {/* Map controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12, padding: "12px 16px", background: "#fff", borderRadius: 12 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: "0.04em" }}>
            Filter by Hour
          </label>
          <select
            value={selectedHour}
            onChange={(e) => setSelectedHour(e.target.value)}
            style={{ padding: "8px 16px", border: "1px solid #E2E8F0", borderRadius: 12, fontSize: 14, minHeight: 44 }}
          >
            <option value="all">All Hours</option>
            {Array.from({ length: 24 }, (_, i) => (
              <option key={i} value={i}>{i}:00 - {(i + 1) % 24}:00</option>
            ))}
          </select>
        </div>

        {/* Map */}
        <div ref={mapRef} style={{ height: 480, borderRadius: 16, overflow: "hidden", marginBottom: 24, border: "1px solid #E2E8F0" }} />

        {/* Charts */}
        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
            {/* Severity */}
            <div style={{ background: "#fff", padding: 20, borderRadius: 16, border: "1px solid #E2E8F0" }}>
              <h3 style={{ margin: "0 0 16px", fontFamily: '"Hubot Sans","Nunito","Quicksand",system-ui,sans-serif', fontSize: 16, fontWeight: 600 }}>Severity Distribution</h3>
              {Object.entries(stats.severity).map(([sev, count]) => (
                <div key={sev} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#475569", marginBottom: 2 }}>
                    <span>{sev.charAt(0).toUpperCase() + sev.slice(1)}</span>
                    <span style={{ fontWeight: 700 }}>{count}</span>
                  </div>
                  <div style={{ height: 8, background: "#E2E8F0", borderRadius: 999 }}>
                    <div style={{ width: `${(count / stats.total) * 100}%`, height: "100%", background: sevColors[sev] || "#3B82F6", borderRadius: 999 }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Vehicle Types */}
            <div style={{ background: "#fff", padding: 20, borderRadius: 16, border: "1px solid #E2E8F0" }}>
              <h3 style={{ margin: "0 0 16px", fontFamily: '"Hubot Sans","Nunito","Quicksand",system-ui,sans-serif', fontSize: 16, fontWeight: 600 }}>Vehicle Types</h3>
              {Object.entries(stats.vehicles).map(([v, count]) => (
                <div key={v} style={{ marginBottom: 8 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#475569", marginBottom: 2 }}>
                    <span>{v}</span>
                    <span style={{ fontWeight: 700 }}>{count}</span>
                  </div>
                  <div style={{ height: 8, background: "#E2E8F0", borderRadius: 999 }}>
                    <div style={{ width: `${(count / stats.total) * 100}%`, height: "100%", background: "#A855F7", borderRadius: 999 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
