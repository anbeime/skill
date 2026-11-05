// @vitest-environment jsdom
import { StrictMode, createRef } from "react";
import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { frames, observers, pending } from "./dom";
import { Basket, Branches, Cabinet, Dish, Drawer, Elevator, Exploded, Format, Hub, Keyboard, Laptop, Lockers, Loupe, Padlock, Patch, Phone, Phosphor, Plot, Plug, Query, Rail, Rebuild, Relay, Riffle, Router, Settle, Sieve, Slow, Stack, Terminal, Terrain, Turntable, Vault } from "../src/react";

afterEach(cleanup);

const key = (el: Element, k: string) => el.dispatchEvent(new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true }));
/** The rendered div, sized as dom.ts's host() is, so a client point is a viewBox point. */
const sized = (el: Element) => {
  el.getBoundingClientRect = () => ({ left: 0, top: 0, width: 400, height: 320, right: 400, bottom: 320, x: 0, y: 0, toJSON() {} });
  return el;
};
const svg = (el: Element) => el.querySelector("svg")!.innerHTML.replace(/hl-fd\d+/g, "hl-fd");

describe("components", () => {
  it("play walks the figure, and taking it away brings the read-out back to rest", () => {
    const reads: string[] = [];
    const { container, rerender } = render(<Terrain play onRead={(t) => reads.push(t)} />);
    sized(container.firstElementChild as HTMLElement);
    let n = 0;
    while (reads.at(-1) === "rest" && n++ < 800) frames();
    expect(reads.at(-1)).not.toBe("rest");
    rerender(<Terrain onRead={(t) => reads.push(t)} />);
    frames(60);
    expect(reads.at(-1)).toBe("rest");
  });

  it("renders each figure into one div", () => {
    const { container } = render(<><Riffle /><Terrain /><Exploded /><Phosphor /><Slow /><Turntable /><Keyboard /><Elevator /><Phone /><Laptop /><Terminal /><Cabinet /><Branches /><Vault /><Lockers /><Padlock /><Patch /><Dish /><Router /><Loupe /><Sieve /><Rail /><Plug /><Query /><Drawer /><Basket /><Plot /><Hub /><Relay /><Settle /><Format /><Rebuild /><Stack /></>);
    const ids = [...container.children].map((el) => el.getAttribute("data-hairline"));
    expect(ids).toEqual(["riffle", "terrain", "exploded", "phosphor", "slow", "turntable", "keyboard", "elevator", "phone", "laptop", "terminal", "cabinet", "branches", "vault", "lockers", "padlock", "patch", "dish", "router", "loupe", "sieve", "rail", "plug", "query", "drawer", "basket", "plot", "hub", "relay", "settle", "format", "rebuild", "stack"]);
    for (const el of container.children) expect(el.querySelectorAll(":scope > svg")).toHaveLength(1);
  });

  it("passes div attributes through, forwards the ref, and keeps the options off the DOM", () => {
    const ref = createRef<HTMLDivElement>();
    const { container } = render(<Riffle ref={ref} id="cards" className="w-80" data-x="1" style={{ width: 320 }} intensity={0.8} theme="dark" label="Cards" onRead={() => {}} />);
    const el = container.firstElementChild as HTMLDivElement;
    expect(ref.current).toBe(el);
    expect(el.id).toBe("cards");
    expect(el.className).toBe("w-80");
    expect(el.getAttribute("data-x")).toBe("1");
    expect(el.style.width).toBe("320px");
    expect(el.style.aspectRatio).toBe("5 / 4");
    for (const name of ["intensity", "theme", "label", "onread"]) expect(el.hasAttribute(name)).toBe(false);
    expect(el.getAttribute("data-hairline-theme")).toBe("dark");
    expect(el.getAttribute("aria-label")).toBe("Cards");
  });

  it("lets the style prop override the aspect ratio", () => {
    const { container } = render(<Terrain style={{ aspectRatio: "1 / 1" }} />);
    expect((container.firstElementChild as HTMLElement).style.aspectRatio).toBe("1 / 1");
  });

  it("uses the label prop, and aria-label when the caller sets that instead", () => {
    const { container, rerender } = render(<Terrain label="Dunes" />);
    const el = container.firstElementChild!;
    expect(el.getAttribute("aria-label")).toBe("Dunes");
    rerender(<Terrain aria-label="Hills" />);
    expect(el.getAttribute("aria-label")).toBe("Hills");
  });

  it("updates the running figure when a prop changes, without remounting", () => {
    const { container, rerender } = render(<Riffle theme="dark" />);
    const el = container.firstElementChild!, drawing = el.querySelector("svg");
    rerender(<Riffle theme="light" />);
    expect(el.getAttribute("data-hairline-theme")).toBe("light");
    rerender(<Riffle />);
    expect(el.hasAttribute("data-hairline-theme")).toBe(false);
    expect(el.querySelector("svg")).toBe(drawing);
  });

  // Review Focus 2: a prop that is removed goes back to its default
  it("puts intensity back to 0.5 when the prop is removed", () => {
    const { container, rerender } = render(<><Terrain intensity={1} /><Terrain /><Terrain intensity={1} /></>);
    const [gone, standard, strong] = [...container.children].map(sized);
    rerender(<><Terrain /><Terrain /><Terrain intensity={1} /></>);
    for (const el of [gone, standard, strong]) el.dispatchEvent(new MouseEvent("pointermove", { clientX: 200, clientY: 160, bubbles: true }));
    frames(20);
    expect(svg(gone)).toBe(svg(standard));
    expect(svg(gone)).not.toBe(svg(strong));
  });

  // Review Focus 4: a function written inline is new on every render
  it("does not remount, and does not loop, on an inline onRead", () => {
    const seen: string[] = [];
    let renders = 0;
    function App({ n }: { n: number }) {
      renders++;
      return <Riffle data-n={n} onRead={(t) => seen.push(`${n}:${t}`)} />;
    }
    const { container, rerender } = render(<App n={1} />);
    const el = container.firstElementChild!, drawing = el.querySelector("svg");
    rerender(<App n={2} />);
    rerender(<App n={3} />);
    expect(renders).toBe(3);
    expect(el.querySelector("svg")).toBe(drawing);
    key(el, "ArrowLeft");
    // one call at mount, and the latest function is the one called afterwards
    expect(seen).toEqual(["1:rest", "3:01"]);
  });

  it("calls a state setter from onRead without looping", () => {
    const onRead = vi.fn();
    const { container } = render(<Slow onRead={onRead} />);
    expect(onRead.mock.calls).toEqual([["rate 1.00×"]]);
    expect(container.firstElementChild!.querySelectorAll("svg")).toHaveLength(1);
  });

  it("survives StrictMode's double mount with one drawing", () => {
    const onRead = vi.fn();
    const { container } = render(<StrictMode><Riffle onRead={onRead} /></StrictMode>);
    const el = container.firstElementChild!;
    expect(el.querySelectorAll(":scope > svg")).toHaveLength(1);
    expect(el.querySelectorAll("[data-hairline-live]")).toHaveLength(1);
    expect(observers.size).toBe(1);
    key(el, "ArrowLeft");
    expect(onRead).toHaveBeenLastCalledWith("01");
  });

  it("cleans up on unmount", () => {
    const { container, unmount } = render(<><Slow /><Phosphor /></>);
    expect(container.querySelectorAll("svg")).toHaveLength(2);
    unmount();
    expect(pending()).toBe(0);
    expect(observers.size).toBe(0);
  });

  it("names the components for the dev tools", () => {
    expect([Riffle, Terrain, Exploded, Phosphor, Slow, Turntable, Keyboard, Elevator, Phone, Laptop, Terminal, Cabinet, Branches, Vault, Lockers, Padlock, Patch, Dish, Router, Loupe, Sieve, Rail, Plug, Query, Drawer, Basket, Plot, Hub, Relay, Settle, Format, Rebuild, Stack].map((c) => c.displayName))
      .toEqual(["Riffle", "Terrain", "Exploded", "Phosphor", "Slow", "Turntable", "Keyboard", "Elevator", "Phone", "Laptop", "Terminal", "Cabinet", "Branches", "Vault", "Lockers", "Padlock", "Patch", "Dish", "Router", "Loupe", "Sieve", "Rail", "Plug", "Query", "Drawer", "Basket", "Plot", "Hub", "Relay", "Settle", "Format", "Rebuild", "Stack"]);
  });
});
