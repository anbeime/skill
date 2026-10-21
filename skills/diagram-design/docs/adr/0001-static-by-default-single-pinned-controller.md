# ADR 0001 — Static by default; one pinned controller for motion

**Status:** accepted (v2.3)

## Context

Diagrams are shared as single HTML files and embedded in posts, decks, and docs. Arbitrary inline JavaScript in a shareable artifact is both a security surface and a review burden: every generated file would need its script audited. Motion, however, genuinely clarifies ordered change (queues filling, policy traces diverging).

## Decision

Output is static and script-free by default (`data-motion-mode="none"`). When motion is requested, the file may carry exactly one `<script data-diagram-controls>` block whose body must byte-match the reviewed controller in `assets/template-motion.html`. The match is enforced twice: SHA-256 in `lint-skin.py` and string equality in `verify-motion.py`; the packaged `scripts/self_check.py` repeats the check for installed agents.

## Consequences

- Any behavior change to motion is a change to `template-motion.html`, reviewed once, and re-propagated verbatim; hand-edited controllers fail every gate.
- The controller cannot be extended per-diagram. A diagram needing bespoke interaction is out of scope for this skill.
- The check anchors to the template in the same commit, so a PR that weakens template and copies together still passes the identity check — reviewer attention on `template-motion.html` diffs is the real gate.
