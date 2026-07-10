"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase-browser";

interface AccidentItem {
  id: number;
  severity: string;
  district: string;
  ward: string;
  junctionName: string;
  occurredAt: string;
  description: string;
  photoUrl: string;
  verificationStatus: string;
  upvoteCount: number;
  vehicleTypes: string[];
  casualties: number;
  fatalities: number;
  injuries: number;
  weather: string;
  roadCondition: string;
}

export default function EditorPage() {
  const [accidents, setAccidents] = useState<AccidentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<any>(null);
  const [role, setRole] = useState<string>("");
  const [actionId, setActionId] = useState<number | null>(null);
  const [filter, setFilter] = useState("pending");

  useEffect(() => {
    const init = async () => {
      const supabase = createClient();
      const { data: { user: su } } = await supabase.auth.getUser();
      if (!su) { window.location.href = "/login"; return; }

      const res = await fetch("/api/auth/me");
      const data = await res.json();
      setUser(data.supabaseUser);
      setRole(data.role);

      if (data.role !== "editor" && data.role !== "admin" && !data.dbUser?.isStaff) {
        window.location.href = "/dashboard";
        return;
      }

      const accRes = await fetch(`/api/accidents?status=${filter}`);
      setAccidents(await accRes.json());
      setLoading(false);
    };
    init();
  }, [filter]);

  const handleVerify = async (id: number) => {
    setActionId(id);
    await fetch(`/api/accidents/${id}/verify`, { method: "POST", body: JSON.stringify({ status: "verified" }) });
    setAccidents((prev) => prev.filter((a) => a.id !== id));
    setActionId(null);
  };

  const handleReject = async (id: number) => {
    const reason = prompt("Rejection reason:");
    if (!reason) return;
    setActionId(id);
    await fetch(`/api/accidents/${id}/verify`, { method: "POST", body: JSON.stringify({ status: "rejected", reason }) });
    setAccidents((prev) => prev.filter((a) => a.id !== id));
    setActionId(null);
  };

  const sevColors: Record<string, string> = { fatal: "#DC2626", critical: "#FBBF24", serious: "#3B82F6", minor: "#22C55E" };
  const statusColors: Record<string, string> = { pending: "#FBBF24", verified: "#22C55E", rejected: "#DC2626" };

  if (loading) return <div style={{ padding: 48, textAlign: "center", color: "#94A3B8" }}>Loading...</div>;

  return (
    <div style={{ minHeight: "100vh", background: "#F8FAFC" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 24px", background: "#3B82F6", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 19 }}>
          <img src="/accident-protection.png" alt="" style={{ width: 28, height: 28, objectFit: "contain", filter: "brightness(10)" }} />
          Editor Queue
        </div>
        <nav style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <Link href="/dashboard" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Dashboard</Link>
          <Link href="/authority" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Authority</Link>
          <span style={{ color: "#93C5FD", fontSize: 13 }}>{user?.email}</span>
        </nav>
      </header>

      <main style={{ maxWidth: 1000, margin: "0 auto", padding: "32px 24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h2 style={{ margin: 0, fontSize: 24 }}>Verification Queue</h2>
          <div style={{ display: "flex", gap: 8 }}>
            {["pending", "verified", "rejected"].map((s) => (
              <button key={s} onClick={() => setFilter(s)} style={{ background: filter === s ? "#3B82F6" : "#fff", color: filter === s ? "#fff" : "#475569", border: "1px solid #E2E8F0", padding: "8px 20px", borderRadius: 45, fontSize: 13, fontWeight: 600, cursor: "pointer", textTransform: "capitalize" }}>
                {s}
              </button>
            ))}
          </div>
        </div>

        {accidents.length === 0 && (
          <div style={{ textAlign: "center", padding: 64, color: "#94A3B8" }}>
            <p style={{ fontSize: 18 }}>No {filter} accidents</p>
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {accidents.map((a) => (
            <div key={a.id} style={{ background: "#fff", borderRadius: 16, padding: 20, border: "1px solid #E2E8F0", display: "flex", gap: 16 }}>
              {a.photoUrl && (
                <img src={a.photoUrl} alt="" style={{ width: 120, height: 90, objectFit: "cover", borderRadius: 8, flexShrink: 0 }} />
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                  <span style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: sevColors[a.severity] }} />
                  <strong style={{ fontSize: 15, textTransform: "capitalize" }}>{a.severity}</strong>
                  <span style={{ fontSize: 12, color: "#94A3B8" }}>#{a.id}</span>
                  <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 999, background: `${statusColors[a.verificationStatus]}20`, color: statusColors[a.verificationStatus], fontWeight: 600, textTransform: "capitalize" }}>{a.verificationStatus}</span>
                </div>
                <div style={{ fontSize: 13, color: "#475569", marginBottom: 2 }}>{a.junctionName}{a.district ? `, ${a.district}` : ""}</div>
                <div style={{ fontSize: 12, color: "#94A3B8", marginBottom: 6 }}>{new Date(a.occurredAt).toLocaleDateString()} · {a.vehicleTypes?.join(", ")} · {a.casualties} casualties</div>
                {a.description && <div style={{ fontSize: 13, color: "#64748B", marginBottom: 8, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>{a.description}</div>}
                {a.verificationStatus === "pending" && (
                  <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                    <button onClick={() => handleVerify(a.id)} disabled={actionId === a.id} style={{ background: "#22C55E", color: "#fff", border: "none", padding: "8px 20px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                      {actionId === a.id ? "..." : "Verify"}
                    </button>
                    <button onClick={() => handleReject(a.id)} disabled={actionId === a.id} style={{ background: "#FEE2E2", color: "#DC2626", border: "1px solid #FECACA", padding: "8px 20px", borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
