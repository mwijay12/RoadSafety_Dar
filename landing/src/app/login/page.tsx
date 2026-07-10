"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase-browser";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const supabase = createClient();

  const handleGoogleLogin = async () => {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${location.origin}/auth/callback` },
    });
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const { error: err } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (err) {
      setError(err.message);
    } else {
      window.location.href = "/dashboard";
    }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: "100vh", background: "#F8FAFC" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 24px", background: "#3B82F6", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 19 }}>
          <img src="/accident-protection.png" alt="" style={{ width: 28, height: 28, objectFit: "contain", filter: "brightness(10)" }} />
          Road Safety Dar es Salaam
        </div>
        <nav style={{ display: "flex", gap: 16 }}>
          <Link href="/dashboard" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Dashboard</Link>
        </nav>
      </header>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", paddingTop: 80 }}>
        <div style={{ background: "#fff", padding: 48, borderRadius: 28, maxWidth: 420, width: "100%", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ textAlign: "center", marginBottom: 32 }}>
            <img src="/sign-in.png" alt="Sign in" style={{ width: 80, height: 80, objectFit: "contain", marginBottom: 12 }} />
            <h2 style={{ margin: "0 0 4px" }}>Welcome Back</h2>
            <p style={{ color: "#475569", margin: 0, fontSize: 14 }}>Sign in to Road Safety Dar es Salaam</p>
          </div>

          {error && (
            <div style={{ background: "#FEE2E2", color: "#DC2626", padding: "12px 16px", borderRadius: 8, marginBottom: 16, fontSize: 14 }}>
              {error}
            </div>
          )}

          {/* Google Sign In */}
          <button
            onClick={handleGoogleLogin}
            style={{ width: "100%", background: "#fff", color: "#1E293B", border: "1px solid #E2E8F0", padding: "14px", borderRadius: 45, fontSize: 16, fontWeight: 600, cursor: "pointer", marginBottom: 16, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Continue with Google
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 16 }}>
            <div style={{ flex: 1, height: 1, background: "#E2E8F0" }} />
            <span style={{ fontSize: 13, color: "#94A3B8" }}>or</span>
            <div style={{ flex: 1, height: 1, background: "#E2E8F0" }} />
          </div>

          {/* Email Sign In */}
          <form onSubmit={handleEmailLogin}>
            <label style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 16 }}>
              <span style={{ fontSize: 14, fontWeight: 600 }}>Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="your@email.com"
                style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }}
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 24 }}>
              <span style={{ fontSize: 14, fontWeight: 600 }}>Password</span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }}
              />
            </label>

            <button type="submit" disabled={loading} style={{ width: "100%", background: "#3B82F6", color: "#fff", border: "none", padding: "14px", borderRadius: 45, fontSize: 16, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.6 : 1, marginBottom: 16 }}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <div style={{ textAlign: "center", fontSize: 14, color: "#475569" }}>
            <span>Don&apos;t have an account? </span>
            <button onClick={async () => { setError(""); setLoading(true); const { error: err } = await supabase.auth.signUp({ email, password }); setLoading(false); if (err) setError(err.message); else alert("Check your email for confirmation link!"); }} disabled={loading || !email} style={{ background: "none", border: "none", color: "#3B82F6", fontWeight: 600, cursor: "pointer", fontSize: 14, padding: 0 }}>
              Register
            </button>
          </div>

          <div style={{ marginTop: 24, textAlign: "center" }}>
            <Link href="/dashboard" style={{ color: "#475569", fontSize: 13, textDecoration: "none" }}>
              Continue as Guest
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
