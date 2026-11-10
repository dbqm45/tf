import { auth } from "@/auth";
import { db } from "@/lib/db";

export async function DELETE(req: Request, { params }: { params: { id: string } }) {
  const session = await auth();
  if (!session?.user?.isAdmin) return new Response(null, { status: 403 });
  await db.order.delete({ where: { id: params.id } });
  return new Response(null, { status: 204 });
}
