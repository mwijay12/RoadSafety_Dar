import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Road Safety Dar es Salaam — Real-time Accident Intelligence",
  description: "Crowdsourced accident hotspot intelligence for Tanzania's commercial capital.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" defer />
        <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js" defer />
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js" defer />
      </head>
      <body>{children}</body>
    </html>
  );
}
