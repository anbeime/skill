const piece = (id) => `.it[data-piece="${id}"]`;
const engine = { view: "apart", layers: [1], hide: ["stand"] };

export default {
  page: "raptor-engine-light.html",
  out: "raptor-engine",
  layers: ".rp-stage > svg.rp-back, .rp-stage > svg.rp-front",
  rasterSelector: ".rp-stage",
  strip: [".rp-deckglow"],
  views: {
    rest: {},
    apart: { actions: [["key", " "], ["wait", 2500]], reset: [["key", " "], ["wait", 2500]] },
    firing: { actions: [["key", "i"], ["wait", 3500]], raster: { region: [250, 150, 432, 530] }, reset: [["key", "Escape"], ["wait", 2500]] },
  },

  name: "Raptor 2",
  title: "Raptor 2: how a rocket engine works",
  number: "AN-001",
  tagline: "Full-flow staged combustion",
  question: "How does a rocket engine work?",
  lead: "Two very cold liquids, liquid oxygen and methane, are pumped up to 300 bar. A little of each burns in two small preburners whose hot gas spins the pumps. Then both hot gases meet in the main chamber, and the bell nozzle turns that pressure into 230 tonnes of thrust.",
  quote: "Every drop passes through a turbine before it burns",
  numbers: [
    ["230", "tf", "thrust at sea level"],
    ["300", "bar", "main chamber pressure"],
    ["3.6", ": 1", "oxygen to methane, by mass"],
    ["1,630", "kg", "dry mass"],
    ["1.3", "m", "nozzle exit"],
  ],
  spec: [
    ["Cycle", "Full-flow staged combustion"],
    ["Propellants", "LOX / methane"],
    ["Mixture", "3.6 : 1"],
    ["Chamber", "300 bar"],
    ["Thrust", "230 tf, sea level"],
    ["Exit", "1.3 m"],
    ["Dry mass", "1,630 kg"],
  ],
  why: {
    title: "Why full flow?",
    text: "In most engines only part of the propellant drives the turbines. In a full-flow engine every drop passes through one, so each turbine can run cooler for the same power, and the two gases meet already hot, so the main chamber needs no igniter.",
  },

  parts: [
    { id: "gimbal", name: "Gimbal and thrust puck", say: "Carries 230 tf into the stand and lets the engine steer.", select: piece("gimbal") },
    { id: "otp", name: "Oxygen turbopump", say: "Spun by oxygen-rich gas; raises the oxygen to chamber pressure.", select: piece("otp") },
    { id: "orpb", name: "Oxygen-rich preburner", say: "All the oxygen, a little methane: hot gas for the oxygen turbine.", select: piece("orpb") },
    { id: "lox", name: "Oxygen duct and main valve", say: "Carries liquid oxygen from the pump to the preburner.", select: piece("lox") },
    { id: "controller", name: "Engine controller and harness", say: "Opens the valves, reads the sensors, runs the start.", select: piece("controller"), at: [338, 262] },
    { id: "chamber", name: "Injector and main chamber", say: "Both hot gases meet and burn at 300 bar. No igniter of its own.", select: piece("chamber") },
    { id: "hotgas", name: "Hot-gas manifold", say: "Brings the fuel-rich gas round to the injector.", select: piece("hotgas") },
    { id: "ftp", name: "Methane turbopump and fuel-rich preburner", say: "All the methane, a little oxygen: hot gas for the methane turbine.", select: piece("ftp") },
    { id: "downcomer", name: "Downcomer and main fuel valve", say: "Sends methane down to the nozzle's cooling jacket.", select: piece("downcomer"), at: [523, 480] },
    { id: "plumbing", name: "Plumbing", say: "Sense lines into a block, plus feed, purge and igniter lines.", select: piece("plumbing"), at: [390, 302] },
    { id: "nozzle", name: "Nozzle", say: "A 1.3 m bell, cooled by the methane running through its wall.", select: piece("nozzle") },
    { id: "stand", select: piece("stand") },
  ],

  main: { ...engine, crop: [272, 52, 420, 664] },
  inset: { label: "Assembled", view: "rest", crop: [150, 10, 632, 880] },
  steps: [
    { ...engine, title: "Pumps raise the pressure", text: "Liquid oxygen at −183 °C and methane at −162 °C each get their own turbopump: oxygen on the centre line, methane on the side.", focus: ["otp", "ftp"] },
    { ...engine, title: "Methane cools the bell", text: "Before it burns, the methane runs down the downcomer and through the wall of the nozzle, carrying the heat away.", focus: ["downcomer", "nozzle"] },
    { ...engine, title: "Preburners spin the pumps", text: "All of the oxygen burns with a little methane, and all of the methane with a little oxygen. Each hot gas drives one turbine.", focus: ["orpb", "ftp"] },
    { ...engine, title: "Hot gases meet", text: "Oxygen-rich gas from above and fuel-rich gas through the manifold burn together at 300 bar. They arrive hot, so nothing has to light them.", focus: ["chamber", "hotgas"] },
    { view: "firing", title: "Thrust", text: "The bell turns the pressure into speed, past the speed of sound. The load cell above the gimbal reads about 230 tf." },
  ],
  assemblies: [
    { ...engine, title: "The oxygen side", text: "The oxygen turbopump sits on the centre line under the gimbal. All of the oxygen goes through it and then through the oxygen-rich preburner below, whose hot gas spins the pump's turbine.", parts: ["otp", "orpb", "lox"] },
    { ...engine, title: "The methane side", text: "The methane turbopump and its fuel-rich preburner hang beside the engine. The downcomer carries methane down to the nozzle's cooling jacket before it burns.", parts: ["ftp", "downcomer", "hotgas"] },
    { ...engine, title: "Chamber and nozzle", text: "The two hot gases meet at the injector and burn at 300\u00a0bar. The 1.3\u00a0m bell turns that pressure into speed and thrust.", parts: ["chamber", "nozzle"] },
    { ...engine, title: "Mount and controls", text: "The gimbal carries 230\u00a0tf into the stand and lets the engine steer. The controller opens the valves in order and reads the sense lines.", parts: ["gimbal", "controller", "plumbing"] },
  ],
  details: [
    { ...engine, title: "Oxygen turbopump", text: "Raises liquid oxygen to chamber pressure, spun by the oxygen-rich gas from the preburner under it.", around: ["otp"], focus: ["otp"] },
    { ...engine, title: "Methane side", text: "The methane pump and its fuel-rich preburner hang beside the engine; all the methane passes through them.", around: ["ftp"], focus: ["ftp"] },
    { ...engine, title: "Engine controller", text: "Opens the valves in order, reads the sense lines and runs the start.", around: ["controller"], focus: ["controller"] },
  ],
};
