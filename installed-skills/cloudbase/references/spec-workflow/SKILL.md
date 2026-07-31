---
name: spec-workflow
description: Standard software engineering workflow for requirement analysis, technical design, and task planning. Use this skill when developing new features, complex architecture designs, multi-module integrations, or projects involving database/UI design.
alwaysApply: false
---

## When to use this skill

Use this skill for **structured development workflow** when you need to:

- Develop new features from scratch
- Design complex architecture
- Integrate multiple modules
- Work on projects involving database design
- Work on projects involving UI design
- Ensure high-quality requirement analysis and acceptance criteria

**Do NOT use for:**
- Simple bug fixes
- Documentation updates
- Configuration changes
- Code refactoring (unless explicitly requested)

---

## How to use this skill (for a coding agent)

1. **Follow the workflow strictly**
   - Each phase must be completed and confirmed by user before proceeding to next phase
   - Never skip phases or proceed without user confirmation
   - Use `interactiveDialog` tool when clarification is needed

2. **Apply EARS requirement syntax**
   - Use EARS (Easy Approach to Requirements Syntax) for requirement descriptions
   - Format: `While <optional precondition>, when <optional trigger>, the <system name> shall <system response>`

3. **Reference UI design rules when needed**
   - If requirements involve frontend pages, must strictly reference `ui-design` skill
   - Determine design style and color palette in requirements phase
   - Confirm design details with user before finalizing requirements

4. **Update task status**
   - Keep task status updated in `tasks.md` file
   - Mark tasks as completed when finished
   - Work independently and efficiently while maintaining quality

---

# Spec Workflow

**Important: You must follow these rules. Each phase must be confirmed by the user before proceeding to the next phase.**

## Workflow Overview

1. If you determine that the user's input is a new requirement, you can work independently following standard software engineering practices. Confirm with user when necessary, and can use `interactiveDialog` tool to collect information.

2. Whenever the user inputs a new requirement, to standardize requirement quality and acceptance criteria, you must first understand the problem and requirements clearly. You must confirm with the user before proceeding to the next phase.

## Phase 1: Requirements Document and Acceptance Criteria Design

First complete the requirements design using EARS (Easy Approach to Requirements Syntax) method. If you determine the requirements involve frontend pages, **you must strictly reference `ui-design` skill**. Determine design style and color palette in the requirements phase. You must confirm requirement details with the user. After final confirmation, the requirements are finalized, then proceed to the next phase.

Save to `specs/spec_name/requirements.md`. After confirming with the user, proceed to the next phase.

**Reference format:**

```markdown
# Requirements Document

## Introduction

Requirement description

## Requirements

### Requirement 1 - Requirement Name

**User Story:** User story content

#### Acceptance Criteria

1. Use EARS syntax: While <optional precondition>, when <optional trigger>, the <system name> shall <system response>. For example: When "Mute" is selected, the laptop shall suppress all audio output.
2. ...
...
```

## Phase 2: Technical Solution Design

After completing the requirements design, based on the current technical architecture and the confirmed requirements above, design the technical solution. It should be concise but accurately describe the technical architecture (e.g., architecture, tech stack, technology selection, database/interface design, test strategy, security). Use mermaid diagrams when necessary.

Save to `specs/spec_name/design.md`. You must confirm with the user clearly, then proceed to the next phase.

## Phase 3: Task Breakdown

After completing the technical solution design, based on the requirements document and technical solution, break down specific tasks. You must confirm with the user clearly, then save to `specs/spec_name/tasks.md`. After confirming with the user, proceed to the next phase and begin formal task execution. You need to update task status in a timely manner. When executing, work as independently and autonomously as possible to ensure efficiency and quality.

**Task reference format:**

```markdown
# Implementation Plan

- [ ] 1. Task Information
  - Specific things to do
  - ...
  - _Requirement: Related requirement point number
```

## Phase 4: Task Execution

- Begin formal task execution
- Update task status in `tasks.md` file in real-time
- Work independently and autonomously
- Ensure efficiency and quality
- Mark tasks as completed when finished

## Key Principles

1. **User Confirmation Required**: Each phase must be confirmed by the user before proceeding
2. **EARS Syntax**: Use EARS method for requirement descriptions
3. **UI Design Integration**: When requirements involve frontend pages, must reference UI design rules and determine design style in requirements phase
4. **Technical Accuracy**: Technical solutions should be concise but accurate
5. **Task Tracking**: Keep task status updated throughout execution
6. **Independent Execution**: Work autonomously while maintaining quality

