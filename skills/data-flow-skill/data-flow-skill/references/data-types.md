# Dataset Type Reference

## `tabular_generic`

Use for structured CSV, TSV, XLSX, JSON tables, analytics exports, keyword sheets, ranking tables, content inventories, and business metrics.

## `questionnaire`

Use for surveys, scales, feedback forms, and mixed closed/open-ended responses. Confirm scale direction, response coding, skip logic, and grouping variables.

## `time_series`

Use when date/time is central: daily metrics, ranking trends, traffic logs, revenue by period, or repeated observations. Confirm time zone, granularity, gaps, and period comparability.

## `literary`

Use for novels, poems, scripts, dialogues, essays, lyrics, and other text corpora. Confirm corpus boundaries, metadata, segmentation units, and interpretation scope.

## Detection Artifact

`dataset_detection.json` should record `strategy`, `confidence`, `evidence`, `alternatives`, `assumptions`, and `fallback_plan`.