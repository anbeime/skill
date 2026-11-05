"use client";

import { useEffect, useRef } from "react";
import { phosphor } from "@lucasmarkes/hairline";

export function Vanilla() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const figure = phosphor(ref.current!, { intensity: 0.8 });
    return () => figure.destroy();
  }, []);
  return <div id="phosphor" ref={ref} />;
}
