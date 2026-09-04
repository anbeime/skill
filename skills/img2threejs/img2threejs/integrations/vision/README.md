# Optional local vision adapters

This environment adds SAM2 masks, Depth Anything V2 relative-depth priors, and MediaPipe
face/pose landmarks without adding dependencies to the stdlib-only `forge` core.

Install and prefetch:

```bash
uv sync --project integrations/vision --python 3.11
python3 forge/stage1_intake/run_vision_adapter.py prefetch
python3 forge/stage1_intake/run_vision_adapter.py health
```

Use:

```bash
python3 forge/stage1_intake/run_vision_adapter.py \
  segment reference.png --point 512 320 --out evidence/subject-mask.png

python3 forge/stage1_intake/run_vision_adapter.py \
  depth reference.png --out evidence/relative-depth.png

python3 forge/stage1_intake/run_vision_adapter.py \
  landmarks face reference.png --out evidence/face-landmarks.json

python3 forge/stage1_intake/run_vision_adapter.py \
  landmarks pose reference.png --out evidence/pose-landmarks.json
```

Every command emits provenance and an evidence boundary. SAM2 masks still require agent
confirmation that the intended component was selected. Depth is relative, not metric, and cannot
justify hidden geometry. MediaPipe landmarks require anatomy review before they enter the sculpt
spec.

The environment and models are local-only:

- environment: `integrations/vision/.venv/`
- Hugging Face cache: `runtime/vision/huggingface/`
- MediaPipe task models and manifest: `runtime/vision/models/`

See `docs/integrations/reference_fidelity_tooling.md` for pipeline routing and MCP usage.
