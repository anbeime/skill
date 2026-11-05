import { basket, branches, cabinet, dish, drawer, elevator, exploded, format, hub, keyboard, laptop, lockers, loupe, padlock, patch, phone, phosphor, plot, plug, query, rail, rebuild, relay, riffle, router, settle, sieve, slow, stack, terminal, terrain, turntable, vault, type Figure } from "@lucasmarkes/hairline";

/** No framework: thirty-three elements, thirty-three calls. */
const el = (id: string) => document.getElementById(id)!;
const read = el("read");

const cards: Figure = riffle(el("riffle"), {
  intensity: 1,
  onRead: (text) => { read.textContent = text; },
});
terrain(el("terrain"), { intensity: 0.75 });
exploded(el("exploded"));
phosphor(el("phosphor"), { theme: "dark" });
slow(el("slow"));
turntable(el("turntable"));
keyboard(el("keyboard"));
elevator(el("elevator"));
phone(el("phone"));
laptop(el("laptop"));
terminal(el("terminal"));
cabinet(el("cabinet"));
branches(el("branches"));
vault(el("vault"));
lockers(el("lockers"));
padlock(el("padlock"));
patch(el("patch"));
dish(el("dish"));
router(el("router"));
loupe(el("loupe"));
sieve(el("sieve"));
rail(el("rail"));
plug(el("plug"));
query(el("query"));
drawer(el("drawer"));
basket(el("basket"));
plot(el("plot"));
hub(el("hub"));
relay(el("relay"));
settle(el("settle"));
format(el("format"));
rebuild(el("rebuild"));
stack(el("stack"));

cards.update({ intensity: 0.8 });
