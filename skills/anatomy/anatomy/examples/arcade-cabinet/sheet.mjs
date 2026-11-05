const named = (...prefixes) => prefixes.map((prefix) => `[data-name^="${prefix}"]`).join(", ");
const has = (part) => `document.querySelector('[data-part="${part}"]').innerHTML.length > 0`;
const readout = (text) => `document.querySelector('[data-readout]').textContent.includes(${JSON.stringify(text)})`;

export default {
  page: "arcade-cabinet-light.html",
  out: "arcade-cabinet",
  reduced: false,
  views: {
    off: { actions: [["key", "Escape"], ["wait", 600]] },
    rolling: { actions: [["key", "c"], ["wait", 1450], ["slow", 0.03], ["until", has("coin-chute"), 30000]] },
    falling: { actions: [["until", has("coin-fall"), 30000], ["wait", 120]] },
    test: { actions: [["slow", 1], ["until", readout("RAM OK"), 15000]] },
    attract: { actions: [["wait", 6500]] },
  },

  name: "Arcade cabinet",
  title: "Arcade cabinet: how a coin starts the game",
  number: "AN-002",
  tagline: "Upright, 1981 style",
  question: "What happens when you drop in a coin?",
  lead: "The quarter rolls through a mech that checks it, then falls past a thin switch wire into the cash box. That one pulse counts the coin, latches the power on, warms the picture tube, tests the game board and starts the attract mode.",
  quote: "One wire, one pulse, one credit",
  numbers: [
    ["178", "cm", "cabinet height"],
    ["24.26", "mm", "a US quarter"],
    ["27", "cm", "drop into the cash box"],
    ["224 × 288", "px", "picture, on its side"],
    ["15.734", "kHz", "line rate"],
  ],
  spec: [
    ["Style", "Upright, 1981"],
    ["Height", "178 cm"],
    ["Coin", "US quarter, 24.26 mm"],
    ["Drop", "27 cm into the cash box"],
    ["Picture", "224 × 288, on its side"],
    ["Line rate", "15.734 kHz"],
    ["Warm-up", "About 2 s"],
  ],
  why: {
    title: "Why is the screen on its side?",
    text: "The game is taller than it is wide, so the monitor lies on its side. Its scan lines run up and down the glass instead of across, and when the power goes the picture collapses to a vertical line.",
  },

  parts: [
    { id: "door", name: "Coin door and slot", say: "The quarter goes in here; a reject comes back out of the return.", select: named("door") },
    { id: "mech", name: "Coin mech", say: "Checks the coin's size and metal before it lets it through.", select: named("mech") },
    { id: "switch", name: "Coin switch", say: "A thin wire the falling coin brushes past: one pulse per coin.", select: named("coin.switch") },
    { id: "chute", name: "Coin chute", say: "A 30° slope the coin rolls down before it drops.", select: named("chute") },
    { id: "cash", name: "Cash box", say: "An open box the coin lands in, 27 cm below the chute.", select: named("cash") },
    { id: "meter", name: "Coin meter", say: "Counts every coin, pulsed by the switch.", select: named("meter", "wire.meter") },
    { id: "power", name: "Power relay, transformer and supply", say: "The first coin latches the relay and wakes the whole cabinet.", select: named("relay", "xfmr", "psu", "fuse", "pw.", "cable.power") },
    { id: "pcb", name: "Game board", say: "CPU, RAM and ROMs: tests itself, then runs the game.", select: named("pcb") },
    { id: "harness", name: "Harness and edge connector", say: "Carries the coin line, the controls and the video to the board.", select: named("loom", "cable.video", "wire.coin") },
    { id: "monitor", name: "Monitor: CRT and chassis", say: "Lies on its side for a vertical game; warms up in about 2 s.", select: named("crt", "chassis", "mon.", "lead.anode", "bezel", "cable.neck") },
    { id: "marquee", name: "Marquee lamp", say: "A fluorescent tube that strikes when the power comes on.", select: named("marquee") },
    { id: "coin", select: '[data-part="coin-fly"], [data-part="coin-chute"], [data-part="coin-fall"], [data-part="pile"]' },
    { id: "panel", name: "Control panel", say: "The stick closes a microswitch underneath; buttons fire and start.", select: named("stick", "button.", "cp.", "wire.stick") },
  ],

  main: { view: "off" },
  steps: [
    { view: "rolling", title: "The mech checks the coin", text: "A 24.26 mm quarter goes in the left slot. The mech checks it and lets it roll on down the chute.", focus: ["coin", "mech", "chute"], hide: ["door"] },
    { view: "rolling", title: "It brushes the switch wire", text: "Rolling down the 30° chute, the coin pushes the thin switch wire aside. That is one pulse: one coin.", focus: ["coin", "switch", "chute"] },
    { view: "falling", title: "It drops into the cash box", text: "The coin leaves the chute and falls 27 cm into the open cash box. The meter counts it.", focus: ["coin", "cash", "chute", "meter"] },
    { view: "test", title: "The relay wakes the cabinet", text: "The same pulse latches the power relay. The marquee strikes, the tube heats, and the board tests its RAM and ROMs.", focus: ["power", "pcb", "harness"] },
    { view: "attract", title: "Attract mode", text: "After about 2 s the picture appears, drawn up and down the glass, and the game shows itself off until someone presses start.", focus: ["monitor", "marquee"] },
  ],
  details: [
    { view: "off", title: "Coin mech", text: "Checks each coin before it reaches the chute.", around: ["mech"], focus: ["mech"], hide: ["door"] },
    { view: "off", title: "Cash box", text: "Open at the top, so you can see the coins land.", around: ["cash"], focus: ["cash"] },
    { view: "off", title: "Game board", text: "The edge connector on the left carries every wire in and out.", around: ["pcb"], focus: ["pcb"] },
  ],
};
