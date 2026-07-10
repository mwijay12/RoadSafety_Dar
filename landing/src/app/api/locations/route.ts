import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const district = searchParams.get("district");
  const ward = searchParams.get("ward");
  const query = searchParams.get("q");

  // Districts
  if (!district && !ward && !query) {
    const districts = await prisma.location.groupBy({
      by: ["district", "districtCode"],
      where: { region: "DAR-ES-SALAAM" },
    });
    return NextResponse.json(
      districts.map((d) => ({ name: d.district, code: d.districtCode }))
    );
  }

  // Wards for district
  if (district && !ward) {
    const wards = await prisma.location.groupBy({
      by: ["ward", "wardCode"],
      where: { district, region: "DAR-ES-SALAAM" },
    });
    return NextResponse.json(
      wards.map((w) => ({ name: w.ward, code: w.wardCode }))
    );
  }

  // Streets for ward
  if (district && ward) {
    const streets = await prisma.location.findMany({
      where: { district, ward, region: "DAR-ES-SALAAM" },
      select: { id: true, street: true, places: true },
      orderBy: { street: "asc" },
    });
    return NextResponse.json(streets.filter((s) => s.street));
  }

  // Search
  if (query) {
    const results = await prisma.location.findMany({
      where: {
        region: "DAR-ES-SALAAM",
        OR: [
          { street: { contains: query } },
          { places: { contains: query } },
          { ward: { contains: query } },
          { district: { contains: query } },
        ],
      },
      take: 20,
    });
    return NextResponse.json(results);
  }

  return NextResponse.json({ error: "bad request" }, { status: 400 });
}
