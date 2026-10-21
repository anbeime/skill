# ADR 0003 — `reveal` is the only sanctioned autoplay

**Status:** accepted (v2.3, clarified after review)

## Context

The motion contract lists "autoplay on load" as an anti-pattern, yet the canonical controller starts a `reveal` run on load. Early drafts of `animation.md` stated both without reconciling them, which reads as a contradiction to anyone copying the template.

## Decision

`reveal` mode may run **once** on initial load — it exists for short ordered explanations where a click-to-start would be friction — and then remains complete. It never restarts on viewport re-entry, tab return, or without an explicit Replay action. Every other mode is user-initiated (`step`) or CSS-scoped (`loop`); `none` stays inert. Under `prefers-reduced-motion: reduce` and without JavaScript, all modes show the complete static frame.

## Consequences

- The anti-pattern is precisely "repeated or attention-trapping autoplay," not "any motion before interaction."
- `verify-motion.py` needs no autoplay heuristic: the pinned controller is the only code that can start a run, and it implements exactly this policy.
