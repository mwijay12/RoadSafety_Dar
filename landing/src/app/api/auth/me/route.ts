import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase-server";
import { prisma } from "@/lib/prisma";

export async function GET() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) return NextResponse.json({ user: null });

  let profile = null;
  let dbUser = null;

  if (user.id) {
    profile = await prisma.userProfile.findUnique({
      where: { supabaseUid: user.id },
      include: { user: true },
    });

    if (profile) dbUser = profile.user;

    // Fallback: match by email for existing Django users
    if (!dbUser && user.email) {
      dbUser = await prisma.user.findUnique({ where: { email: user.email } });
      if (dbUser) {
        // Link the Supabase UID to the existing Django user profile
        await prisma.userProfile.upsert({
          where: { userId: dbUser.id },
          update: { supabaseUid: user.id },
          create: { userId: dbUser.id, role: dbUser.isSuperuser ? "admin" : "community", supabaseUid: user.id },
        });
      }
    }
  }

  return NextResponse.json({
    supabaseUser: {
      id: user.id,
      email: user.email,
      name: user.user_metadata?.full_name || user.email,
      avatar: user.user_metadata?.avatar_url || null,
    },
    role: profile?.role || "community",
    dbUser: dbUser
      ? { id: dbUser.id, username: dbUser.username, email: dbUser.email, isStaff: dbUser.isStaff, isSuperuser: dbUser.isSuperuser }
      : null,
  });
}
