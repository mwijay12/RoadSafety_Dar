import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";
import { createClient } from "@/lib/supabase-server";

export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const profile = await prisma.userProfile.findUnique({ where: { supabaseUid: user.id } });
  const dbUser = profile?.supabaseUid === user.id || user.email === "admin@roadsafety.local"
    ? await prisma.user.findFirst({ where: { OR: [{ id: profile?.userId }, { email: user.email }] } })
    : null;

  const isStaff = dbUser?.isStaff || dbUser?.isSuperuser || profile?.role === "editor" || profile?.role === "admin";

  if (!isStaff) return NextResponse.json({ error: "Forbidden" }, { status: 403 });

  const body = await request.json();
  const accidentId = parseInt(id);

  if (body.status === "verified") {
    await prisma.accident.update({
      where: { id: accidentId },
      data: { verificationStatus: "verified", verified: true, verifiedById: dbUser?.id, verifiedAt: new Date() },
    });
    await prisma.auditLog.create({
      data: { accidentId, userId: dbUser?.id, action: "verified", description: "Verified by editor" },
    });
  } else if (body.status === "rejected") {
    await prisma.accident.update({
      where: { id: accidentId },
      data: { verificationStatus: "rejected", verified: false, verifiedById: dbUser?.id, verifiedAt: new Date(), rejectionReason: body.reason || "" },
    });
    await prisma.auditLog.create({
      data: { accidentId, userId: dbUser?.id, action: "rejected", description: body.reason || "Rejected by editor" },
    });
  }

  return NextResponse.json({ success: true });
}
