import Database from "better-sqlite3";
import { PrismaClient } from "@prisma/client";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DJANGO_DB = path.resolve(__dirname, "../../db.sqlite3");

async function main() {
  console.log("Opening Django SQLite DB...");
  const django = new Database(DJANGO_DB);
  django.pragma("journal_mode = WAL");

  const prisma = new PrismaClient();

  // ── Clear existing data ──────────────────────────────────
  console.log("Clearing existing Prisma data...");
  await prisma.auditLog.deleteMany();
  await prisma.accidentUpvote.deleteMany();
  await prisma.accident.deleteMany();
  await prisma.junction.deleteMany();
  await prisma.userProfile.deleteMany();
  await prisma.user.deleteMany();
  await prisma.siteSettings.deleteMany();
  await prisma.location.deleteMany();

  // ── 1. Users ────────────────────────────────────────────
  console.log("Migrating users...");
  const djangoUsers = django.prepare("SELECT * FROM auth_user").all() as any[];
  for (const u of djangoUsers) {
    await prisma.user.create({
      data: {
        id: u.id,
        username: u.username,
        email: u.email,
        firstName: u.first_name || "",
        lastName: u.last_name || "",
        password: u.password,
        isActive: u.is_active === 1,
        isStaff: u.is_staff === 1,
        isSuperuser: u.is_superuser === 1,
        lastLogin: u.last_login ? new Date(u.last_login) : null,
        dateJoined: new Date(u.date_joined),
      },
    });
  }
  console.log(`  → ${djangoUsers.length} users`);

  // ── 2. User Profiles ────────────────────────────────────
  console.log("Migrating user profiles...");
  const profiles = django.prepare("SELECT * FROM accidents_userprofile").all() as any[];
  for (const p of profiles) {
    await prisma.userProfile.create({
      data: {
        id: p.id,
        userId: p.user_id,
        role: p.role,
        phone: p.phone || "",
        emailNotifications: p.email_notifications === 1,
        supabaseUid: p.supabase_uid || null,
        avatarUrl: p.avatar_url || null,
        createdAt: new Date(p.created_at),
        updatedAt: new Date(p.updated_at),
      },
    });
  }
  console.log(`  → ${profiles.length} profiles`);

  // ── 3. Junctions ────────────────────────────────────────
  console.log("Migrating junctions...");
  const junctions = django.prepare("SELECT * FROM accidents_junction").all() as any[];
  for (const j of junctions) {
    await prisma.junction.create({
      data: {
        id: j.id,
        name: j.name,
        slug: j.slug || "",
        lat: j.lat,
        lng: j.lng,
        district: j.district || "",
        description: j.description || "",
        isDemo: j.is_demo === 1,
        createdAt: new Date(j.created_at),
      },
    });
  }
  console.log(`  → ${junctions.length} junctions`);

  // ── 4. Accidents ────────────────────────────────────────
  console.log("Migrating accidents...");
  const accidents = django.prepare("SELECT * FROM accidents_accident").all() as any[];
  let migrated = 0;
  for (const a of accidents) {
    await prisma.accident.create({
      data: {
        id: a.id,
        lat: a.lat,
        lng: a.lng,
        h3Cell: a.h3_cell || "",
        district: a.district || "",
        ward: a.ward || "",
        locationId: a.location_id || "",
        junctionName: a.junction_name || "",
        junctionId: a.junction_id || null,
        occurredAt: new Date(a.occurred_at),
        reportedAt: new Date(a.reported_at),
        severity: a.severity,
        vehicleTypes: a.vehicle_types || "[]",
        reporterType: a.reporter_type || "community",
        casualties: a.casualties || 0,
        fatalities: a.fatalities || 0,
        injuries: a.injuries || 0,
        description: a.description || "",
        weather: a.weather || "",
        roadCondition: a.road_condition || "",
        contact: a.contact || "",
        photoUrl: a.photo_url || "",
        sourceNotes: a.source_notes || "",
        verified: a.verified === 1,
        isDemo: a.is_demo === 1,
        submittedById: a.submitted_by_id || null,
        trustLevel: a.trust_level || "anonymous",
        upvoteCount: a.upvote_count || 0,
        verificationStatus: a.verification_status || "pending",
        officialNotes: a.official_notes || null,
        rejectionReason: a.rejection_reason || null,
        verifiedById: a.verified_by_id || null,
        verifiedAt: a.verified_at ? new Date(a.verified_at) : null,
      },
    });
    migrated++;
    if (migrated % 100 === 0) process.stdout.write(`  → ${migrated}/${accidents.length}\r`);
  }
  console.log(`  → ${migrated} accidents`);

  // ── 5. Upvotes ──────────────────────────────────────────
  console.log("Migrating upvotes...");
  const upvotes = django.prepare("SELECT * FROM accidents_accidentupvote").all() as any[];
  for (const v of upvotes) {
    await prisma.accidentUpvote.create({
      data: {
        id: v.id,
        accidentId: v.accident_id,
        userId: v.user_id,
        createdAt: new Date(v.created_at),
      },
    });
  }
  console.log(`  → ${upvotes.length} upvotes`);

  // ── 6. Audit Logs ───────────────────────────────────────
  console.log("Migrating audit logs...");
  const logs = django.prepare("SELECT * FROM accidents_auditlog").all() as any[];
  for (const l of logs) {
    await prisma.auditLog.create({
      data: {
        id: l.id,
        accidentId: l.accident_id || null,
        userId: l.user_id || null,
        action: l.action,
        description: l.description || "",
        createdAt: new Date(l.created_at),
      },
    });
  }
  console.log(`  → ${logs.length} audit logs`);

  // ── 7. Site Settings ────────────────────────────────────
  console.log("Migrating site settings...");
  const settings = django.prepare("SELECT * FROM accidents_sitesettings").all() as any[];
  for (const s of settings) {
    await prisma.siteSettings.create({
      data: {
        id: s.id,
        showDemoData: s.show_demo_data === 1,
      },
    });
  }
  console.log(`  → ${settings.length} site settings`);

  // Re-import Tanzania locations from CSV
  console.log("Re-importing Tanzania locations...");
  const fs = await import("fs");
  const csvPath = "C:\\Users\\MWIJAY TECH\\Desktop\\PROJECTS\\tanzania-locations-db-main\\location-files\\dar-es-salaam.csv";
  if (fs.existsSync(csvPath)) {
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
    console.log(`  → ${data.length} locations`);
  } else {
    console.log("  → CSV not found, skipping locations import");
  }

  django.close();
  await prisma.$disconnect();
  console.log("Migration complete!");
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

main().catch((e) => {
  console.error("Migration failed:", e);
  process.exit(1);
});
