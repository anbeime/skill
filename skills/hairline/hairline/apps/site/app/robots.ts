import type { MetadataRoute } from "next";

const SITE = process.env.NEXT_PUBLIC_SITE_URL!;

/** Every crawler may read every page. /og stays open too: its own tag keeps it out of an index, and a crawler has to read the page to see it. */
export default function robots(): MetadataRoute.Robots {
  return { rules: { userAgent: "*", allow: "/" }, sitemap: `${SITE}/sitemap.xml` };
}
