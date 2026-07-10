import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const status = searchParams.get("status");

  const where: any = {};
  if (status && ["pending", "verified", "rejected"].includes(status)) {
    where.verificationStatus = status;
  }

  const accidents = await prisma.accident.findMany({
    where,
    orderBy: { occurredAt: "desc" },
    select: {
      id: true,
      lat: true,
      lng: true,
      severity: true,
      vehicleTypes: true,
      district: true,
      junctionName: true,
      occurredAt: true,
      casualties: true,
      fatalities: true,
      verified: true,
      trustLevel: true,
      upvoteCount: true,
      verificationStatus: true,
      photoUrl: true,
      description: true,
    },
  });

  const weight: Record<string, number> = {
    minor: 1,
    serious: 2,
    critical: 3,
    fatal: 4,
  };

  const data = accidents.map((a) => ({
    ...a,
    vehicleTypes: JSON.parse(a.vehicleTypes as string),
    intensity: weight[a.severity] || 1,
    occurredAt: a.occurredAt.toISOString(),
  }));

  return NextResponse.json(data);
}
