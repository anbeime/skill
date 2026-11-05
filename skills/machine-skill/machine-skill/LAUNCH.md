# Launch

Everything here is ready locally. Nothing has been pushed to GitHub. These are the steps that are yours.

## 1. Publish the repository (10 minutes)

```sh
cd "~/Documents/Airsup Main/airsup-lab-skill"
gh repo create AirsupHQ/machine-skill --public --source . --push --description "Describe any machine in one line. Claude builds a photoreal, physics based, interactive simulation of it in one HTML file, plus the film to post it. An open source Claude Code skill."
gh repo edit AirsupHQ/machine-skill --homepage https://airsup.ai/lab/skill --add-topic claude,claude-code,agent-skills,claude-skill,anthropic,threejs,webgl,simulation,physics,engineering,mechanical-engineering,interactive,explainer,cutaway,education,product-visualization
```

If you publish under another owner or name, replace `AirsupHQ/machine-skill` in: README.md, film/launch.html (`CMD`), and on the site in `plm-app/rocket-engine/skill.html` (two places). Then re-record the end card of the launch film (`node scripts/record.mjs film/launch.html out/launch.mp4 --from 34`), or the whole film.

Then on GitHub:

- Settings, General, Social preview: upload `.github/assets/social.jpg`.
- Pin the repo on your profile.
- Check that the README hero (`.github/assets/hero.webp`) plays and the gallery images load.
- Run the install once on a clean machine: `npx skills add AirsupHQ/machine-skill -g -a claude-code`, then `/machine a hand crank pencil sharpener` in Claude Code.

## 2. Post on X

**When:** a weekday, 8:00 to 9:30 in San Francisco (17:00 to 18:30 CET). One hero post that day, nothing else from the lab.

The post copy, reply clips and prepared answers are in `~/Documents/New sims/38 Machine Skill (open source)/post.md`. Order:

1. Main post with `launch.mp4` (no link, no hashtags).
2. Reply 1 within a minute: the GitHub link, the install command and the live gallery link.
3. Replies 2 to 5 over the first hour: one machine clip each (turbofan break, rocket engine burn-through, watch, heart pump), each with its one line.
4. Reply 6: the Claude Code usage screenshot for the build (time, tokens, cost), "typos and all" prompt.
5. Next day: quote your own post with one claim line (see post.md), no link.

## 3. Show it where builders look (same day, after X)

- Hacker News, Show HN: "Show HN: Machine Skill, describe a machine in one line and Claude builds a physics simulation" with the GitHub link. Be in the thread for two hours.
- r/ClaudeAI and r/threejs: the launch film plus the repo link, written as "here is how it works", not an ad.
- The Claude Code skills directories that accept submissions (agentskills.io, the skills CLI registry), one line description from `.github/REPO.md`.
- Reply to the Anatomy thread only if it is natural (a kind word to Ryan, link in your reply, not a dunk).

## 4. Keep it alive for three days

- Day 1 evening and day 2: a new machine clip as a reply each time someone asks for one ("built your request: ..."). Build them live with the skill; it takes about an hour each.
- Answer every reply on day 1. Replies weigh more than likes.
- Day 3: a short thread on how the cutaway works (the section face shader paragraph in the README) for the technical crowd.

## Before you post: checklist

- [ ] `gh repo view AirsupHQ/machine-skill --web` shows the README with the hero and gallery
- [ ] airsup.ai/lab/skill loads, the film plays, every machine opens live
- [ ] `npx skills add AirsupHQ/machine-skill` works on a clean machine
- [ ] Build stats in post.md filled from your Claude Code usage
