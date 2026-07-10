"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface Ward {
  name: string;
  code: number;
}

interface Street {
  id: number;
  street: string;
  places: string;
}

export default function ReportPage() {
  const [districts, setDistricts] = useState<string[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);
  const [streets, setStreets] = useState<Street[]>([]);
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [selectedWard, setSelectedWard] = useState("");
  const [selectedStreet, setSelectedStreet] = useState("");

  const [form, setForm] = useState({
    severity: "minor",
    vehicleType: "car",
    casualties: 0,
    fatalities: 0,
    injuries: 0,
    description: "",
    weather: "",
    roadCondition: "",
    contact: "",
  });

  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  // Photo upload
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string>("");
  const [uploading, setUploading] = useState(false);
  const [photoUrl, setPhotoUrl] = useState("");

  const handlePhotoSelect = (file: File) => {
    const allowed = ["image/jpeg", "image/png", "image/webp", "image/gif"];
    if (!allowed.includes(file.type)) { alert("Only JPEG, PNG, WebP, or GIF photos allowed."); return; }
    if (file.size > 5 * 1024 * 1024) { alert("Photo must be under 5 MB."); return; }
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
  };

  const uploadPhoto = async () => {
    if (!photoFile) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", photoFile);
      fd.append("upload_preset", "darroeadsafety");
      const res = await fetch("https://api.cloudinary.com/v1_1/roougsg4/image/upload", { method: "POST", body: fd });
      const data = await res.json();
      if (data.secure_url) {
        setPhotoUrl(data.secure_url);
        setPhotoPreview(data.secure_url);
      } else {
        alert("Upload failed — try again");
      }
    } catch { alert("Upload error — check your connection"); }
    setUploading(false);
  };

  const removePhoto = () => {
    setPhotoFile(null);
    setPhotoPreview("");
    setPhotoUrl("");
  };

  useEffect(() => {
    fetch("/api/locations")
      .then((r) => r.json())
      .then((data) => setDistricts(data.map((d: any) => d.name)));
  }, []);

  useEffect(() => {
    if (!selectedDistrict) return;
    fetch(`/api/locations?district=${selectedDistrict}`)
      .then((r) => r.json())
      .then((data) => setWards(data));
    setSelectedWard("");
    setStreets([]);
  }, [selectedDistrict]);

  useEffect(() => {
    if (!selectedDistrict || !selectedWard) return;
    fetch(`/api/locations?district=${selectedDistrict}&ward=${selectedWard}`)
      .then((r) => r.json())
      .then((data) => setStreets(data));
    setSelectedStreet("");
  }, [selectedDistrict, selectedWard]);

  const getLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({ ...f, lat: pos.coords.latitude, lng: pos.coords.longitude }));
        alert(`Location captured: ${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`);
      },
      () => alert("Could not get location. Enable GPS on your device.")
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const payload = {
      ...form,
      photoUrl,
      occurredAt: new Date().toISOString(),
      district: selectedDistrict,
      ward: selectedWard,
      locationId: selectedStreet,
    };

    try {
      const res = await fetch("/api/accidents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setSubmitted(true);
      } else {
        alert("Failed to submit report");
      }
    } catch {
      alert("Network error");
    }
    setLoading(false);
  };

  if (submitted) {
    return (
      <div style={{ minHeight: "100vh", background: "#F8FAFC", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ background: "#fff", padding: 48, borderRadius: 28, textAlign: "center", boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
          <h2 style={{ margin: "0 0 8px" }}>Report Submitted</h2>
          <p style={{ color: "#475569", marginBottom: 24 }}>Thank you for helping make Dar es Salaam safer.</p>
          <Link href="/dashboard" style={{ background: "#3B82F6", color: "#fff", padding: "12px 32px", borderRadius: 45, textDecoration: "none", fontWeight: 600, display: "inline-block" }}>
            View Map
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#F8FAFC" }}>
      {/* Topbar */}
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 24px", background: "#3B82F6", color: "#fff" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 19 }}>
          <img src="/accident-protection.png" alt="" style={{ width: 28, height: 28, objectFit: "contain" }} />
          Road Safety Dar es Salaam
        </div>
        <nav style={{ display: "flex", gap: 16 }}>
          <Link href="/dashboard" style={{ color: "#fff", textDecoration: "none", fontWeight: 600, fontSize: 14 }}>Dashboard</Link>
        </nav>
      </header>

      <main style={{ maxWidth: 760, margin: "0 auto", padding: "48px 24px" }}>
          <div style={{ background: "#fff", padding: 48, borderRadius: 28, boxShadow: "0 1px 3px rgba(0,0,0,0.04)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 8 }}>
            <img src="/accident-icon.png" alt="Report" style={{ width: 56, height: 56, objectFit: "contain" }} />
            <div>
              <h2 style={{ margin: 0, fontSize: 32 }}>Report an Accident</h2>
              <p style={{ color: "#475569", margin: "4px 0 0" }}>Fill in the details below. Swahili or English — either is fine.</p>
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Location */}
            <div style={{ marginBottom: 32 }}>
              <h4 style={{ fontSize: 14, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 16 }}>Location</h4>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>District</span>
                  <select value={selectedDistrict} onChange={(e) => setSelectedDistrict(e.target.value)} required style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }}>
                    <option value="">Select district</option>
                    {districts.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Ward</span>
                  <select value={selectedWard} onChange={(e) => setSelectedWard(e.target.value)} disabled={!selectedDistrict} required style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }}>
                    <option value="">Select ward</option>
                    {wards.map((w) => <option key={w.code} value={w.name}>{w.name}</option>)}
                  </select>
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 4, gridColumn: "span 2" }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Street / Location</span>
                  <select value={selectedStreet} onChange={(e) => setSelectedStreet(e.target.value)} disabled={!selectedWard} style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }}>
                    <option value="">Select street</option>
                    {streets.map((s) => <option key={s.id} value={s.street}>{s.street}{s.places ? ` (${s.places})` : ""}</option>)}
                  </select>
                </label>
              </div>
              <button type="button" onClick={getLocation} style={{ marginTop: 12, background: "none", border: "1px solid #E2E8F0", padding: "10px 20px", borderRadius: 8, cursor: "pointer", fontSize: 14 }}>
                📍 Use my current location
              </button>
            </div>

            {/* Severity & Vehicle */}
            <div style={{ marginBottom: 32 }}>
              <h4 style={{ fontSize: 14, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 16 }}>Incident Details</h4>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Severity</span>
                  <select value={form.severity} onChange={(e) => setForm((f) => ({ ...f, severity: e.target.value }))} required style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }}>
                    <option value="minor">Minor (no casualties)</option>
                    <option value="serious">Serious (injury)</option>
                    <option value="fatal">Fatal (1+ deaths)</option>
                    <option value="critical">Critical (multiple casualties)</option>
                  </select>
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Vehicle Type</span>
                  <select value={form.vehicleType} onChange={(e) => setForm((f) => ({ ...f, vehicleType: e.target.value }))} required style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }}>
                    <option value="motorcycle">Motorcycle / Bodaboda</option>
                    <option value="car">Car</option>
                    <option value="bus">Bus / Daladala</option>
                    <option value="truck">Truck / Lorry</option>
                    <option value="bicycle">Bicycle</option>
                    <option value="pedestrian">Pedestrian</option>
                  </select>
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Casualties</span>
                  <input type="number" min="0" value={form.casualties} onChange={(e) => setForm((f) => ({ ...f, casualties: parseInt(e.target.value) || 0 }))} style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }} />
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Fatalities</span>
                  <input type="number" min="0" value={form.fatalities} onChange={(e) => setForm((f) => ({ ...f, fatalities: parseInt(e.target.value) || 0 }))} style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }} />
                </label>
              </div>
            </div>

            {/* Photo Evidence */}
            <div style={{ marginBottom: 32 }}>
              <h4 style={{ fontSize: 14, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 16 }}>Photo Evidence (optional)</h4>
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handlePhotoSelect(f); }}
                onClick={() => document.getElementById("fileInput")?.click()}
                style={{ border: "2px dashed #CBD5E1", borderRadius: 16, padding: 32, textAlign: "center", cursor: "pointer", background: photoPreview ? "#F0FDF4" : "#F8FAFC" }}
              >
                <input
                  type="file"
                  id="fileInput"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  style={{ display: "none" }}
                  onChange={(e) => { const f = e.target.files?.[0]; if (f) handlePhotoSelect(f); }}
                />
                {photoPreview ? (
                  <div>
                    <img src={photoPreview} alt="Preview" style={{ maxHeight: 200, borderRadius: 12, marginBottom: 12, maxWidth: "100%", objectFit: "cover" }} />
                    <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
                      {!photoUrl && (
                        <button type="button" onClick={(e) => { e.stopPropagation(); uploadPhoto(); }} disabled={uploading} style={{ background: "#3B82F6", color: "#fff", border: "none", padding: "8px 20px", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: uploading ? "not-allowed" : "pointer" }}>
                          {uploading ? "Uploading..." : "Upload Photo"}
                        </button>
                      )}
                      {photoUrl && <span style={{ color: "#22C55E", fontSize: 14, fontWeight: 600, padding: "8px 0" }}>✅ Photo uploaded</span>}
                      <button type="button" onClick={(e) => { e.stopPropagation(); removePhoto(); }} style={{ background: "none", border: "1px solid #E2E8F0", padding: "8px 16px", borderRadius: 8, fontSize: 14, cursor: "pointer" }}>
                        Remove
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: 32, marginBottom: 8 }}>📸</div>
                    <p style={{ margin: 0, fontSize: 14, color: "#475569" }}>Drag & drop a photo here, or click to browse</p>
                    <p style={{ margin: "4px 0 0", fontSize: 12, color: "#94A3B8" }}>JPEG, PNG, WebP, GIF — max 5 MB</p>
                  </div>
                )}
              </div>
            </div>

            {/* Description */}
            <div style={{ marginBottom: 32 }}>
              <h4 style={{ fontSize: 14, fontWeight: 600, color: "#475569", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: 16 }}>Description</h4>
              <textarea
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="What happened? (English or Swahili)"
                rows={3}
                style={{ width: "100%", padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 80, resize: "vertical", fontFamily: "inherit" }}
              />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Weather</span>
                  <input value={form.weather} onChange={(e) => setForm((f) => ({ ...f, weather: e.target.value }))} placeholder="clear / rainy / drizzle" style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }} />
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span style={{ fontSize: 14, fontWeight: 600 }}>Road Condition</span>
                  <input value={form.roadCondition} onChange={(e) => setForm((f) => ({ ...f, roadCondition: e.target.value }))} placeholder="good / wet / potholed" style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }} />
                </label>
              </div>
              <label style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 16 }}>
                <span style={{ fontSize: 14, fontWeight: 600 }}>Contact (optional)</span>
                <input value={form.contact} onChange={(e) => setForm((f) => ({ ...f, contact: e.target.value }))} placeholder="phone or email for follow-up" style={{ padding: "12px 16px", border: "1px solid #E2E8F0", borderRadius: 8, fontSize: 16, minHeight: 48 }} />
              </label>
            </div>

            <button type="submit" disabled={loading} style={{ width: "100%", background: "#3B82F6", color: "#fff", border: "none", padding: "16px", borderRadius: 45, fontSize: 16, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.6 : 1 }}>
              {loading ? "Submitting..." : "Submit Report"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
