import type { CSSProperties } from "react";
import { Riffle, Terrain } from "@/components/ui/hairline";

/** shadcn's tokens, as a dark theme would define them. */
const tokens = { "--background": "#101014", "--foreground": "#fafafa", "--muted-foreground": "#a1a1aa", "--border": "#27272a" } as CSSProperties;

/**
 * The shadcn registry item, as `shadcn add` would leave it:
 * scripts/consumers.mjs writes components/ui/hairline.tsx from the built item
 * before it builds this app.
 */
export default function Page() {
  return (
    <main style={{ width: 400, margin: "40px auto", background: "var(--background)", ...tokens }}>
      <Terrain id="themed" />
      <Riffle intensity={0.8} />
    </main>
  );
}
