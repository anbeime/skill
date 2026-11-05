import type { MetadataRoute } from "next";
import { PAGES } from "@/lib/share";

const SITE = process.env.NEXT_PUBLIC_SITE_URL!;

/** The pages a reader can land on, each at its canonical address. No dates: a build is not a change to a page. */
export default function sitemap(): MetadataRoute.Sitemap {
  return PAGES.map((path) => ({ url: path === "/" ? SITE : SITE + path }));
}
