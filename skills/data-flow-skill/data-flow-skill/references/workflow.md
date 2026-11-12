# Workflow Reference

Data Flow Skill follows this stage order:

1. Confirm dataset path, task goal, audience, deliverables, language, and style.
2. Detect dataset strategy and save `output/artifacts/dataset_detection.json`.
3. Draft `plan.md` and wait for user confirmation.
4. Profile raw data and save `output/artifacts/data_profile.json`.
5. Preprocess transparently and log changes.
6. Run analysis in small, inspectable task units.
7. Create `output/artifacts/visualization_plan.json` before final charts.
8. Save evidence-backed findings to `analysis_findings.json`.
9. Build reports and slides from validated artifacts.
10. End with a concise handoff summary.

`plan.md` should include objective, audience, dataset summary, detected strategy, assumptions, preprocessing plan, analysis tasks, visualization outline, expected outputs, risks, and validation checkpoints.