/**
 * The pointer script each figure is put through, on the site (to capture the
 * goldens) and on the package (to compare). Points are in the figure's own
 * viewBox (400 × 320). `adv` is a count of 60 Hz frames on the virtual clock.
 */
export const FIGURES = ["riffle", "terrain", "exploded", "phosphor", "slow", "turntable"];

/** The option each figure has, and the value the script changes it to. */
export const OPTION = {
  riffle: ["stagger", 60], terrain: ["radius", 4], exploded: ["gap", 36],
  phosphor: ["afterglow", 900], slow: ["rate", 0.4], turntable: ["coast", 1000],
};

/** The intensity the package is set to at `set`: each maps exactly onto the value in OPTION (test/intensity.test.ts holds them together). */
export const INTENSITY = {
  riffle: 0.7, terrain: 0.75, exploded: 5 / 6,
  phosphor: 0.5 + 190 / 980, slow: 0.25, turntable: 0.5 + 175 / 850,
};

export const SCRIPTS = {
  riffle: [
    { adv: 30 }, { cp: "rest" },
    { move: [150, 120] }, { adv: 60 }, { cp: "pulled" },
    { set: true }, { move: [200, 100] }, { adv: 20 }, { cp: "stagger in flight" },
    { out: true }, { adv: 150 }, { cp: "left" },
    { focus: true }, { key: "ArrowLeft" }, { adv: 60 }, { cp: "arrow" },
    { key: "ArrowRight" }, { adv: 60 }, { cp: "arrow back" },
    { key: "Escape" }, { adv: 120 }, { cp: "escape" },
  ],
  terrain: [
    { adv: 30 }, { cp: "rest" },
    { move: [200, 160] }, { adv: 40 }, { cp: "raised" },
    { set: true }, { adv: 30 }, { cp: "wider" },
    { move: [150, 200] }, { adv: 10 }, { cp: "moving" },
    { out: true }, { adv: 150 }, { cp: "left" },
  ],
  exploded: [
    { adv: 30 }, { cp: "rest" },
    { move: [100, 80] }, { adv: 40 }, { cp: "opening" },
    { move: [180, 60] }, { adv: 40 }, { cp: "pick high" },
    { move: [180, 120] }, { adv: 40 }, { cp: "pick middle" },
    { move: [180, 190] }, { adv: 40 }, { cp: "pick low" },
    { set: true }, { adv: 40 }, { cp: "wider" },
    { out: true }, { adv: 150 }, { cp: "left" },
  ],
  phosphor: [
    { adv: 30 }, { cp: "loop" },
    { move: [240, 140] }, { adv: 2 }, { move: [260, 145] }, { adv: 2 }, { move: [280, 150] }, { adv: 20 }, { cp: "painted" },
    { set: true }, { out: true }, { adv: 30 }, { cp: "afterglow" },
    { adv: 240 }, { cp: "loop again" },
  ],
  slow: [
    { adv: 30 }, { cp: "rest" },
    { move: [200, 160] }, { adv: 60 }, { cp: "slowed" },
    { set: true }, { adv: 60 }, { cp: "less slow" },
    { out: true }, { adv: 150 }, { cp: "left" },
  ],
  turntable: [
    { adv: 30 }, { cp: "rest" },
    { move: [50, 176] }, { adv: 1 }, { move: [120, 176] }, { adv: 1 }, { move: [200, 176] }, { adv: 1 },
    { move: [280, 176] }, { adv: 1 }, { move: [350, 176] }, { adv: 6 }, { cp: "spinning" },
    { set: true }, { out: true }, { adv: 60 }, { cp: "coasting" },
    { adv: 360 }, { cp: "seated" },
  ],
};
