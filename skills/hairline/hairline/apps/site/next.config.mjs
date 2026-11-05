import { resolveBaseUrl } from "../../scripts/base-url.mjs";

/**
 * The site's own address, resolved once at build (see scripts/base-url.mjs):
 * the Open Graph tags, the shadcn command and /llms.txt all need it absolute.
 */
export default {
  env: { NEXT_PUBLIC_SITE_URL: resolveBaseUrl() },
  // the page was /skill while there was one skill; only the page moved, its examples stay under /skill/
  redirects: async () => [{ source: "/skill", destination: "/skills", permanent: true }],
};
