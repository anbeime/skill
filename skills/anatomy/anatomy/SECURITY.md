# Security

## What is in scope

Anatomy is a set of instructions, a drawing kit and local Node scripts. The scripts that start Chrome (`capture.mjs`, `drive.mjs`, `lines.mjs`, `turn-check.mjs`) run it headless with a throwaway profile and `--allow-file-access-from-files`, and `drive.mjs` runs JavaScript you pass it in the page. Point them only at pages you trust.

A security problem is anything in this repository that could let a page, a prompt or a file run code, read files or reach the network in a way the user did not ask for: in the kit, in the scripts, in the built example pages, or in instructions in `SKILL.md` and `references/` that would lead Claude to do something unsafe.

## Supported versions

Only the latest commit on `main` is supported.

## Reporting a vulnerability

Please don't open a public issue for a security problem. Report it privately through GitHub's [private vulnerability reporting](https://github.com/wheresryan22/anatomy/security/advisories/new) for this repository. If that link does not work, send a direct message to [@wheresryan22](https://x.com/wheresryan22) on X asking for a private channel, without the details.

Include what you found, how to reproduce it, and what it could let someone do.
