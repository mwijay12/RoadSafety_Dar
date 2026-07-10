import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const accidents = await prisma.accident.findMany({
    select: {
      severity: true,
      vehicleTypes: true,
      occurredAt: true,
      fatalities: true,
      casualties: true,
      verified: true,
    },
  });

  const total = accidents.length;
  const severity: Record<string, number> = {};
  const fatalities = accidents.reduce((s, a) => s + a.fatalities, 0);
  const casualties = accidents.reduce((s, a) => s + a.casualties, 0);
  const verified = accidents.filter((a) => a.verified).length;
  const vehicleCounts: Record<string, number> = {};

  for (const a of accidents) {
    severity[a.severity] = (severity[a.severity] || 0) + 1;
    const vtypes = JSON.parse(a.vehicleTypes as string);
    for (const v of vtypes) {
      vehicleCounts[v] = (vehicleCounts[v] || 0) + 1;
    }
  }

  const monthly: Record<string, number> = {};
  for (const a of accidents) {
    const key = a.occurredAt.toISOString().slice(0, 7);
    monthly[key] = (monthly[key] || 0) + 1;
  }

  const hourly: number[] = Array(24).fill(0);
  for (const a of accidents) {
    hourly[a.occurredAt.getHours()]++;
  }

  const junctionCount = await prisma.junction.count();
  const pending = await prisma.accident.count({ where: { verificationStatus: "pending" } });

  return NextResponse.json({
    total,
    pending,
    fatal: severity.fatal || 0,
    serious: severity.serious || 0,
    minor: severity.minor || 0,
    critical: severity.critical || 0,
    verified,
    totalFatalities: fatalities,
    totalCasualties: casualties,
    junctionCount,
    severity,
    vehicles: vehicleCounts,
    monthly: Object.entries(monthly).map(([month, count]) => ({ month, count })),
    hourly: hourly.map((count, hour) => ({ hour, count })),
  });
}
