import { PrismaClient } from "@prisma/client";
import * as fs from "fs";

const prisma = new PrismaClient();

async function main() {
  console.log("Seeding database...");

  const existing = await prisma.location.count();
  if (existing > 0) {
    console.log(`Database already has ${existing} locations.`);
  } else {
    const csvPath =
      "C:\\Users\\MWIJAY TECH\\Desktop\\PROJECTS\\tanzania-locations-db-main\\location-files\\dar-es-salaam.csv";

    if (!fs.existsSync(csvPath)) {
      console.error("CSV not found at", csvPath);
      return;
    }

    const content = fs.readFileSync(csvPath, "utf-8");
    const lines = content.trim().split("\n");
    const data: any[] = [];

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;
      const parts = parseCSVLine(line);
      if (parts.length >= 6) {
        data.push({
          region: parts[0].trim(),
          regionCode: parseInt(parts[1].trim(), 10),
          district: parts[2].trim(),
          districtCode: parseInt(parts[3].trim(), 10),
          ward: parts[4].trim(),
          wardCode: parseInt(parts[5].trim(), 10),
          street: (parts[6] || "").trim(),
          places: (parts[7] || "").trim(),
        });
      }
    }

    for (let i = 0; i < data.length; i += 100) {
      await prisma.location.createMany({ data: data.slice(i, i + 100) });
    }
    console.log(`Imported ${data.length} locations`);
  }

  // Seed demo data
  const accidentCount = await prisma.accident.count();
  if (accidentCount === 0) {
    const districts = ["Ilala", "Kinondoni", "Temeke", "Ubungo", "Kigamboni"];
    const severities = ["minor", "serious", "fatal", "critical"];
    const vehicles = ["motorcycle", "car", "bus", "truck", "pedestrian"];

    // Real Dar es Salaam hotspot coordinates (known accident-prone areas)
    const hotspots = [
      { name: "Kariakoo Market", district: "Ilala", lat: -6.816, lng: 39.273 },
      { name: "Mchikichini", district: "Ilala", lat: -6.822, lng: 39.269 },
      { name: "Gerezani", district: "Ilala", lat: -6.810, lng: 39.280 },
      { name: "Mnazi Mmoja", district: "Ilala", lat: -6.800, lng: 39.272 },
      { name: "Kivukoni Front", district: "Ilala", lat: -6.793, lng: 39.289 },
      { name: "Mbagala Circle", district: "Temeke", lat: -6.900, lng: 39.267 },
      { name: "Temeke Market", district: "Temeke", lat: -6.877, lng: 39.285 },
      { name: "Keko", district: "Temeke", lat: -6.860, lng: 39.270 },
      { name: "Mtoni", district: "Temeke", lat: -6.912, lng: 39.290 },
      { name: "Kurasini", district: "Temeke", lat: -6.830, lng: 39.290 },
      { name: "Mwenge", district: "Kinondoni", lat: -6.772, lng: 39.230 },
      { name: "Mikocheni", district: "Kinondoni", lat: -6.765, lng: 39.240 },
      { name: "Kawe", district: "Kinondoni", lat: -6.742, lng: 39.225 },
      { name: "Kunduchi", district: "Kinondoni", lat: -6.680, lng: 39.220 },
      { name: "Tegeta", district: "Kinondoni", lat: -6.650, lng: 39.188 },
      { name: "Ubungo", district: "Ubungo", lat: -6.783, lng: 39.167 },
      { name: "Manzese", district: "Ubungo", lat: -6.790, lng: 39.180 },
      { name: "Kimara", district: "Ubungo", lat: -6.798, lng: 39.150 },
      { name: "Mabibo", district: "Ubungo", lat: -6.788, lng: 39.175 },
      { name: "Kigamboni Ferry", district: "Kigamboni", lat: -6.820, lng: 39.295 },
      { name: "Kigamboni Mwisho", district: "Kigamboni", lat: -6.850, lng: 39.317 },
      { name: "Mbezi Louis", district: "Kinondoni", lat: -6.712, lng: 39.210 },
      { name: "Tabata", district: "Ilala", lat: -6.810, lng: 39.220 },
      { name: "Buguruni", district: "Ilala", lat: -6.840, lng: 39.235 },
      { name: "Vingunguti", district: "Ilala", lat: -6.815, lng: 39.215 },
    ];

    const demoAccidents: any[] = [];
    for (let i = 0; i < 200; i++) {
      const spot = hotspots[Math.floor(Math.random() * hotspots.length)];
      const sev = severities[Math.floor(Math.random() * severities.length)];
      // Add slight jitter so points aren't stacked exactly
      const jitterLat = (Math.random() - 0.5) * 0.006;
      const jitterLng = (Math.random() - 0.5) * 0.006;
      demoAccidents.push({
        lat: parseFloat((spot.lat + jitterLat).toFixed(6)),
        lng: parseFloat((spot.lng + jitterLng).toFixed(6)),
        district: spot.district,
        ward: spot.name,
        junctionName: spot.name,
        occurredAt: new Date(Date.now() - Math.random() * 90 * 86400000),
        severity: sev,
        vehicleTypes: JSON.stringify([vehicles[Math.floor(Math.random() * vehicles.length)]]),
        casualties: Math.floor(Math.random() * 5) + 1,
        fatalities: sev === "fatal" ? Math.floor(Math.random() * 3) + 1 : 0,
        injuries: Math.floor(Math.random() * 5),
        description: `Accident reported at ${spot.name}`,
        isDemo: true,
      });
    }
    await prisma.accident.createMany({ data: demoAccidents });
    console.log(`Seeded ${demoAccidents.length} demo accidents`);
  }

  // Ensure site settings
  await prisma.siteSettings.upsert({
    where: { id: 1 },
    update: {},
    create: { id: 1, showDemoData: true },
  });
  console.log("Site settings seeded");
}

function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') inQuotes = !inQuotes;
    else if (char === "," && !inQuotes) {
      result.push(current);
      current = "";
    } else current += char;
  }
  result.push(current);
  return result;
}

main()
  .catch(console.error)
  .finally(() => prisma.$disconnect());
