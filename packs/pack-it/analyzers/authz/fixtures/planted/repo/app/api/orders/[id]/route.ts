import { db } from "@/lib/db";

export async function GET(req: Request) {
  return Response.json(await db.order.findMany());
}

export async function DELETE(req: Request, { params }: { params: { id: string } }) {
  await db.order.delete({ where: { id: params.id } });
  return new Response(null, { status: 204 });
}
