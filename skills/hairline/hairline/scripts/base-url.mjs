/**
 * Where this build thinks it lives.
 *
 * Two things need an absolute URL in their output and may not have one in
 * their source: the shadcn registry item, which `shadcn add` fetches by URL,
 * and the Open Graph tags, which crawlers do not resolve relatively. Both ask
 * here, so localhost, a preview and production differ only by environment.
 *
 * The ladder goes from the most specific answer to the least. An explicit
 * override wins; production names itself; anything else on Vercel is a preview
 * and names itself too, which is what makes a preview testable: its registry
 * item installs from that preview.
 */

export const FALLBACK = "http://localhost:3000";

export function resolveBase() {
  const explicit = process.env.HAIRLINE_REGISTRY_URL?.trim();
  if (explicit) return { url: explicit, source: "HAIRLINE_REGISTRY_URL" };

  const productionHost = process.env.VERCEL_PROJECT_PRODUCTION_URL?.trim();
  if (process.env.VERCEL_ENV === "production" && productionHost) {
    return { url: `https://${productionHost}`, source: "VERCEL_PROJECT_PRODUCTION_URL" };
  }

  const deploymentHost = process.env.VERCEL_URL?.trim();
  if (deploymentHost) return { url: `https://${deploymentHost}`, source: "VERCEL_URL" };

  return { url: FALLBACK, source: "fallback" };
}

/** The same answer without trailing slashes, ready to have a path added. */
export function resolveBaseUrl() {
  return resolveBase().url.replace(/\/+$/, "");
}
