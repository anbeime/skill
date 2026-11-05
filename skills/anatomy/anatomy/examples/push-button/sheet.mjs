const piece = (id) => `[data-piece="${id}"]`;
const press = `document.querySelector(".iso-stage").dispatchEvent(new PointerEvent("pointerdown", { pointerId: 1 }))`;
const release = `document.querySelector(".iso-stage").dispatchEvent(new PointerEvent("pointerup", { pointerId: 1 }))`;

export default {
  page: "push-button-light.html",
  out: "push-button",
  views: {
    off: {},
    on: { actions: [["eval", press], ["wait", 400]], reset: [["eval", release], ["wait", 400]] },
  },

  name: "Push button",
  title: "Push button: how a switch closes a circuit",
  number: "AN-003",
  tagline: "A loop, a gap and a spring",
  question: "How does a button turn a light on?",
  lead: "A battery can only push current round a closed loop. The button is a gap in that loop: a spring holds a copper bridge just above two contact posts. Press the cap and the bridge lands on both posts, the loop closes and the bulb lights. Let go and the spring opens the gap again.",
  quote: "No loop, no current",
  numbers: [
    ["1.5", "V", "from the cell"],
    ["0.30", "A", "round the closed loop"],
    ["0.45", "W", "in the bulb"],
    ["7", "px", "gap the bridge closes"],
  ],
  spec: [
    ["Cell", "1.5 V"],
    ["Current", "0.30 A when closed"],
    ["Power", "0.45 W"],
    ["Travel", "7 px to contact"],
    ["Action", "Momentary, spring return"],
  ],
  why: {
    title: "Why a spring?",
    text: "The spring keeps the button open until you press it, and opens it again the moment you let go. That is a momentary switch, the kind in a doorbell. A light switch adds a latch so it stays where you leave it.",
  },

  parts: [
    { id: "cap", name: "Cap", say: "Where your finger pushes; it carries the plunger.", select: piece("cap") },
    { id: "spring", name: "Return spring", say: "Holds the button open and lifts it when you let go.", select: piece("spring") },
    { id: "bridge", name: "Copper bridge", say: "Rides on the plunger and closes the gap between the posts.", select: piece("bridge") },
    { id: "contacts", name: "Contact posts", say: "Two brass posts, one for each end of the gap.", select: piece("contacts") },
    { id: "frame", name: "Frame and base", say: "An insulating block and a frame that guides the plunger.", select: piece("frame") },
    { id: "cell", name: "1.5 V cell", say: "Pushes current round the loop once it is closed.", select: piece("cell") },
    { id: "bulb", name: "Bulb", say: "Glows when current runs through its thin filament.", select: piece("bulb") },
    { id: "wires", name: "Wires", say: "Carry current from the cell, through the button, to the bulb and back.", select: piece("wires") },
  ],

  main: { view: "on" },
  inset: { label: "Released", view: "off" },
  steps: [
    { view: "off", title: "The loop is open", text: "The spring holds the bridge 7 px above the posts, so there is a gap in the loop and no current flows.", focus: ["spring", "bridge", "contacts"] },
    { view: "on", title: "Press the cap", text: "The cap pushes the plunger down and squeezes the spring.", focus: ["cap", "spring"] },
    { view: "on", title: "The bridge lands", text: "The copper bridge comes down onto both posts and closes the gap.", focus: ["bridge", "contacts"] },
    { view: "on", title: "Current goes round", text: "With the loop closed, 1.5 V pushes about 0.3 A from the cell, through the button and the bulb, and back.", focus: ["wires", "cell", "bulb"] },
    { view: "on", title: "The bulb lights", text: "The current heats the bulb's thin filament until it glows: about 0.45 W.", focus: ["bulb"] },
  ],
  details: [
    { view: "on", title: "The gap, closed", text: "The bridge sits on both posts while you hold the cap down.", around: ["bridge", "contacts"], focus: ["bridge", "contacts"] },
    { view: "on", title: "The bulb", text: "A thin filament in a glass globe, in a threaded socket.", around: ["bulb"], focus: ["bulb"] },
    { view: "on", title: "The cell", text: "A 1.5 V cell in a holder; a strap carries the top terminal down.", around: ["cell"], focus: ["cell"] },
  ],
};
