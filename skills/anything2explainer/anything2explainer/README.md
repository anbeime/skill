# anything2explainer

[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-D97757?logo=anthropic&logoColor=white)](https://claude.com/claude-code)
[![Codex](https://img.shields.io/badge/Codex-skill-000000)](https://openai.com/codex)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-0B84F3)](https://remotion.dev)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-informational)](LICENSE)

**English** | [简体中文](README_ZH.md)

**Topic in, narrated explainer video out.** anything2explainer is a [Claude Code](https://claude.com/claude-code) / [Codex](https://openai.com/codex) skill that turns any topic into a black-canvas motion-graphics explainer video with TTS voiceover, subtitles and a chapter progress bar, in Chinese or English. Every frame is drawn in code with [Remotion](https://remotion.dev) (React + TypeScript). No stock footage, no generative video model, no frames lifted from anyone else's work.

It is not a CLI. What ships here is the whole method an AI coding agent needs to finish the film: a compilable Remotion template, a primitives and lighting library, tooling for voiceover / storyboard / rendering / quantitative QC, written style and motion specs, a multi-agent division-of-labour protocol, and one complete reference film as the quality bar.

**English cut** — *RAG & Knowledge Bases*, 5′02″, 44 lines / 785 words, voiced by kokoro-82m `am_liam` at natural speed:

https://github.com/user-attachments/assets/e2771c68-a28c-4459-ac5a-a5b685181eeb

**Chinese cut** — *RAG 与知识库* v2, 4′54″, 44 lines / 1490 characters, dot-field backdrop (`bg: 'dots'`), voiced through the bring-your-own-TTS path (Volcengine TTS 2.0 + forced alignment):

https://github.com/user-attachments/assets/5c213990-cbba-439e-8371-fbb3aa348e05

Both cuts share one storyboard and 44 shots; the English cut re-times every shot to the English voiceover. The full paper trail of the original Chinese cut (4′35″, star-field backdrop, 8 build agents in parallel for 40 minutes, two QC rounds) lives in [`examples/rag/`](examples/rag/) (research → narration → storyboard → shot source → QC reports → delivery notes); rendered frames are in [`examples/rag/frames/`](examples/rag/frames/).

## What it does

- **Input**: a topic ("explain vector databases"), or an article / document you want turned into a video. You also pick the length and the language.
- **Output**: a 1280×720 H.264 MP4 with synchronized voiceover, word-boundary-aligned subtitles, chapter cards, a top HUD and a bottom chapter progress bar, plus the full paper trail (research doc with sources, narration, storyboard, per-shot source code, QC reports).
- **How**: the agent researches the topic with sources, writes the narration, generates the voiceover and frame-accurate timeline, storyboards every shot, then dispatches parallel build agents that write one Remotion component per shot. QC agents review the rendered frames against written criteria before delivery.
- **Time**: roughly 1 to 3 hours of wall clock depending on length, most of it agents building shots in parallel. You are consulted at exactly four checkpoints.

## Output spec

| | |
|---|---|
| Frame / rate | 1280×720 @ 30fps, H.264 |
| Length | your call (see table below); 2–8 minutes all work |
| Language | Chinese or English (`lang` in `src/config.ts`); typography, subtitle budgets and TTS switch with it |
| Look | black canvas with one of two backdrops, star field + fog gradient or dot-field wave (`bg` in `src/config.ts`; the dot-field wave is ported from video-talkcraft); white line art + purple accents; ultra-bold headline type |
| Persistent layers | 44px white-on-black-stroke subtitles, bottom chapter progress bar, top capsule HUD, optional pipeline rail, `built by Anything2Explainer skill` end credit (`builtBy`, set to `''` to drop) |
| Voiceover | Chinese: edge-tts `zh-CN-YunxiNeural` (Yunxi, male, unmodified rate ≈5.5 chars/s). English: kokoro-82m `am_liam` (Liam, male). Or bring your own TTS / finished audio |

Length drives how much ground the film covers, and the size of the whole pipeline:

| Length | Chinese chars | English words | Lines / shots | Build agents | Wall clock | Disk |
|---|---|---|---|---|---|---|
| 2–3 min | 650–880 | 280–420 | 24–32 | 4–6 | ≈1 h | ≈2 GB |
| 3–5 min (reference tier) | 1100–1400 | 420–700 | 40–50 | 8 | ≈2 h | ≈2 GB |
| 5–8 min | 1650–2200 | 700–1150 | 60–80 | 10–14 | ≈2–3 h | ≈3 GB |

Chapter count follows the content, within limits set by length: under 3 minutes use a single chapter (no chapter cards), 3–5 minutes 3–4 chapters of at least 60 s each, 5–8 minutes 4–6. The progress bar splits evenly across however many chapters the narration declares. A blank line in the narration marks a paragraph, which is also one shot: sentences inside a paragraph are separated by 10 frames, paragraph ends by 30, so the pause lands where the picture changes and every shot holds 1–1.5 s after its last element lands. The finished video runs 5–8% longer than the raw speech by design.

## Install

```bash
git clone https://github.com/Vincentwei1021/anything2explainer.git
ln -s "$PWD/anything2explainer" ~/.claude/skills/anything2explainer   # Claude Code
ln -s "$PWD/anything2explainer" ~/.codex/skills/anything2explainer    # Codex
```

Dependencies:

```bash
# Node ≥18 (the template's npm install pulls remotion 4.0.507 / react 19)
brew install ffmpeg          # frame extraction / transcoding, required

python3 -m venv ~/.venvs/a2e && source ~/.venvs/a2e/bin/activate
pip install 'edge-tts==7.2.8' numpy pillow scipy   # pin edge-tts: it tracks a Microsoft endpoint and breaks across upgrades (7.2.0+ needs word boundaries requested explicitly; the script does)

# only needed for English narration (kokoro-82m runs locally)
pip install kokoro soundfile && brew install espeak-ng
```

`scipy` is only used by the QC script `frame_metrics.py`. The shell scripts are zsh + Python 3, developed and verified on macOS; Linux should work, Windows is untested.

### Linux / Raspberry Pi (ARM)

Verified on a Raspberry Pi 5 (ARM64, Python 3.13). Three things differ from macOS:

```bash
sudo apt install zsh espeak-ng                 # scripts are #!/bin/zsh; espeak-ng for kokoro/piper G2P

# Remotion has no linux-arm64 headless browser → point it at system Chromium:
sudo apt install chromium                       # or chromium-browser
export REMOTION_BROWSER_EXECUTABLE=/usr/bin/chromium   # read by template/remotion.config.ts (no-op on macOS)
```

**TTS on Linux/ARM.** `kokoro` (the default English engine) is hard to install on ARM/Python 3.13 (it pins an old numpy and pulls spaCy → blis, which lack aarch64 wheels). Two local engines that install cleanly instead — pass one via `TTS_ENGINE`:

```bash
# kokoro_onnx — natural voice, onnxruntime (no torch/spaCy). Download model + voices from
#   github.com/thewh1teagle/kokoro-onnx releases (kokoro-v1.0.onnx, voices-v1.0.bin)
pip install kokoro-onnx
TTS_ENGINE=kokoro_onnx KOKORO_ONNX_MODEL=…/kokoro-v1.0.onnx KOKORO_ONNX_VOICES=…/voices-v1.0.bin \
  KOKORO_ONNX_VOICE=am_michael python3 scripts/tts_build.py

# piper — fastest local, robotic; a Pi-native fallback. Voice .onnx from github.com/rhasspy/piper
pip install piper-tts
TTS_ENGINE=piper PIPER_MODEL=…/en_US-ryan-medium.onnx python3 scripts/tts_build.py
```

The `edge` engine (natural, free, word-boundary timing) also works on Linux and needs no local model — it's a cloud call to Microsoft: `TTS_ENGINE=edge VOICE=en-US-AndrewNeural python3 scripts/tts_build.py`.

## Usage

In Claude Code or Codex, just say what you want. The skill triggers itself:

> Make me an explainer video about vector databases.

> 讲一下向量数据库，做成一条讲解视频

It then walks the 9 stages in `SKILL.md`:

1. **Scaffold** the Remotion project from the template.
2. **Research** (1 agent): a sourced research doc with a list of numbers and analogies, every item with a URL.
3. **Narration & timeline**: the script, then TTS voiceover with per-word boundaries turned into a frame-accurate timeline and subtitle table.
4. **Storyboard**: one line per shot with frame range, beat, visuals, motion, hero element and lighting.
5. **Overlays & primitives**: title, chapter cards, HUD, pipeline rail, plus 2–5 topic-specific icons.
6. **Pilot** (1 agent): the first shot group, then a 30-second cut for you to judge the look.
7. **Parallel build**: the remaining groups, 5–7 shots per agent, each writing pure-function Remotion components.
8. **Render** the full film and run quantitative frame metrics.
9. **QC & fixes**: one QC agent per chapter, fix agents per group, re-verification, then delivery notes.

You can also drive the template by hand:

```bash
template/scripts/new_project.sh ~/work/my-video myslug
cd ~/work/my-video
# 1. research/调研.md          2. script/narration.txt → python3 scripts/tts_build.py
# 3. script/storyboard_src.md → python3 scripts/render_storyboard.py     4. edit src/config.ts
# 5. src/shots/G1..Gn          6. scripts/preview.sh 30   (first 30 seconds)
# 7. VER=v1 scripts/render.sh + python3 scripts/frame_metrics.py         8. QC → fix → v2/v3
```

## Four checkpoints

The run stops and waits for you at exactly four points instead of ploughing through (details in `SKILL.md`):

1. **Length and language**: before the script is written. Length decides the line count, shot count and how many agents run in parallel, i.e. how much the film can actually cover; language flips `lang` in `src/config.ts`, which drives typography, subtitle budgets and the default voice.
2. **Narration sign-off**: before voiceover. Once locked, frame numbers are hard-coded into every shot; changing one word re-times the whole film. This is the cheapest place to intervene.
3. **Voiceover**: before TTS runs you get asked whether you have a preferred engine. If not, defaults apply (edge-tts Yunxi for Chinese, kokoro-82m Liam for English). You can also hand over finished audio and fill the per-line timeline yourself.
4. **First 30 seconds**: only the first build group is done, then 30 seconds get rendered for you to judge the look. Fixing the style here costs one group; after the full render it costs every group.

## How it compares

| Tool class | What it produces | Where anything2explainer differs |
|---|---|---|
| Generative video models (Sora, Veo, Runway) | Footage synthesized from a prompt | Deterministic code, not pixels. Every number on screen traces to a source URL, and any frame can be fixed by editing one shot file |
| Avatar / presenter tools (HeyGen, Synthesia) | A digital presenter reading a script | No presenter. Motion-graphics diagrams that show the mechanism, with the narration driving the visuals |
| Remotion or Motion Canvas by hand | A programmable video canvas | Ships the method on top of the canvas: research → narration → storyboard → parallel build → QC, with style specs, motion vocabulary and a reference film to match |
| Manim | Python mathematical animations | An agent-driven end-to-end pipeline with TTS-aligned subtitles, chapters and QC; React / TypeScript rather than Python |

## FAQ

**Which AI coding agents does it work with?**
It is written for Claude Code and Codex, and those two are what it has been run with. The skill itself is plain Markdown plus a Remotion project, so any agent that reads `SKILL.md`-style skill folders and can run shell commands should be able to follow it.

**Does it need a GPU?**
No. Remotion renders through headless Chromium on the CPU. The Chinese default voice (edge-tts) is a cloud call to a Microsoft endpoint; the English default (kokoro-82m) is an 82M-parameter model that runs locally on CPU.

**Can I use my own voice or a different TTS?**
Yes. Put the finished audio at `public/assets/<slug>/audio.wav` and fill `src/common/timeline.ts` and `subs.ts` by hand (format documented at the top of `tts_build.py`). Everything downstream is unchanged.

**Can I change the visual style?**
There is one visual style, on purpose, with a single switch: the backdrop, `bg` in `src/config.ts` (`'dots'` dot-field wave by default, `'stars'` star field with fog). To change anything else, edit `reference/style-guide.md` and `src/ui.tsx`; the shot code only uses those primitives.

**Are the renders reproducible?**
Yes. Every animation is a pure function of the frame number with seeded randomness, and text fitting is computed rather than measured in the DOM, so re-rendering produces identical frames.

**Can I use it commercially?**
The toolkit is licensed under PolyForm Noncommercial: free for noncommercial use, commercial use requires prior authorization from the author. The videos you make with it are yours. See [License](#license).

**Does it do vertical (9:16) video?**
Not currently. The template and every safe-area rule assume 1280×720 landscape.

**Which languages?**
Chinese and English. Each has its own pacing model, subtitle budget and default voice. Both cuts are embedded at the top of this page; the written paper trail in `examples/rag/` is from the Chinese cut.

## Repo layout

```
SKILL.md                  the process: 9 stages, four checkpoints, quality bar
reference/                specs written for the main session and the agents
  style-guide.md            safe areas, palette, fonts, primitive catalogue, layout habits
  motion-vocabulary.md      entrance / emphasis / light / exit / camera formulas and frame counts
  composition-and-light.md  three size tiers, light follows the hero, set-piece choreography, QC metrics
  narration-storyboard.md   how to write narration, voiceover params, storyboard tokens, shot pattern table
  research-brief.md         researcher prompt and fact rules
  agent-build-rules.md      build-agent protocol
  agent-qc-rules.md         QC-agent protocol
  prompts.md                six prompt templates: research / build / QC / fix / recheck / final pass
  lessons.md                every trap hit across three films, with root causes
template/                 the compilable Remotion 4 project (copy it with scripts/new_project.sh)
  src/common/               fog, star field, dot-field wave, glitch, easings, subtitles, progress bar, footage layer
  src/ui.tsx  src/fx.tsx    primitives and palette / light, depth and camera primitives
  src/overlay/              title, chapter cards, HUD, pipeline rail, ending
  scripts/                  voiceover, storyboard, stills, test render, 30s preview, full render, QC metrics
  public/fonts/             four fonts + their OFL license
examples/rag/             the reference film's full paper trail and rendered frames
examples/contrast/        6 bad/good frame pairs — the yardstick for composition and light
```

## Acknowledgements

The visual language and the quality bar are inspired by the Douyin creator **@图灵宇宙** — black canvas, white line art with purple accents, ultra-bold headline type: that vocabulary was learned from their videos. Everything in this repo is drawn from scratch in code; none of their frames, assets or project files are used. If you feel this crosses a line, please open an issue.

## Originality

- **Every frame is drawn in code.** No frames or clips from existing videos. Optional live-action B-roll must come from royalty-free sources and be logged in a MANIFEST (sha256 / source URL / license / usage).
- **Every fact is sourced.** Every number, year, organisation and English term shown on screen must trace back to a source URL in that film's research document. Anything unverified stays off the screen and out of the narration.

## License

The toolkit: [PolyForm Noncommercial 1.0.0](LICENSE) — free for noncommercial use; commercial use requires prior authorization from the author. **Videos you make with it are yours.**
The four bundled fonts (Noto Sans SC / Orbitron / Exo 2 / Audiowide) are licensed separately under SIL OFL 1.1; see [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md).
Remotion itself has its own license terms for companies — see [remotion.dev/license](https://remotion.dev/license).

## Known limits

- Chinese and English are both supported (`lang: 'zh' | 'en'`), each with its own pacing, subtitle budget (16 chars / 48 characters per block) and default voice. Both cuts are embedded above; the paper trail in `examples/rag/` is from the Chinese cut. One visual style with two backdrops (`bg: 'stars' | 'dots'`); changing anything else means editing `reference/style-guide.md` + `src/ui.tsx`.
- Not for: replicating an existing video, talking-head presenter footage, or films that are mostly live action.
- Once the narration is voiced, the words are frozen — shot code hard-codes frame numbers, so a rewrite re-times everything.
- Parallel builds are demanding: several agents bundle Remotion at once, so keep ≥5 GB free; tmux panes are capped, so past ~12 you have to dispatch in waves.

## Star History

<a href="https://www.star-history.com/?type=date&repos=Vincentwei1021%2Fanything2explainer">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=Vincentwei1021/anything2explainer&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=Vincentwei1021/anything2explainer&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=Vincentwei1021/anything2explainer&type=date&legend=top-left" />
 </picture>
</a>
