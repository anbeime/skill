/**
 * The home's way to the skill: one line by an empty hexagon. A hover draws the
 * hexagon's three inner edges, one after another, and it becomes a cube: the
 * words say "draw your own" and the mark does. CSS only.
 */
export function SkillLink() {
  return (
    <a className="skill-link" href="/skills">
      <svg viewBox="0 0 16 16" width="15" height="15" fill="none" strokeWidth="1.1" strokeLinejoin="round" strokeLinecap="round" aria-hidden="true">
        <path className="skill-link-hex" d="M8 1.5 13.6 4.75v6.5L8 14.5 2.4 11.25v-6.5z" />
        <path className="skill-link-edge" pathLength={1} d="M8 8 2.4 4.75" />
        <path className="skill-link-edge" pathLength={1} d="M8 8l5.6-3.25" />
        <path className="skill-link-edge" pathLength={1} d="M8 8v6.5" />
      </svg>
      <span>Or draw your own with the skill</span>
    </a>
  );
}
