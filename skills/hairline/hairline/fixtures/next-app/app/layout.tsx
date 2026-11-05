import type { ReactNode } from "react";

export const metadata = { title: "hairline fixture", icons: { icon: "data:," } };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
