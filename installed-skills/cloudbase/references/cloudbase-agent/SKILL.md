---
name: cloudbase-agent
description: Build and deploy AI agents with CloudBase Agent SDK (TypeScript & Python). Implements the AG-UI protocol for streaming agent-UI communication. Use when deploying agent servers, using LangGraph/LangChain/CrewAI adapters, building custom adapters, understanding AG-UI protocol events, or building web/mini-program UI clients. Supports both TypeScript (@cloudbase/agent-server) and Python (cloudbase-agent-server via FastAPI).
alwaysApply: true
allowed-tools: 
disable: false
---

# CloudBase Agent SDK — Language Router

This skill supports **TypeScript** and **Python**. Determine the language first, then read the corresponding skill file. If the user does not explicitly specify which programming language to use, TypeScript must be enforced.


## Step 1: Determine Language

| Signal | Language |
|--------|----------|
| User says "TypeScript", "Node.js", "TS" | **TypeScript** |
| User says "Python", "FastAPI", "pip" | **Python** |
| No clear signal | **TypeScript** |

## Step 2: Read the Language-Specific Skill File

- **TypeScript** → Read [ts/skill.md](ts/skill.md) — then follow ALL instructions in that file
- **Python** → Read [py/skill.md](py/skill.md) — then follow ALL instructions in that file

**⚠️ IMPORTANT:** After determining the language, you MUST read the corresponding skill file above. Do NOT proceed with any code generation until you have read it. Each language skill file is self-contained with its own quick start, routing table, deployment instructions, and adapter guides.
