# Contributing

Thank you for helping. Machine Skill gets better in three ways: better machines, a better kit, and a sharper SKILL.md.

## A new example machine

1. Start from the one line. Put it in `prompt` exactly as typed.
2. Follow SKILL.md step by step, including the research block at the top of the script and at least four review rounds with `scripts/shot.mjs`.
3. Keep the kit linked while you work (`<script type="module" src="../kit/lab-kit.js">`), then run `node scripts/inline.mjs examples/<id>.html` so the file stands alone.
4. Add a poster (`examples/posters/<id>.jpg`, 1600 x 1000) and a film made with `scripts/record.mjs`. The recorder must finish with `pinkscan clean`.
5. In the pull request, state the operating point your solver reaches and the public figure you checked it against.

## Kit changes (`kit/lab-kit.js`)

- Every example must still load without errors and look the same or better. Run `node scripts/shot.mjs examples/<id>.html out/<id>.png` for all of them and attach before and after images.
- New features go behind an option with today's behaviour as the default.
- No build step and no runtime dependency other than three.js from the pinned CDN.

## House rules

- Real units, real proportions, real constants. A number on screen must come from a solver.
- Calm editorial writing: short sentences, units with a space (`338 kN`), no hype.
- No em dashes or en dashes in code, comments or copy.
- Be kind in issues and reviews.

## Reporting a problem

Open an issue with the one line you typed, the browser and GPU, a screenshot, and anything in the console.
