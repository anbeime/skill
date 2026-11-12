# Validation Reference

Before handoff, verify:

- Dataset strategy selected and documented.
- User confirmed `plan.md` before formal analysis.
- Field semantics, metric definitions, time windows, and scale directions are confirmed or listed as assumptions.
- Source data preserved.
- Preprocessing actions logged.
- Analysis split into small, inspectable tasks.
- Visualization plan created before final chart generation.
- Key charts include interpretation and limitations.
- Findings include claim, evidence, artifact path, scope, limitation, confidence, and action.
- Reports and slides are built from structured artifacts.
- Claims do not exceed evidence.
- Output paths are predictable and included in the handoff summary.

Common failure modes:

- Treating descriptive correlations as causal proof.
- Cleaning data without recording changes.
- Running one monolithic script for the whole workflow.
- Generating chart galleries without narrative.
- Ignoring scale direction in questionnaire data.
- Comparing time periods with different coverage or leakage.
- Mixing live web collection into analysis without explicit permission.