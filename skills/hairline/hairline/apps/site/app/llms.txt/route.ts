import { llms } from "@/lib/llms";

export const dynamic = "force-static";

export function GET() {
  return new Response(llms(process.env.NEXT_PUBLIC_SITE_URL!), { headers: { "content-type": "text/plain; charset=utf-8" } });
}
